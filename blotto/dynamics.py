"""Finite reasoning, response dynamics, and certified mixed equilibria."""

from __future__ import annotations

import numpy as np
from scipy.optimize import linprog

from .game import (
    BUDGET,
    VALUES,
    best_response,
    expected_rewards,
    marginals,
    payoff_matrix,
)
from .game import validate_allocations


def near_best_responses(
    marginal, count=24, slack=0.10, seed=20261103, values=VALUES, budget=BUDGET
):
    """Sample legal allocations whose expected score is within slack of optimal."""
    if not isinstance(count, (int, np.integer)) or count < 1:
        raise ValueError("count must be a positive integer.")
    if not isinstance(budget, (int, np.integer)) or budget < 0:
        raise ValueError("The budget must be a nonnegative integer.")
    if not np.isfinite(slack) or slack < 0:
        raise ValueError("slack must be finite and nonnegative.")
    rewards = expected_rewards(marginal, values)
    castles = len(rewards)
    if rewards.shape[1] != budget + 1:
        raise ValueError("Marginal columns must run from zero through budget.")

    # prefix[k, b] is the best score using exactly b soldiers on castles 0:k.
    prefix = np.full((castles + 1, budget + 1), -np.inf)
    prefix[0, 0] = 0
    amounts = np.arange(budget + 1)
    remaining = amounts[:, None] - amounts[None, :]
    for castle in range(castles):
        candidates = prefix[castle, np.maximum(remaining, 0)] + rewards[castle]
        candidates[remaining < 0] = -np.inf
        prefix[castle + 1] = candidates.max(axis=1)

    rng = np.random.default_rng(seed)
    allocations = np.empty((count, castles), dtype=int)
    for sample in range(count):
        remaining_budget = budget
        required_score = prefix[-1, budget] - slack
        for castle in range(castles - 1, -1, -1):
            choices = np.arange(remaining_budget + 1)
            best_completion = (
                prefix[castle, remaining_budget - choices] + rewards[castle, choices]
            )
            feasible = choices[best_completion >= required_score - 1e-12]
            selected = int(rng.choice(feasible))
            allocations[sample, castle] = selected
            remaining_budget -= selected
            # Carry one total threshold through the entire allocation.
            required_score -= rewards[castle, selected]
    return allocations


def finite_reasoning_population(
    backgrounds,
    samples_per_belief=24,
    slack=0.10,
    seed=20261103,
    depth=3,
    values=VALUES,
    budget=BUDGET,
):
    """Build levels 1..depth from heterogeneous beliefs and near-best responses."""
    if not isinstance(depth, (int, np.integer)) or depth < 1:
        raise ValueError("depth must be a positive integer.")
    backgrounds = np.asarray(backgrounds, dtype=float)
    if backgrounds.ndim != 3 or len(backgrounds) == 0:
        raise ValueError("Supply a nonempty list of marginal tables.")
    for background in backgrounds:
        rewards = expected_rewards(background, values)
        if rewards.shape[1] != budget + 1:
            raise ValueError("Marginal columns must run from zero through budget.")

    belief_count = len(backgrounds)
    response_shares = (
        np.linspace(0.35, 0.65, belief_count) if belief_count > 1 else np.array([0.50])
    )
    rng = np.random.default_rng(seed)
    allocations_by_depth = []
    depth_marginals = []
    diagnostics = []

    for level in range(1, depth + 1):
        lower_levels = np.mean(depth_marginals, axis=0) if level > 1 else None
        level_allocations = []
        level_gaps = []
        for background, response_share in zip(backgrounds, response_shares):
            belief = background
            if lower_levels is not None:
                belief = (
                    1 - response_share
                ) * background + response_share * lower_levels
            responses = near_best_responses(
                belief,
                count=samples_per_belief,
                slack=slack,
                seed=int(rng.integers(0, 2**32)),
                values=values,
                budget=budget,
            )
            rewards = expected_rewards(belief, values)
            scores = rewards[np.arange(len(values)), responses].sum(axis=1)
            _, optimum = best_response(belief, values, budget)
            level_allocations.append(responses)
            level_gaps.extend(np.maximum(optimum - scores, 0))

        allocations = np.vstack(level_allocations)
        allocations_by_depth.append(allocations)
        depth_marginals.append(marginals(allocations, budget=budget))
        diagnostics.append(
            {
                "depth": level,
                "sample_count": len(allocations),
                "unique_allocations": len(np.unique(allocations, axis=0)),
                "max_optimality_gap": float(np.max(level_gaps)),
                "mean_optimality_gap": float(np.mean(level_gaps)),
            }
        )

    allocations = np.vstack(allocations_by_depth)
    return {
        "marginals": marginals(allocations, budget=budget),
        "allocations": allocations,
        "depth_marginals": depth_marginals,
        "allocations_by_depth": allocations_by_depth,
        "parameters": {
            "samples_per_belief": samples_per_belief,
            "belief_count": belief_count,
            "slack": slack,
            "seed": seed,
            "depth": depth,
            "response_shares": response_shares.tolist(),
        },
        "diagnostics": {
            "by_depth": diagnostics,
            "max_optimality_gap": max(
                item["max_optimality_gap"] for item in diagnostics
            ),
        },
    }


