"""Choose a fixed allocation when a small group reasons one step further."""

import argparse
import json
from pathlib import Path

import numpy as np

from blotto.dynamics import near_best_responses
from blotto.game import best_response, marginals, payoff
from blotto.robust import minimax_regret, score_allocations
from experiments.run_experiments import CANDIDATES, build_population_suite, evaluate, save_json


CURRENT = [8, 9, 10, 11, 62]
SHARE_CAP = 0.15
SAMPLE_COUNT = 48


def flatten_suite(suite):
    populations = {
        f"original/{name}": np.asarray(population)
        for name, population in suite["training"]["scenarios"].items()
    }
    for group, data in suite["validation"].items():
        populations.update(
            {
                f"{group}/{name}": np.asarray(population)
                for name, population in data["scenarios"].items()
            }
        )
    return populations


def local_allocations(allocation):
    """Include the center and all legal transfers of one soldier."""
    center = np.asarray(allocation)
    rows = [center.copy()]
    for donor in range(5):
        for receiver in range(5):
            if donor != receiver and center[donor] > 0:
                row = center.copy()
                row[donor] -= 1
                row[receiver] += 1
                rows.append(row)
    return np.asarray(rows)


def response_sample(belief, rng, slack):
    allocations = near_best_responses(
        belief,
        count=SAMPLE_COUNT,
        slack=slack,
        seed=int(rng.integers(0, 2**32)),
    )
    return {"allocations": allocations, "marginals": marginals(allocations)}


def build_advanced_types(bases, shared, belief_shares, seed, slack):
    """Peers optimize Q; anticipators optimize a belief containing peers."""
    rng = np.random.default_rng(seed)
    types, supports = {}, {}
    for name, population in bases.items():
        peers = response_sample(population, rng, slack)
        local_types = {"peers_model": peers["marginals"], "peers_shared": shared}
        local_supports = {"peers_model": peers["allocations"]}
        for peer_name, peer_population in list(local_types.items()):
            for beta in belief_shares:
                belief = (1 - beta) * population + beta * peer_population
                result = response_sample(belief, rng, slack)
                key = f"anticipate_{peer_name}/belief{round(100 * beta):02d}"
                local_types[key] = result["marginals"]
                local_supports[key] = result["allocations"]
        types[name] = local_types
        supports[name] = local_supports
    return {"types": types, "supports": supports}


def endpoint_scenarios(bases, types, cap=SHARE_CAP):
    scenarios = {}
    for name, population in bases.items():
        scenarios[f"{name}/base"] = population
        for kind, advanced in types[name].items():
            scenarios[f"{name}/{kind}/share{round(100 * cap):02d}"] = (
                1 - cap
            ) * population + cap * advanced
    return scenarios


def shared_types(bases, types):
    return {name: types for name in bases}


def direct_counter_types(allocation, seed):
    target = marginals([allocation])
    exact, score = best_response(target)
    sampled = near_best_responses(target, count=96, slack=0, seed=seed)
    return {
        "types": {
            "exact_counter": marginals([exact]),
            "diverse_counters": marginals(sampled),
        },
        "exact_counter": exact,
        "counter_score": score,
        "target_score": payoff(allocation, exact),
        "sampled_allocations": sampled,
    }


def evaluate_share_curve(candidates, bases, types):
    result = {}
    for share in [0, 0.05, 0.10, 0.15, 0.25]:
        evaluation = evaluate(candidates, endpoint_scenarios(bases, types, share))
        result[f"{share:.2f}"] = {
            name: {
                key: row[key]
                for key in ("max_regret", "worst_scenario", "min_score", "max_score")
            }
            for name, row in evaluation["candidates"].items()
        }
    return result


def equilibrium_checks(candidates, source):
    equilibrium = json.loads((source.parent / "equilibrium.json").read_text())
    adaptive = json.loads((source / "adaptive_diagnostic.json").read_text())
    saved = json.loads((source / "populations.json").read_text())
    central = np.asarray(saved["training"]["scenarios"]["base/h05/balanced"])
    finite_s = np.asarray(
        saved["training"]["metadata"]["base/h05/balanced"]["S_marginals"]
    )
    fixed_part = central - 0.475 * finite_s
    full_population = fixed_part + 0.475 * marginals(
        adaptive["allocations"], adaptive["weights"]
    )
    return evaluate(
        candidates,
        {
            "E": marginals(equilibrium["allocations"], equilibrium["weights"]),
            "fully_adjusted_population": full_population,
        },
    )


