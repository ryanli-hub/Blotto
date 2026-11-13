"""Joint allocation populations and a broad candidate pool for Game 2."""

from itertools import combinations

import numpy as np

from .game import BUDGET, VALUES, validate_allocations
from .opponents import round_allocation


TEAMMATE = np.array([0, 1, 36, 0, 63])
USER = np.array([0, 0, 49, 51, 0])
PROFILES = {
    "balanced": {},
    "fifth_crowded": {"fifth_weight": 3.0},
    "fifth_avoided": {"fifth_weight": 0.25},
    "small_bids": {
        "small_bids": [2, 3, 4, 5, 6],
        "small_bid_probabilities": [0.25, 0.30, 0.25, 0.15, 0.05],
    },
}


def population(allocations, weights=None):
    """Store legal full vectors with probabilities, combining repeated vectors."""
    allocations = validate_allocations(allocations, BUDGET, 5)
    if weights is None:
        weights = np.ones(len(allocations), dtype=float)
    else:
        weights = np.asarray(weights, dtype=float)
    if weights.shape != (len(allocations),):
        raise ValueError("Supply one probability per allocation.")
    if not np.all(np.isfinite(weights)) or np.any(weights < 0) or weights.sum() <= 0:
        raise ValueError("Probabilities must be finite, nonnegative, and nonzero.")
    support, inverse = np.unique(allocations, axis=0, return_inverse=True)
    probabilities = np.bincount(inverse, weights=weights, minlength=len(support))
    positive = probabilities > 0
    return {
        "allocations": support[positive],
        "weights": probabilities[positive] / probabilities.sum(),
    }


def mix_populations(components, weights):
    """Mix full-vector distributions with the requested population shares."""
    weights = np.asarray(weights, dtype=float)
    if weights.shape != (len(components),):
        raise ValueError("Supply one share per population.")
    if not np.all(np.isfinite(weights)) or np.any(weights < 0) or weights.sum() <= 0:
        raise ValueError("Population shares must be finite, nonnegative, and nonzero.")
    shares = weights / weights.sum()
    allocations = np.vstack([component["allocations"] for component in components])
    probabilities = np.concatenate(
        [share * component["weights"] for share, component in zip(shares, components)]
    )
    return population(allocations, probabilities)


def sample_triples(distribution, count, rng):
    """Draw three complete opponent vectors independently for each game."""
    if not isinstance(count, (int, np.integer)) or count <= 0:
        raise ValueError("Draw a positive integer number of games.")
    indices = rng.choice(
        len(distribution["allocations"]), size=(count, 3), p=distribution["weights"]
    )
    return distribution["allocations"][indices]


