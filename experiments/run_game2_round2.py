"""Separate Game 2 population effects, retrain responses, and test fresh opponents."""

import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from blotto.game2_population import (
    baseline_populations,
    candidate_pool,
    concentrated_by_count,
    concentration_mixture,
    mix_populations,
    population,
)
from blotto.game2_search import (
    evaluate_scenarios,
    finite_reasoning,
    independent_evaluation,
    maximum_regrets,
    neighbors,
    response_search,
    shortlist_indices,
)
from experiments.run_game2 import PROFILES, save_json, scenario, summarize_results, validate


def load_previous():
    folder = Path("results/game2")
    results = json.loads((folder / "combined_comparison.json").read_text())
    index = json.loads((folder / "population_index.json").read_text())
    followup = json.loads((folder / "followup_design.json").read_text())
    scenarios = {}
    for filename, entries in [
        ("populations.npz", index["validation"]),
        ("followup_populations.npz", followup["population_index"]),
    ]:
        with np.load(folder / filename) as saved:
            for name, prefix in entries.items():
                scenarios["previous/" + name] = {
                    "allocations": saved[prefix + "_allocations"],
                    "weights": saved[prefix + "_weights"],
                }
    candidates = {name: row["allocation"] for name, row in results["summary"].items()}
    candidates["round1_robust"] = candidates.pop("new_robust")
    references = np.array([row["reference"] for row in results["scenarios"].values()])
    return scenarios, candidates, references


def build_models(pool, rng, args, fresh=False):
    """Share H/T and conditional C supports while changing exact mixture weights."""
    anchor_seed = int(rng.integers(2**32))
    anchors = baseline_populations(args.population_samples, anchor_seed)
    models, metadata = {}, {}
    shares = [0.10, 0.25, 0.40] if fresh else [0.05, 0.15, 0.30, 0.45]
    all_in_fractions = [0.20, 0.80] if fresh else [0.50]
    for profile in PROFILES:
        conditional_seed = int(rng.integers(2**32))
        response_seed = int(rng.integers(2**32))
        for bids in ["low", "high"]:
            conditional = concentrated_by_count(
                args.population_samples, conditional_seed, profile, bids
            )
            settings = [(a, z) for a in shares for z in all_in_fractions]
            if not fresh and bids == "low":
                # Matched control measures the newly explicit all-in branch.
                settings.append((0.15, 0.0))
            for alpha, z in settings:
                key = f"{profile}/{bids}/single{alpha:.2f}/allin{z:.2f}"
                base = {**anchors, "C": concentration_mixture(conditional, alpha, z)}
                levels, diagnostics = finite_reasoning(
                    base,
                    pool,
                    np.random.default_rng(response_seed),
                    depth=4,
                    screen=args.response_screen,
                    check=args.response_check,
                )
                base["levels"] = levels
                models[key] = base
                c = base["C"]
                metadata[key] = {
                    "profile": profile,
                    "bids": bids,
                    "single_share": alpha,
                    "all_in_fraction": z,
                    "anchor_seed": anchor_seed,
                    "conditional_parameters": conditional["parameters"],
                    "response_seed": response_seed,
                    "reasoning": diagnostics,
                    "C_exact_100_fifth_mass": float(
                        c["weights"][c["allocations"][:, 4] == 100].sum()
                    ),
                }
                print(
                    f"  {'Fresh' if fresh else 'Training'} model {len(models)}: {key}",
                    flush=True,
                )
    return models, metadata


def depth_weights(depth):
    # The deeper mixture replaces half of S3 by the new fourth level.
    return [0.15, 0.35, 0.50, 0] if depth == 3 else [0.075, 0.175, 0.25, 0.50]


