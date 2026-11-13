"""Compare candidate scores across weighted opponent-population scenarios."""

import numpy as np


def summarize_scores(scores, weights, reference_scores=None, tail_mass=0.2):
    """Return mean, minimum, lower-tail mean, and two regret measures per row."""
    scores = np.asarray(scores, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if scores.ndim != 2 or min(scores.shape) == 0 or not np.all(np.isfinite(scores)):
        raise ValueError(
            "Scores must be a nonempty finite candidate-by-scenario matrix."
        )
    if weights.shape != (scores.shape[1],):
        raise ValueError("Supply one weight per scenario.")
    if not np.all(np.isfinite(weights)) or np.any(weights < 0) or weights.sum() <= 0:
        raise ValueError("Scenario weights must be finite, nonnegative, and nonzero.")
    if not np.isfinite(weights.sum()):
        raise ValueError("The sum of scenario weights must be finite.")
    if not np.isfinite(tail_mass) or not 0 < tail_mass <= 1:
        raise ValueError("tail_mass must lie in (0, 1].")
    references = (
        scores.max(axis=0)
        if reference_scores is None
        else np.asarray(reference_scores, dtype=float)
    )
    if references.shape != (scores.shape[1],) or not np.all(np.isfinite(references)):
        raise ValueError("Supply one finite reference score per scenario.")

    positive = weights > 0
    weights = weights[positive] / weights.sum()
    scores = scores[:, positive]
    references = references[positive]
    order = np.argsort(scores, axis=1, kind="stable")
    sorted_scores = np.take_along_axis(scores, order, axis=1)
    sorted_weights = weights[order]
    mass_before = np.cumsum(sorted_weights, axis=1) - sorted_weights
    # A scenario crossing the tail boundary contributes only its remaining mass.
    tail_weights = np.minimum(sorted_weights, np.maximum(tail_mass - mass_before, 0))
    regrets = references - scores
    return {
        "weighted_mean": scores @ weights,
        "minimum": scores.min(axis=1),
        "lower_tail_mean": (sorted_scores * tail_weights).sum(axis=1) / tail_mass,
        "maximum_regret": regrets.max(axis=1),
        "mean_regret": regrets @ weights,
    }


def select_by_objective(
    scores, weights, reference_scores=None, tail_mass=0.2, tail_tolerance=0.25
):
    """Select one row per objective; exact ties keep the earlier candidate."""
    if not np.isfinite(tail_tolerance) or tail_tolerance < 0:
        raise ValueError("tail_tolerance must be finite and nonnegative.")
    metrics = summarize_scores(scores, weights, reference_scores, tail_mass)
    means = metrics["weighted_mean"]
    tails = metrics["lower_tail_mean"]
    allowed = tails >= tails.max() - tail_tolerance
    return {
        "mean": int(np.argmax(means)),
        "maximin": int(np.argmax(metrics["minimum"])),
        "tail": int(np.argmax(tails)),
        "minimax_regret": int(np.argmin(metrics["maximum_regret"])),
        "mean_with_tail_guard": int(np.argmax(np.where(allowed, means, -np.inf))),
    }


def pareto_indices(weighted_mean, lower_tail_mean):
    """Keep rows no other row improves in one metric without worsening the other."""
    means = np.asarray(weighted_mean, dtype=float)
    tails = np.asarray(lower_tail_mean, dtype=float)
    if means.ndim != 1 or means.size == 0 or tails.shape != means.shape:
        raise ValueError("Supply matching nonempty mean and tail vectors.")
    if not np.all(np.isfinite(means)) or not np.all(np.isfinite(tails)):
        raise ValueError("Mean and tail scores must be finite.")
    order = np.lexsort((-tails, -means))
    selected = []
    best_tail, best_mean = -np.inf, -np.inf
    for index in order:
        if tails[index] > best_tail:
            selected.append(index)
            best_tail, best_mean = tails[index], means[index]
        elif tails[index] == best_tail and means[index] == best_mean:
            selected.append(index)
    return np.sort(np.asarray(selected, dtype=int))
