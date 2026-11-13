"""Coherent Game 2 populations with explicit concentration and reasoning groups."""

import numpy as np

from .game import validate_allocations
from .game2_population import (
    baseline_populations,
    first_three_population,
    mix_populations,
    population,
)
from .game2_search import response_search


TYPE_NAMES = ["H", "C", "Z", "F", "T", "S"]
TRAINING_SHARES = {
    "concentration": [0.02, 0.38, 0.10, 0.10, 0.15, 0.25],
    "calculation": [0.02, 0.18, 0.10, 0.10, 0.10, 0.50],
    "fifth": [0.02, 0.28, 0.20, 0.05, 0.10, 0.35],
    "first_three": [0.02, 0.23, 0.05, 0.25, 0.10, 0.35],
    "original": [0.02, 0.23, 0.10, 0.10, 0.25, 0.30],
}
FRESH_SHARES = {
    "concentration": [0.02, 0.33, 0.12, 0.12, 0.15, 0.26],
    "calculation": [0.02, 0.16, 0.12, 0.12, 0.08, 0.50],
    "fifth": [0.02, 0.27, 0.18, 0.08, 0.10, 0.35],
    "first_three": [0.02, 0.25, 0.08, 0.22, 0.10, 0.33],
    "original": [0.02, 0.22, 0.08, 0.12, 0.28, 0.28],
}
FIFTH_WEIGHTS = dict(zip(TRAINING_SHARES, [1.0, 1.0, 1.5, 0.8, 1.0]))
TEAMMATE_SHARES = dict(zip(TRAINING_SHARES, [0.50, 0.50, 0.75, 0.25, 0.50]))


def structural_probabilities(distribution):
    """Measure recognizable allocation shapes across every contributing type."""
    allocations, weights = distribution["allocations"], distribution["weights"]
    first_three_only = np.all(allocations[:, 3:] == 0, axis=1)
    all_first_three_positive = np.all(allocations[:, :3] > 0, axis=1)
    return {
        "actual_exact_100_fifth_probability": float(
            weights[allocations[:, 4] == 100].sum()
        ),
        "actual_first_three_only_probability": float(weights[first_three_only].sum()),
        "actual_first_three_only_positive_probability": float(
            weights[first_three_only & all_first_three_positive].sum()
        ),
    }


def _reasoning_levels(
    components, candidates, shares, rng, screen, check, belief_floor=0.02
):
    """Keep explicit H/Z/F/T shares while predicting C and earlier responders."""
    if not np.isfinite(belief_floor) or not 0 <= belief_floor <= 0.30:
        raise ValueError("The belief floor must lie between zero and 0.30.")
    levels, diagnostics = [], []
    for level in range(4):
        earlier = mix_populations(levels, np.ones(level)) if level else None
        responses = []
        for belief, (z_offset, f_offset, response_fraction) in enumerate(
            [(-0.05, 0.05, 0.40), (0.0, 0.0, 0.60), (0.05, -0.05, 0.80)]
        ):
            h = 0.02
            z = float(np.clip(shares["Z"] + z_offset, belief_floor, 0.30))
            f = float(np.clip(shares["F"] + f_offset, belief_floor, 0.30))
            t = shares["T"]
            remainder = 1 - h - z - f - t
            r = response_fraction if level else 0.0
            predicted_shares = {
                "H": h,
                "C": remainder * (1 - r),
                "Z": z,
                "F": f,
                "T": t,
            }
            predicted_components = [components[name] for name in predicted_shares]
            weights = list(predicted_shares.values())
            if level:
                predicted_components.append(earlier)
                weights.append(remainder * r)
            predicted_shares["earlier_S"] = remainder * r
            predicted = mix_populations(predicted_components, weights)
            response_seed = int(rng.integers(2**32))
            response, diagnostic = response_search(
                candidates,
                predicted,
                np.random.default_rng(response_seed),
                screen=screen,
                check=check,
                count=12,
            )
            responses.append(response)
            diagnostics.append(
                {
                    "level": level + 1,
                    "belief": belief + 1,
                    "belief_floor": belief_floor,
                    "predicted_shares": predicted_shares,
                    "earlier_level_weights": [1 / level] * level if level else [],
                    "response_fraction_of_remainder": r,
                    "response_seed": response_seed,
                    **diagnostic,
                }
            )
        levels.append(mix_populations(responses, [1 / 3] * 3))
    return levels, diagnostics


