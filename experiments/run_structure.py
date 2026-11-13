"""Test a substantial cohort concentrating on castles 2, 4, and 5."""

import argparse
import json
from pathlib import Path

import numpy as np

from blotto.dynamics import near_best_responses
from blotto.game import marginals
from blotto.opponents import focused_245_population
from blotto.robust import minimax_regret
from experiments.run_anticipation import (
    CURRENT,
    build_advanced_types,
    endpoint_scenarios,
    equilibrium_checks,
    feedback_opponents,
    flatten_suite,
    shared_types,
)
from experiments.run_experiments import CANDIDATES, build_population_suite, evaluate, save_json


ANCHORS = [[2, 16, 1, 37, 44], [1, 14, 1, 37, 47]]
TRAINING_SHARES = [0.10, 0.25, 0.40, 0.60]
VALIDATION_SHARES = [0.05, 0.10, 0.15, 0.25, 0.35, 0.40, 0.55, 0.60]


def atomic_cohort(weights):
    return {
        "allocations": ANCHORS,
        "weights": weights,
        "marginals": marginals(ANCHORS, weights),
        "parameters": {"anchor_weights": weights},
    }


def load_known_bases():
    old = json.loads(Path("results/anticipation/populations.json").read_text())
    latest = json.loads(
        Path("results/anticipation/refinement_populations.json").read_text()
    )
    groups = {
        "first": old["training_bases"],
        "second": old["validation_bases"],
        "third": latest["bases"],
    }
    return {
        f"{group}/{name}": np.asarray(population)
        for group, data in groups.items()
        for name, population in data.items()
    }


def load_legacy_scenarios():
    """Retain the prior search and final validation cases at the 15% cap."""
    folder = Path("results/anticipation")
    saved = json.loads((folder / "populations.json").read_text())
    checks = json.loads((folder / "feedback.json").read_text())
    final = json.loads((folder / "refinement_populations.json").read_text())

    def arrays(data):
        return {key: np.asarray(value) for key, value in data.items()}

    def expand(bases, types):
        return endpoint_scenarios(
            arrays(bases), {key: arrays(value) for key, value in types.items()}
        )

    early = expand(saved["training_bases"], saved["training_types"]["types"])
    old_counters = arrays(saved["direct_counter"]["types"])
    early.update(
        endpoint_scenarios(
            arrays(saved["training_bases"]),
            shared_types(saved["training_bases"], old_counters),
        )
    )
    second = expand(saved["validation_bases"], saved["validation_types"]["types"])
    second.update(arrays(checks["feedback"]))
    second.update(arrays(checks["targeted"]))
    third = expand(final["bases"], final["advanced"]["types"])
    third.update(arrays(final["checks"]["feedback"]))
    third.update(arrays(final["checks"]["targeted"]))
    return {
        f"legacy/{group}/{name}": q
        for group, data in [("first", early), ("second", second), ("third", third)]
        for name, q in data.items()
        if not name.endswith("/base")
    }


def build_scenarios(bases, cohorts, shares, seed, belief_offsets, slack):
    """Keep the new cohort fixed; some remaining players respond to its arrival."""
    rng = np.random.default_rng(seed)
    scenarios = {f"{name}/base": population for name, population in bases.items()}
    metadata = {
        name + "/base": {"cohort_share": 0, "response_fraction_of_remainder": 0}
        for name in bases
    }
    for share in shares:
        print(f"  New cohort share {share:.0%}", flush=True)
        for cohort_name, cohort in cohorts.items():
            focused = cohort["marginals"]
            belief_shares = np.unique(np.clip(share + np.asarray(belief_offsets), 0, 1))
            for base_name, population in bases.items():
                key = f"{base_name}/{cohort_name}/share{round(100 * share):02d}"
                fixed = (1 - share) * population + share * focused
                scenarios[key + "/fixed"] = fixed
                responses = []
                for belief_share in belief_shares:
                    belief = (1 - belief_share) * population + belief_share * focused
                    responses.append(
                        near_best_responses(
                            belief,
                            count=24,
                            slack=slack,
                            seed=int(rng.integers(0, 2**32)),
                        )
                    )
                response_population = marginals(np.vstack(responses))
                # T keeps its actual share; responders replace 15% of the remainder.
                scenarios[key + "/responsive"] = share * focused + (1 - share) * (
                    0.85 * population + 0.15 * response_population
                )
                for kind, response_fraction in [("fixed", 0), ("responsive", 0.15)]:
                    metadata[key + "/" + kind] = {
                        "cohort_share": share,
                        "cohort": cohort_name,
                        "response_fraction_of_remainder": response_fraction,
                        "belief_shares": belief_shares.tolist(),
                    }
    return scenarios, metadata


