"""Hand-calculated and invariant checks for weighted Game 2 objectives."""

import unittest

import numpy as np

from blotto.game2_metrics import pareto_indices, select_by_objective, summarize_scores


class WeightedMetricTests(unittest.TestCase):
    def setUp(self):
        self.scores = np.array([[2, 6, 9], [4, 4, 8]], dtype=float)
        self.weights = np.array([0.1, 0.3, 0.6])

    def test_fractional_tail_boundary_by_hand(self):
        result = summarize_scores(self.scores, self.weights, tail_mass=0.25)
        np.testing.assert_allclose(result["weighted_mean"], [7.4, 6.4])
        np.testing.assert_allclose(result["minimum"], [2, 4])
        # The first row uses all 10% at score 2, then 15% of the score-6 scenario.
        np.testing.assert_allclose(result["lower_tail_mean"], [4.4, 4])
        np.testing.assert_allclose(result["maximum_regret"], [2, 2])
        np.testing.assert_allclose(result["mean_regret"], [0.2, 1.2])

    def test_full_tail_equals_mean(self):
        result = summarize_scores(self.scores, self.weights, tail_mass=1)
        np.testing.assert_allclose(result["lower_tail_mean"], result["weighted_mean"])

    def test_split_scenario_weight_invariance(self):
        original = summarize_scores(self.scores, self.weights, tail_mass=0.25)
        duplicated = summarize_scores(
            self.scores[:, [0, 0, 1, 2]], [0.04, 0.06, 0.3, 0.6], tail_mass=0.25
        )
        for metric in original:
            np.testing.assert_allclose(duplicated[metric], original[metric])

    def test_zero_weights_excluded_and_scale_does_not_change_metrics(self):
        original = summarize_scores(self.scores, self.weights)
        augmented = summarize_scores(
            np.column_stack([self.scores, [-999, 999]]), [1, 3, 6, 0]
        )
        for metric in original:
            np.testing.assert_allclose(augmented[metric], original[metric])

    def test_mean_regret_and_mean_have_equivalent_rankings(self):
        scores = np.array([[0, 9], [5.5, 5.5], [5.3, 7.5]])
        weights = np.array([0.2, 0.8])
        reference = np.array([8, 9])
        result = summarize_scores(scores, weights, reference_scores=reference)
        np.testing.assert_allclose(result["mean_regret"], 8.8 - result["weighted_mean"])
        np.testing.assert_array_equal(
            np.argsort(result["mean_regret"]), np.argsort(-result["weighted_mean"])
        )

    def test_objectives_and_tail_guard_tradeoff(self):
        scores = np.array([[0, 9], [5.5, 5.5], [5.3, 7.5]])
        selected = select_by_objective(scores, [0.2, 0.8], tail_tolerance=0.25)
        self.assertEqual(
            selected,
            {
                "mean": 0,
                "maximin": 1,
                "tail": 1,
                "minimax_regret": 2,
                "mean_with_tail_guard": 2,
            },
        )
        self.assertEqual(
            select_by_objective(scores, [0.2, 0.8], tail_tolerance=0.1)[
                "mean_with_tail_guard"
            ],
            1,
        )
        self.assertEqual(
            select_by_objective(scores, [0.2, 0.8], tail_tolerance=6)[
                "mean_with_tail_guard"
            ],
            0,
        )

    def test_pareto_retains_tradeoffs_and_exact_duplicates(self):
        means = [8, 6, 7.56, 7.56, 5, 7.5, 6]
        tails = [0, 6, 5.8, 5.8, 5, 5.8, 5]
        np.testing.assert_array_equal(pareto_indices(means, tails), [0, 1, 2, 3])

    def test_invalid_weights_inputs_and_tolerances(self):
        for weights in [[0, 0, 0], [1, -1, 1], [1, np.nan, 1], [1, np.inf, 1], [1, 1]]:
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                summarize_scores(self.scores, weights)
        for tail_mass in [0, -0.1, 1.1, np.nan]:
            with self.subTest(tail_mass=tail_mass), self.assertRaises(ValueError):
                summarize_scores(self.scores, self.weights, tail_mass=tail_mass)
        for scores in [[], [1, 2], [[np.nan]], np.empty((0, 3))]:
            with self.subTest(scores=scores), self.assertRaises(ValueError):
                summarize_scores(scores, self.weights)
        for references in [[1, 2], [1, np.inf, 3]]:
            with self.subTest(references=references), self.assertRaises(ValueError):
                summarize_scores(self.scores, self.weights, reference_scores=references)
        for tolerance in [-1, np.nan, np.inf]:
            with self.subTest(tolerance=tolerance), self.assertRaises(ValueError):
                select_by_objective(self.scores, self.weights, tail_tolerance=tolerance)


if __name__ == "__main__":
    unittest.main()
