"""Final Game 1 study: exact objectives, varied opponent reasoning, fresh checks."""

import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from blotto.game import best_response, expected_rewards, marginals
from blotto.game1_field import build_field, response_sample
from blotto.game1_objectives import search_objectives
from blotto.game2_metrics import select_by_objective, summarize_scores
from blotto.opponents import mixture
from blotto.robust import score_allocations
from experiments.run_experiments import save_json


BASELINES = {
    "teammate": [2, 16, 1, 37, 44],
    "original": [1, 14, 1, 37, 47],
    "previous_broad": [2, 2, 3, 39, 54],
    "previous_search": [2, 16, 10, 12, 60],
    "incumbent": [8, 9, 10, 11, 62],
}


def priors(field):
    """Equal family weights, then put 50% on each family in turn."""
    names = list(field["scenarios"])
    weights = np.array([field["weights"][name] for name in names])
    families = [field["metadata"][name]["family"] for name in names]
    result = {"balanced": weights}
    for family in dict.fromkeys(families):
        result[family + "_likely"] = weights * np.array(
            [2.5 if value == family else 0.625 for value in families]
        )
    return result


def save_field(output, label, field):
    names = list(field["scenarios"])
    np.savez_compressed(
        output / (label + "_populations.npz"),
        names=np.array(names),
        marginals=np.array([field["scenarios"][name] for name in names]),
    )
    save_json(
        output,
        label + "_design.json",
        {key: value for key, value in field.items() if key != "scenarios"},
    )


def evaluate_panel(candidates, scenarios, prior_weights, output, label):
    """Score frozen allocations exactly; every regret reference is an exact DP."""
    names = list(scenarios)
    rows = np.array(list(candidates.values()))
    responses = [best_response(q) for q in scenarios.values()]
    optima = np.array([value for _, value in responses])
    scores = np.column_stack([score_allocations(rows, q) for q in scenarios.values()])
    np.savez_compressed(
        output / (label + "_scores.npz"),
        candidate_names=np.array(list(candidates)),
        allocations=rows,
        scenario_names=np.array(names),
        scores=scores,
        optimal_scores=optima,
        best_responses=np.array([row for row, _ in responses]),
    )
    report = {
        "scenario_count": len(names),
        "candidates": candidates,
        "priors": {},
        "weakest_scenarios": {},
    }
    for prior, weights in prior_weights.items():
        metrics = summarize_scores(scores, weights, optima)
        choices = select_by_objective(scores, weights, optima)
        report["priors"][prior] = {
            "metrics": {
                name: {key: float(value[i]) for key, value in metrics.items()}
                for i, name in enumerate(candidates)
            },
            "choices_among_frozen": {
                key: list(candidates)[index] for key, index in choices.items()
            },
        }
    for i, name in enumerate(candidates):
        low = int(scores[i].argmin())
        gap = int((optima - scores[i]).argmax())
        report["weakest_scenarios"][name] = {
            "minimum": names[low],
            "maximum_regret": names[gap],
            "regret_reference": responses[gap][0],
        }
    save_json(output, label + ".json", report)
    return report


def freeze_candidates(search):
    candidates, aliases = dict(BASELINES), {}
    for prior, data in search["priors"].items():
        for objective, result in data["choices"].items():
            row = list(result["allocation"])
            proposed = prior + "/" + objective
            name = next(
                (key for key, value in candidates.items() if value == row), proposed
            )
            candidates[name] = row
            aliases[proposed] = name
    return candidates, aliases


def combine_fields(fields):
    scenarios, metadata, weights = {}, {}, {}
    for i, field in enumerate(fields, 1):
        for name, population in field["scenarios"].items():
            key = f"replicate{i}/{name}"
            scenarios[key] = population
            metadata[key] = {**field["metadata"][name], "replicate": i}
            weights[key] = field["weights"][name] / len(fields)
    return {"scenarios": scenarios, "metadata": metadata, "weights": weights}


def describe_behavior(candidates, field, output):
    """Explain fresh scores by population family and castle contribution."""
    names = list(field["scenarios"])
    weights = np.array([field["weights"][name] for name in names])
    with np.load(output / "validation_scores.npz") as saved:
        scores = saved["scores"]
    groups = {}
    for factor in ["family", "response_style", "depth_style", "bids"]:
        labels = [field["metadata"][name][factor] for name in names]
        groups[factor] = {}
        for label in dict.fromkeys(labels):
            mask = np.array([value == label for value in labels])
            means = np.average(scores[:, mask], axis=1, weights=weights[mask])
            groups[factor][label] = dict(zip(candidates, means))
    pooled = mixture(list(field["scenarios"].values()), weights)
    rewards = expected_rewards(pooled)
    save_json(
        output,
        "diagnostics.json",
        {
            "source": "Fresh populations, weighted within each reported group",
            "group_mean_scores": groups,
            "mean_castle_contributions": {
                name: rewards[np.arange(5), row] for name, row in candidates.items()
            },
        },
    )