def build_scenarios(models, model_metadata, fresh=False):
    scenarios, metadata = {}, {}
    settings = (
        [("T_A", 0.0, 0.80, 0.30, 0.80), ("T_B", 0.10, 0.50, 0.60, 0.20)]
        if fresh
        else [
            ("central", 0.05, 0.65, 0.20, 0.50),
            ("T_heavy", 0.0, 0.80, 0.40, 0.50),
            ("C_heavy", 0.10, 0.50, 0.0, 0.50),
        ]
    )
    for model, base in models.items():
        for depth in [3, 4]:
            for label, h, s, t, a in settings:
                key = f"{model}/depth{depth}/{label}"
                scenarios[key], description = scenario(
                    base, h, s, t, a, depth_weights(depth)
                )
                metadata[key] = {
                    "model": model,
                    "depth": depth,
                    "mixture": label,
                    **{
                        k: model_metadata[model][k]
                        for k in ["profile", "bids", "single_share", "all_in_fraction"]
                    },
                    **description,
                }
    return scenarios, metadata


def select(pool, scenarios, old_candidates, rng, args):
    print(
        f"Search {len(pool):,} allocations across {len(scenarios)} development scenarios",
        flush=True,
    )
    scores = evaluate_scenarios(pool, scenarios, args.search_screen, rng)
    order = np.argsort(maximum_regrets(scores))
    refined = np.unique(
        np.vstack(
            [
                pool[shortlist_indices(scores, robust_count=48, per_scenario=3)],
                neighbors(pool[order[:10]]),
                neighbors(pool[np.unique(scores.argmax(axis=0))], steps=(1, 2)),
                np.array(list(old_candidates.values())),
            ]
        ),
        axis=0,
    )
    print(f"  Refine {len(refined):,} allocations", flush=True)
    scores = evaluate_scenarios(refined, scenarios, args.search_refine, rng)
    finalists = np.unique(
        np.vstack(
            [
                refined[shortlist_indices(scores, robust_count=48, per_scenario=2)],
                np.array(list(old_candidates.values())),
            ]
        ),
        axis=0,
    )
    print(f"  Calibrate {len(finalists):,} finalists", flush=True)
    scores = evaluate_scenarios(finalists, scenarios, args.search_calibration, rng)
    regrets = maximum_regrets(scores)
    chosen = finalists[regrets.argmin()]
    candidates = {**old_candidates, "round2_robust": chosen.tolist()}
    summary = {
        "pool_count": len(pool),
        "refined_count": len(refined),
        "finalist_count": len(finalists),
        "scenario_count": len(scenarios),
        "selected": chosen.tolist(),
        "maximum_training_regret": float(regrets.min()),
        "frozen_candidates": candidates,
    }
    for name, allocation in candidates.items():
        index = np.flatnonzero(np.all(finalists == allocation, axis=1))[0]
        summary.setdefault("candidate_training_regrets", {})[name] = float(
            regrets[index]
        )
    return candidates, finalists, scores, summary


def add_stresses(models, pool, candidates, rng, args):
    scenarios, metadata = {}, {}
    targets = {}
    for name in ["all_fifth", "round1_robust", "round2_robust"]:
        targets.setdefault(tuple(candidates[name]), name)
    for profile in PROFILES:
        model = f"{profile}/low/single0.25/allin0.80"
        q, description = scenario(
            models[model], 0.05, 0.65, 0.20, 0.50, depth_weights(4)
        )
        for allocation, target in targets.items():
            copied = population([allocation])
            for share in [0.05, 0.15]:
                predicted = mix_populations([q, copied], [1 - share, share])
                responses, diagnostic = response_search(
                    pool, predicted, rng, args.response_screen, args.response_check
                )
                for kind, extra in [("copy", copied), ("anticipate", responses)]:
                    key = f"stress/{profile}/{target}/{kind}{share:.2f}"
                    scenarios[key] = mix_populations([q, extra], [1 - share, share])
                    metadata[key] = {
                        "base_model": model,
                        "base_mixture": description,
                        "target": list(allocation),
                        "extra_type": kind,
                        "extra_share": share,
                        "response_search": diagnostic,
                    }
        # Some smart players predict the wrong popularity of castle 5.
        other_profile = {
            "balanced": "fifth_crowded",
            "fifth_crowded": "fifth_avoided",
            "fifth_avoided": "fifth_crowded",
        }[profile]
        belief = f"{other_profile}/low/single0.25/allin0.80"
        for fraction in [0.50, 1.0]:
            level_mixes = [
                mix_populations([ours, theirs], [1 - fraction, fraction])
                for ours, theirs in zip(
                    models[model]["levels"], models[belief]["levels"]
                )
            ]
            mistaken = {**models[model], "levels": level_mixes}
            key = f"belief/{profile}/wrong{fraction:.2f}"
            scenarios[key], description = scenario(
                mistaken, 0.05, 0.65, 0.20, 0.50, depth_weights(4)
            )
            metadata[key] = {
                "actual_model": model,
                "believed_model": belief,
                "fraction_of_S_with_other_belief": fraction,
                **description,
            }
    return scenarios, metadata


