"""Thoughtful Game 1 populations with diverse, certified finite responses."""

import numpy as np

from .dynamics import near_best_responses
from .game import (
    VALUES,
    best_response,
    expected_rewards,
    marginals,
    validate_allocations,
)
from .opponents import considered_population, focused_245_population, mixture


TYPE_NAMES = ["H", "C", "T", "S"]
TRAINING_SHARES = {
    "concentration": [0.02, 0.58, 0.10, 0.30],
    "calculation": [0.02, 0.28, 0.10, 0.60],
    "original": [0.02, 0.28, 0.35, 0.35],
    "T_free": [0.02, 0.48, 0.0, 0.50],
    "avoid_fifth": [0.02, 0.43, 0.10, 0.45],
}
FRESH_SHARES = {
    "concentration": [0.02, 0.53, 0.12, 0.33],
    "calculation": [0.02, 0.23, 0.12, 0.63],
    "original": [0.02, 0.28, 0.30, 0.40],
    "T_free": [0.02, 0.43, 0.0, 0.55],
    "avoid_fifth": [0.02, 0.38, 0.12, 0.48],
}
TEAM_ANCHORS = [[2, 16, 1, 37, 44], [1, 14, 1, 37, 47]]


def distribution(allocations, weights=None):
    """Keep legal joint allocations and their sufficient Game 1 marginals."""
    allocations = validate_allocations(allocations, 100, 5)
    table = marginals(allocations, weights)
    weights = (
        np.ones(len(allocations)) if weights is None else np.asarray(weights, float)
    )
    return {
        "allocations": allocations,
        "weights": weights / weights.sum(),
        "marginals": table,
    }


def mix_distributions(components, weights):
    """Preserve full allocations when mixing their population probabilities."""
    weights = np.asarray(weights, dtype=float)
    # The existing marginal-mixture function validates the component weights.
    table = mixture([component["marginals"] for component in components], weights)
    weights = weights / weights.sum()
    allocations = np.vstack([component["allocations"] for component in components])
    probabilities = np.concatenate(
        [
            weight * component["weights"]
            for weight, component in zip(weights, components)
        ]
    )
    return {"allocations": allocations, "weights": probabilities, "marginals": table}


def response_sample(marginal, rng, count_per_order=8, slack=0.10, orders=None):
    """Sample responses under chosen castle orders and certify original-game gaps."""
    marginal = np.asarray(marginal, dtype=float)
    rewards = expected_rewards(marginal)
    _, optimum = best_response(marginal)
    if orders is None:
        orders = [rng.permutation(5) for _ in range(4)]
    orders = np.atleast_2d(np.asarray(orders))
    if orders.shape[1:] != (5,) or not np.all(np.sort(orders, axis=1) == np.arange(5)):
        raise ValueError(
            "Each sampling order must be a permutation of castles 0 through 4."
        )
    orders = orders.astype(int)
    batches, seeds = [], []
    for order in orders:
        seed = int(rng.integers(2**32))
        samples = near_best_responses(
            marginal[order],
            count=count_per_order,
            slack=slack,
            seed=seed,
            values=VALUES[order],
        )
        restored = np.empty_like(samples)
        restored[:, order] = samples
        batches.append(restored)
        seeds.append(seed)
    allocations = validate_allocations(np.vstack(batches), 100, 5)
    scores = rewards[np.arange(5), allocations].sum(axis=1)
    gaps = optimum - scores
    if np.any(gaps > slack + 1e-9) or np.any(gaps < -1e-9):
        raise RuntimeError(
            "A sampled response failed its original-game optimality check."
        )
    return allocations, {
        "slack": float(slack),
        "orders": orders.tolist(),
        "order_seeds": seeds,
        "count_per_order": count_per_order,
        "sample_count": len(allocations),
        "unique_allocations": len(np.unique(allocations, axis=0)),
        "best_response_score": float(optimum),
        "max_optimality_gap": float(max(0.0, gaps.max())),
        "mean_optimality_gap": float(np.maximum(gaps, 0).mean()),
    }


def _response_population(marginal, rng, style, count_per_order, fresh):
    if style == "narrow":
        slacks = [0.08] * 4 if fresh else [0.05, 0.10, 0.05, 0.10]
        orders = [rng.permutation(5) for _ in range(4)]
        if not fresh:
            orders[:2] = [np.arange(5), np.arange(5)]
    else:
        slacks = [0.35, 0.60] * 2 if fresh else [0.30, 0.50] * 2
        orders = [rng.permutation(5) for _ in range(4)]
    batches, diagnostics = [], []
    for slack, order in zip(slacks, orders):
        allocations, diagnostic = response_sample(
            marginal, rng, count_per_order, slack, orders=[order]
        )
        batches.append(allocations)
        diagnostics.append(diagnostic)
    return distribution(np.vstack(batches)), diagnostics


