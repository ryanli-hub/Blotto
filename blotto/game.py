"""Game 1 scoring, opponent marginals, and an exact best-response DP."""

from __future__ import annotations

import numpy as np

BUDGET = 100
VALUES = np.array([1, 2, 3, 4, 5])


def validate_allocations(allocations, budget=BUDGET, castle_count=None):
    """Return a two-dimensional integer array of legal allocations."""
    array = np.asarray(allocations)
    if array.ndim == 1:
        array = array[None, :]
    if array.ndim != 2 or array.shape[0] == 0 or array.shape[1] == 0:
        raise ValueError("Allocations must be a nonempty vector or matrix.")
    if castle_count is not None and array.shape[1] != castle_count:
        raise ValueError("The allocation width must match the number of castles.")
    if not np.all(np.isfinite(array)) or np.any(array < 0):
        raise ValueError("Soldier counts must be finite and nonnegative.")
    if np.any(array != np.floor(array)):
        raise ValueError("Soldier counts must be integers.")
    if not isinstance(budget, (int, np.integer)) or budget < 0:
        raise ValueError("The budget must be a nonnegative integer.")
    if np.any(array.sum(axis=1) != budget):
        raise ValueError("Every allocation must spend exactly the budget.")
    return array.astype(int)


def _values(values):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("Castle values must be a nonempty vector.")
    if not np.all(np.isfinite(values)) or np.any(values <= 0):
        raise ValueError("Castle values must be finite and positive.")
    return values


def payoff_matrix(rows, cols, values=VALUES):
    """Return scores: entry [i, j] is row allocation i versus column j."""
    values = _values(values)
    rows = np.atleast_2d(rows)
    cols = np.atleast_2d(cols)
    if rows.size == 0:
        raise ValueError("At least one row allocation is required.")
    budget = int(rows[0].sum())
    rows = validate_allocations(rows, budget, len(values))
    cols = validate_allocations(cols, budget, len(values))
    # Accumulate one castle at a time instead of allocating an N x M x K tensor.
    scores = np.zeros((len(rows), len(cols)), dtype=float)
    for castle, value in enumerate(values):
        ours = rows[:, castle, None]
        theirs = cols[None, :, castle]
        scores += value * ((ours > theirs) + 0.5 * (ours == theirs))
    return scores


def payoff(x, y, values=VALUES):
    """Score one allocation against another, including half points for ties."""
    if np.asarray(x).ndim != 1 or np.asarray(y).ndim != 1:
        raise ValueError("payoff expects two allocation vectors.")
    return float(payoff_matrix([x], [y], values)[0, 0])


def marginals(allocations, weights=None, budget=BUDGET):
    """Return a K x (budget + 1) table of opponent soldier probabilities."""
    allocations = validate_allocations(allocations, budget)
    count, castles = allocations.shape
    if weights is None:
        weights = np.full(count, 1 / count)
    else:
        weights = np.asarray(weights, dtype=float)
        if weights.shape != (count,):
            raise ValueError("Supply one weight for each allocation.")
        if not np.all(np.isfinite(weights)) or np.any(weights < 0):
            raise ValueError("Weights must be finite and nonnegative.")
        if weights.sum() <= 0:
            raise ValueError("At least one weight must be positive.")
        weights = weights / weights.sum()
    table = np.zeros((castles, budget + 1))
    for castle in range(castles):
        table[castle] = np.bincount(
            allocations[:, castle], weights=weights, minlength=budget + 1
        )
    return table


def expected_rewards(marginal, values=VALUES):
    """Return reward[k, a] = v[k] * (P(Y[k] < a) + P(Y[k] = a)/2)."""
    values = _values(values)
    marginal = np.asarray(marginal, dtype=float)
    if marginal.ndim != 2 or marginal.shape[0] != len(values):
        raise ValueError("Marginal rows must match castle values.")
    if marginal.shape[1] == 0 or not np.all(np.isfinite(marginal)):
        raise ValueError("Marginals must be a nonempty finite table.")
    if np.any(marginal < 0) or not np.allclose(
        marginal.sum(axis=1), 1, rtol=0, atol=1e-8
    ):
        raise ValueError("Each marginal row must be a probability distribution.")
    cumulative = np.cumsum(marginal, axis=1)
    return values[:, None] * (cumulative - 0.5 * marginal)


def best_response(marginal, values=VALUES, budget=BUDGET):
    """Maximize expected castle points over all legal integer allocations."""
    if not isinstance(budget, (int, np.integer)) or budget < 0:
        raise ValueError("The budget must be a nonnegative integer.")
    rewards = expected_rewards(marginal, values)
    castles = rewards.shape[0]
    if rewards.shape[1] != budget + 1:
        raise ValueError("Marginal columns must run from zero through budget.")

    amounts = np.arange(budget + 1)
    remaining = amounts[:, None] - amounts[None, :]
    feasible = remaining >= 0
    previous = np.full(budget + 1, -np.inf)
    previous[0] = 0
    choices = np.zeros((castles, budget + 1), dtype=int)

    for castle in range(castles):
        candidates = previous[np.maximum(remaining, 0)] + rewards[castle]
        candidates[~feasible] = -np.inf
        # Columns enumerate current-castle allocations in increasing order.
        # argmax therefore selects the smallest allocation on computed ties.
        choices[castle] = np.argmax(candidates, axis=1)
        previous = candidates[amounts, choices[castle]]

    allocation = np.empty(castles, dtype=int)
    remaining_budget = budget
    for castle in range(castles - 1, -1, -1):
        allocation[castle] = choices[castle, remaining_budget]
        remaining_budget -= allocation[castle]
    return allocation, float(previous[budget])