def feedback_opponents(bases, candidates, seed):
    """All candidates face the same responses to a pool of distinct strategies."""
    allocations = list(dict.fromkeys(map(tuple, candidates.values())))
    peer_pool = marginals(allocations)
    rng = np.random.default_rng(seed)
    types, supports = {}, {}
    for name, population in bases.items():
        response = response_sample(0.85 * population + 0.15 * peer_pool, rng, 0.05)
        types[name] = {"after_selection": response["marginals"]}
        supports[name] = response["allocations"]
    counters, details, seen = {}, {}, set()
    for index, (name, allocation) in enumerate(candidates.items()):
        if tuple(allocation) in seen:
            continue
        seen.add(tuple(allocation))
        item = direct_counter_types(allocation, seed + 1000 + index)
        details[name] = item
        counters.update(
            {f"target_{name}/{key}": value for key, value in item["types"].items()}
        )
    return {
        "types": types,
        "supports": supports,
        "direct_types": counters,
        "direct_counters": details,
        "feedback": endpoint_scenarios(bases, types),
        "targeted": endpoint_scenarios(bases, shared_types(bases, counters)),
    }


def constrained_refinement(args, known_scenarios, known_bases, candidates):
    """One final search preserves old scores; a third fresh suite checks it."""
    output = Path(args.output)
    design = {
        "maximum_base_score_loss": 0.10,
        "reference": CURRENT,
        "known_bases": len(known_bases),
        "known_scenarios": len(known_scenarios),
        "validation_seed": 20510329,
        "belief_shares": [0.10, 0.20],
        "near_best_slack": 0.075,
        "advanced_share_cap": SHARE_CAP,
        "purpose": "preserve each known base score, then minimize worst regret including observed follow-on responses",
    }
    save_json(output, "refinement_design.json", design)
    print(
        "Building the third fresh validation suite for constrained refinement...",
        flush=True,
    )
    fresh = flatten_suite(
        build_population_suite(args.samples, design["validation_seed"])
    )
    advanced = build_advanced_types(
        fresh,
        marginals(local_allocations(CURRENT)),
        design["belief_shares"],
        design["validation_seed"] + 500,
        design["near_best_slack"],
    )
    floors = {
        name: (population, float(score_allocations([CURRENT], population)[0]) - 0.10)
        for name, population in known_bases.items()
    }
    print(f"Searching with {len(floors)} base-score constraints...", flush=True)
    optimum = minimax_regret(
        known_scenarios, initial_allocation=CURRENT, score_floors=floors
    )
    candidates = {**candidates, "refined": optimum["allocation"]}
    focused = {name: candidates[name] for name in ["current", "main", "refined"]}
    checks = feedback_opponents(fresh, focused, design["validation_seed"] + 1000)
    primary = endpoint_scenarios(fresh, advanced["types"])
    combined = {**primary, **checks["feedback"], **checks["targeted"]}
    all_types = {
        name: {
            **advanced["types"][name],
            **checks["types"][name],
            **checks["direct_types"],
        }
        for name in fresh
    }
    known_base_scores = evaluate(candidates, known_bases)
    fresh_base_scores = evaluate(candidates, fresh)
    base_losses = {}
    for label, evaluation in [
        ("known", known_base_scores),
        ("fresh", fresh_base_scores),
    ]:
        reference = evaluation["candidates"]["current"]["scores"]
        base_losses[label] = {
            name: max(reference[key] - score for key, score in row["scores"].items())
            for name, row in evaluation["candidates"].items()
        }
    result = {
        "design": design,
        "search": optimum,
        "counts": {
            "fresh_bases": len(fresh),
            "primary": len(primary),
            "combined": len(combined),
        },
        "known": evaluate(candidates, known_scenarios),
        "known_base": known_base_scores,
        "fresh_base": fresh_base_scores,
        "base_score_losses": base_losses,
        "primary": evaluate(candidates, primary),
        "feedback": evaluate(candidates, checks["feedback"]),
        "targeted": evaluate(candidates, checks["targeted"]),
        "combined": evaluate(candidates, combined),
        "primary_share_curve": evaluate_share_curve(focused, fresh, advanced["types"]),
        "combined_share_curve": evaluate_share_curve(focused, fresh, all_types),
        "equilibrium": equilibrium_checks(candidates, Path(args.source)),
    }
    save_json(
        output,
        "refinement_populations.json",
        {"bases": fresh, "advanced": advanced, "checks": checks},
    )
    save_json(output, "refinement.json", result)
    print(
        f"Refined: {optimum['allocation']}; third-suite combined regrets:", flush=True
    )
    for name in focused:
        print(
            f"{name}: {result['combined']['candidates'][name]['max_regret']:.6f}",
            flush=True,
        )
    return result