def build_field(
    candidates, seed=20261104, samples=3000, screen=1024, check=8192, fresh=False
):
    """Build 90 weighted population scenarios and their four-level reasoning banks."""
    candidates = validate_allocations(candidates, 100, 5)
    rng = np.random.default_rng(seed)
    shared_seeds = {
        name: int(rng.integers(2**32)) for name in ["anchors", "F_zero", "F_secondary"]
    }
    anchors = baseline_populations(samples=samples, seed=shared_seeds["anchors"])
    f_zero = first_three_population(samples, shared_seeds["F_zero"], "zero")
    f_secondary = first_three_population(
        samples, shared_seeds["F_secondary"], "shifted" if fresh else "small"
    )
    f_weights = [0.50, 0.50] if fresh else [0.75, 0.25]
    focused = mix_populations([f_zero, f_secondary], f_weights)
    all_fifth = population([[0, 0, 0, 0, 100]])

    family_shares = FRESH_SHARES if fresh else TRAINING_SHARES
    h_values = [0.01, 0.03, 0.05] if fresh else [0.0, 0.02, 0.05]
    styles = (
        {
            "shallow": [0.05, 0.50, 0.45, 0.0],
            "central": [0.0, 0.25, 0.50, 0.25],
            "deep": [0.0, 0.10, 0.35, 0.55],
        }
        if fresh
        else {
            "shallow": [0.10, 0.50, 0.40, 0.0],
            "central": [0.05, 0.30, 0.50, 0.15],
            "deep": [0.0, 0.15, 0.40, 0.45],
        }
    )
    bid_settings = (
        {
            "low": ([0, 1, 2, 3, 4], [0.20, 0.25, 0.30, 0.15, 0.10]),
            "raised": ([1, 2, 3, 4, 5], [0.15, 0.25, 0.30, 0.20, 0.10]),
        }
        if fresh
        else {
            "low": ([0, 1, 2, 3], [0.25, 0.35, 0.25, 0.15]),
            "raised": ([1, 2, 3, 4], [0.25, 0.35, 0.25, 0.15]),
        }
    )
    scenarios, metadata, world_weights, models = {}, {}, {}, {}
    for family, raw_shares in family_shares.items():
        base_shares = dict(zip(TYPE_NAMES, raw_shares))
        a_share = TEAMMATE_SHARES[family]
        team = mix_populations([anchors["TA"], anchors["TB"]], [a_share, 1 - a_share])
        for bids, (bid_values, bid_probabilities) in bid_settings.items():
            bank = f"{family}/{bids}"
            print(
                f"  Building {'fresh' if fresh else 'training'} field {len(models) + 1}/10: {bank}",
                flush=True,
            )
            c_seed, s_seed = [int(rng.integers(2**32)) for _ in range(2)]
            c_model = baseline_populations(
                samples=samples,
                seed=c_seed,
                overrides={
                    "active_count_probabilities": (
                        [0.10, 0.60, 0.30] if fresh else [0.05, 0.70, 0.25]
                    ),
                    "small_bids": bid_values,
                    "small_bid_probabilities": bid_probabilities,
                    "noise_sigma": 0.35 if fresh else 0.25,
                    "fifth_weight": FIFTH_WEIGHTS[family],
                },
            )
            components = {
                "H": anchors["H"],
                "C": c_model["C"],
                "Z": all_fifth,
                "F": focused,
                "T": team,
            }
            ordered_components = [components[name] for name in TYPE_NAMES[:-1]]
            levels, diagnostics = _reasoning_levels(
                components,
                candidates,
                base_shares,
                np.random.default_rng(s_seed),
                screen,
                check,
            )
            models[bank] = {
                "components": components,
                "levels": levels,
                "base_shares": base_shares,
                "parameters": {"C": c_model["parameters"], "A_fraction_of_T": a_share},
                "reasoning": diagnostics,
                "seeds": {"C": c_seed, "S": s_seed},
            }
            for h, h_weight in zip(h_values, [0.25, 0.50, 0.25]):
                actual_shares = {
                    **base_shares,
                    "H": h,
                    "C": base_shares["C"] + base_shares["H"] - h,
                }
                for (style, depth_weights), depth_weight in zip(
                    styles.items(), [0.25, 0.50, 0.25]
                ):
                    name = f"{bank}/h{h:.2f}/{style}"
                    strategic = mix_populations(levels, depth_weights)
                    distribution = mix_populations(
                        ordered_components + [strategic],
                        [actual_shares[type_name] for type_name in TYPE_NAMES],
                    )
                    world_weight = 0.20 * 0.50 * h_weight * depth_weight
                    scenarios[name] = distribution
                    world_weights[name] = world_weight
                    metadata[name] = {
                        "bank": bank,
                        "family": family,
                        "bids": bids,
                        "shares": actual_shares,
                        "S_style": style,
                        "S_level_weights": depth_weights,
                        "A_fraction_of_T": a_share,
                        "world_weight": world_weight,
                        **structural_probabilities(distribution),
                    }
    return {
        "scenarios": scenarios,
        "metadata": metadata,
        "weights": world_weights,
        "models": models,
        "parameters": {
            "seed": seed,
            "samples": samples,
            "screen": screen,
            "check": check,
            "fresh": fresh,
            "shared_seeds": shared_seeds,
            "family_shares": {
                name: dict(zip(TYPE_NAMES, values))
                for name, values in family_shares.items()
            },
            "family_world_weights": {name: 0.20 for name in family_shares},
            "bid_world_weights": {name: 0.50 for name in bid_settings},
            "H_values": h_values,
            "H_world_weights": [0.25, 0.50, 0.25],
            "S_styles": styles,
            "S_style_world_weights": [0.25, 0.50, 0.25],
            "F_mixture_weights": f_weights,
            "F_components": [f_zero["parameters"], f_secondary["parameters"]],
            "Z_allocation": [0, 0, 0, 0, 100],
        },
    }
