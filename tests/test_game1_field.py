"""Regression checks for Game 1 response permutations and population construction."""

from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import patch

import numpy as np

from blotto.game import best_response, payoff_matrix
from blotto.game1_field import (
    _reasoning_levels,
    build_field,
    distribution,
    response_sample,
)


class Game1FieldTests(unittest.TestCase):
    def test_permuted_responses_are_legal_and_near_optimal_in_original_game(self):
        opponents = distribution(
            [[8, 14, 2, 35, 41], [2, 16, 1, 37, 44], [25, 0, 25, 0, 50]],
            [0.20, 0.35, 0.45],
        )
        orders = [[4, 2, 0, 3, 1], [1, 3, 4, 0, 2]]
        slack = 0.15
        rows, diagnostic = response_sample(
            opponents["marginals"],
            np.random.default_rng(42),
            count_per_order=6,
            slack=slack,
            orders=orders,
        )
        self.assertEqual(rows.shape, (12, 5))
        self.assertTrue(np.all(rows >= 0))
        np.testing.assert_array_equal(rows, rows.astype(int))
        np.testing.assert_array_equal(rows.sum(axis=1), np.full(12, 100))

        # Score against complete opponent vectors, bypassing the reward lookup.
        response, _ = best_response(opponents["marginals"])
        optimum = float(
            payoff_matrix([response], opponents["allocations"])[0]
            @ opponents["weights"]
        )
        scores = payoff_matrix(rows, opponents["allocations"]) @ opponents["weights"]
        gaps = optimum - scores
        self.assertTrue(np.all(gaps >= -1e-12))
        self.assertTrue(np.all(gaps <= slack + 1e-12))
        self.assertAlmostEqual(diagnostic["best_response_score"], optimum)
        self.assertAlmostEqual(diagnostic["max_optimality_gap"], max(0, gaps.max()))
        self.assertEqual(diagnostic["orders"], orders)

    def test_reasoning_preserves_actual_H_and_T_masses_across_levels(self):
        atoms = np.eye(5, dtype=int) * 100
        components = {
            "H": distribution([atoms[0]]),
            "C": distribution([atoms[1]]),
            "T": distribution([atoms[2]]),
        }
        team_types = {name: components["T"] for name in ["A", "B", "variations"]}
        strategic = distribution([atoms[3]])
        alternative_c = distribution([atoms[4]])
        shares = {"H": 0.02, "C": 0.48, "T": 0.20, "S": 0.30}

        for fresh in [False, True]:
            beliefs = []

            def response(marginal, *_arguments):
                beliefs.append(marginal.copy())
                return strategic, [{"max_optimality_gap": 0.0}]

            with patch("blotto.game1_field._response_population", side_effect=response):
                levels, _ = _reasoning_levels(
                    components,
                    team_types,
                    shares,
                    np.random.default_rng(81),
                    "diverse",
                    2,
                    fresh,
                    alternative_c,
                )
            self.assertEqual(len(levels), 4)
            self.assertEqual(len(beliefs), 12)
            expected_h = [0.01, 0.03, 0.05] if fresh else [0.0, 0.02, 0.05]
            expected_t = [0.12, 0.23, 0.32] if fresh else [0.10, 0.20, 0.30]
            response_fractions = [0.45, 0.65, 0.85] if fresh else [0.40, 0.60, 0.80]
            for index, belief in enumerate(beliefs):
                level, choice = divmod(index, 3)
                h, t = expected_h[choice], expected_t[choice]
                fraction = response_fractions[choice] if level else 0
                c = (1 - h - t) * (1 - fraction)
                s = (1 - h - t) * fraction
                c_fraction = [0, 1, 0.5][choice]
                # Each atom's 100-soldier coordinate uniquely identifies its mass.
                np.testing.assert_allclose(
                    belief[:, 100], [h, c * c_fraction, t, s, c * (1 - c_fraction)]
                )
                np.testing.assert_allclose(belief.sum(axis=1), 1)

    def test_training_and_fresh_fields_have_legal_banks_and_correct_weights(self):
        strategic = distribution([[0, 0, 0, 100, 0]])
        for fresh in [False, True]:
            with patch(
                "blotto.game1_field._response_population",
                return_value=(strategic, [{"max_optimality_gap": 0.0}]),
            ), redirect_stdout(StringIO()):
                field = build_field(
                    seed=37, samples=20, responses_per_order=2, fresh=fresh
                )
            self.assertEqual(len(field["scenarios"]), 80)
            self.assertEqual(len(field["models"]), 20)
            self.assertAlmostEqual(sum(field["weights"].values()), 1)
            families = {item["family"] for item in field["metadata"].values()}
            self.assertEqual(len(families), 5)
            for family in families:
                weight = sum(
                    field["weights"][name]
                    for name, item in field["metadata"].items()
                    if item["family"] == family
                )
                self.assertAlmostEqual(weight, 0.20)
            for bank in field["models"].values():
                distributions = (
                    list(bank["components"].values())
                    + bank["levels"]
                    + [bank["alternative_C"]]
                )
                for group in distributions:
                    rows, weights = group["allocations"], group["weights"]
                    self.assertTrue(np.all(rows >= 0))
                    np.testing.assert_array_equal(rows, rows.astype(int))
                    np.testing.assert_array_equal(
                        rows.sum(axis=1), np.full(len(rows), 100)
                    )
                    self.assertTrue(np.all(weights >= 0))
                    self.assertAlmostEqual(weights.sum(), 1)
            for name, marginal in field["scenarios"].items():
                info = field["metadata"][name]
                shares = info["shares"]
                self.assertGreaterEqual(shares["H"], 0)
                self.assertLessEqual(shares["H"], 0.05)
                self.assertAlmostEqual(sum(shares.values()), 1)
                self.assertTrue(np.all(marginal >= 0))
                np.testing.assert_allclose(marginal.sum(axis=1), 1)
                if info["family"] == "T_free":
                    self.assertEqual(shares["T"], 0)
                    components = field["models"][info["bank"]]["components"]
                    expected = (
                        shares["H"] * components["H"]["marginals"]
                        + shares["C"] * components["C"]["marginals"]
                        + shares["S"] * strategic["marginals"]
                    )
                    np.testing.assert_allclose(marginal, expected)


if __name__ == "__main__":
    unittest.main()