def _team_population(team_types, a_share, exact_share):
    return mix_distributions(
        [team_types["A"], team_types["B"], team_types["variations"]],
        [exact_share * a_share, exact_share * (1 - a_share), 1 - exact_share],
    )


def _reasoning_levels(
    components, team_types, shares, rng, style, count_per_order, fresh, alternative_c
):
    settings = (
        [(0.01, -0.08, 0.45, 0.15), (0.03, 0.03, 0.65, 0.55), (0.05, 0.12, 0.85, 0.85)]
        if fresh
        else [
            (0.0, -0.10, 0.40, 0.25),
            (0.02, 0.0, 0.60, 0.50),
            (0.05, 0.10, 0.80, 0.75),
        ]
    )
    exact_share = 0.15 if fresh else 0.30
    levels, diagnostics = [], []
    for level in range(4):
        previous = (
            np.mean([part["marginals"] for part in levels], axis=0) if level else None
        )
        responses = []
        for belief_index, (h, t_offset, response_fraction, a_share) in enumerate(
            settings
        ):
            t = float(np.clip(shares["T"] + t_offset, 0, 0.50))
            r = response_fraction if level else 0.0
            remainder = 1 - h - t
            team = _team_population(team_types, a_share, exact_share)
            actual_c_fraction = [0.0, 1.0, 0.50][belief_index]
            predicted_c = mixture(
                [components["C"]["marginals"], alternative_c["marginals"]],
                [actual_c_fraction, 1 - actual_c_fraction],
            )
            belief_shares = {
                "H": h,
                "C": remainder * (1 - r),
                "T": t,
                "earlier_S": remainder * r,
            }
            tables = [components["H"]["marginals"], predicted_c, team["marginals"]]
            weights = [h, belief_shares["C"], t]
            if level:
                tables.append(previous)
                weights.append(belief_shares["earlier_S"])
            belief = mixture(tables, weights)
            response, checks = _response_population(
                belief, rng, style, count_per_order, fresh
            )
            responses.append(response)
            diagnostics.append(
                {
                    "level": level + 1,
                    "belief": belief_index + 1,
                    "shares": belief_shares,
                    "A_fraction_of_exact_T": a_share,
                    "exact_fraction_of_T": exact_share,
                    "actual_C_fraction_in_C_belief": actual_c_fraction,
                    "earlier_level_weights": [1 / level] * level if level else [],
                    "sampling_checks": checks,
                    "max_optimality_gap": max(
                        check["max_optimality_gap"] for check in checks
                    ),
                }
            )
        levels.append(mix_distributions(responses, [1 / 3] * 3))
    return levels, diagnostics


