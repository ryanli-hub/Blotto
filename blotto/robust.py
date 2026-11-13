"""Exact pure-strategy minimax regret over specified Game 1 scenarios."""

import numpy as np

from .game import BUDGET, VALUES, best_response, expected_rewards, validate_allocations


def allocation_blocks(budget=BUDGET):
    """Enumerate five-castle allocations in bounded-memory blocks."""
    for first in range(budget + 1):
        pieces = []
        for second in range(budget - first + 1):
            remaining = budget - first - second
            third = np.repeat(np.arange(remaining + 1), np.arange(remaining + 1, 0, -1))
            fourth = np.concatenate(
                [np.arange(remaining - t + 1) for t in range(remaining + 1)]
            )
            pieces.append(
                np.column_stack(
                    [
                        np.full(len(third), first),
                        np.full(len(third), second),
                        third,
                        fourth,
                        remaining - third - fourth,
                    ]
                )
            )
        yield np.concatenate(pieces)


def score_allocations(allocations, marginal, values=VALUES):
    """One expected castle score per allocation, with no Monte Carlo matchups."""
    rewards = expected_rewards(marginal, values)
    allocations = validate_allocations(allocations, rewards.shape[1] - 1, len(values))
    return rewards[np.arange(len(values)), allocations].sum(axis=1)


def minimax_regret(
    scenarios,
    budget=BUDGET,
    values=VALUES,
    initial_allocation=None,
    score_floors=None,
):
    """Minimize the largest shortfall from each scenario's exact optimum."""
    if len(values) != 5 or not scenarios:
        raise ValueError("Enumeration requires five castles and at least one scenario.")
    names = list(scenarios)
    responses = [best_response(scenarios[name], values, budget) for name in names]
    optima = np.array([score for _, score in responses])
    rewards = np.array([expected_rewards(scenarios[name], values) for name in names])
    castles = np.arange(len(values))
    tolerance = 1e-12
    floor_rewards = []
    floor_minima = []
    if score_floors:
        if initial_allocation is None:
            raise ValueError(
                "Score floors require an explicit feasible initial allocation."
            )
        for population, minimum_score in score_floors.values():
            if not np.isfinite(minimum_score):
                raise ValueError("Score floors must be finite.")
            floor_rewards.append(expected_rewards(population, values))
            floor_minima.append(float(minimum_score))
    if initial_allocation is None:
        initial_allocation = responses[0][0]
    initial = validate_allocations(initial_allocation, budget, len(values))
    if len(initial) != 1:
        raise ValueError("Supply one initial allocation.")
    best_allocation = initial[0].tolist()
    for reward, minimum in zip(floor_rewards, floor_minima):
        if reward[castles, best_allocation].sum() < minimum - tolerance:
            raise ValueError("The initial allocation must satisfy every score floor.")
    initial_scores = rewards[:, castles, best_allocation].sum(axis=1)
    initial_regrets = optima - initial_scores
    best_regret = float(initial_regrets.max())
    # Start with constraints that are most restrictive for the incumbent.
    order = np.argsort(-initial_regrets, kind="stable")
    examined = 0
    for allocations in allocation_blocks(budget):
        examined += len(allocations)
        for reward, minimum in zip(floor_rewards, floor_minima):
            scores = reward[castles, allocations].sum(axis=1)
            allocations = allocations[scores >= minimum - tolerance]
            if len(allocations) == 0:
                break
        if len(allocations) == 0:
            continue
        regrets = np.full(len(allocations), -np.inf)
        for scenario in order:
            scores = rewards[scenario, castles, allocations].sum(axis=1)
            regrets = np.maximum(regrets, optima[scenario] - scores)
            # Further scenarios cannot reduce an already excessive maximum.
            keep = regrets <= best_regret + tolerance
            allocations = allocations[keep]
            regrets = regrets[keep]
            if len(allocations) == 0:
                break
        if len(allocations) == 0:
            continue
        minimum = float(regrets.min())
        index = int(np.flatnonzero(regrets <= minimum + tolerance)[0])
        candidate = allocations[index].tolist()
        candidate_regret = float(regrets[index])
        improves = candidate_regret < best_regret - tolerance
        tied = abs(candidate_regret - best_regret) <= tolerance
        if improves or (tied and candidate < best_allocation):
            best_regret = candidate_regret
            best_allocation = candidate
    best_scores = rewards[:, castles, best_allocation].sum(axis=1)
    return {
        "allocation": best_allocation,
        "max_regret": best_regret,
        "scenarios": names,
        "scores": best_scores.tolist(),
        "optimal_scores": optima.tolist(),
        "allocations_examined": examined,
    }