def save_populations(folder, filename, scenarios):
    arrays, index = {}, {}
    for i, (name, q) in enumerate(scenarios.items()):
        prefix = f"p{i:04d}"
        index[name] = prefix
        arrays[prefix + "_allocations"] = q["allocations"]
        arrays[prefix + "_weights"] = q["weights"]
    np.savez_compressed(folder / (filename + ".npz"), **arrays)
    save_json(folder, filename + "_index.json", index)


def factorial_diagnostics(candidates, models, metadata, rng, args):
    """Measure fixed strategies on matched central scenarios, without selecting them."""
    scenarios, descriptions = {}, {}
    for name, base in models.items():
        for depth in [3, 4]:
            key = f"{name}/depth{depth}"
            scenarios[key], description = scenario(
                base, 0.05, 0.65, 0.20, 0.50, depth_weights(depth)
            )
            descriptions[key] = {
                **{
                    k: metadata[name][k]
                    for k in ["profile", "bids", "single_share", "all_in_fraction"]
                },
                "depth": depth,
                **description,
                "C_exact_100_fifth_mass": metadata[name]["C_exact_100_fifth_mass"],
            }
    rows = np.array(list(candidates.values()))
    measurements = []
    for i, (name, q) in enumerate(scenarios.items(), 1):
        measurements.append(
            independent_evaluation(
                rows, candidates["all_fifth"], q, args.test_groups, rng
            )
        )
        if i % 12 == 0:
            print(f"  Factorial check {i}/{len(scenarios)}", flush=True)
    return {
        "candidate_order": list(candidates),
        "scenario_order": list(scenarios),
        "scores": np.array([m["scores"] for m in measurements]).T.tolist(),
        "standard_errors": np.array(
            [m["score_standard_errors"] for m in measurements]
        ).T.tolist(),
        "metadata": descriptions,
        "games_per_scenario": args.test_groups,
    }