def stress_populations(field, candidates, targets, seed):
    """Give each frozen candidate the same copy, anticipation, and counter checks."""
    rng = np.random.default_rng(seed)
    scenarios, metadata = {}, {}
    families = list(
        dict.fromkeys(info["family"] for info in field["metadata"].values())
    )
    for family in families:
        names = [
            name for name, info in field["metadata"].items() if info["family"] == family
        ]
        q = mixture(
            [field["scenarios"][name] for name in names],
            [field["weights"][name] for name in names],
        )
        for target in targets:
            copied = marginals([candidates[target]])
            direct, direct_info = response_sample(copied, rng, slack=0.0)
            direct_q = marginals(direct)
            for share in [0.05, 0.15]:
                prediction = (1 - share) * q + share * copied
                responses, response_info = response_sample(prediction, rng, slack=0.15)
                for kind, extra in [
                    ("copy", copied),
                    ("anticipate", marginals(responses)),
                    ("direct_counter", direct_q),
                ]:
                    name = f"{family}/{target}/{kind}{share:.2f}"
                    scenarios[name] = (1 - share) * q + share * extra
                    checks = {
                        "copy": None,
                        "anticipate": response_info,
                        "direct_counter": direct_info,
                    }
                    metadata[name] = {
                        "family": family,
                        "target": target,
                        "type": kind,
                        "share": share,
                        "response": checks[kind],
                    }
    return scenarios, metadata


def historical_populations():
    folder = Path("results/structure")
    with np.load(folder / "populations.npz") as saved:
        populations = dict(zip(saved["validation_names"].tolist(), saved["validation"]))
    other = json.loads((folder / "fresh_legacy.json").read_text())["scenarios"]
    populations.update({name: np.asarray(q) for name, q in other.items()})
    return populations


def run(args):
    started = perf_counter()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    print("Build Game 1 training populations", flush=True)
    training = build_field(args.seed, args.samples, args.responses_per_order)
    save_field(output, "training", training)
    print("Search every legal allocation for each objective and prior", flush=True)
    search = search_objectives(training["scenarios"], priors(training))
    save_json(output, "search.json", search)
    candidates, aliases = freeze_candidates(search)
    primary = aliases["balanced/guard_0.25"]
    selection = {
        "objective": "Highest weighted mean within 0.25 castle points of the globally best worst-20% mean",
        "tail_tolerance": 0.25,
        "primary": primary,
        "allocation": candidates[primary],
        "candidates": candidates,
        "aliases": aliases,
        "arguments": vars(args),
    }
    save_json(output, "selection.json", selection)
    print(
        f"Frozen primary: {candidates[primary]}; {len(candidates)} distinct candidates",
        flush=True,
    )
    evaluate_panel(
        candidates, training["scenarios"], priors(training), output, "training"
    )

    fresh_fields = []
    for replicate in [1, 2]:
        print(f"Build independent fresh population suite {replicate}/2", flush=True)
        field = build_field(
            args.seed + 10000 * replicate,
            args.samples,
            args.responses_per_order,
            fresh=True,
        )
        fresh_fields.append(field)
        label = f"validation{replicate}"
        save_field(output, label, field)
        evaluate_panel(candidates, field["scenarios"], priors(field), output, label)
    fresh = combine_fields(fresh_fields)
    report = evaluate_panel(
        candidates, fresh["scenarios"], priors(fresh), output, "validation"
    )
    describe_behavior(candidates, fresh, output)
    print(json.dumps(report["priors"]["balanced"], indent=2), flush=True)

    print("Separate copy/counter and historical audits", flush=True)
    targets = list(candidates)
    stresses, stress_meta = stress_populations(
        fresh, candidates, targets, args.seed + 30000
    )
    save_json(output, "stress_design.json", stress_meta)
    np.savez_compressed(
        output / "stress_populations.npz",
        names=np.array(list(stresses)),
        marginals=np.array(list(stresses.values())),
    )
    evaluate_panel(
        candidates, stresses, {"audit": np.ones(len(stresses))}, output, "stress"
    )
    historical = historical_populations()
    evaluate_panel(
        candidates,
        historical,
        {"audit": np.ones(len(historical))},
        output,
        "historical",
    )

    saved = json.loads(Path("results/equilibrium.json").read_text())
    equilibrium = marginals(saved["allocations"], saved["weights"])
    response, best = best_response(equilibrium)
    save_json(
        output,
        "equilibrium.json",
        {
            "best_response": response,
            "best_response_score": best,
            "exploitability": best - 7.5,
            "scores": dict(
                zip(
                    candidates,
                    score_allocations(list(candidates.values()), equilibrium),
                )
            ),
        },
    )
    save_json(
        output,
        "run.json",
        {
            "arguments": vars(args),
            "elapsed_seconds": perf_counter() - started,
            "training_scenarios": len(training["scenarios"]),
            "fresh_scenarios": len(fresh["scenarios"]),
            "stress_scenarios": len(stresses),
            "historical_scenarios": len(historical),
        },
    )
    print(f"Completed in {perf_counter()-started:.1f} seconds", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026110401)
    parser.add_argument("--samples", type=int, default=4000)
    parser.add_argument("--responses-per-order", type=int, default=8)
    parser.add_argument("--output", default="results/game1_final")
    run(parser.parse_args())
