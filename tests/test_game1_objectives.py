"""Independent small-game checks for exact weighted Game 1 optimization."""

from itertools import product
from math import comb
import unittest

import numpy as np

from blotto.game import best_response, marginals
from blotto.game1_objectives import search_objectives


def legal_rows(budget):
    return np.array(
        [row for row in product(range(budget + 1), repeat=5) if sum(row) == budget]
    )


def literal_score(own, other, values):
    return sum(
        value if x > y else value / 2 if x == y else 0
        for x, y, value in zip(own, other, values)
    )


def literal_metrics(scores, weights, optima, tail_mass):
    weights = np.asarray(weights, float)
    weights /= weights.sum()
    active = np.flatnonzero(weights)
    tail_left, tail_total = tail_mass, 0.0
    for index in sorted(active, key=lambda i: scores[i]):
        used = min(tail_left, weights[index])
        tail_total += used * scores[index]
        tail_left -= used
        if tail_left <= 1e-14:
            break
    return {
        "weighted_mean": sum(weights[i] * scores[i] for i in active),
        "lower_tail_mean": tail_total / tail_mass,
        "minimum": min(scores[i] for i in active),
        "maximum_regret": max(optima[i] - scores[i] for i in active),
        "mean_regret": sum(weights[i] * (optima[i] - scores[i]) for i in active),
    }


class Game1ObjectiveTests(unittest.TestCase):
    def test_all_objectives_match_independent_exhaustion(self):
        budget = 4
        values = np.array([1, 2, 3, 4, 5])
        opponents = [
            ([[0, 0, 0, 0, 4], [1, 0, 1, 2, 0]], [1, 3]),
            ([[0, 0, 0, 4, 0], [0, 2, 2, 0, 0]], [2, 1]),
            ([[1, 1, 1, 1, 0], [2, 0, 0, 0, 2]], [1, 1]),
        ]
        scenarios = {
            str(i): marginals(rows, weights, budget)
            for i, (rows, weights) in enumerate(opponents)
        }
        priors = {"balanced": [2, 3, 5], "ignore_second": [1, 0, 2]}
        rows = legal_rows(budget)
        scores = np.array(
            [
                [
                    sum(
                        w * literal_score(own, other, values)
                        for w, other in zip(weights, support)
                    )
                    / sum(weights)
                    for support, weights in opponents
                ]
                for own in rows
            ]
        )
        optima = scores.max(axis=0)
        result = search_objectives(
            scenarios,
            priors,
            tail_mass=0.35,
            tolerances=(0, 0.1, 0.25, 20),
            budget=budget,
            block_size=7,
        )
        self.assertEqual(result["allocations_examined"], comb(budget + 4, 4))
        np.testing.assert_allclose(result["optimal_scores"], optima)
        for name, weights in priors.items():
            metrics = [literal_metrics(row, weights, optima, 0.35) for row in scores]
            choices = result["priors"][name]["choices"]
            best_tail = max(row["lower_tail_mean"] for row in metrics)
            for objective, choice in choices.items():
                index = int(
                    np.flatnonzero(np.all(rows == choice["allocation"], axis=1))[0]
                )
                for metric, expected in metrics[index].items():
                    self.assertAlmostEqual(choice[metric], expected, places=11)
                if objective.startswith("guard_"):
                    tolerance = float(objective[6:])
                    feasible = [
                        row
                        for row in metrics
                        if row["lower_tail_mean"] >= best_tail - tolerance - 1e-12
                    ]
                    self.assertGreaterEqual(
                        choice["lower_tail_mean"], best_tail - tolerance - 1e-12
                    )
                    self.assertAlmostEqual(
                        choice["weighted_mean"],
                        max(row["weighted_mean"] for row in feasible),
                    )
                else:
                    metric = {
                        "mean": "weighted_mean",
                        "tail": "lower_tail_mean",
                        "maximin": "minimum",
                        "minimax_regret": "maximum_regret",
                    }[objective]
                    optimum = (
                        min(row[metric] for row in metrics)
                        if objective == "minimax_regret"
                        else max(row[metric] for row in metrics)
                    )
                    self.assertAlmostEqual(choice[metric], optimum)
            mixed = sum(
                weight * scenarios[str(i)] for i, weight in enumerate(weights)
            ) / sum(weights)
            _, dp_score = best_response(mixed, values, budget)
            self.assertAlmostEqual(choices["mean"]["weighted_mean"], dp_score)
            self.assertAlmostEqual(result["priors"][name]["mean_dp_score"], dp_score)

    def test_tail_guard_changes_the_mean_optimum(self):
        scenarios = {
            "fifth": marginals([[0, 0, 0, 0, 2]], budget=2),
            "fourth": marginals([[0, 0, 0, 2, 0]], budget=2),
        }
        result = search_objectives(
            scenarios, {"prior": [0.8, 0.2]}, budget=2, block_size=3
        )
        choices = result["priors"]["prior"]["choices"]
        self.assertEqual(choices["mean"]["allocation"], [0, 0, 1, 1, 0])
        self.assertAlmostEqual(choices["mean"]["weighted_mean"], 8.2)
        self.assertAlmostEqual(choices["mean"]["lower_tail_mean"], 7)
        self.assertEqual(choices["guard_0.25"]["allocation"], [0, 0, 0, 0, 2])
        self.assertAlmostEqual(choices["guard_0.25"]["weighted_mean"], 7.6)
        self.assertAlmostEqual(choices["guard_0.25"]["lower_tail_mean"], 7.5)
        self.assertEqual(
            choices["guard_0.50"]["allocation"], choices["mean"]["allocation"]
        )

    def test_zero_weight_scenario_is_excluded_from_every_objective(self):
        first = marginals([[0, 0, 0, 0, 3]], budget=3)
        second = marginals([[0, 0, 0, 3, 0]], budget=3)
        alone = search_objectives(
            {"first": first}, {"prior": [1]}, budget=3, block_size=1
        )
        extended = search_objectives(
            {"first": first, "unused": second},
            {"prior": [2, 0]},
            budget=3,
            block_size=17,
        )
        for objective, expected in alone["priors"]["prior"]["choices"].items():
            observed = extended["priors"]["prior"]["choices"][objective]
            for metric in [
                "weighted_mean",
                "lower_tail_mean",
                "minimum",
                "maximum_regret",
                "mean_regret",
            ]:
                self.assertAlmostEqual(observed[metric], expected[metric])

    def test_zero_budget_has_one_allocation(self):
        result = search_objectives(
            {"empty": marginals([[0] * 5], budget=0)}, {"prior": [1]}, budget=0
        )
        self.assertEqual(result["allocations_examined"], 1)
        for choice in result["priors"]["prior"]["choices"].values():
            self.assertEqual(choice["allocation"], [0] * 5)
            self.assertAlmostEqual(choice["weighted_mean"], 7.5)
            self.assertAlmostEqual(choice["maximum_regret"], 0)

    def test_invalid_inputs(self):
        scenarios = {"one": marginals([[0, 0, 0, 0, 2]], budget=2)}
        for weights in [[0], [-1], [np.nan], [np.inf], [1, 1]]:
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                search_objectives(scenarios, {"prior": weights}, budget=2)
        for options in [
            {"tail_mass": 0},
            {"tolerances": [-1]},
            {"block_size": 0},
            {"budget": -1},
            {"tolerances": [0.001, 0.002]},
        ]:
            arguments = {"budget": 2, **options}
            with self.subTest(options=options), self.assertRaises(ValueError):
                search_objectives(scenarios, {"prior": [1]}, **arguments)


if __name__ == "__main__":
    unittest.main()
