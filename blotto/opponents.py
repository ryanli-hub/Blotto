"""Explicit, reproducible hypotheses about the Game 1 population."""

from itertools import combinations, product
from math import comb

import numpy as np
from scipy.stats import binom

from .game import BUDGET, VALUES, marginals


CONSIDERED_PROFILES = {
    "base": {},
    "overbid": {
        "small_bid_probabilities": [0.05, 0.15, 0.45, 0.35],
        "equal_share_probability": 0.55,
        "round_five_probability": 0.60,
        "transfer_probability": 0.80,
    },
    "avoid_high": {
        "high_castle_penalty": 0.45,
        "noise_sigma": 0.30,
    },
}


FOCUSED_245_BOUNDS = {
    "local": [(1, 3), (12, 19), (1, 3), (34, 40), (38, 51)],
    "broad": [(0, 4), (10, 22), (0, 4), (30, 43), (35, 55)],
    "shifted": [(1, 4), (16, 22), (1, 4), (38, 43), (32, 48)],
    "overbid": [(2, 5), (12, 21), (2, 5), (34, 42), (33, 52)],
}


def focused_245_population(profile="local"):
    """Enumerate a population focused on castles 2, 4, and 5."""
    bounds = FOCUSED_245_BOUNDS[profile]
    ranges = [range(lower, upper + 1) for lower, upper in bounds[:4]]
    allocations = []
    for first_four in product(*ranges):
        fifth = BUDGET - sum(first_four)
        if bounds[4][0] <= fifth <= bounds[4][1]:
            allocations.append((*first_four, fifth))
    allocations = np.asarray(allocations, dtype=int)

    weights = np.ones(len(allocations))
    parameters = {"profile": profile, "bounds": bounds, "weighting": "uniform"}
    if profile == "shifted":
        second_distance = (allocations[:, 1] - 18) / 2
        fourth_distance = (allocations[:, 3] - 40) / 1.5
        weights = np.exp(-0.5 * (second_distance**2 + fourth_distance**2))
        parameters.update(
            weighting="Gaussian weights on castles 2 and 4",
            centers=[18, 40],
            scales=[2, 1.5],
        )
    weights /= weights.sum()
    return {
        "allocations": allocations,
        "weights": weights,
        "marginals": marginals(allocations, weights),
        "parameters": parameters,
    }


def shallow_population():
    """Equal mixture of three unadjusted allocation templates for H."""
    allocations = [[20, 20, 20, 20, 20], [7, 13, 20, 27, 33], [0, 0, 0, 50, 50]]
    return marginals(allocations)