def pure_response_path(initial, values=VALUES, budget=BUDGET, max_steps=10000):
    """Follow x[t+1] = BR(x[t]) until a repeated state or the step limit."""
    if max_steps < 1:
        raise ValueError("max_steps must be positive.")
    current = validate_allocations(initial, budget, len(values))
    if len(current) != 1:
        raise ValueError("Supply exactly one initial allocation.")
    current = tuple(current[0])
    seen = {}
    allocations = []
    scores = []
    for _ in range(max_steps):
        if current in seen:
            start = seen[current]
            length = len(allocations) - start
            return {
                "allocations": allocations,
                "scores": scores,
                "cycle_start": start,
                "cycle_length": length,
                "repeated_allocation": list(map(int, current)),
                "steps": len(allocations),
                "converged": length == 1,
            }
        seen[current] = len(allocations)
        allocations.append(list(map(int, current)))
        response, score = best_response(
            marginals([current], budget=budget), values, budget
        )
        scores.append(score)
        current = tuple(response)

    # Check the final successor, so a cycle closing on the last step is detected.
    start = seen.get(current)
    length = None if start is None else len(allocations) - start
    return {
        "allocations": allocations,
        "scores": scores,
        "cycle_start": start,
        "cycle_length": length,
        "repeated_allocation": None if start is None else list(map(int, current)),
        "steps": len(allocations),
        "converged": length == 1,
    }


def fictitious_play(
    initial, iterations=2000, checkpoints=None, values=VALUES, budget=BUDGET
):
    """Respond to the empirical distribution of all previous allocations."""
    if iterations < 0:
        raise ValueError("iterations must be nonnegative.")
    initial = validate_allocations(initial, budget, len(values))
    if len(initial) != 1:
        raise ValueError("Supply exactly one initial allocation.")
    if checkpoints is None:
        checkpoints = [0, 1, 10, 50, 100, 500, 1000, 2000, 5000, 10000]
    checkpoints = set(checkpoints) | {iterations}
    counts = {tuple(initial[0]): 1}
    marginal_counts = marginals(initial, budget=budget)
    history = []
    baseline = float(np.sum(values) / 2)

    for iteration in range(iterations + 1):
        sample_count = iteration + 1
        response, score = best_response(marginal_counts / sample_count, values, budget)
        exploitability = max(0.0, score - baseline)
        if iteration in checkpoints:
            history.append(
                {
                    "iteration": iteration,
                    "sample_count": sample_count,
                    "support_size": len(counts),
                    "exploitability": exploitability,
                }
            )
        if iteration == iterations:
            break
        key = tuple(response)
        counts[key] = counts.get(key, 0) + 1
        marginal_counts[np.arange(len(values)), response] += 1

    return {
        "allocations": [list(map(int, allocation)) for allocation in counts],
        "weights": [count / sample_count for count in counts.values()],
        "best_response": response.tolist(),
        "best_response_score": score,
        "exploitability": exploitability,
        "worst_case_score": baseline - exploitability,
        "iterations": iterations,
        "sample_count": sample_count,
        "history": history,
    }


