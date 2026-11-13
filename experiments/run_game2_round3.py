"""Choose Game 2 objectives on plausible populations, with first-three opponents."""

import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from blotto.game2_field import (
    TYPE_NAMES,
    _reasoning_levels,
    build_field,
    structural_probabilities,
)
from blotto.game2_metrics import summarize_scores, select_by_objective
from blotto.game2_population import (
    baseline_populations,
    candidate_pool,
    first_three_population,
    mix_populations,
    population,
)
from blotto.game2_search import (
    evaluate_scenarios,
    independent_evaluation,
    neighbors,
    response_search,
)
from experiments.run_game2 import save_json, validate
from experiments.run_game2_round2 import save_populations


TOLERANCES = [0, 0.10, 0.25, 0.50]


def priors(field):
    """Change weights on possible populations, keeping within-family weights fixed."""
    names = list(field["scenarios"])
    base = np.array([field["weights"][name] for name in names])
    families = [field["metadata"][name]["family"] for name in names]
    result = {"balanced": base}
    for family in dict.fromkeys(families):
        multipliers = np.array([2.5 if f == family else 0.625 for f in families])
        result[family + "_likely"] = base * multipliers
    return result


def objective_shortlist(rows, scores, prior_weights):
    """Preserve mean, tail, minimum, regret, and constrained first-three contenders."""
    references = scores.max(axis=0)
    chosen, centers = set(), set()
    subsets = [np.arange(len(rows)), np.flatnonzero((rows[:, 3:] == 0).all(axis=1))]
    for indices in subsets:
        for weights in prior_weights.values():
            metrics = summarize_scores(scores[indices], weights, references)
            for metric in [
                "weighted_mean",
                "lower_tail_mean",
                "minimum",
                "maximum_regret",
            ]:
                sign = 1 if metric == "maximum_regret" else -1
                order = np.argsort(sign * metrics[metric], kind="stable")
                chosen.update(indices[order[:12]].tolist())
                centers.add(int(indices[order[0]]))
            for tolerance in TOLERANCES:
                allowed = (
                    metrics["lower_tail_mean"]
                    >= metrics["lower_tail_mean"].max() - tolerance
                )
                order = np.argsort(
                    -np.where(allowed, metrics["weighted_mean"], -np.inf), kind="stable"
                )
                chosen.update(indices[order[:8]].tolist())
                centers.add(int(indices[order[0]]))
    # Specialists make the searched-reference regret meaningful in every scenario.
    chosen.update(np.argsort(-scores, axis=0, kind="stable")[:2].ravel().tolist())
    return np.array(sorted(chosen)), np.array(sorted(centers))


def select(pool, field, baselines, rng, args):
    prior_weights = priors(field)
    print(
        f"Screen {len(pool):,} allocations on {len(field['scenarios'])} core populations",
        flush=True,
    )
    scores = evaluate_scenarios(pool, field["scenarios"], args.search_screen, rng)
    shortlist, centers = objective_shortlist(pool, scores, prior_weights)
    refined = np.unique(
        np.vstack(
            [
                pool[shortlist],
                neighbors(pool[centers]),
                np.array(list(baselines.values())),
            ]
        ),
        axis=0,
    )
    print(f"Refine {len(refined):,} allocations for all objectives", flush=True)
    scores = evaluate_scenarios(refined, field["scenarios"], args.search_refine, rng)
    shortlist, _ = objective_shortlist(refined, scores, prior_weights)
    finalists = np.unique(
        np.vstack([refined[shortlist], np.array(list(baselines.values()))]), axis=0
    )
    print(f"Calibrate {len(finalists):,} finalists", flush=True)
    scores = evaluate_scenarios(
        finalists, field["scenarios"], args.search_calibration, rng
    )
    weights = prior_weights["balanced"]
    selections = select_by_objective(
        scores, weights, tail_tolerance=args.tail_tolerance
    )
    selections.update(
        {
            f"guard_{tolerance:.2f}": select_by_objective(
                scores, weights, tail_tolerance=tolerance
            )["mean_with_tail_guard"]
            for tolerance in TOLERANCES
        }
    )
    first_three = np.flatnonzero((finalists[:, 3:] == 0).all(axis=1))
    restricted = select_by_objective(
        scores[first_three],
        weights,
        scores.max(axis=0),
        tail_tolerance=args.tail_tolerance,
    )
    selections["first3_mean"] = int(first_three[restricted["mean"]])
    selections["first3_guard"] = int(first_three[restricted["mean_with_tail_guard"]])
    for name, prior in prior_weights.items():
        selections["prior_" + name] = select_by_objective(
            scores, prior, tail_tolerance=args.tail_tolerance
        )["mean_with_tail_guard"]

    candidates = dict(baselines)
    choices = {}
    for label, index in selections.items():
        allocation = finalists[index].tolist()
        canonical = next(
            (name for name, row in candidates.items() if row == allocation), label
        )
        candidates[canonical] = allocation
        choices[label] = canonical
    all_metrics = summarize_scores(scores, weights)
    metrics = {}
    for name, allocation in candidates.items():
        index = int(np.flatnonzero(np.all(finalists == allocation, axis=1))[0])
        metrics[name] = {key: float(value[index]) for key, value in all_metrics.items()}
    selection = {
        "initial_pool": len(pool),
        "refined_pool": len(refined),
        "finalists": len(finalists),
        "core_scenarios": len(field["scenarios"]),
        "tail_mass": 0.20,
        "tail_tolerance": args.tail_tolerance,
        "choices": choices,
        "primary_candidate": choices["mean_with_tail_guard"],
        "frozen_candidates": candidates,
        "training_metrics": metrics,
    }
    return candidates, finalists, scores, selection