def add_concentration_holdout(args):
    """Check a larger C share using the frozen candidates and fresh saved S/T."""
    output = Path(args.output)
    original = json.loads((output / "comparison.json").read_text())
    selection = json.loads((output / "selection.json").read_text())
    design = json.loads((output / "design.json").read_text())
    index = json.loads((output / "validation_populations_index.json").read_text())
    candidates = selection["frozen_candidates"]
    if original["candidate_order"] != list(candidates):
        raise ValueError("Saved results must use the frozen candidate order.")

    streams = np.random.SeedSequence([args.seed, 434]).spawn(2)
    seeds = [int(stream.generate_state(1)[0]) for stream in streams]
    calibration_rng, test_rng = [np.random.default_rng(seed) for seed in seeds]
    first_model = next(iter(design["fresh_models"].values()))
    h = baseline_populations(
        first_model["conditional_parameters"]["samples"], first_model["anchor_seed"]
    )["H"]
    previous = json.loads(Path("results/game2/combined_comparison.json").read_text())
    previous_references = np.array(
        [row["reference"] for row in previous["scenarios"].values()]
    )
    conditional_cache, scenarios, metadata = {}, {}, {}
    with np.load(output / "validation_populations.npz") as saved:
        pool_parts = [candidate_pool(args.seed), previous_references]
        with np.load(output / "training_scores.npz") as training:
            pool_parts.append(training["allocations"])
        pool_parts.extend(
            saved[key] for key in saved.files if key.endswith("_allocations")
        )
        pool = np.unique(np.vstack(pool_parts), axis=0)
        for model, description in design["fresh_models"].items():
            parameters = description["conditional_parameters"]
            condition = (
                parameters["samples"],
                parameters["seed"],
                parameters["profile"],
                parameters["secondary_bid_profile"],
            )
            if condition not in conditional_cache:
                conditional_cache[condition] = concentrated_by_count(*condition)
            c = concentration_mixture(
                conditional_cache[condition],
                description["single_share"],
                description["all_in_fraction"],
            )
            mass = float(c["weights"][c["allocations"][:, 4] == 100].sum())
            if not np.isclose(
                mass, description["C_exact_100_fifth_mass"], rtol=0, atol=1e-14
            ):
                raise ValueError(
                    f"Reconstructed C differs from its saved model: {model}"
                )
            for depth in [3, 4]:
                source = f"{model}/depth{depth}/T_A"
                source_shares = design["validation_scenarios"][source]["shares"]
                if not np.allclose(
                    [source_shares[key] for key in ["H", "C", "S", "TA", "TB"]],
                    [0, 0.14, 0.56, 0.24, 0.06],
                    rtol=0,
                    atol=1e-12,
                ):
                    raise ValueError(f"The source mixture changed: {source}")
                prefix = index[source]
                q = {
                    "allocations": saved[prefix + "_allocations"],
                    "weights": saved[prefix + "_weights"],
                }
                name = f"concentration_holdout/{model}/depth{depth}"
                # 0.60*(0.14 C + 0.56 S + 0.30 T) + 0.35 C + 0.05 H.
                scenarios[name] = mix_populations([q, c, h], [0.60, 0.35, 0.05])
                metadata[name] = {
                    "source_scenario": source,
                    "model": model,
                    "depth": depth,
                    "reweighting": {"saved_population": 0.60, "C": 0.35, "H": 0.05},
                    "shares": {
                        "H": 0.05,
                        "C": 0.434,
                        "S": 0.336,
                        "TA": 0.144,
                        "TB": 0.036,
                    },
                    "single_share": description["single_share"],
                    "all_in_fraction": description["all_in_fraction"],
                    "C_exact_100_fifth_mass": mass,
                }

    print(
        f"Concentration holdout: {len(scenarios)} fresh scenarios with 43.4% C; "
        "all candidate allocations remain fixed.",
        flush=True,
    )
    save_populations(output, "concentration_holdout_populations", scenarios)
    save_json(
        output,
        "concentration_holdout_design.json",
        {
            "timing": "Planned by the coverage audit while training was running, before the round 2 choice was frozen; holdout results do not enter training.",
            "reason": "Extend fresh validation from 14%/15% C to 43.4% C.",
            "arguments": vars(args),
            "stage_seed_entropy": [args.seed, 434],
            "stage_seeds": seeds,
            "stage_seed_order": ["reference_calibration", "test_games"],
            "frozen_candidates": candidates,
            "benchmark_pool_size": len(pool),
            "benchmark_pool_definition": "Union of the initial pool, training finalists, previous-round reference allocations, and saved fresh population supports.",
            "conditional_C_generations": len(conditional_cache),
            "H_anchor_seed": first_model["anchor_seed"],
            "scenarios": metadata,
        },
    )
    results = validate(candidates, pool, scenarios, calibration_rng, test_rng, args)
    save_json(output, "concentration_holdout_comparison.json", results)
    combined = summarize_results(
        candidates, {**original["scenarios"], **results["scenarios"]}
    )
    combined["scenario_groups"] = {
        "main_validation": list(original["scenarios"]),
        "concentration_holdout": list(results["scenarios"]),
    }
    save_json(output, "combined_comparison.json", combined)
    print(json.dumps(combined["summary"], indent=2), flush=True)
    return combined


