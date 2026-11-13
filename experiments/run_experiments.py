"""Compare fixed Game 1 allocations under revised population assumptions."""

import argparse
import json
from pathlib import Path

import numpy as np

from blotto.dynamics import (
    double_oracle,
    finite_reasoning_population,
    near_best_responses,
)
from blotto.game import best_response, marginals
from blotto.opponents import considered_population, shallow_population
from blotto.robust import minimax_regret, score_allocations


CANDIDATES = {
    "teammate": [2, 16, 1, 37, 44],
    "previous_eight": [1, 2, 2, 40, 55],
    "previous_broad": [2, 2, 3, 39, 54],
}
STYLES = {
    "manual_heavy": {"response_share": 0.25, "depth_weights": [0.70, 0.25, 0.05]},
    "balanced": {"response_share": 0.50, "depth_weights": [0.35, 0.45, 0.20]},
    "computation_heavy": {"response_share": 0.75, "depth_weights": [0.15, 0.35, 0.50]},
}
SHIFTS = {
    "higher_small_bids": {"small_bid_probabilities": [0.02, 0.08, 0.25, 0.40, 0.25]},
    "rounding_and_avoidance": {
        "round_five_probability": 0.75,
        "high_castle_penalty": 0.25,
        "noise_sigma": 0.35,
    },
}