def metric_report(results, field, tail_tolerance):
    names = results["candidate_order"]
    scenario_names = list(field["scenarios"])
    scores = np.array(
        [results["scenarios"][name]["scores"] for name in scenario_names]
    ).T
    standard_errors = np.array(
        [results["scenarios"][name]["score_standard_errors"] for name in scenario_names]
    ).T
    references = np.array(
        [results["scenarios"][name]["reference_score"] for name in scenario_names]
    )
    report = {"candidate_order": names, "priors": {}}
    for prior, weights in priors(field).items():
        metrics = summarize_scores(scores, weights, references)
        metrics["weighted_mean_standard_error"] = np.sqrt(
            (standard_errors**2) @ (weights**2)
        )
        choices = select_by_objective(
            scores, weights, references, tail_tolerance=tail_tolerance
        )
        guards = {
            f"{tolerance:.2f}": names[
                select_by_objective(
                    scores, weights, references, tail_tolerance=tolerance
                )["mean_with_tail_guard"]
            ]
            for tolerance in TOLERANCES
        }
        report["priors"][prior] = {
            "metrics": {
                name: {key: float(values[i]) for key, values in metrics.items()}
                for i, name in enumerate(names)
            },
            "choices_among_frozen": {
                key: names[index] for key, index in choices.items()
            },
            "tail_tolerance_choices": guards,
        }
    return report


def targeted_stresses(field, pool, candidates, choices, rng, args):
    scenarios, metadata = {}, {}
    for family in ["concentration", "first_three", "fifth"]:
        name = next(
            name for name, info in field["metadata"].items() if info["family"] == family
        )
        q = field["scenarios"][name]
        bank = field["models"][field["metadata"][name]["bank"]]
        for cohort in ["F", "Z"]:
            key = f"cohort/{family}/{cohort}40"
            scenarios[key] = mix_populations(
                [q, bank["components"][cohort]], [0.60, 0.40]
            )
            metadata[key] = {"base": name, "extra_cohort": cohort, "extra_share": 0.40}
        targets = dict.fromkeys(
            [
                choices["mean"],
                choices["mean_with_tail_guard"],
                choices["minimax_regret"],
            ]
        )
        for target in targets:
            copied = population([candidates[target]])
            predicted = mix_populations([q, copied], [0.85, 0.15])
            response, diagnostic = response_search(
                pool, predicted, rng, args.response_screen, args.response_check
            )
            for kind, extra in [("copy", copied), ("anticipate", response)]:
                key = f"strategy/{family}/{target}/{kind}15"
                scenarios[key] = mix_populations([q, extra], [0.85, 0.15])
                metadata[key] = {
                    "base": name,
                    "target": target,
                    "extra_share": 0.15,
                    "kind": kind,
                    "response": diagnostic,
                }
    return scenarios, metadata


def historical_audit(candidates, rng, args):
    """Replay old population stresses; none of their scores enters core selection."""
    folder = Path("results/game2_round2")
    old = json.loads((folder / "combined_comparison.json").read_text())
    rows = np.array(list(candidates.values()))
    results = {}
    for kind in ["validation", "concentration_holdout"]:
        index = json.loads((folder / (kind + "_populations_index.json")).read_text())
        with np.load(folder / (kind + "_populations.npz")) as saved:
            for name, prefix in index.items():
                q = {
                    "allocations": saved[prefix + "_allocations"],
                    "weights": saved[prefix + "_weights"],
                }
                results[name] = independent_evaluation(
                    rows, old["scenarios"][name]["reference"], q, args.audit_groups, rng
                )
                if len(results) % 32 == 0:
                    print(f"  Historical stress {len(results)}/258", flush=True)
    from experiments.run_game2 import summarize_results

    return summarize_results(candidates, results)