def select_range(scenarios, metadata, cap, kind=None):
    return {
        name: population
        for name, population in scenarios.items()
        if metadata[name]["cohort_share"] <= cap + 1e-12
        and (
            kind is None
            or name.endswith("/" + kind)
            or name.endswith("/base")
            or metadata[name].get("legacy", False)
        )
    }


def compact_evaluation(candidates, scenarios):
    result = evaluate(candidates, scenarios)
    return {
        name: {
            key: row[key]
            for key in [
                "allocation",
                "max_regret",
                "worst_scenario",
                "min_score",
                "max_score",
            ]
        }
        for name, row in result["candidates"].items()
    }


def run(args):
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    design = {
        "anchors": ANCHORS,
        "training_shares": TRAINING_SHARES,
        "validation_shares": VALIDATION_SHARES,
        "training_seed": args.seed,
        "validation_seed": 20891413,
        "C_samples_per_fresh_profile": args.samples,
        "response_fraction_of_remainder": 0.15,
        "response_samples_per_belief": 24,
        "training_belief_offsets": [-0.10, 0, 0.10],
        "validation_belief_offsets": [-0.15, 0.05, 0.15],
        "training_response_slack": 0.10,
        "validation_response_slack": 0.05,
        "objective": "unrestricted minimax regret over bases, fixed mixtures, and finite response scenarios",
        "score_floors": None,
        "selection": "one fixed strategy covering new-cohort shares from zero through 60 percent",
        "legacy_cases": "retain prior search and final validation scenarios at the 15 percent cap",
        "baseline_control": "same unrestricted objective before adding the new cohort",
        "fresh_legacy_checks": "new peers and further responses at up to 15 percent, against a common current/selected pool",
    }
    save_json(output, "design.json", design)
    cohorts = {
        "exact_A": atomic_cohort([1, 0]),
        "exact_B": atomic_cohort([0, 1]),
        "local": focused_245_population("local"),
        "broad": focused_245_population("broad"),
    }
    holdout_cohorts = {
        "A_heavy": atomic_cohort([0.8, 0.2]),
        "B_heavy": atomic_cohort([0.2, 0.8]),
        "shifted": focused_245_population("shifted"),
        "overbid": focused_245_population("overbid"),
    }
    save_json(
        output, "cohorts.json", {"training": cohorts, "validation": holdout_cohorts}
    )
    bases = load_known_bases()
    print(
        f"Building new cohort scenarios over {len(bases)} observed bases...", flush=True
    )
    training, train_meta = build_scenarios(
        bases,
        cohorts,
        TRAINING_SHARES,
        args.seed,
        design["training_belief_offsets"],
        0.10,
    )
    legacy = load_legacy_scenarios()
    training.update(legacy)
    train_meta.update({name: {"cohort_share": 0, "legacy": True} for name in legacy})
    print(
        "Building fresh bases and shifted cohort behavior before strategy selection...",
        flush=True,
    )
    fresh = flatten_suite(
        build_population_suite(args.samples, design["validation_seed"])
    )
    validation, valid_meta = build_scenarios(
        fresh,
        holdout_cohorts,
        VALIDATION_SHARES,
        design["validation_seed"] + 500,
        design["validation_belief_offsets"],
        0.05,
    )
    save_json(
        output,
        "scenario_metadata.json",
        {"training": train_meta, "validation": valid_meta},
    )
    np.savez_compressed(
        output / "populations.npz",
        training_names=np.asarray(list(training)),
        training=np.asarray(list(training.values())),
        validation_names=np.asarray(list(validation)),
        validation=np.asarray(list(validation.values())),
    )

    candidates = {
        **CANDIDATES,
        "user_second": ANCHORS[1],
        "current": CURRENT,
        "previous_defensive": [5, 11, 11, 12, 61],
    }
    baseline_control = minimax_regret(
        select_range(training, train_meta, 0), initial_allocation=CURRENT
    )
    candidates["baseline_control"] = baseline_control["allocation"]
    print(
        f"No-new-cohort control: {baseline_control['allocation']}; regret {baseline_control['max_regret']:.6f}",
        flush=True,
    )
    searches = {}
    for cap in TRAINING_SHARES:
        selected = select_range(training, train_meta, cap)
        print(
            f"Searching every legal allocation with cohort share up to {cap:.0%}...",
            flush=True,
        )
        result = minimax_regret(selected, initial_allocation=CURRENT)
        label = f"cap{round(100 * cap):02d}"
        searches[label] = result
        candidates[label] = result["allocation"]
        print(
            f"  {result['allocation']}, maximum regret {result['max_regret']:.6f}",
            flush=True,
        )
    # This diagnostic measures how much allowing reactions changes the selection.
    fixed_search = minimax_regret(
        select_range(training, train_meta, 0.60, "fixed"), initial_allocation=CURRENT
    )
    candidates["fixed_only"] = fixed_search["allocation"]
    fresh_types = build_advanced_types(
        fresh, marginals([CURRENT]), [0.10, 0.25], design["validation_seed"] + 700, 0.05
    )
    fresh_checks = feedback_opponents(
        fresh,
        {"current": CURRENT, "selected": candidates["cap60"]},
        design["validation_seed"] + 1000,
    )
    fresh_legacy = {
        **endpoint_scenarios(fresh, fresh_types["types"]),
        **fresh_checks["feedback"],
        **fresh_checks["targeted"],
    }
    fresh_legacy = {
        "legacy_fresh/" + name: q
        for name, q in fresh_legacy.items()
        if not name.endswith("/base")
    }
    save_json(
        output,
        "fresh_legacy.json",
        {"scenarios": fresh_legacy, "advanced": fresh_types, "checks": fresh_checks},
    )
    results = {
        "design": design,
        "searches": searches,
        "fixed_only_search": fixed_search,
        "baseline_control_search": baseline_control,
        "selected": searches["cap60"]["allocation"],
        "counts": {
            "training_bases": len(bases),
            "training": len(training),
            "fresh_bases": len(fresh),
            "validation": len(validation),
            "legacy_training": len(legacy),
            "fresh_legacy": len(fresh_legacy),
        },
        "training": evaluate(candidates, training),
        "validation": evaluate(candidates, validation),
        "legacy_known": evaluate(candidates, legacy),
        "legacy_fresh": evaluate(candidates, fresh_legacy),
        "combined_validation": evaluate(candidates, {**validation, **fresh_legacy}),
        "validation_fixed": evaluate(
            candidates, select_range(validation, valid_meta, 0.60, "fixed")
        ),
        "validation_responsive": evaluate(
            candidates, select_range(validation, valid_meta, 0.60, "responsive")
        ),
        "training_by_cap": {
            f"{cap:.2f}": compact_evaluation(
                candidates, select_range(training, train_meta, cap)
            )
            for cap in TRAINING_SHARES
        },
        "validation_by_cap": {
            f"{cap:.2f}": compact_evaluation(
                candidates, select_range(validation, valid_meta, cap)
            )
            for cap in TRAINING_SHARES
        },
        "pure_cohorts": evaluate(
            candidates,
            {
                name: data["marginals"]
                for name, data in {
                    **cohorts,
                    **holdout_cohorts,
                    "equal_anchors": atomic_cohort([0.5, 0.5]),
                }.items()
            },
        ),
        "equilibrium": equilibrium_checks(candidates, Path("results/revised")),
    }
    save_json(output, "comparison.json", results)
    for name in ["current", "previous_broad", "cap60"]:
        row = results["validation"]["candidates"][name]
        print(
            f"{name}: {row['allocation']}; validation maximum regret {row['max_regret']:.6f}",
            flush=True,
        )
    print(f"Done: {output / 'comparison.json'}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/structure")
    parser.add_argument("--seed", type=int, default=20650619)
    parser.add_argument("--samples", type=int, default=4000)
    run(parser.parse_args())