def save_json(directory, name, data):
    def encode(value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        raise TypeError(type(value).__name__)

    (directory / name).write_text(
        json.dumps(data, indent=2, default=encode) + "\n", encoding="utf-8"
    )


def make_profiles(samples, seed, shifted=False):
    specifications = (
        SHIFTS if shifted else {name: {} for name in ("base", "overbid", "avoid_high")}
    )
    return {
        name: considered_population(
            samples=samples,
            seed=seed + index,
            profile="base" if shifted else name,
            overrides=overrides,
        )
        for index, (name, overrides) in enumerate(specifications.items())
    }


def make_advice(shallow, profile, seed):
    belief = 0.05 * shallow + 0.95 * profile["marginals"]
    allocations = near_best_responses(belief, count=3, slack=0.05, seed=seed)
    weights = [0.60, 0.30, 0.10]
    return {
        "allocations": allocations,
        "weights": weights,
        "marginals": marginals(allocations, weights),
    }


def make_scenarios(profiles, references, h_shares, styles, seed, slack=0.10):
    """Rebuild finite responders for each actual C profile and H share."""
    shallow = shallow_population()
    rng = np.random.default_rng(seed)
    scenarios, metadata, contexts = {}, {}, {}
    depth = len(next(iter(styles.values()))["depth_weights"])
    for profile_name, profile in profiles.items():
        concentrated = profile["marginals"]
        for h_share in h_shares:
            belief_h_shares = np.unique(
                np.clip([h_share - 0.05, h_share, h_share + 0.05], 0, 0.15)
            )
            beliefs = [
                belief_h * shallow
                + (1 - belief_h) * (0.70 * concentrated + 0.30 * reference["marginals"])
                for belief_h in belief_h_shares
                for reference in references.values()
            ]
            # Random ordering prevents belief type from determining response share.
            beliefs = np.asarray(beliefs)[rng.permutation(len(beliefs))]
            response = finite_reasoning_population(
                beliefs,
                samples_per_belief=24,
                slack=slack,
                seed=int(rng.integers(0, 2**32)),
                depth=depth,
            )
            context_name = f"{profile_name}/h{round(100 * h_share):02d}"
            contexts[context_name] = {
                "parameters": response["parameters"],
                "diagnostics": response["diagnostics"],
                "belief_h_shares": belief_h_shares,
            }
            for style_name, style in styles.items():
                smart = np.average(
                    response["depth_marginals"], axis=0, weights=style["depth_weights"]
                )
                response_share = style["response_share"]
                name = f"{context_name}/{style_name}"
                scenarios[name] = h_share * shallow + (1 - h_share) * (
                    (1 - response_share) * concentrated + response_share * smart
                )
                metadata[name] = {
                    "H": h_share,
                    "C": (1 - h_share) * (1 - response_share),
                    "S": (1 - h_share) * response_share,
                    "profile": profile_name,
                    "depth_weights": style["depth_weights"],
                    "S_marginals": smart,
                }
    return {"scenarios": scenarios, "metadata": metadata, "contexts": contexts}


def clustered_scenarios(base, advice, fraction):
    scenarios, metadata = {}, {}
    for name, population in base["scenarios"].items():
        if not name.startswith("base/") or not name.endswith("/balanced"):
            continue
        info = base["metadata"][name]
        shifted = population + info["S"] * fraction * (
            advice["marginals"] - info["S_marginals"]
        )
        scenarios[name + "/shared_advice"] = shifted
        metadata[name + "/shared_advice"] = {**info, "advice_fraction_of_S": fraction}
    return {"scenarios": scenarios, "metadata": metadata}


def evaluate(candidates, scenarios):
    names = list(scenarios)
    optima = np.array(
        [best_response(population)[1] for population in scenarios.values()]
    )
    scores = np.column_stack(
        [
            score_allocations(list(candidates.values()), population)
            for population in scenarios.values()
        ]
    )
    rows = {}
    for index, (name, allocation) in enumerate(candidates.items()):
        regrets = optima - scores[index]
        worst = int(np.argmax(regrets))
        rows[name] = {
            "allocation": allocation,
            "scores": dict(zip(names, scores[index])),
            "regrets": dict(zip(names, regrets)),
            "max_regret": float(regrets[worst]),
            "worst_scenario": names[worst],
            "min_score": float(scores[index].min()),
            "max_score": float(scores[index].max()),
        }
    return {"optimal_scores": dict(zip(names, optima)), "candidates": rows}


def equilibrium_diagnostics(candidates, central_profile, output):
    old_result = Path(__file__).resolve().parents[1] / "results/equilibrium.json"
    equilibrium = (
        json.loads(old_result.read_text())
        if old_result.exists()
        else double_oracle(tolerance=1e-8, max_iterations=1500)
    )
    equilibrium_marginal = marginals(equilibrium["allocations"], equilibrium["weights"])
    epsilon = best_response(equilibrium_marginal)[1] - 7.5
    if epsilon > 1e-7:
        raise ValueError("The equilibrium certificate failed.")
    # Central composition is 5% H, 47.5% C, 47.5% S.
    fixed_weight = 0.525
    background = (
        0.05 * shallow_population() + 0.475 * central_profile["marginals"]
    ) / fixed_weight
    adaptive = double_oracle(
        background=background,
        background_weight=fixed_weight,
        tolerance=1e-6,
        max_iterations=1500,
    )
    smart = marginals(adaptive["allocations"], adaptive["weights"])
    population = fixed_weight * background + (1 - fixed_weight) * smart
    save_json(output, "adaptive_diagnostic.json", adaptive)
    return {
        "equilibrium_epsilon": epsilon,
        "adaptive_residual": adaptive["population_exploitability"],
        "adaptive_converged": adaptive["converged"],
        "adaptive_iterations": adaptive["iterations"],
        **evaluate(
            candidates,
            {"E": equilibrium_marginal, "fully_adjusted_population": population},
        ),
    }


def build_population_suite(samples=4000, seed=20261103):
    """Build the 40 selection and 34 validation populations, without searching."""
    profiles = make_profiles(samples, seed)
    advice = make_advice(shallow_population(), profiles["base"], seed + 100)
    train = make_scenarios(
        profiles, profiles, [0, 0.05, 0.10, 0.15], STYLES, seed + 200
    )
    clustered = clustered_scenarios(train, advice, 0.25)
    train["scenarios"].update(clustered["scenarios"])
    train["metadata"].update(clustered["metadata"])

    fresh_profiles = make_profiles(samples, seed + 10000)
    fresh = make_scenarios(
        fresh_profiles, fresh_profiles, [0.05, 0.15], STYLES, seed + 10200
    )
    shifted_profiles = make_profiles(samples, seed + 20000, shifted=True)
    shifted = make_scenarios(
        shifted_profiles, fresh_profiles, [0, 0.15], STYLES, seed + 20200
    )
    deep_styles = {
        "depth_four": {
            "response_share": 0.75,
            "depth_weights": [0.05, 0.15, 0.30, 0.50],
        }
    }
    deep = make_scenarios(
        {"base": fresh_profiles["base"]},
        fresh_profiles,
        [0.05, 0.15],
        deep_styles,
        seed + 30000,
        slack=0.05,
    )
    fresh_advice = make_advice(
        shallow_population(), fresh_profiles["base"], seed + 10100
    )
    crowded = clustered_scenarios(fresh, fresh_advice, 0.50)
    validation_groups = {
        "fresh": fresh,
        "shifted": shifted,
        "deep": deep,
        "crowded": crowded,
    }
    validation = {
        f"{group}/{name}": population
        for group, data in validation_groups.items()
        for name, population in data["scenarios"].items()
    }
    populations = {
        "training": train,
        "validation": validation_groups,
        "C_parameters": {
            group: {name: profile["parameters"] for name, profile in values.items()}
            for group, values in {
                "training": profiles,
                "fresh": fresh_profiles,
                "shifted": shifted_profiles,
            }.items()
        },
        "advice": {"training": advice, "validation": fresh_advice},
        "base_C_marginals": {
            "training": profiles["base"]["marginals"],
            "fresh": fresh_profiles["base"]["marginals"],
        },
    }
    assert len(train["scenarios"]) == 40 and len(validation) == 34

    return populations


def run(args):
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    design = {
        "seed": args.seed,
        "C_samples_per_profile": args.samples,
        "H_shares": [0, 0.05, 0.10, 0.15],
        "styles": STYLES,
        "near_best_slack": 0.10,
        "samples_per_belief": 24,
        "training_advice_fraction_of_S": 0.25,
        "validation_seeds": {
            "fresh": args.seed + 10000,
            "shifted": args.seed + 20000,
            "deep": args.seed + 30000,
        },
        "validation_shifts": SHIFTS,
        "validation_deep_weights": [0.05, 0.15, 0.30, 0.50],
        "validation_deep_slack": 0.05,
        "validation_advice_fraction_of_S": 0.50,
        "selection_objective": "maximum regret across 40 primary scenarios",
        "existing_candidates": CANDIDATES,
    }
    save_json(output, "design.json", design)
    print("Building selection and validation populations...", flush=True)
    populations = build_population_suite(args.samples, args.seed)
    train = populations["training"]
    validation_groups = populations["validation"]
    validation = {
        f"{group}/{name}": population
        for group, data in validation_groups.items()
        for name, population in data["scenarios"].items()
    }
    base_C = populations["base_C_marginals"]["training"]
    save_json(output, "populations.json", populations)

    print(
        "Searching all 4,598,126 legal allocations across 40 training scenarios...",
        flush=True,
    )
    optimum = minimax_regret(train["scenarios"])
    candidates = {**CANDIDATES, "new_minimax": optimum["allocation"]}
    training_result = evaluate(candidates, train["scenarios"])
    validation_result = evaluate(candidates, validation)
    print(
        f"Selected {optimum['allocation']}; training max regret {optimum['max_regret']:.6f}",
        flush=True,
    )
    for name, result in validation_result["candidates"].items():
        print(f"{name}: validation max regret {result['max_regret']:.6f}", flush=True)

    neighbors = {}
    winner = np.array(optimum["allocation"])
    for donor in range(5):
        for receiver in range(5):
            if donor != receiver and winner[donor] > 0:
                neighbor = winner.copy()
                neighbor[donor] -= 1
                neighbor[receiver] += 1
                neighbors[f"{donor + 1}_to_{receiver + 1}"] = neighbor.tolist()
    neighborhood = {
        "training": evaluate(neighbors, train["scenarios"]),
        "validation": evaluate(neighbors, validation),
    }
    save_json(output, "neighbors.json", neighborhood)
    result = {
        "design": design,
        "search": optimum,
        "training": training_result,
        "validation": validation_result,
        "central_components": evaluate(
            candidates,
            {
                "H": shallow_population(),
                "C": base_C,
                "S": train["metadata"]["base/h05/balanced"]["S_marginals"],
            },
        ),
        "validation_by_group": {
            group: evaluate(candidates, data["scenarios"])
            for group, data in validation_groups.items()
        },
    }
    save_json(output, "comparison.json", result)
    print(
        "Checking equilibrium and fully adjusted population separately...", flush=True
    )
    result["diagnostics"] = equilibrium_diagnostics(
        candidates, {"marginals": base_C}, output
    )
    save_json(output, "comparison.json", result)
    print(f"Done. Results: {output / 'comparison.json'}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261103)
    parser.add_argument("--samples", type=int, default=4000)
    parser.add_argument("--output", default="results/revised")
    run(parser.parse_args())