def coverage_weight_sensitivity(output):
    """Reweight saved core and absent-F populations without searching new candidates."""
    core = json.loads((output / "core_comparison.json").read_text())
    design = json.loads((output / "core_design.json").read_text())
    cohort = json.loads((output / "cohort_sensitivity.json").read_text())
    names = core["candidate_order"]
    core_names = list(core["scenarios"])
    absent_names = [name for name in cohort["scenarios"] if "/f0.00/" in name]
    rows = [core["scenarios"][name] for name in core_names] + [
        cohort["scenarios"][name] for name in absent_names
    ]
    scores = np.array([row["scores"] for row in rows]).T
    references = np.array([row["reference_score"] for row in rows])
    core_weights = np.array([design["weights"][name] for name in core_names])
    report = {
        "interpretation": "Exploratory prior sensitivity among the 19 frozen candidates; no new search or validation.",
        "absent_F_scenarios": absent_names,
        "candidate_order": names,
        "priors": {},
    }
    for absent_weight in [0, 0.25, 0.50, 0.75, 1.0]:
        weights = np.r_[
            (1 - absent_weight) * core_weights,
            np.full(len(absent_names), absent_weight / len(absent_names)),
        ]
        metrics = summarize_scores(scores, weights, references)
        choices = select_by_objective(scores, weights, references)
        report["priors"][f"{absent_weight:.2f}"] = {
            "absent_F_weight": absent_weight,
            "core_weight": 1 - absent_weight,
            "tail_tolerance": 0.25,
            "choices_among_frozen": {key: names[i] for key, i in choices.items()},
            "metrics": {
                name: {key: float(values[i]) for key, values in metrics.items()}
                for i, name in enumerate(names)
            },
        }
    save_json(output, "coverage_weights.json", report)
    return report


