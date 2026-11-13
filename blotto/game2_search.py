"""Sampled responses, finite reasoning, and robust candidate selection for Game 2."""

import numpy as np

from .game2 import evaluate_candidates, prepare_triples
from .game2_population import mix_populations, population, sample_triples


def neighbors(allocations, steps=(1, 2, 5, 10)):
    """Move soldiers between two castles while preserving the budget."""
    rows = [np.asarray(row).copy() for row in allocations]
    for row in allocations:
        for donor in range(5):
            for receiver in range(5):
                if donor == receiver:
                    continue
                for amount in steps:
                    if row[donor] >= amount:
                        moved = np.asarray(row).copy()
                        moved[donor] -= amount
                        moved[receiver] += amount
                        rows.append(moved)
    return np.unique(rows, axis=0)


def sampled_scores(candidates, opponents, groups, rng):
    """Use common random opponents to compare all candidate allocations."""
    triples = sample_triples(opponents, groups, rng)
    return evaluate_candidates(candidates, prepare_triples(triples))


def response_search(candidates, opponents, rng, screen=2048, check=8192, count=12):
    """Screen broadly, refine promising allocations, then independently rescore."""
    scores = sampled_scores(candidates, opponents, screen, rng)
    order = np.argsort(-scores, kind="stable")
    refined = np.unique(
        np.vstack([candidates[order[:64]], neighbors(candidates[order[:6]])]), axis=0
    )
    scores = sampled_scores(refined, opponents, check, rng)
    order = np.argsort(-scores, kind="stable")
    selected = []
    # Multiple nearby strong choices represent different submissions by peers.
    for index in order:
        if scores[index] < scores[order[0]] - 0.12:
            break
        row = refined[index]
        if not selected or all(np.abs(row - other).sum() >= 4 for other in selected):
            selected.append(row)
        if len(selected) == count:
            break
    return population(selected), {
        "screen_candidates": len(candidates),
        "refined_candidates": len(refined),
        "screen_groups": screen,
        "check_groups": check,
        "best_allocation": refined[order[0]].tolist(),
        "estimated_best_score": float(scores[order[0]]),
        "response_support": len(selected),
    }


def finite_reasoning(components, candidates, rng, depth=3, screen=2048, check=8192):
    """Each level predicts a mixture of base players and earlier reasoning levels."""
    beliefs = [(0.05, 0.10, 0.50), (0.00, 0.30, 0.80), (0.10, 0.30, 0.20)]
    levels, diagnostics = [], []
    for level in range(depth):
        responses = []
        earlier = mix_populations(levels, np.ones(level)) if level else None
        for belief, (h_share, t_share, a_share) in enumerate(beliefs):
            base = mix_populations(
                [components[key] for key in ("H", "C", "TA", "TB")],
                [
                    h_share,
                    1 - h_share - t_share,
                    t_share * a_share,
                    t_share * (1 - a_share),
                ],
            )
            strategic_share = [0.35, 0.50, 0.65][belief] if level else 0
            predicted = (
                mix_populations([base, earlier], [1 - strategic_share, strategic_share])
                if level
                else base
            )
            response, diagnostic = response_search(
                candidates, predicted, rng, screen, check
            )
            responses.append(response)
            diagnostics.append(
                {
                    "level": level + 1,
                    "belief_H": h_share,
                    "belief_T": t_share,
                    "belief_A_within_T": a_share,
                    "belief_earlier_levels": strategic_share,
                    **diagnostic,
                }
            )
        levels.append(mix_populations(responses, np.ones(len(responses))))
    return levels, diagnostics


def evaluate_scenarios(candidates, scenarios, groups, rng):
    """Return a candidate-by-scenario matrix of sampled mean payouts."""
    columns = []
    for index, (name, opponents) in enumerate(scenarios.items(), 1):
        columns.append(sampled_scores(candidates, opponents, groups, rng))
        if index % 12 == 0:
            print(f"  Scored {index}/{len(scenarios)} scenarios", flush=True)
    return np.column_stack(columns)


def maximum_regrets(scores):
    """Shortfalls from the best searched candidate in each sampled scenario."""
    return (scores.max(axis=0) - scores).max(axis=1)


def shortlist_indices(scores, robust_count=32, per_scenario=4):
    """Keep both robust choices and specialists for every tested population."""
    robust = np.argsort(maximum_regrets(scores), kind="stable")[:robust_count]
    specialists = np.argsort(-scores, axis=0, kind="stable")[:per_scenario].ravel()
    return np.unique(np.r_[robust, specialists])


def independent_evaluation(candidates, reference, opponents, groups, rng, batch=8192):
    """Estimate scores and paired gaps to a reference frozen before this draw."""
    rows = np.vstack([candidates, reference])
    sums = np.zeros(len(rows))
    squares = np.zeros(len(rows))
    gap_sums = np.zeros(len(candidates))
    gap_squares = np.zeros(len(candidates))
    for start in range(0, groups, batch):
        triples = sample_triples(opponents, min(batch, groups - start), rng)
        samples = evaluate_candidates(
            rows, prepare_triples(triples), return_samples=True
        )
        sums += samples.sum(axis=1)
        squares += (samples * samples).sum(axis=1)
        gaps = samples[-1] - samples[:-1]
        gap_sums += gaps.sum(axis=1)
        gap_squares += (gaps * gaps).sum(axis=1)

    def standard_error(total, squared):
        variance = np.maximum((squared - total * total / groups) / (groups - 1), 0)
        return np.sqrt(variance / groups)

    return {
        "scores": (sums[:-1] / groups).tolist(),
        "score_standard_errors": standard_error(sums, squares)[:-1].tolist(),
        "reference": np.asarray(reference).tolist(),
        "reference_score": float(sums[-1] / groups),
        "score_gaps": (gap_sums / groups).tolist(),
        "gap_standard_errors": standard_error(gap_sums, gap_squares).tolist(),
        "groups": groups,
    }
