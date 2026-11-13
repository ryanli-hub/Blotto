"""First Game 2 study: model peers, search, freeze candidates, and validate."""

import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from blotto.game2_population import (
    TEAMMATE,
    USER,
    baseline_populations,
    candidate_pool,
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


PROFILES = ["balanced", "fifth_crowded", "fifth_avoided"]
COMPARATORS = {
    "teammate": TEAMMATE.tolist(),
    "user": USER.tolist(),
    "game1": [8, 9, 10, 11, 62],
    "previous_compromise": [6, 37, 50, 7, 0],
    "all_fifth": [0, 0, 0, 0, 100],
    "castles_4_5": [0, 0, 0, 49, 51],
}


def save_json(folder, name, data):
    (folder / name).write_text(json.dumps(data, indent=2) + "\n")


def build_components(profiles, candidates, rng, args, fresh=False):
    components, metadata = {}, {}
    for profile in profiles:
        print(f"  Building {'fresh' if fresh else 'training'} {profile}", flush=True)
        seed = int(rng.integers(2**32))
        base = baseline_populations(args.population_samples, seed, profile)
        depth = 4 if profile == "small_bids" else 3
        levels, diagnostics = finite_reasoning(
            base, candidates, rng, depth, args.response_screen, args.response_check
        )
        components[profile] = {**base, "levels": levels}
        metadata[profile] = {"population": base["parameters"], "reasoning": diagnostics}
    return components, metadata


def scenario(components, h, s, t, a=0.5, depth_weights=None):
    levels = components["levels"]
    if depth_weights is None:
        if len(levels) == 4:
            depth_weights = [0.05, 0.15, 0.30, 0.50]
        elif s <= 0.35:
            depth_weights = [0.70, 0.25, 0.05]
        elif s >= 0.65:
            depth_weights = [0.15, 0.35, 0.50]
        else:
            depth_weights = [0.35, 0.45, 0.20]
    strategic = mix_populations(levels, depth_weights)
    remaining = 1 - h - t
    weights = [h, remaining * (1 - s), remaining * s, t * a, t * (1 - a)]
    mixed = mix_populations(
        [
            components["H"],
            components["C"],
            strategic,
            components["TA"],
            components["TB"],
        ],
        weights,
    )
    metadata = {
        "shares": dict(zip(["H", "C", "S", "TA", "TB"], weights)),
        "S_fraction_of_non_H_T": s,
        "S_level_weights": depth_weights,
        "A_fraction_of_T": a,
    }
    return mixed, metadata


def build_scenarios(components, fresh=False):
    scenarios, metadata = {}, {}
    for profile, base in components.items():
        settings = (
            [
                (h, s, t, a)
                for h in (0, 0.10)
                for s in (0.50, 0.80)
                for t in (0.10, 0.30, 0.60)
                for a in (0.20, 0.80)
            ]
            + [(0.05, 0.65, 0, 0.5)]
            if fresh
            else [
                (h, s, t, 0.5)
                for h in (0, 0.05, 0.15)
                for s in (0.35, 0.65)
                for t in (0, 0.20, 0.40)
            ]
        )
        for h, s, t, a in settings:
            name = f"{profile}/h{h:.2f}/s{s:.2f}/t{t:.2f}/a{a:.2f}"
            scenarios[name], metadata[name] = scenario(base, h, s, t, a)
            metadata[name]["profile"] = profile
    return scenarios, metadata


def select_candidates(pool, scenarios, rng, args):
    anchors = np.asarray(list(COMPARATORS.values()))
    print(
        f"Screening {len(pool):,} allocations on {len(scenarios)} scenarios", flush=True
    )
    scores = evaluate_scenarios(pool, scenarios, args.search_screen, rng)
    chosen = shortlist_indices(scores)
    robust_order = np.argsort(maximum_regrets(scores))
    specialist_rows = pool[np.unique(scores.argmax(axis=0))]
    refined = np.unique(
        np.vstack(
            [
                pool[chosen],
                anchors,
                neighbors(pool[robust_order[:8]]),
                neighbors(specialist_rows, steps=(1, 2)),
            ]
        ),
        axis=0,
    )
    print(f"Refining {len(refined):,} allocations", flush=True)
    scores = evaluate_scenarios(refined, scenarios, args.search_refine, rng)
    finalists = np.unique(
        np.vstack(
            [
                refined[shortlist_indices(scores, robust_count=48)],
                anchors,
            ]
        ),
        axis=0,
    )
    print(f"Calibrating {len(finalists):,} finalists", flush=True)
    scores = evaluate_scenarios(finalists, scenarios, args.search_calibration, rng)
    regrets = maximum_regrets(scores)
    best = int(regrets.argmin())
    central_name = "balanced/h0.05/s0.65/t0.20/a0.50"
    central_index = list(scenarios).index(central_name)
    central = int(scores[:, central_index].argmax())
    candidates = {
        **COMPARATORS,
        "new_robust": finalists[best].tolist(),
        "central_specialist": finalists[central].tolist(),
    }
    summary = {
        "initial_candidates": len(pool),
        "refined_candidates": len(refined),
        "calibrated_candidates": len(finalists),
        "scenarios": list(scenarios),
        "selected": candidates["new_robust"],
        "selected_maximum_search_regret": float(regrets[best]),
        "central_scenario": central_name,
        "frozen_candidates": candidates,
    }
    return candidates, finalists, scores, summary


def stress_scenarios(components, pool, selected, rng, args):
    scenarios, metadata = {}, {}
    copied = population([selected])
    for profile in PROFILES:
        base, base_metadata = scenario(components[profile], 0.05, 0.65, 0.20)
        predicted = mix_populations([base, copied], [0.85, 0.15])
        responders, diagnostic = response_search(
            pool, predicted, rng, args.response_screen, args.response_check
        )
        for name, extra in [
            ("same_recommendation", copied),
            ("anticipators", responders),
        ]:
            key = f"stress/{profile}/{name}"
            scenarios[key] = mix_populations([base, extra], [0.85, 0.15])
            metadata[key] = {
                "base": base_metadata,
                "base_share": 0.85,
                "extra_share": 0.15,
                "extra": name,
                "response_search": diagnostic if name == "anticipators" else None,
            }
        # Half the strategic share adopts one common recommendation.
        strategic = mix_populations(components[profile]["levels"], [0.15, 0.35, 0.50])
        recommendation, diagnostic = response_search(
            pool, base, rng, args.response_screen, args.response_check, count=1
        )
        clustered = mix_populations([strategic, recommendation], [0.50, 0.50])
        key = f"stress/{profile}/shared_advice"
        scenarios[key] = mix_populations(
            [
                components[profile]["H"],
                components[profile]["C"],
                clustered,
                components[profile]["TA"],
                components[profile]["TB"],
            ],
            [0.05, 0.75 * 0.35, 0.75 * 0.65, 0.10, 0.10],
        )
        metadata[key] = {
            "base": base_metadata,
            "common_advice_fraction_of_S": 0.50,
            "recommendation": recommendation["allocations"].tolist(),
        }
    return scenarios, metadata


def validate(candidates, pool, scenarios, calibration_rng, test_rng, args):
    rows = np.asarray(list(candidates.values()))
    results = {}
    for index, (name, opponents) in enumerate(scenarios.items(), 1):
        # The reference is chosen without seeing any final evaluation games.
        response, diagnostic = response_search(
            pool,
            opponents,
            calibration_rng,
            args.response_screen,
            args.response_check,
            count=1,
        )
        result = independent_evaluation(
            rows, response["allocations"][0], opponents, args.test_groups, test_rng
        )
        result["reference_search"] = diagnostic
        results[name] = result
        if index % 8 == 0 or index == len(scenarios):
            print(f"  Validated {index}/{len(scenarios)} scenarios", flush=True)
    return summarize_results(candidates, results)


def summarize_results(candidates, results):
    """Summarize the same frozen candidates across a supplied set of scenarios."""
    names = list(candidates)
    scores = np.array([row["scores"] for row in results.values()])
    gaps = np.array([row["score_gaps"] for row in results.values()])
    summary = {}
    scenario_names = list(results)
    for index, name in enumerate(names):
        worst = int(gaps[:, index].argmax())
        detail = results[scenario_names[worst]]
        summary[name] = {
            "allocation": candidates[name],
            "maximum_estimated_regret": float(gaps[worst, index]),
            "worst_regret_scenario": scenario_names[worst],
            "worst_gap_95_halfwidth": 1.96 * detail["gap_standard_errors"][index],
            "minimum_score": float(scores[:, index].min()),
            "maximum_score": float(scores[:, index].max()),
            "mean_across_scenarios": float(scores[:, index].mean()),
        }
    return {"candidate_order": names, "summary": summary, "scenarios": results}


def followup_all_fifth(args):
    """Apply the original copy/anticipation stresses to the strong all-fifth baseline."""
    output = Path(args.output)
    original = json.loads((output / "comparison.json").read_text())
    selection = json.loads((output / "selection.json").read_text())
    index = json.loads((output / "population_index.json").read_text())
    candidates = selection["frozen_candidates"]
    if original["candidate_order"] != list(candidates):
        raise ValueError("Saved results must use the original frozen candidate order.")

    streams = np.random.SeedSequence([args.seed, 2002]).spawn(3)
    seeds = [int(stream.generate_state(1)[0]) for stream in streams]
    response_rng, calibration_rng, test_rng = [
        np.random.default_rng(seed) for seed in seeds
    ]
    selected = np.asarray(candidates["new_robust"])
    copied = population([candidates["all_fifth"]])
    bases = {}
    with np.load(output / "populations.npz") as saved:
        # The first run saved every joint distribution, rather than its search pool.
        pool_parts = [candidate_pool(args.seed)]
        pool_parts.extend(
            saved[key] for key in saved.files if key.endswith("_allocations")
        )
        with np.load(output / "training_scores.npz") as training:
            pool_parts.append(training["allocations"])
        pool = np.unique(np.vstack(pool_parts), axis=0)
        for profile in PROFILES:
            source = f"stress/{profile}/same_recommendation"
            prefix = index["validation"][source]
            rows = saved[prefix + "_allocations"]
            weights = saved[prefix + "_weights"].copy()
            selected_row = np.all(rows == selected, axis=1)
            if selected_row.sum() != 1:
                raise ValueError(f"Missing the copied training selection in {source}.")
            # Saved P = 0.85 Q + 0.15 delta(selected); recover the same Q exactly.
            weights[selected_row] -= 0.15
            if weights.min() < -1e-12:
                raise ValueError(f"The saved copy share is inconsistent in {source}.")
            weights[selected_row & (np.abs(weights) < 1e-14)] = 0
            bases[profile] = population(rows, np.maximum(weights, 0) / 0.85)

    print(
        "Post-validation follow-up: six copy/anticipation scenarios for "
        "0/0/0/0/100; the original eight candidates remain fixed.",
        flush=True,
    )
    scenarios, metadata, arrays, population_index = {}, {}, {}, {}
    for profile, base in bases.items():
        predicted = mix_populations([base, copied], [0.85, 0.15])
        responders, diagnostic = response_search(
            pool, predicted, response_rng, args.response_screen, args.response_check
        )
        for kind, extra in [
            ("same_recommendation", copied),
            ("anticipators", responders),
        ]:
            name = f"followup_all_fifth/{profile}/{kind}"
            scenarios[name] = mix_populations([base, extra], [0.85, 0.15])
            prefix = f"followup_{len(population_index):03d}"
            population_index[name] = prefix
            arrays[prefix + "_allocations"] = scenarios[name]["allocations"]
            arrays[prefix + "_weights"] = scenarios[name]["weights"]
            metadata[name] = {
                "source": f"stress/{profile}/same_recommendation",
                "base_reconstruction": "(saved population - 0.15 * training-choice point mass) / 0.85",
                "base_share": 0.85,
                "extra_share": 0.15,
                "extra": kind,
                "anticipated_allocation": candidates["all_fifth"],
                "response_search": diagnostic if kind == "anticipators" else None,
            }
    np.savez_compressed(output / "followup_populations.npz", **arrays)
    save_json(
        output,
        "followup_design.json",
        {
            "timing": "Added after the first 109 validation results; candidates were not retuned.",
            "reason": "The all-fifth baseline had the lowest maximum estimated regret; test the same copy and anticipation risks for it.",
            "arguments": vars(args),
            "stage_seed_entropy": [args.seed, 2002],
            "stage_seeds": seeds,
            "stage_seed_order": ["responders", "reference_calibration", "test_games"],
            "frozen_candidates": candidates,
            "benchmark_pool_size": len(pool),
            "benchmark_pool_definition": "Union of the initial candidate pool, saved finalists, and all saved joint-population support allocations.",
            "scenarios": metadata,
            "population_index": population_index,
        },
    )
    followup = validate(candidates, pool, scenarios, calibration_rng, test_rng, args)
    save_json(output, "followup_comparison.json", followup)
    combined = summarize_results(
        candidates, {**original["scenarios"], **followup["scenarios"]}
    )
    combined["scenario_groups"] = {
        "initial_validation": list(original["scenarios"]),
        "post_validation_followup": list(followup["scenarios"]),
    }
    save_json(output, "combined_comparison.json", combined)
    print(json.dumps(combined["summary"], indent=2), flush=True)
    return combined


def save_populations(folder, training, validation, references):
    arrays = {}
    index = {}
    for phase, scenarios in [
        ("training", training),
        ("validation", validation),
        ("reference", references),
    ]:
        index[phase] = {}
        for i, (name, distribution) in enumerate(scenarios.items()):
            prefix = f"{phase}_{i:03d}"
            arrays[prefix + "_allocations"] = distribution["allocations"]
            arrays[prefix + "_weights"] = distribution["weights"]
            index[phase][name] = prefix
    np.savez_compressed(folder / "populations.npz", **arrays)
    save_json(folder, "population_index.json", index)


def run(args):
    started = perf_counter()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    streams = np.random.SeedSequence(args.seed).spawn(7)
    seeds = [int(stream.generate_state(1)[0]) for stream in streams]
    rngs = [np.random.default_rng(seed) for seed in seeds]
    print("Building broad candidate pool", flush=True)
    initial = candidate_pool(args.seed)
    training_components, training_model = build_components(
        PROFILES, initial, rngs[0], args
    )
    response_rows = [
        level["allocations"]
        for c in training_components.values()
        for level in c["levels"]
    ]
    pool = np.unique(np.vstack([initial, *response_rows]), axis=0)
    training, training_metadata = build_scenarios(training_components)
    candidates, finalists, training_scores, selection = select_candidates(
        pool, training, rngs[1], args
    )
    print(f"Frozen robust candidate: {candidates['new_robust']}", flush=True)
    save_json(output, "selection.json", selection)
    np.savez_compressed(
        output / "training_scores.npz", allocations=finalists, scores=training_scores
    )

    fresh_components, fresh_model = build_components(
        PROFILES + ["small_bids"], initial, rngs[2], args, fresh=True
    )
    validation, validation_metadata = build_scenarios(fresh_components, fresh=True)
    benchmark_pool = np.unique(
        np.vstack(
            [
                pool,
                finalists,
                *[
                    level["allocations"]
                    for c in fresh_components.values()
                    for level in c["levels"]
                ],
            ]
        ),
        axis=0,
    )
    stress, stress_metadata = stress_scenarios(
        fresh_components, benchmark_pool, candidates["new_robust"], rngs[3], args
    )
    validation.update(stress)
    validation_metadata.update(stress_metadata)
    base = fresh_components["balanced"]
    central, central_metadata = scenario(base, 0.05, 0.65, 0.20)
    references = {
        "central": central,
        "H": base["H"],
        "C": base["C"],
        "S": mix_populations(base["levels"], [0.15, 0.35, 0.50]),
        "T": mix_populations([base["TA"], base["TB"]], [0.50, 0.50]),
        "exact_80A_20B": population([TEAMMATE, USER], [0.80, 0.20]),
        "exact_20A_80B": population([TEAMMATE, USER], [0.20, 0.80]),
    }
    save_populations(output, training, validation, references)
    save_json(
        output,
        "design.json",
        {
            "arguments": vars(args),
            "stage_seeds": seeds,
            "stage_seed_order": [
                "training_population",
                "selection",
                "fresh_population",
                "stress_models",
                "benchmark_calibration",
                "test_games",
                "reference_games",
            ],
            "training_model": training_model,
            "fresh_model": fresh_model,
            "training_scenarios": training_metadata,
            "validation_scenarios": validation_metadata,
            "reference_central": central_metadata,
            "regret_definition": "Mean payout gap to a searched reference chosen on independent calibration games.",
            "sampling": "Three independent full-vector draws from the population for each match.",
        },
    )
    print(
        f"Independent test: {len(validation)} scenarios, {args.test_groups:,} games each",
        flush=True,
    )
    results = validate(candidates, benchmark_pool, validation, rngs[4], rngs[5], args)
    save_json(output, "comparison.json", results)
    reference_results = validate(
        candidates, benchmark_pool, references, rngs[4], rngs[6], args
    )
    save_json(output, "references.json", reference_results)
    print(json.dumps(results["summary"], indent=2), flush=True)
    followup_all_fifth(args)
    print(f"Completed in {perf_counter() - started:.1f} seconds", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261104)
    parser.add_argument("--population-samples", type=int, default=3000)
    parser.add_argument("--response-screen", type=int, default=2048)
    parser.add_argument("--response-check", type=int, default=8192)
    parser.add_argument("--search-screen", type=int, default=2048)
    parser.add_argument("--search-refine", type=int, default=8192)
    parser.add_argument("--search-calibration", type=int, default=20000)
    parser.add_argument("--test-groups", type=int, default=200000)
    parser.add_argument("--output", default="results/game2")
    parser.add_argument(
        "--followup-only",
        action="store_true",
        help="Reuse saved first-run results and run the six all-fifth follow-up stresses.",
    )
    arguments = parser.parse_args()
    if arguments.followup_only:
        followup_all_fifth(arguments)
    else:
        run(arguments)