def cohort_sensitivity(args):
    """Vary low Z/F shares after primary evaluation, keeping candidates fixed."""
    started = perf_counter()
    output = Path(args.output)
    selection = json.loads((output / "selection.json").read_text())
    candidates = selection["frozen_candidates"]
    primary_results = json.loads((output / "core_comparison.json").read_text())
    if primary_results["candidate_order"] != list(candidates):
        raise ValueError("Saved primary results must use the frozen candidate order.")
    seeds = [
        int(stream.generate_state(1)[0])
        for stream in np.random.SeedSequence([args.seed, 313]).spawn(3)
    ]
    model_rng, calibration_rng, test_rng = [
        np.random.default_rng(seed) for seed in seeds
    ]
    shared_seeds = {
        name: int(model_rng.integers(2**32))
        for name in ["anchors", "F_zero", "F_shifted"]
    }
    anchors = baseline_populations(args.population_samples, shared_seeds["anchors"])
    f_zero = first_three_population(
        args.population_samples, shared_seeds["F_zero"], "zero"
    )
    f_shifted = first_three_population(
        args.population_samples, shared_seeds["F_shifted"], "shifted"
    )
    common = {
        "H": anchors["H"],
        "Z": population([[0, 0, 0, 0, 100]]),
        "F": mix_populations([f_zero, f_shifted], [0.50, 0.50]),
        "T": mix_populations([anchors["TA"], anchors["TB"]], [0.50, 0.50]),
    }
    first_three = np.array(
        [(a, b, 100 - a - b, 0, 0) for a in range(101) for b in range(101 - a)]
    )
    old = json.loads(Path("results/game2_round2/combined_comparison.json").read_text())
    references = np.array(
        [
            row["reference"]
            for results in [primary_results, old]
            for row in results["scenarios"].values()
        ]
    )
    with np.load(output / "training_scores.npz") as saved:
        pool = np.unique(
            np.vstack(
                [
                    candidate_pool(args.seed),
                    first_three,
                    saved["allocations"],
                    references,
                    np.array(list(candidates.values())),
                ]
            ),
            axis=0,
        )

    bid_settings = {
        "low": ([0, 1, 2, 3, 4], [0.20, 0.25, 0.30, 0.15, 0.10]),
        "raised": ([1, 2, 3, 4, 5], [0.15, 0.25, 0.30, 0.20, 0.10]),
    }
    styles = {
        "central": [0.0, 0.25, 0.50, 0.25],
        "deep": [0.0, 0.10, 0.35, 0.55],
    }
    scenarios, metadata, banks, response_rows = {}, {}, {}, []
    print(
        "Exploratory cohort sensitivity: 18 reasoning banks, 36 populations", flush=True
    )
    for bids, (bid_values, bid_probabilities) in bid_settings.items():
        c_seed, response_seed = [int(model_rng.integers(2**32)) for _ in range(2)]
        c_model = baseline_populations(
            args.population_samples,
            c_seed,
            overrides={
                "active_count_probabilities": [0.10, 0.60, 0.30],
                "small_bids": bid_values,
                "small_bid_probabilities": bid_probabilities,
                "noise_sigma": 0.35,
                "fifth_weight": 1.0,
            },
        )
        components = {**common, "C": c_model["C"]}
        for z in [0.01, 0.05, 0.15]:
            for f in [0.0, 0.10, 0.20]:
                shares = {
                    "H": 0.02,
                    "C": 0.43 - z - f,
                    "Z": z,
                    "F": f,
                    "T": 0.15,
                    "S": 0.40,
                }
                bank = f"{bids}/z{z:.2f}/f{f:.2f}"
                # Reset the same RNG across shares so response sampling is matched.
                levels, diagnostics = _reasoning_levels(
                    components,
                    pool,
                    shares,
                    np.random.default_rng(response_seed),
                    args.response_screen,
                    args.response_check,
                    belief_floor=0,
                )
                response_rows.extend(level["allocations"] for level in levels)
                banks[bank] = {
                    "shares": shares,
                    "C_parameters": c_model["parameters"],
                    "response_seed": response_seed,
                    "reasoning": diagnostics,
                }
                for style, weights in styles.items():
                    s = mix_populations(levels, weights)
                    q = mix_populations(
                        [s if name == "S" else components[name] for name in TYPE_NAMES],
                        [shares[name] for name in TYPE_NAMES],
                    )
                    name = f"{bank}/{style}"
                    scenarios[name] = q
                    metadata[name] = {
                        "bank": bank,
                        "bids": bids,
                        "shares": shares,
                        "S_style": style,
                        "S_level_weights": weights,
                        **structural_probabilities(q),
                    }
                print(f"  Built sensitivity bank {len(banks)}/18: {bank}", flush=True)
    benchmark_pool = np.unique(np.vstack([pool, *response_rows]), axis=0)
    save_populations(output, "cohort_sensitivity_populations", scenarios)
    save_json(
        output,
        "cohort_sensitivity_design.json",
        {
            "timing": "Exploratory model sensitivity added after the primary evaluation; all candidates remain frozen.",
            "arguments": vars(args),
            "stage_seed_entropy": [args.seed, 313],
            "stage_seeds": seeds,
            "stage_order": [
                "fresh_distributions",
                "reference_calibration",
                "test_games",
            ],
            "shared_seeds": shared_seeds,
            "primary_candidate": selection["primary_candidate"],
            "frozen_candidates": candidates,
            "response_pool_size": len(pool),
            "benchmark_pool_size": len(benchmark_pool),
            "F_mixture_weights": [0.50, 0.50],
            "F_components": [f_zero["parameters"], f_shifted["parameters"]],
            "A_fraction_of_T": 0.50,
            "belief_floor": 0.0,
            "groups_per_scenario": args.audit_groups,
            "models": banks,
            "scenarios": metadata,
        },
    )
    evaluation_args = argparse.Namespace(
        **{**vars(args), "test_groups": args.audit_groups}
    )
    results = validate(
        candidates,
        benchmark_pool,
        scenarios,
        calibration_rng,
        test_rng,
        evaluation_args,
    )
    results["primary_candidate"] = selection["primary_candidate"]
    results["elapsed_seconds"] = perf_counter() - started
    save_json(output, "cohort_sensitivity.json", results)
    coverage_weight_sensitivity(output)
    print(json.dumps(results["summary"], indent=2), flush=True)
    print(
        f"Cohort sensitivity completed in {results['elapsed_seconds']:.1f} seconds",
        flush=True,
    )
    return results