def run(args):
    started = perf_counter()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    streams = np.random.SeedSequence(args.seed).spawn(8)
    seeds = [int(s.generate_state(1)[0]) for s in streams]
    rngs = [np.random.default_rng(seed) for seed in seeds]
    previous, old_candidates, old_references = load_previous()
    initial = np.unique(
        np.vstack(
            [
                candidate_pool(args.seed),
                old_references,
                np.array(list(old_candidates.values())),
            ]
        ),
        axis=0,
    )
    training_models, training_model_metadata = build_models(initial, rngs[0], args)
    fresh_training, training_metadata = build_scenarios(
        training_models, training_model_metadata
    )
    training = {**fresh_training, **previous}
    save_json(
        output,
        "training_design.json",
        {
            "models": training_model_metadata,
            "scenarios": training_metadata,
            "previous_development_scenarios": list(previous),
        },
    )
    pool = np.unique(
        np.vstack(
            [
                initial,
                *[
                    level["allocations"]
                    for model in training_models.values()
                    for level in model["levels"]
                ],
            ]
        ),
        axis=0,
    )
    save_populations(output, "training_populations", training)
    candidates, finalists, scores, selection = select(
        pool, training, old_candidates, rngs[1], args
    )
    save_json(output, "selection.json", selection)
    np.savez_compressed(
        output / "training_scores.npz",
        allocations=finalists,
        scores=scores,
        scenario_names=np.array(list(training)),
    )
    print(f"Frozen round 2 choice: {candidates['round2_robust']}", flush=True)
    save_json(
        output,
        "factorial.json",
        factorial_diagnostics(
            candidates, training_models, training_model_metadata, rngs[2], args
        ),
    )
    fresh_models, fresh_model_metadata = build_models(
        initial, rngs[3], args, fresh=True
    )
    validation, validation_metadata = build_scenarios(
        fresh_models, fresh_model_metadata, fresh=True
    )
    benchmark_pool = np.unique(
        np.vstack(
            [
                pool,
                finalists,
                *[
                    level["allocations"]
                    for model in fresh_models.values()
                    for level in model["levels"]
                ],
            ]
        ),
        axis=0,
    )
    stresses, stress_metadata = add_stresses(
        fresh_models, benchmark_pool, candidates, rngs[4], args
    )
    validation.update(stresses)
    validation_metadata.update(stress_metadata)
    save_populations(output, "validation_populations", validation)
    save_json(
        output,
        "design.json",
        {
            "arguments": vars(args),
            "stage_seeds": seeds,
            "stage_seed_order": [
                "training_models",
                "selection",
                "factorial_scores",
                "fresh_models",
                "stress_models",
                "reference_calibration",
                "final_games",
                "reserve",
            ],
            "training_models": training_model_metadata,
            "fresh_models": fresh_model_metadata,
            "training_scenarios": training_metadata,
            "previous_development_scenarios": list(previous),
            "validation_scenarios": validation_metadata,
            "depth_3_weights": depth_weights(3),
            "depth_4_weights": depth_weights(4),
        },
    )
    print(
        f"Evaluate {len(validation)} fresh scenarios, {args.test_groups:,} games each",
        flush=True,
    )
    results = validate(candidates, benchmark_pool, validation, rngs[5], rngs[6], args)
    save_json(output, "comparison.json", results)
    grouped = {}
    for group in ["base", "stress", "belief"]:
        cases = {
            name: row
            for name, row in results["scenarios"].items()
            if (
                name.split("/")[0]
                if name.startswith(("stress/", "belief/"))
                else "base"
            )
            == group
        }
        grouped[group] = summarize_results(candidates, cases)["summary"]
    save_json(output, "grouped_summary.json", grouped)
    print(json.dumps(results["summary"], indent=2), flush=True)
    add_concentration_holdout(args)
    print(f"Completed in {perf_counter() - started:.1f} seconds", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026110402)
    parser.add_argument("--population-samples", type=int, default=3000)
    parser.add_argument("--response-screen", type=int, default=1024)
    parser.add_argument("--response-check", type=int, default=8192)
    parser.add_argument("--search-screen", type=int, default=1024)
    parser.add_argument("--search-refine", type=int, default=8192)
    parser.add_argument("--search-calibration", type=int, default=20000)
    parser.add_argument("--test-groups", type=int, default=200000)
    parser.add_argument("--output", default="results/game2_round2")
    parser.add_argument(
        "--concentration-holdout-only",
        action="store_true",
        help="Reuse saved results and evaluate the 72 fresh scenarios with 43.4%% C.",
    )
    arguments = parser.parse_args()
    if arguments.concentration_holdout_only:
        add_concentration_holdout(arguments)
    else:
        run(arguments)