def run(args):
    output, source = Path(args.output), Path(args.source)
    output.mkdir(parents=True, exist_ok=True)
    design = {
        "current": CURRENT,
        "advanced_share_cap": SHARE_CAP,
        "training_belief_shares": [0.05, 0.15],
        "training_slack": 0.10,
        "validation_belief_shares": [0.10, 0.25],
        "validation_slack": 0.05,
        "response_samples": SAMPLE_COUNT,
        "training_seed": args.seed,
        "validation_seeds": [20270117, 20390117],
        "C_samples": args.samples,
        "development_bases": "all 74 previously observed populations",
        "main_objective": "minimax regret with total added peer/anticipator share from 0 to 15 percent",
        "guarded_objective": "same objective plus direct counters to the previous current allocation",
        "validation_shared_peers": "current allocation and all legal one-soldier transfers, equal weights",
        "feedback_belief_share": 0.15,
        "feedback_peer_pool": "equal mixture of distinct current, main winner, and guarded winner allocations",
        "share_curve": [0, 0.05, 0.10, 0.15, 0.25],
    }
    save_json(output, "design.json", design)
    bases = flatten_suite(json.loads((source / "populations.json").read_text()))
    training = build_advanced_types(
        bases, marginals([CURRENT]), [0.05, 0.15], args.seed, 0.10
    )
    main_scenarios = endpoint_scenarios(bases, training["types"])
    direct = direct_counter_types(CURRENT, args.seed + 1)
    direct_scenarios = endpoint_scenarios(bases, shared_types(bases, direct["types"]))
    guarded_scenarios = {**main_scenarios, **direct_scenarios}

    print("Building two fresh validation populations before selection...", flush=True)
    validation_bases, validation_types, validation_supports = {}, {}, {}
    for seed in design["validation_seeds"]:
        fresh = flatten_suite(build_population_suite(args.samples, seed))
        fresh = {f"seed{seed}/{name}": population for name, population in fresh.items()}
        advanced = build_advanced_types(
            fresh, marginals(local_allocations(CURRENT)), [0.10, 0.25], seed + 500, 0.05
        )
        validation_bases.update(fresh)
        validation_types.update(advanced["types"])
        validation_supports.update(advanced["supports"])
    validation_scenarios = endpoint_scenarios(validation_bases, validation_types)
    save_json(
        output,
        "populations.json",
        {
            "training_bases": bases,
            "training_types": training,
            "validation_bases": validation_bases,
            "validation_types": {
                "types": validation_types,
                "supports": validation_supports,
            },
            "direct_counter": direct,
        },
    )

    print(f"Searching {len(main_scenarios)} main endpoint scenarios...", flush=True)
    main = minimax_regret(main_scenarios, initial_allocation=CURRENT)
    print(f"Main: {main['allocation']}, regret {main['max_regret']:.6f}", flush=True)
    print(
        f"Searching {len(guarded_scenarios)} guarded endpoint scenarios...", flush=True
    )
    guarded = minimax_regret(guarded_scenarios, initial_allocation=main["allocation"])
    print(
        f"Guarded: {guarded['allocation']}, regret {guarded['max_regret']:.6f}",
        flush=True,
    )
    candidates = {
        **CANDIDATES,
        "current": CURRENT,
        "main": main["allocation"],
        "guarded": guarded["allocation"],
    }

    checks = feedback_opponents(
        validation_bases,
        {name: candidates[name] for name in ["current", "main", "guarded"]},
        args.seed + 1000,
    )
    feedback, future_targeted = checks["feedback"], checks["targeted"]

    results = {
        "design": design,
        "main_search": main,
        "guarded_search": guarded,
        "counts": {
            "development_bases": len(bases),
            "main": len(main_scenarios),
            "guarded": len(guarded_scenarios),
            "validation_bases": len(validation_bases),
            "validation": len(validation_scenarios),
        },
        "base": evaluate(candidates, bases),
        "main": evaluate(candidates, main_scenarios),
        "guarded": evaluate(candidates, guarded_scenarios),
        "validation": evaluate(candidates, validation_scenarios),
        "validation_by_seed": {
            str(seed): evaluate(
                candidates,
                {
                    name: q
                    for name, q in validation_scenarios.items()
                    if name.startswith(f"seed{seed}/")
                },
            )
            for seed in design["validation_seeds"]
        },
        "feedback": evaluate(candidates, feedback),
        "direct_old": evaluate(
            candidates,
            endpoint_scenarios(
                validation_bases, shared_types(validation_bases, direct["types"])
            ),
        ),
        "direct_future": evaluate(candidates, future_targeted),
        "share_curve": evaluate_share_curve(
            candidates, validation_bases, validation_types
        ),
        "equilibrium": equilibrium_checks(candidates, source),
    }
    save_json(
        output,
        "feedback.json",
        checks,
    )
    save_json(output, "comparison.json", results)
    for name, row in results["validation"]["candidates"].items():
        print(
            f"{name}: {row['allocation']}; validation regret {row['max_regret']:.6f}",
            flush=True,
        )
    constrained_refinement(
        args,
        {**guarded_scenarios, **validation_scenarios, **feedback, **future_targeted},
        {**bases, **validation_bases},
        candidates,
    )
    print(f"Done: {output / 'comparison.json'}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="results/revised")
    parser.add_argument("--output", default="results/anticipation")
    parser.add_argument("--seed", type=int, default=20261107)
    parser.add_argument("--samples", type=int, default=4000)
    run(parser.parse_args())