def run(args):
    started = perf_counter()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    seeds = [
        int(s.generate_state(1)[0]) for s in np.random.SeedSequence(args.seed).spawn(8)
    ]
    rngs = [np.random.default_rng(seed) for seed in seeds]
    old = json.loads(Path("results/game2_round2/combined_comparison.json").read_text())
    baselines = {name: row["allocation"] for name, row in old["summary"].items()}
    baselines.update(
        {
            "first3_equal": [33, 33, 34, 0, 0],
            "first3_proportional": [17, 33, 50, 0, 0],
            "first3_third_heavy": [15, 30, 55, 0, 0],
        }
    )
    first3 = np.array(
        [(a, b, 100 - a - b, 0, 0) for a in range(101) for b in range(101 - a)]
    )
    old_references = np.array([row["reference"] for row in old["scenarios"].values()])
    initial = np.unique(
        np.vstack(
            [
                candidate_pool(args.seed),
                first3,
                old_references,
                np.array(list(baselines.values())),
            ]
        ),
        axis=0,
    )
    print("Generate thoughtful core populations and four reasoning levels", flush=True)
    train = build_field(
        initial,
        seeds[0],
        args.population_samples,
        args.response_screen,
        args.response_check,
    )
    pool = np.unique(
        np.vstack(
            [
                initial,
                *[
                    level["allocations"]
                    for bank in train["models"].values()
                    for level in bank["levels"]
                ],
                *[
                    bank["components"]["F"]["allocations"]
                    for bank in train["models"].values()
                ],
            ]
        ),
        axis=0,
    )
    save_populations(output, "training_populations", train["scenarios"])
    save_json(
        output,
        "training_design.json",
        {key: train[key] for key in ["metadata", "weights", "parameters"]},
    )
    candidates, finalists, scores, selection = select(
        pool, train, baselines, rngs[1], args
    )
    save_json(output, "selection.json", selection)
    np.savez_compressed(
        output / "training_scores.npz",
        allocations=finalists,
        scores=scores,
        scenario_names=np.array(list(train["scenarios"])),
    )
    primary = selection["primary_candidate"]
    print(f"Frozen primary choice: {primary} {candidates[primary]}", flush=True)

    fresh = build_field(
        initial,
        seeds[2],
        args.population_samples,
        args.response_screen,
        args.response_check,
        fresh=True,
    )
    benchmark_pool = np.unique(
        np.vstack(
            [
                pool,
                finalists,
                *[
                    level["allocations"]
                    for bank in fresh["models"].values()
                    for level in bank["levels"]
                ],
            ]
        ),
        axis=0,
    )
    save_populations(output, "core_validation_populations", fresh["scenarios"])
    save_json(
        output,
        "core_design.json",
        {
            "arguments": vars(args),
            "stage_seeds": seeds,
            "stage_order": [
                "training_models",
                "selection",
                "fresh_models",
                "reference_search",
                "core_games",
                "stress_models",
                "stress_games",
                "old_stress_games",
            ],
            **{key: fresh[key] for key in ["metadata", "weights", "parameters"]},
        },
    )
    print("Validate frozen candidates on the 90 fresh core populations", flush=True)
    results = validate(
        candidates, benchmark_pool, fresh["scenarios"], rngs[3], rngs[4], args
    )
    save_json(output, "core_comparison.json", results)
    report = metric_report(results, fresh, args.tail_tolerance)
    save_json(output, "metrics.json", report)
    print(json.dumps(report["priors"]["balanced"], indent=2), flush=True)

    print("Separate targeted stresses and historical population audit", flush=True)
    stresses, description = targeted_stresses(
        fresh, benchmark_pool, candidates, selection["choices"], rngs[5], args
    )
    save_populations(output, "stress_populations", stresses)
    save_json(output, "stress_design.json", description)
    stress_args = argparse.Namespace(**{**vars(args), "test_groups": args.audit_groups})
    stress = validate(
        candidates, benchmark_pool, stresses, rngs[3], rngs[6], stress_args
    )
    save_json(output, "targeted_stress.json", stress)
    save_json(
        output, "historical_stress.json", historical_audit(candidates, rngs[7], args)
    )
    cohort_sensitivity(args)
    print(f"Completed in {perf_counter()-started:.1f} seconds", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026110403)
    parser.add_argument("--population-samples", type=int, default=3000)
    parser.add_argument("--response-screen", type=int, default=1024)
    parser.add_argument("--response-check", type=int, default=8192)
    parser.add_argument("--search-screen", type=int, default=1024)
    parser.add_argument("--search-refine", type=int, default=8192)
    parser.add_argument("--search-calibration", type=int, default=20000)
    parser.add_argument("--test-groups", type=int, default=200000)
    parser.add_argument("--audit-groups", type=int, default=50000)
    parser.add_argument("--tail-tolerance", type=float, default=0.25)
    parser.add_argument("--output", default="results/game2_round3")
    parser.add_argument(
        "--cohort-sensitivity-only",
        action="store_true",
        help="Reuse frozen candidates and evaluate the 36 low-Z/F sensitivity populations.",
    )
    arguments = parser.parse_args()
    if arguments.cohort_sensitivity_only:
        cohort_sensitivity(arguments)
    else:
        run(arguments)
