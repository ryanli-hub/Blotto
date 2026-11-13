"""Exact four-player castle scoring and fast sampled ranking rewards."""

from __future__ import annotations

import numpy as np

from .game import BUDGET, VALUES, validate_allocations


PRIZES = np.array([9.0, 4.0, 2.0, 0.0])
RANK_REWARDS = np.full((4, 4), np.nan)
for better in range(4):
    for tied_others in range(4 - better):
        RANK_REWARDS[better, tied_others] = PRIZES[
            better : better + tied_others + 1
        ].mean()


def _validate_groups(groups, players):
    array = np.asarray(groups)
    if array.ndim != 3 or array.shape[1:] != (players, len(VALUES)):
        raise ValueError(f"Expected shape (groups, {players}, 5).")
    return validate_allocations(array.reshape(-1, 5), BUDGET, 5).reshape(array.shape)


def score_groups(groups):
    """Return castle points and ranking payouts, both shaped (groups, 4)."""
    groups = _validate_groups(groups, 4)
    winners = groups == groups.max(axis=1, keepdims=True)
    winner_counts = winners.sum(axis=1, keepdims=True)
    # All possible castle shares are exact integers in units of 1/12 point.
    castle_units = (winners * (12 * VALUES[None, None, :] // winner_counts)).sum(axis=2)
    differences = castle_units[:, :, None] - castle_units[:, None, :]
    better = (differences < 0).sum(axis=2)
    tied_others = (differences == 0).sum(axis=2) - 1
    return castle_units / 12, RANK_REWARDS[better, tied_others]


def prepare_triples(opponents):
    """Precompute score differences: shape (5, 101, 3, sampled_groups)."""
    opponents = _validate_groups(opponents, 3)
    group_count = len(opponents)
    table = np.empty((5, BUDGET + 1, 3, group_count), dtype=np.int16)
    bids = np.arange(BUDGET + 1)[:, None]

    for castle, value in enumerate(VALUES):
        allocations = opponents[:, :, castle]
        maximum = allocations.max(axis=1)
        winners = allocations == maximum[:, None]
        winner_count = winners.sum(axis=1)
        lose_share = 12 * value // winner_count
        tied_share = 12 * value // (winner_count + 1)
        for player in range(3):
            # Our score minus this opponent's score, for this castle alone.
            lose_difference = winners[:, player] * -lose_share
            tie_difference = (~winners[:, player]) * tied_share
            table[castle, :, player] = np.where(
                bids > maximum,
                12 * value,
                np.where(bids == maximum, tie_difference, lose_difference),
            )
    return table


def evaluate_candidates(candidates, prepared, chunk_size=64, return_samples=False):
    """Score each allocation on the same sampled triples of opponents."""
    candidates = validate_allocations(candidates, BUDGET, 5)
    if not isinstance(chunk_size, (int, np.integer)) or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer.")
    prepared = np.asarray(prepared)
    if prepared.ndim != 4 or prepared.shape[:3] != (5, BUDGET + 1, 3):
        raise ValueError("Use a table returned by prepare_triples.")
    group_count = prepared.shape[-1]
    if group_count == 0:
        raise ValueError("At least one sampled group is required.")
    shape = (len(candidates), group_count) if return_samples else (len(candidates),)
    result = np.empty(shape)

    for start in range(0, len(candidates), chunk_size):
        block = candidates[start : start + chunk_size]
        differences = prepared[0, block[:, 0]].copy()
        for castle in range(1, 5):
            differences += prepared[castle, block[:, castle]]
        better = (differences < 0).sum(axis=1)
        tied_others = (differences == 0).sum(axis=1)
        rewards = RANK_REWARDS[better, tied_others]
        result[start : start + len(block)] = (
            rewards if return_samples else rewards.mean(axis=1)
        )
    return result