def considered_population(samples=4000, seed=20261103, profile="base", overrides=None):
    """Generate concentrated allocations with small bids on secondary castles."""
    parameters = {
        "active_count_probabilities": [0.25, 0.50, 0.25],
        "small_bid_probabilities": [0.10, 0.45, 0.35, 0.10],
        "equal_share_probability": 0.35,
        "noise_sigma": 0.25,
        "round_five_probability": 0.35,
        "transfer_probability": 0.40,
        "high_castle_penalty": 1.0,
    }
    if samples <= 0:
        raise ValueError("Generate at least one allocation.")
    parameters.update(CONSIDERED_PROFILES[profile])
    if overrides:
        unknown = set(overrides) - set(parameters)
        if unknown:
            raise ValueError(f"Unknown population parameters: {sorted(unknown)}")
        parameters.update(overrides)

    rng = np.random.default_rng(seed)
    choices = {size: list(combinations(range(5), size)) for size in (2, 3, 4)}
    subset_probabilities = {}
    for size, subsets in choices.items():
        weights = np.array([VALUES[list(subset)].sum() for subset in subsets], float)
        weights *= [
            parameters["high_castle_penalty"] if 4 in subset else 1.0
            for subset in subsets
        ]
        subset_probabilities[size] = weights / weights.sum()

    small_probabilities = parameters["small_bid_probabilities"]
    allocations = np.zeros((samples, 5), dtype=int)
    for row in allocations:
        size = int(rng.choice([2, 3, 4], p=parameters["active_count_probabilities"]))
        subset_index = rng.choice(len(choices[size]), p=subset_probabilities[size])
        active = np.array(choices[size][subset_index])
        secondary = np.setdiff1d(np.arange(5), active)
        row[secondary] = rng.choice(
            len(small_probabilities), size=len(secondary), p=small_probabilities
        )
        remaining = BUDGET - row.sum()

        shares = VALUES[active].astype(float)
        if rng.random() < parameters["equal_share_probability"]:
            shares = np.ones(size)
        shares *= rng.lognormal(mean=0, sigma=parameters["noise_sigma"], size=size)

        # Shuffle before rounding so exact ties do not favor a castle index.
        order = rng.permutation(size)
        active_bids = np.empty(size, dtype=int)
        if rng.random() < parameters["round_five_probability"]:
            active_bids[order] = 5 * round_allocation(shares[order], remaining // 5)
            active_bids += rng.multinomial(remaining % 5, np.full(size, 1 / size))
        else:
            active_bids[order] = round_allocation(shares[order], remaining)

        # Model a small adjustment around a threshold while keeping the budget.
        if rng.random() < parameters["transfer_probability"]:
            donor, receiver = rng.choice(size, size=2, replace=False)
            amount = int(rng.integers(1, 3))
            if active_bids[donor] > amount:
                active_bids[donor] -= amount
                active_bids[receiver] += amount
        row[active] = active_bids

    return {
        "marginals": marginals(allocations),
        "allocations": allocations,
        "parameters": {
            "profile": profile,
            "samples": samples,
            "seed": seed,
            **parameters,
        },
    }


def uniform_allocations(budget=BUDGET, castles=5):
    """Marginals of a uniform draw from all legal integer allocations."""
    if castles < 2 or budget < 0:
        raise ValueError("Need at least two castles and a nonnegative budget.")
    denominator = comb(budget + castles - 1, castles - 1)
    probabilities = [
        comb(budget - amount + castles - 2, castles - 2) / denominator
        for amount in range(budget + 1)
    ]
    return np.tile(probabilities, (castles, 1))


def independent_soldiers(budget=BUDGET, castles=5):
    """Each soldier independently picks a castle, not independent totals."""
    probabilities = binom.pmf(np.arange(budget + 1), budget, 1 / castles)
    return np.tile(probabilities, (castles, 1))


def round_allocation(shares, budget=BUDGET):
    """Largest remainders preserve the exact integer budget."""
    shares = np.asarray(shares, dtype=float)
    if shares.ndim != 1 or not np.all(np.isfinite(shares)):
        raise ValueError("Shares must be a finite vector.")
    if np.any(shares < 0) or shares.sum() <= 0:
        raise ValueError("Shares must be nonnegative with positive total.")
    quotas = budget * shares / shares.sum()
    allocation = np.floor(quotas).astype(int)
    order = np.argsort(-(quotas - allocation), kind="stable")
    allocation[order[: budget - allocation.sum()]] += 1
    return allocation


def heuristic_population(samples=4000, seed=20261103):
    """Round-number anchors, some with small budget-preserving transfers."""
    anchors = np.array(
        [
            [20, 20, 20, 20, 20],
            [7, 13, 20, 27, 33],
            [5, 10, 20, 30, 35],
            [0, 0, 20, 35, 45],
            [0, 0, 0, 50, 50],
            [0, 0, 0, 0, 100],
        ]
    )
    rng = np.random.default_rng(seed)
    allocations = anchors[rng.integers(len(anchors), size=samples)].copy()
    # Half remain exact anchors; the rest make eight one-soldier transfers.
    for row in allocations[samples // 2 :]:
        for _ in range(8):
            donor = rng.choice(np.flatnonzero(row))
            receiver = rng.integers(5)
            row[donor] -= 1
            row[receiver] += 1
    return marginals(allocations)


def concentrated_population(samples=4000, seed=20261104):
    """Select 2, 3, or 4 castles, then vary relative spending within them."""
    rng = np.random.default_rng(seed)
    subsets = {size: list(combinations(range(5), size)) for size in (2, 3, 4)}
    allocations = np.zeros((samples, 5), dtype=int)
    for row in allocations:
        size = int(rng.choice([2, 3, 4]))
        choices = subsets[size]
        # Prefer subsets with higher total point value.
        probabilities = np.array([VALUES[list(s)].sum() for s in choices], float)
        chosen = list(
            choices[rng.choice(len(choices), p=probabilities / probabilities.sum())]
        )
        shares = VALUES[chosen] * rng.lognormal(mean=0, sigma=0.35, size=size)
        row[chosen] = round_allocation(shares)
    return marginals(allocations)


def mixture(components, weights):
    """Mix valid population marginals without asserting castle independence."""
    components = np.asarray(components, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if components.ndim != 3 or weights.shape != (len(components),):
        raise ValueError("One weight is required per marginal table.")
    if not np.all(np.isfinite(weights)) or np.any(weights < 0) or weights.sum() <= 0:
        raise ValueError("Weights must be finite, nonnegative, and nonzero.")
    return np.einsum("s,skt->kt", weights / weights.sum(), components)