def _concentrated(samples, rng, parameters):
    choices = {
        1: [(2,), (3,), (4,)],
        2: list(combinations(range(5), 2)),
        3: list(combinations(range(5), 3)),
    }
    subset_weights = {}
    for size, subsets in choices.items():
        weights = (
            np.array([1.0, 2.0, 4.0])
            if size == 1
            else np.array(
                [VALUES[list(subset)].sum() ** 2 for subset in subsets], float
            )
        )
        weights *= [
            parameters["fifth_weight"] if 4 in subset else 1 for subset in subsets
        ]
        subset_weights[size] = weights / weights.sum()

    allocations = np.zeros((samples, 5), dtype=int)
    for row in allocations:
        size = int(rng.choice([1, 2, 3], p=parameters["active_count_probabilities"]))
        subset = rng.choice(len(choices[size]), p=subset_weights[size])
        active = np.array(choices[size][subset])
        secondary = np.setdiff1d(np.arange(5), active)
        row[secondary] = rng.choice(
            parameters["small_bids"],
            len(secondary),
            p=parameters["small_bid_probabilities"],
        )
        budget = BUDGET - row.sum()
        shares = VALUES[active].astype(float)
        if rng.random() < parameters["equal_share_probability"]:
            shares = np.ones(size)
        shares *= rng.lognormal(0, parameters["noise_sigma"], size)

        # Randomize rounding ties so a castle index has no artificial advantage.
        order = rng.permutation(size)
        bids = np.empty(size, dtype=int)
        if rng.random() < parameters["round_five_probability"]:
            bids[order] = 5 * round_allocation(shares[order], budget // 5)
            bids += rng.multinomial(budget % 5, np.full(size, 1 / size))
        else:
            bids[order] = round_allocation(shares[order], budget)
        if size > 1 and rng.random() < parameters["transfer_probability"]:
            donor, receiver = rng.choice(size, 2, replace=False)
            amount = min(int(rng.integers(1, 4)), int(bids[donor]))
            bids[donor] -= amount
            bids[receiver] += amount
        row[active] = bids
    return allocations


def _anchor_neighborhood(anchor, samples, rng):
    """Keep one quarter exact; others move up to six soldiers in total."""
    allocations = np.tile(anchor, (samples, 1))
    active = np.flatnonzero(anchor >= 10)
    exact_count = max(1, round(samples * 0.25))
    for row in allocations[exact_count:]:
        moves = int(rng.integers(1, 7))
        for _ in range(moves):
            donor = int(rng.choice(np.flatnonzero(row)))
            receivers = active if rng.random() < 0.75 else np.arange(5)
            receiver = int(rng.choice(receivers))
            row[donor] -= 1
            row[receiver] += 1
    return allocations


def _parameters(samples, seed, profile, overrides=None):
    """Validate the adjustable C settings and retain reproducibility metadata."""
    if not isinstance(samples, (int, np.integer)) or samples <= 0:
        raise ValueError("Generate a positive integer number of allocations.")
    if profile not in PROFILES:
        raise ValueError(f"Unknown population profile: {profile}")
    adjustable = {
        "active_count_probabilities": [0.15, 0.65, 0.20],
        "small_bids": [0, 1, 2, 3],
        "small_bid_probabilities": [0.50, 0.25, 0.15, 0.10],
        "equal_share_probability": 0.50,
        "noise_sigma": 0.30,
        "round_five_probability": 0.35,
        "transfer_probability": 0.50,
        "fifth_weight": 1.0,
    }
    parameters = {
        "profile": profile,
        "samples": samples,
        "seed": seed,
        **adjustable,
        "anchor_exact_fraction": 0.25,
        "anchor_max_transfers": 6,
        "anchor_active_receiver_probability": 0.75,
    }
    parameters.update(PROFILES[profile])
    if overrides is not None:
        unknown = set(overrides) - set(adjustable)
        if unknown:
            raise ValueError(f"Unknown concentration parameters: {sorted(unknown)}")
        parameters.update(overrides)

    bids = np.asarray(parameters["small_bids"])
    if (
        bids.ndim != 1
        or bids.size == 0
        or not np.all(np.isfinite(bids))
        or np.any(bids != np.floor(bids))
        or np.any((bids < 0) | (bids > BUDGET // 4))
    ):
        raise ValueError("Secondary bids must be integers from 0 through 25.")
    for name, size in [
        ("active_count_probabilities", 3),
        ("small_bid_probabilities", len(bids)),
    ]:
        probabilities = np.asarray(parameters[name], dtype=float)
        if (
            probabilities.shape != (size,)
            or not np.all(np.isfinite(probabilities))
            or np.any(probabilities < 0)
            or not np.isclose(probabilities.sum(), 1, rtol=0, atol=1e-10)
        ):
            raise ValueError(
                f"{name} must contain {size} probabilities summing to one."
            )
    for name in [
        "equal_share_probability",
        "round_five_probability",
        "transfer_probability",
    ]:
        value = parameters[name]
        if not np.isscalar(value) or not np.isfinite(value) or not 0 <= value <= 1:
            raise ValueError(f"{name} must be a probability from zero through one.")
    for name in ["noise_sigma", "fifth_weight"]:
        value = parameters[name]
        if not np.isscalar(value) or not np.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and nonnegative.")
    return parameters


def baseline_populations(
    samples=3000, seed=20261104, profile="balanced", overrides=None
):
    """Build H, concentrated C, and neighborhoods of the two team proposals."""
    parameters = _parameters(samples, seed, profile, overrides)
    rng = np.random.default_rng(seed)
    return {
        "H": population([[20, 20, 20, 20, 20], [7, 13, 20, 27, 33], [0, 0, 0, 50, 50]]),
        "C": population(_concentrated(samples, rng, parameters)),
        "TA": population(_anchor_neighborhood(TEAMMATE, samples, rng)),
        "TB": population(_anchor_neighborhood(USER, samples, rng)),
        "parameters": parameters,
    }


def concentrated_by_count(
    samples=3000, seed=20261104, profile="balanced", small_bids="low"
):
    """Generate separate C distributions conditional on one, two, or three main castles."""
    if small_bids not in ("low", "high"):
        raise ValueError("The secondary-bid profile must be 'low' or 'high'.")
    bid_settings = (
        {
            "small_bids": [0, 1, 2, 3],
            "small_bid_probabilities": [0.50, 0.25, 0.15, 0.10],
        }
        if small_bids == "low"
        else PROFILES["small_bids"]
    )
    parameters = _parameters(samples, seed, profile, bid_settings)
    streams = np.random.SeedSequence(seed).spawn(3)
    count_seeds = [int(stream.generate_state(1)[0]) for stream in streams]
    components = []
    for index, count_seed in enumerate(count_seeds):
        conditional_parameters = {
            **parameters,
            "active_count_probabilities": np.eye(3)[index].tolist(),
        }
        allocations = _concentrated(
            samples, np.random.default_rng(count_seed), conditional_parameters
        )
        components.append(population(allocations))
    all_in_weights = np.array([1.0, 2.0, 4.0 * parameters["fifth_weight"]])
    all_in_weights /= all_in_weights.sum()
    all_in = population(
        [[0, 0, 100, 0, 0], [0, 0, 0, 100, 0], [0, 0, 0, 0, 100]], all_in_weights
    )
    return {
        "components": components,
        "one_castle_all_in": all_in,
        "parameters": {
            **parameters,
            "secondary_bid_profile": small_bids,
            "conditional_main_castle_counts": [1, 2, 3],
            "count_seeds": count_seeds,
            "one_castle_all_in_castles": [3, 4, 5],
            "one_castle_all_in_weights": all_in_weights.tolist(),
        },
    }


def concentration_mixture(conditional, one_castle_share, all_in_fraction=0.5):
    """Set the exact one-main-castle share, keeping the other groups at a 13:4 ratio."""
    share = one_castle_share
    if not np.isscalar(share) or not np.isfinite(share) or not 0 <= share <= 1:
        raise ValueError("The one-main-castle share must lie between zero and one.")
    if len(conditional["components"]) != 3:
        raise ValueError(
            "Supply conditional populations for one, two, and three main castles."
        )
    if (
        not np.isscalar(all_in_fraction)
        or not np.isfinite(all_in_fraction)
        or not 0 <= all_in_fraction <= 1
    ):
        raise ValueError("The all-in fraction must lie between zero and one.")
    one_castle = mix_populations(
        [conditional["components"][0], conditional["one_castle_all_in"]],
        [1 - all_in_fraction, all_in_fraction],
    )
    weights = [share, (1 - share) * 13 / 17, (1 - share) * 4 / 17]
    return mix_populations([one_castle, *conditional["components"][1:]], weights)


def first_three_population(samples=3000, seed=20261104, secondary="zero"):
    """Model players concentrating on castles 1, 2, and 3, with optional small bids."""
    if not isinstance(samples, (int, np.integer)) or samples <= 0:
        raise ValueError("Generate a positive integer number of allocations.")
    settings = {
        "zero": (1.0, 0, 0.20),
        "small": (0.50, 3, 0.20),
        "shifted": (0.20, 5, 0.35),
    }
    if secondary not in settings:
        raise ValueError("The secondary profile must be 'zero', 'small', or 'shifted'.")
    zero_share, maximum_secondary, noise_sigma = settings[secondary]
    anchors = np.array([[33, 33, 34], [17, 33, 50], [15, 30, 55], [20, 25, 55]])
    anchor_weights = np.full(4, 0.25)
    if secondary == "shifted":
        anchors = np.vstack([anchors, [35, 40, 25], [25, 45, 30]])
        anchor_weights = np.array([0.15, 0.15, 0.20, 0.20, 0.15, 0.15])

    def branch(pairs, rng):
        rows, weights = [], []
        # Give the anchor rule an exact quarter of each secondary-bid branch.
        for pair in pairs:
            remaining = BUDGET - sum(pair)
            for anchor, weight in zip(anchors, anchor_weights):
                rows.append(np.r_[round_allocation(anchor, remaining), pair])
                weights.append(0.25 * weight / len(pairs))
        for _ in range(samples):
            pair = pairs[int(rng.integers(len(pairs)))]
            remaining = BUDGET - sum(pair)
            anchor = anchors[rng.choice(len(anchors), p=anchor_weights)]
            shares = anchor * rng.lognormal(0, noise_sigma, 3)
            # These players contest all three target castles with positive bids.
            primary = 1 + round_allocation(shares, remaining - 3)
            if rng.random() < 0.50:
                donor = int(rng.choice(np.flatnonzero(primary > 1)))
                receiver = int(rng.choice([i for i in range(3) if i != donor]))
                primary[donor] -= 1
                primary[receiver] += 1
            rows.append(np.r_[primary, pair])
            weights.append(0.75 / samples)
        return population(rows, weights)

    streams = np.random.SeedSequence(seed).spawn(2)
    components = [branch([(0, 0)], np.random.default_rng(streams[0]))]
    weights = [zero_share]
    positive_pairs = [
        (fourth, fifth)
        for fourth in range(maximum_secondary + 1)
        for fifth in range(maximum_secondary + 1)
        if fourth + fifth > 0
    ]
    if positive_pairs:
        components.append(branch(positive_pairs, np.random.default_rng(streams[1])))
        weights.append(1 - zero_share)
    result = mix_populations(components, weights)
    result["parameters"] = {
        "samples_per_noisy_branch": samples,
        "seed": seed,
        "secondary_profile": secondary,
        "zero_secondary_share": zero_share,
        "positive_secondary_pairs": [list(pair) for pair in positive_pairs],
        "positive_pair_weighting": "uniform",
        "anchor_fraction_within_branch": 0.25,
        "first_three_anchors": anchors.tolist(),
        "anchor_probabilities": anchor_weights.tolist(),
        "noise_sigma": noise_sigma,
        "one_soldier_transfer_probability": 0.50,
        "minimum_first_three_bid": 1,
        "first_three_positive_support_count": int(
            np.all(result["allocations"][:, :3] > 0, axis=1).sum()
        ),
        "support_count": len(result["allocations"]),
    }
    return result


def candidate_pool(seed=20261104, random_count=4000):
    """Combine a coarse exhaustive grid with concentrated and local candidates."""
    if not isinstance(random_count, (int, np.integer)) or random_count < 0:
        raise ValueError("The random candidate count must be a nonnegative integer.")
    candidates = []
    for a in range(21):
        for b in range(21 - a):
            for c in range(21 - a - b):
                for d in range(21 - a - b - c):
                    candidates.append(5 * np.array([a, b, c, d, 20 - a - b - c - d]))
    for first, second in combinations(range(5), 2):
        for bid in range(BUDGET + 1):
            row = np.zeros(5, dtype=int)
            row[first], row[second] = bid, BUDGET - bid
            candidates.append(row)

    anchors = np.array(
        [
            TEAMMATE,
            USER,
            [8, 9, 10, 11, 62],
            [6, 37, 50, 7, 0],
            [0, 0, 0, 0, 100],
            [0, 0, 0, 49, 51],
        ]
    )
    for anchor in anchors:
        candidates.append(anchor)
        for donor in range(5):
            for receiver in range(5):
                if donor == receiver:
                    continue
                for amount in range(1, min(6, int(anchor[donor])) + 1):
                    row = anchor.copy()
                    row[donor] -= amount
                    row[receiver] += amount
                    candidates.append(row)

    rng = np.random.default_rng(seed)
    for index in range(random_count):
        alpha = [0.3, 1.0, 3.0][index % 3]
        candidates.append(round_allocation(rng.dirichlet(np.full(5, alpha))))
    concentrated = baseline_populations(samples=1000, seed=seed + 1)["C"]["allocations"]
    candidates.extend(concentrated)
    return np.unique(validate_allocations(candidates, BUDGET, 5), axis=0)
