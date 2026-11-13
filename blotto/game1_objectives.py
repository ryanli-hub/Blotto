"""Exact pure-allocation searches for several weighted Game 1 objectives."""

from math import comb

import numpy as np

from .game import BUDGET, VALUES, best_response, expected_rewards
from .game2_metrics import summarize_scores
from .robust import allocation_blocks


def search_objectives(
    scenarios,
    priors,
    tail_mass=0.2,
    tolerances=(0, 0.1, 0.25, 0.5),
    budget=BUDGET,
    values=VALUES,
    block_size=8192,
):
    """Search every legal five-castle allocation under each supplied prior."""
    if not isinstance(budget, (int, np.integer)) or budget < 0:
        raise ValueError("budget must be a nonnegative integer.")
    if not isinstance(block_size, (int, np.integer)) or block_size <= 0:
        raise ValueError("block_size must be a positive integer.")
    values = np.asarray(values, dtype=float)
    if values.shape != (5,) or not scenarios or not priors:
        raise ValueError(
            "Supply five castle values, scenarios, and at least one prior."
        )
    if not np.isfinite(tail_mass) or not 0 < tail_mass <= 1:
        raise ValueError("tail_mass must lie in (0, 1].")
    tolerances = np.asarray(tolerances, dtype=float)
    if (
        tolerances.ndim != 1
        or not np.all(np.isfinite(tolerances))
        or np.any(tolerances < 0)
    ):
        raise ValueError("Tail tolerances must be a finite nonnegative vector.")
    guard_names = [f"guard_{tolerance:.2f}" for tolerance in tolerances]
    if len(set(guard_names)) != len(guard_names):
        raise ValueError("Tail tolerances must have distinct two-decimal labels.")

    scenario_names = list(scenarios)
    prior_names = list(priors)
    populations = np.asarray([scenarios[name] for name in scenario_names], dtype=float)
    if populations.shape != (len(scenarios), 5, budget + 1):
        raise ValueError("Scenario tables must have shape (5, budget + 1).")
    rewards = np.stack([expected_rewards(row, values) for row in populations], axis=2)
    optimal_scores = np.array(
        [best_response(row, values, budget)[1] for row in populations]
    )
    weights = np.asarray([priors[name] for name in prior_names], dtype=float)
    if weights.shape != (len(priors), len(scenarios)):
        raise ValueError("Each prior needs one weight per scenario, in scenario order.")
    totals = weights.sum(axis=1)
    if (
        not np.all(np.isfinite(weights))
        or np.any(weights < 0)
        or not np.all(np.isfinite(totals))
        or np.any(totals <= 0)
    ):
        raise ValueError("Prior weights must be finite, nonnegative, and nonzero.")
    weights = weights / totals[:, None]
    mean_rewards = np.einsum("ps,kbs->pkb", weights, rewards)

    # Priors sharing positive scenarios also share the min/max-regret objectives.
    masks, mask_indices = [], []
    for row in weights:
        positive = row > 0
        index = next(
            (i for i, mask in enumerate(masks) if np.array_equal(mask, positive)), None
        )
        if index is None:
            index = len(masks)
            masks.append(positive)
        mask_indices.append(index)
    best_minimum = np.full(len(masks), -np.inf)
    best_regret = np.full(len(masks), np.inf)
    minimum_indices = np.zeros(len(masks), dtype=int)
    regret_indices = np.zeros(len(masks), dtype=int)

    count = comb(budget + 4, 4)
    allocation_dtype = np.int16 if budget <= np.iinfo(np.int16).max else np.int64
    allocations = np.empty((count, 5), dtype=allocation_dtype)
    means = np.empty((len(priors), count))
    tails = np.empty_like(means)
    castles = np.arange(5)
    completed, next_report = 0, 500_000

    for block in allocation_blocks(budget):
        for start in range(0, len(block), block_size):
            rows = block[start : start + block_size]
            end = completed + len(rows)
            allocations[completed:end] = rows
            scores = rewards[0, rows[:, 0]].copy()
            for castle in range(1, 5):
                scores += rewards[castle, rows[:, castle]]

            for index, mask in enumerate(masks):
                active_scores = scores[:, mask]
                minima = active_scores.min(axis=1)
                regrets = (optimal_scores[mask] - active_scores).max(axis=1)
                candidate = int(np.argmax(minima))
                if minima[candidate] > best_minimum[index]:
                    best_minimum[index] = minima[candidate]
                    minimum_indices[index] = completed + candidate
                candidate = int(np.argmin(regrets))
                if regrets[candidate] < best_regret[index]:
                    best_regret[index] = regrets[candidate]
                    regret_indices[index] = completed + candidate

            # Sort once; each prior reuses the same scenario order for its tail.
            order = np.argsort(scores, axis=1, kind="stable")
            sorted_scores = np.take_along_axis(scores, order, axis=1)
            for prior, row_weights in enumerate(weights):
                means[prior, completed:end] = mean_rewards[prior, castles, rows].sum(
                    axis=1
                )
                sorted_weights = row_weights[order]
                mass_before = np.cumsum(sorted_weights, axis=1) - sorted_weights
                included_mass = np.clip(tail_mass - mass_before, 0, sorted_weights)
                tails[prior, completed:end] = (
                    np.einsum("ij,ij->i", sorted_scores, included_mass) / tail_mass
                )
            completed = end
            if completed >= next_report or (completed == count and count >= 500_000):
                print(
                    f"  Exact Game 1 search: {completed:,}/{count:,} allocations",
                    flush=True,
                )
                next_report = completed + 500_000

    if completed != count:
        raise RuntimeError("Allocation enumeration did not cover the full legal set.")
    result = {
        "allocations_examined": completed,
        "scenario_order": scenario_names,
        "optimal_scores": optimal_scores.tolist(),
        "tail_mass": float(tail_mass),
        "tolerances": tolerances.tolist(),
        "priors": {},
    }
    for prior, name in enumerate(prior_names):
        mask_index = mask_indices[prior]
        choices = {
            "mean": int(np.argmax(means[prior])),
            "tail": int(np.argmax(tails[prior])),
            "maximin": int(minimum_indices[mask_index]),
            "minimax_regret": int(regret_indices[mask_index]),
        }
        for label, tolerance in zip(guard_names, tolerances):
            feasible = tails[prior] >= tails[prior].max() - tolerance - 1e-12
            choices[label] = int(np.argmax(np.where(feasible, means[prior], -np.inf)))

        mixture = np.einsum("s,skb->kb", weights[prior], populations)
        _, dp_score = best_response(mixture, values, budget)
        if not np.isclose(means[prior, choices["mean"]], dp_score, atol=1e-10, rtol=0):
            raise RuntimeError("Enumerated weighted mean disagrees with the exact DP.")

        selected = allocations[list(choices.values())]
        selected_scores = rewards[0, selected[:, 0]].copy()
        for castle in range(1, 5):
            selected_scores += rewards[castle, selected[:, castle]]
        metrics = summarize_scores(
            selected_scores, weights[prior], optimal_scores, tail_mass
        )
        result["priors"][name] = {
            "weights": weights[prior].tolist(),
            "mean_dp_score": float(dp_score),
            "choices": {
                label: {
                    "allocation": selected[i].tolist(),
                    **{metric: float(vector[i]) for metric, vector in metrics.items()},
                }
                for i, label in enumerate(choices)
            },
        }
    return result