def build_field(seed=20261104, samples=3000, responses_per_order=8, fresh=False):
    """Return 80 Game 1 marginal scenarios, their weights, and legal population banks."""
    rng = np.random.default_rng(seed)
    h_population = distribution(
        [[20, 20, 20, 20, 20], [7, 13, 20, 27, 33], [0, 0, 0, 50, 50]]
    )
    variation_names = ["shifted", "overbid"] if fresh else ["local", "broad"]
    variations = [focused_245_population(name) for name in variation_names]
    team_types = {
        "A": distribution([TEAM_ANCHORS[0]]),
        "B": distribution([TEAM_ANCHORS[1]]),
        "variations": mix_distributions(variations, [0.50, 0.50]),
    }
    family_shares = FRESH_SHARES if fresh else TRAINING_SHARES
    fifth_weights = (
        [1.35, 0.90, 1.10, 1.0, 0.35] if fresh else [1.50, 1.0, 1.0, 1.0, 0.45]
    )
    a_shares = (
        [0.40, 0.60, 0.25, 0.50, 0.80] if fresh else [0.50, 0.50, 0.75, 0.50, 0.25]
    )
    h_values = [0.01, 0.04] if fresh else [0.0, 0.05]
    depth_styles = (
        {"three_level": [0.10, 0.40, 0.50, 0.0], "four_level": [0.0, 0.15, 0.35, 0.50]}
        if fresh
        else {
            "three_level": [0.15, 0.45, 0.40, 0.0],
            "four_level": [0.05, 0.20, 0.35, 0.40],
        }
    )
    bid_probabilities = (
        {
            "low": [0.05, 0.20, 0.30, 0.25, 0.15, 0.05],
            "raised": [
                0.03,
                0.07,
                0.12,
                0.15,
                0.10,
                0.20,
                0.10,
                0,
                0.08,
                0,
                0.10,
                0,
                0.05,
            ],
        }
        if fresh
        else {
            "low": [0.10, 0.45, 0.35, 0.10],
            "raised": [0.05, 0.10, 0.20, 0.15, 0, 0.35, 0, 0, 0, 0, 0.15],
        }
    )
    scenarios, metadata, world_weights, models = {}, {}, {}, {}
    for (family, raw_shares), fifth_weight, a_share in zip(
        family_shares.items(), fifth_weights, a_shares
    ):
        base_shares = dict(zip(TYPE_NAMES, raw_shares))
        team = _team_population(team_types, a_share, 0.15 if fresh else 0.30)
        c_models = {}
        for bids, probabilities in bid_probabilities.items():
            c_seed = int(rng.integers(2**32))
            c_models[bids] = considered_population(
                samples=samples,
                seed=c_seed,
                overrides={
                    "active_count_probabilities": (
                        [0.20, 0.50, 0.30] if fresh else [0.25, 0.50, 0.25]
                    ),
                    "small_bid_probabilities": probabilities,
                    "equal_share_probability": 0.50 if fresh else 0.35,
                    "noise_sigma": 0.35 if fresh else 0.25,
                    "round_five_probability": 0.60 if fresh else 0.35,
                    "transfer_probability": 0.70 if fresh else 0.40,
                    "high_castle_penalty": fifth_weight,
                },
            )
        concentrated_types = {
            bids: distribution(model["allocations"]) for bids, model in c_models.items()
        }
        for bids, c_model in c_models.items():
            concentrated = concentrated_types[bids]
            alternative_c = concentrated_types["raised" if bids == "low" else "low"]
            components = {"H": h_population, "C": concentrated, "T": team}
            for response_style in ["narrow", "diverse"]:
                bank = f"{family}/{bids}/{response_style}"
                print(
                    f"  Building {'fresh' if fresh else 'training'} Game 1 bank {len(models) + 1}/20: {bank}",
                    flush=True,
                )
                response_seed = int(rng.integers(2**32))
                levels, diagnostics = _reasoning_levels(
                    components,
                    team_types,
                    base_shares,
                    np.random.default_rng(response_seed),
                    response_style,
                    responses_per_order,
                    fresh,
                    alternative_c,
                )
                models[bank] = {
                    "components": components,
                    "alternative_C": alternative_c,
                    "levels": levels,
                    "base_shares": base_shares,
                    "C_parameters": c_model["parameters"],
                    "T_parameters": {
                        "A_fraction_of_exact_T": a_share,
                        "exact_fraction": 0.15 if fresh else 0.30,
                    },
                    "response_style": response_style,
                    "response_seed": response_seed,
                    "diagnostics": diagnostics,
                }
                for h in h_values:
                    shares = {
                        **base_shares,
                        "H": h,
                        "C": base_shares["C"] + base_shares["H"] - h,
                    }
                    for depth_style, depth_weights in depth_styles.items():
                        name = f"{bank}/h{h:.2f}/{depth_style}"
                        strategic = mixture(
                            [level["marginals"] for level in levels], depth_weights
                        )
                        scenarios[name] = mixture(
                            [
                                components[type_name]["marginals"]
                                for type_name in TYPE_NAMES[:-1]
                            ]
                            + [strategic],
                            [shares[type_name] for type_name in TYPE_NAMES],
                        )
                        weight = 0.20 * 0.50 * 0.50 * 0.50 * 0.50
                        world_weights[name] = weight
                        metadata[name] = {
                            "family": family,
                            "bank": bank,
                            "shares": shares,
                            "bids": bids,
                            "response_style": response_style,
                            "depth_style": depth_style,
                            "S_level_weights": depth_weights,
                            "weight": weight,
                        }
    return {
        "scenarios": scenarios,
        "weights": world_weights,
        "metadata": metadata,
        "models": models,
        "parameters": {
            "seed": seed,
            "samples": samples,
            "responses_per_order": responses_per_order,
            "fresh": fresh,
            "H_shares": h_values,
            "S_depth_styles": depth_styles,
            "T_variation_profiles": variation_names,
            "T_variation_weights": [0.50, 0.50],
            "T_types": team_types,
            "family_shares": {
                name: dict(zip(TYPE_NAMES, values))
                for name, values in family_shares.items()
            },
            "family_weights": {name: 0.20 for name in family_shares},
            "factor_weights": {
                "bid_bank": [0.50, 0.50],
                "response_style": [0.50, 0.50],
                "H": [0.50, 0.50],
                "depth_style": [0.50, 0.50],
            },
        },
    }