def _restricted_equilibrium(centered_payoffs):
    """Solve min_q max_i (A q)[i] on the current symmetric strategy set."""
    size = len(centered_payoffs)
    objective = np.zeros(size + 1)
    objective[-1] = 1
    constraints = np.column_stack([centered_payoffs, -np.ones(size)])
    result = linprog(
        objective,
        A_ub=constraints,
        b_ub=np.zeros(size),
        A_eq=[np.append(np.ones(size), 0)],
        b_eq=[1],
        bounds=[(0, None)] * size + [(None, None)],
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"Restricted equilibrium LP failed: {result.message}")
    if abs(result.fun) > 1e-7:
        raise RuntimeError("A symmetric zero-sum restricted game must have value zero.")
    weights = np.maximum(result.x[:-1], 0)
    return weights / weights.sum()


def double_oracle(
    initial_allocations=None,
    values=VALUES,
    budget=BUDGET,
    tolerance=0.02,
    max_iterations=1000,
    background=None,
    background_weight=0.0,
):
    """Find a symmetric equilibrium, optionally facing a fixed background."""
    if tolerance < 0 or max_iterations < 1:
        raise ValueError("Use nonnegative tolerance and positive max_iterations.")
    castles = len(values)
    if not 0 <= background_weight <= 1:
        raise ValueError("background_weight must lie between zero and one.")
    if background is None and background_weight != 0:
        raise ValueError("A positive background weight requires background marginals.")
    if background is not None:
        background = np.asarray(background, dtype=float)
        background_rewards = expected_rewards(background, values)
        if background_rewards.shape[1] != budget + 1:
            raise ValueError("Background columns must run from zero through budget.")
    else:
        background_rewards = np.zeros((castles, budget + 1))

    def background_score(allocation):
        return float(background_rewards[np.arange(castles), allocation].sum())

    if initial_allocations is None:
        initial_allocations = np.eye(castles, dtype=int) * budget
    initial_allocations = validate_allocations(initial_allocations, budget, castles)
    allocations = list(dict.fromkeys(map(tuple, initial_allocations)))
    known = set(allocations)
    baseline = float(np.sum(values) / 2)
    fixed_scores = np.array([background_score(x) for x in allocations])
    centered = (1 - background_weight) * (
        payoff_matrix(allocations, allocations, values) - baseline
    ) + background_weight * (fixed_scores[:, None] - fixed_scores[None, :])
    history = []
    status = "iteration_limit"

    for iteration in range(1, max_iterations + 1):
        weights = _restricted_equilibrium(centered)
        smart_marginal = marginals(allocations, weights, budget)
        population_marginal = (1 - background_weight) * smart_marginal
        if background_weight:
            population_marginal += background_weight * background
        response, score = best_response(population_marginal, values, budget)
        population_score = (
            1 - background_weight
        ) * baseline + background_weight * float(weights @ fixed_scores)
        residual = max(0.0, score - population_score)
        if background_weight:
            _, smart_score = best_response(smart_marginal, values, budget)
            exploitability = max(0.0, smart_score - baseline)
        else:
            exploitability = residual
        history.append(
            {
                "iteration": iteration,
                "strategy_count": len(allocations),
                "support_size": int(np.count_nonzero(weights)),
                "exploitability": exploitability,
                "population_exploitability": residual,
            }
        )
        if residual <= tolerance:
            status = "tolerance_reached"
            break
        key = tuple(response)
        if key in known:
            status = "numerical_stall"
            break
        if iteration == max_iterations:
            break

        response_fixed_score = background_score(response)
        new_row = (1 - background_weight) * (
            payoff_matrix([response], allocations, values)[0] - baseline
        ) + background_weight * (response_fixed_score - fixed_scores)
        centered = np.pad(centered, ((0, 1), (0, 1)))
        centered[-1, :-1] = new_row
        centered[:-1, -1] = -new_row
        allocations.append(key)
        known.add(key)
        fixed_scores = np.append(fixed_scores, response_fixed_score)

    return {
        "allocations": [list(map(int, allocation)) for allocation in allocations],
        "weights": weights.tolist(),
        "best_response": response.tolist(),
        "best_response_score": score,
        "exploitability": exploitability,
        "worst_case_score": baseline - exploitability,
        "population_score": population_score,
        "population_exploitability": residual,
        "background_weight": float(background_weight),
        "iterations": iteration,
        "converged": status == "tolerance_reached",
        "status": status,
        "history": history,
    }
