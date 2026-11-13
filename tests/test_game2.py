"""Independent checks of both tie rules and the fast Game 2 evaluator."""

from fractions import Fraction
from itertools import product
from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import patch

import numpy as np

from blotto.game2 import evaluate_candidates, prepare_triples, score_groups
from blotto.game2_field import _reasoning_levels, build_field
from blotto.game2_metrics import summarize_scores
from blotto.game2_population import (
    concentrated_by_count,
    concentration_mixture,
    first_three_population,
    mix_populations,
    population,
    sample_triples,
)
from blotto.game2_search import (
    finite_reasoning,
    independent_evaluation,
    maximum_regrets,
    neighbors,
    shortlist_indices,
)


def literal_scores(group):
    """Apply the written rules with exact fractions, independently of NumPy."""
    points = [Fraction(0) for _ in range(4)]
    for castle in range(5):
        highest = max(player[castle] for player in group)
        winners = [i for i, player in enumerate(group) if player[castle] == highest]
        for winner in winners:
            points[winner] += Fraction(castle + 1, len(winners))
    prizes = [9, 4, 2, 0]
    rewards = []
    for score in points:
        better = sum(other > score for other in points)
        equal = sum(other == score for other in points)
        rewards.append(Fraction(sum(prizes[better : better + equal]), equal))
    return np.array(points, float), np.array(rewards, float)


class Game2ScoringTests(unittest.TestCase):
    def test_identical_allocations_split_everything(self):
        groups = np.array([[[0, 0, 0, 0, 100]] * 4, [[20] * 5] * 4])
        points, rewards = score_groups(groups)
        np.testing.assert_array_equal(points, np.full((2, 4), 3.75))
        np.testing.assert_array_equal(rewards, np.full((2, 4), 3.75))

    def test_zero_bids_and_three_way_castle_ties(self):
        groups = np.array(
            [
                [
                    [0, 0, 49, 51, 0],
                    [0, 0, 49, 51, 0],
                    [0, 0, 49, 0, 51],
                    [0, 0, 0, 0, 100],
                ],
                [
                    [100, 0, 0, 0, 0],
                    [0, 100, 0, 0, 0],
                    [0, 0, 100, 0, 0],
                    [0, 0, 0, 100, 0],
                ],
            ]
        )
        points, rewards = score_groups(groups)
        for i, group in enumerate(groups):
            exact_points, exact_rewards = literal_scores(group)
            np.testing.assert_array_equal(points[i], exact_points)
            np.testing.assert_array_equal(rewards[i], exact_rewards)

    def test_hand_calculated_tied_first_and_third(self):
        group = np.array(
            [
                [
                    [0, 0, 50, 50, 0],
                    [0, 0, 50, 50, 0],
                    [0, 0, 0, 0, 100],
                    [0, 0, 0, 0, 100],
                ]
            ]
        )
        points, rewards = score_groups(group)
        np.testing.assert_array_equal(points[0], [4.25, 4.25, 3.25, 3.25])
        np.testing.assert_array_equal(rewards[0], [6.5, 6.5, 1, 1])

    def test_first_three_castles_can_finish_second_or_lose_all(self):
        groups = np.array(
            [
                [
                    [33, 33, 34, 0, 0],
                    [0, 0, 0, 49, 51],
                    [30, 30, 30, 10, 0],
                    [30, 30, 30, 0, 10],
                ],
                [
                    [33, 33, 34, 0, 0],
                    [34, 0, 0, 66, 0],
                    [0, 34, 0, 0, 66],
                    [0, 0, 35, 32, 33],
                ],
            ]
        )
        points, rewards = score_groups(groups)
        np.testing.assert_array_equal(points, [[6, 9, 0, 0], [0, 5, 7, 3]])
        np.testing.assert_array_equal(rewards, [[4, 9, 1, 1], [0, 4, 9, 2]])

    def test_literal_rules_random_groups_and_permutations(self):
        rng = np.random.default_rng(20261104)
        dense = rng.multinomial(100, np.full(5, 0.2), size=(120, 4))
        templates = np.array(
            [
                [0, 0, 49, 51, 0],
                [0, 1, 36, 0, 63],
                [0, 0, 0, 50, 50],
                [1, 1, 1, 1, 96],
                [0, 0, 0, 0, 100],
            ]
        )
        sparse = templates[rng.integers(len(templates), size=(120, 4))]
        groups = np.concatenate([dense, sparse])
        points, rewards = score_groups(groups)
        np.testing.assert_allclose(points.sum(axis=1), 15)
        np.testing.assert_allclose(rewards.sum(axis=1), 15)
        for i, group in enumerate(groups):
            exact_points, exact_rewards = literal_scores(group)
            np.testing.assert_array_equal(points[i], exact_points)
            np.testing.assert_array_equal(rewards[i], exact_rewards)
        permutation = [2, 0, 3, 1]
        other_points, other_rewards = score_groups(groups[:, permutation])
        np.testing.assert_array_equal(other_points, points[:, permutation])
        np.testing.assert_array_equal(other_rewards, rewards[:, permutation])

    def test_lookup_matches_direct_scores_including_ties(self):
        rng = np.random.default_rng(94)
        candidates = np.array(
            [
                [0, 0, 49, 51, 0],
                [0, 1, 36, 0, 63],
                [8, 9, 10, 11, 62],
                [0, 0, 0, 0, 100],
                [20, 20, 20, 20, 20],
            ]
        )
        triples = candidates[rng.integers(len(candidates), size=(180, 3))]
        table = prepare_triples(triples)
        sampled = evaluate_candidates(
            candidates, table, chunk_size=2, return_samples=True
        )
        for i, allocation in enumerate(candidates):
            groups = np.concatenate(
                [np.broadcast_to(allocation, (len(triples), 1, 5)), triples], axis=1
            )
            np.testing.assert_array_equal(sampled[i], score_groups(groups)[1][:, 0])
        np.testing.assert_array_equal(
            evaluate_candidates(candidates, table), sampled.mean(axis=1)
        )

    def test_joint_allocations_change_expected_ranking_reward(self):
        # Each castle has the same marginal in both populations, but pairings differ.
        first = np.array([[50, 50, 0, 0, 0], [0, 0, 50, 50, 0]])
        second = np.array([[50, 0, 50, 0, 0], [0, 50, 0, 50, 0]])
        np.testing.assert_array_equal(np.sort(first, axis=0), np.sort(second, axis=0))
        indices = np.array(list(product(range(2), repeat=3)))
        own = [[0, 0, 49, 51, 0]]
        first_reward = evaluate_candidates(own, prepare_triples(first[indices]))[0]
        second_reward = evaluate_candidates(own, prepare_triples(second[indices]))[0]
        self.assertNotAlmostEqual(first_reward, second_reward)

    def test_original_ideas_exact_population_mixtures(self):
        anchors = np.array([[0, 1, 36, 0, 63], [0, 0, 49, 51, 0]])
        indices = np.array(list(product(range(2), repeat=3)))
        samples = evaluate_candidates(
            anchors, prepare_triples(anchors[indices]), return_samples=True
        )
        for share, expected in [(0.5, [3.75, 3.75]), (0.8, [3.12, 6.27])]:
            probabilities = np.array([share, 1 - share])[indices].prod(axis=1)
            np.testing.assert_allclose(samples @ probabilities, expected)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            score_groups(np.zeros((1, 3, 5)))
        with self.assertRaises(ValueError):
            prepare_triples(np.zeros((2, 3, 5)))
        valid = np.array([[[0, 0, 0, 0, 100]] * 3])
        table = prepare_triples(valid)
        for candidate in [[0, 0, 0, 0, 99], [0, 0, 0, 0.5, 99.5]]:
            with self.assertRaises(ValueError):
                evaluate_candidates(candidate, table)
        with self.assertRaises(ValueError):
            evaluate_candidates([0, 0, 0, 0, 100], table, chunk_size=0)


class Game2PopulationAndSearchTests(unittest.TestCase):
    def test_duplicate_vectors_and_population_mixture_weights(self):
        first = [0, 1, 36, 0, 63]
        second = [0, 0, 49, 51, 0]
        repeated = population([first, first, second], [1, 2, 1])
        self.assertEqual(len(repeated["allocations"]), 2)
        mixed = mix_populations([repeated, population([second])], [4, 1])
        weights = dict(zip(map(tuple, mixed["allocations"]), mixed["weights"]))
        self.assertAlmostEqual(weights[tuple(first)], 0.6)
        self.assertAlmostEqual(weights[tuple(second)], 0.4)

    def test_opponents_choose_types_independently_within_groups(self):
        first = [0, 1, 36, 0, 63]
        second = [0, 0, 49, 51, 0]
        mixed = mix_populations([population([first]), population([second])], [0.8, 0.2])
        triples = sample_triples(mixed, 30000, np.random.default_rng(1871))
        is_first = np.all(triples == first, axis=2)
        np.testing.assert_allclose(is_first.mean(axis=0), 0.8, atol=0.01)
        self.assertAlmostEqual(np.all(is_first, axis=1).mean(), 0.8**3, delta=0.015)
        mixed_groups = (is_first.sum(axis=1) > 0) & (is_first.sum(axis=1) < 3)
        self.assertAlmostEqual(mixed_groups.mean(), 1 - 0.8**3 - 0.2**3, delta=0.015)

    def test_neighbors_spend_exact_budget_and_contain_expected_moves(self):
        seed = np.array([[0, 1, 36, 0, 63]])
        nearby = neighbors(seed, steps=(1, 5))
        self.assertTrue(np.all(nearby >= 0))
        np.testing.assert_array_equal(nearby.sum(axis=1), np.full(len(nearby), 100))
        self.assertEqual(len(nearby), len(np.unique(nearby, axis=0)))
        rows = set(map(tuple, nearby))
        self.assertIn(tuple(seed[0]), rows)
        self.assertIn((1, 0, 36, 0, 63), rows)
        self.assertIn((0, 1, 41, 0, 58), rows)
        self.assertNotIn((0, -4, 41, 0, 63), rows)
        for row in nearby:
            change = row - seed[0]
            self.assertIn(int(np.abs(change).sum()), (0, 2, 10))
            self.assertLessEqual(np.count_nonzero(change), 2)

    def test_shortlist_retains_robust_tradeoff_and_scenario_specialists(self):
        scores = np.array([[9.0, 3.0], [3.0, 9.0], [7.0, 7.0], [6.0, 6.0]])
        np.testing.assert_array_equal(maximum_regrets(scores), [6, 6, 2, 3])
        np.testing.assert_array_equal(
            shortlist_indices(scores, robust_count=1, per_scenario=1), [0, 1, 2]
        )
        np.testing.assert_array_equal(
            maximum_regrets(scores + [1, -2]), maximum_regrets(scores)
        )

    def test_independent_evaluation_exact_scores_and_paired_gaps(self):
        first = np.array([0, 1, 36, 0, 63])
        second = np.array([0, 0, 49, 51, 0])
        result = independent_evaluation(
            np.array([first, second]),
            second,
            population([first]),
            groups=17,
            rng=np.random.default_rng(918),
            batch=5,
        )
        np.testing.assert_array_equal(result["scores"], [3.75, 9])
        np.testing.assert_array_equal(result["score_gaps"], [5.25, 0])
        np.testing.assert_array_equal(result["score_standard_errors"], [0, 0])
        np.testing.assert_array_equal(result["gap_standard_errors"], [0, 0])
        self.assertEqual(result["reference_score"], 9)
        self.assertEqual(result["reference"], second.tolist())
        self.assertEqual(result["groups"], 17)


class Game2ConcentrationSensitivityTests(unittest.TestCase):
    def setUp(self):
        # Distinct supports make each concentration cohort's mass observable.
        self.conditional = {
            "components": [
                population([[0, 0, 0, 0, 100], [0, 0, 0, 100, 0]], [1, 3]),
                population([[0, 0, 0, 50, 50], [0, 0, 50, 50, 0]], [2, 3]),
                population([[0, 0, 30, 30, 40], [0, 30, 30, 40, 0]], [3, 1]),
            ],
            "one_castle_all_in": population([[0, 0, 100, 0, 0]]),
            "parameters": {},
        }

    def test_exact_conditional_mixture_and_weighted_coordinates(self):
        mixture = concentration_mixture(self.conditional, 0.32, all_in_fraction=0)
        observed = dict(zip(map(tuple, mixture["allocations"]), mixture["weights"]))
        expected = {
            (0, 0, 0, 0, 100): 0.08,
            (0, 0, 0, 100, 0): 0.24,
            (0, 0, 0, 50, 50): 0.208,
            (0, 0, 50, 50, 0): 0.312,
            (0, 0, 30, 30, 40): 0.12,
            (0, 30, 30, 40, 0): 0.04,
        }
        self.assertEqual(set(observed), set(expected))
        for allocation, weight in expected.items():
            self.assertAlmostEqual(observed[allocation], weight)
        np.testing.assert_allclose(
            mixture["weights"] @ mixture["allocations"], [0, 1.2, 20.4, 55.2, 23.2]
        )

    def test_concentration_share_endpoints(self):
        one_only = concentration_mixture(self.conditional, 1, all_in_fraction=0)
        first = self.conditional["components"][0]
        np.testing.assert_array_equal(one_only["allocations"], first["allocations"])
        np.testing.assert_array_equal(one_only["weights"], first["weights"])
        no_one = concentration_mixture(self.conditional, 0, all_in_fraction=0)
        observed = dict(zip(map(tuple, no_one["allocations"]), no_one["weights"]))
        self.assertTrue(set(map(tuple, first["allocations"])).isdisjoint(observed))
        for component, mass in zip(
            self.conditional["components"][1:], [13 / 17, 4 / 17]
        ):
            for allocation, weight in zip(
                component["allocations"], component["weights"]
            ):
                self.assertAlmostEqual(observed[tuple(allocation)], mass * weight)

    def test_share_changes_preserve_each_joint_component(self):
        components = self.conditional["components"]
        snapshots = [
            (component["allocations"].copy(), component["weights"].copy())
            for component in components
        ]
        for share in [0.05, 0.35, 0.70]:
            mixture = concentration_mixture(self.conditional, share, all_in_fraction=0)
            observed = dict(zip(map(tuple, mixture["allocations"]), mixture["weights"]))
            masses = [share, (1 - share) * 13 / 17, (1 - share) * 4 / 17]
            for component, mass, (saved_rows, saved_weights) in zip(
                components, masses, snapshots
            ):
                recovered = [observed[tuple(row)] / mass for row in saved_rows]
                np.testing.assert_allclose(recovered, saved_weights)
                np.testing.assert_array_equal(component["allocations"], saved_rows)
                np.testing.assert_array_equal(component["weights"], saved_weights)

    def test_all_in_fraction_preserves_outer_cohort_shares(self):
        for fraction in [0, 0.25, 1]:
            mixture = concentration_mixture(
                self.conditional, one_castle_share=0.4, all_in_fraction=fraction
            )
            observed = dict(zip(map(tuple, mixture["allocations"]), mixture["weights"]))
            self.assertAlmostEqual(observed.get((0, 0, 100, 0, 0), 0), 0.4 * fraction)
            masses = [0.4 * (1 - fraction), 0.6 * 13 / 17, 0.6 * 4 / 17]
            for component, mass in zip(self.conditional["components"], masses):
                for allocation, weight in zip(
                    component["allocations"], component["weights"]
                ):
                    self.assertAlmostEqual(
                        observed.get(tuple(allocation), 0), mass * weight
                    )
            np.testing.assert_array_equal(
                mixture["allocations"].sum(axis=1),
                np.full(len(mixture["allocations"]), 100),
            )

    def test_generated_conditional_populations_are_legal_and_reproducible(self):
        for profile in ["balanced", "fifth_crowded", "fifth_avoided"]:
            for small_bids in ["low", "high"]:
                generated = concentrated_by_count(
                    24, seed=417, profile=profile, small_bids=small_bids
                )
                self.assertEqual(len(generated["components"]), 3)
                for component in generated["components"]:
                    rows, weights = component["allocations"], component["weights"]
                    self.assertEqual(rows.shape[1], 5)
                    self.assertTrue(np.all(rows >= 0))
                    np.testing.assert_array_equal(rows, rows.astype(int))
                    np.testing.assert_array_equal(
                        rows.sum(axis=1), np.full(len(rows), 100)
                    )
                    self.assertTrue(np.all(weights > 0))
                    self.assertAlmostEqual(weights.sum(), 1)
                atoms = generated["one_castle_all_in"]
                observed = dict(zip(map(tuple, atoms["allocations"]), atoms["weights"]))
                fifth_weight = {
                    "balanced": 1,
                    "fifth_crowded": 3,
                    "fifth_avoided": 0.25,
                }[profile]
                denominator = 3 + 4 * fifth_weight
                expected = {
                    (0, 0, 100, 0, 0): 1 / denominator,
                    (0, 0, 0, 100, 0): 2 / denominator,
                    (0, 0, 0, 0, 100): 4 * fifth_weight / denominator,
                }
                self.assertEqual(set(observed), set(expected))
                for allocation, weight in expected.items():
                    self.assertAlmostEqual(observed[allocation], weight)
        first = concentrated_by_count(24, seed=89)
        repeated = concentrated_by_count(24, seed=89)
        for left, right in zip(first["components"], repeated["components"]):
            np.testing.assert_array_equal(left["allocations"], right["allocations"])
            np.testing.assert_array_equal(left["weights"], right["weights"])

    def test_fourth_reasoning_level_keeps_first_three_under_common_seed(self):
        candidates = np.array(
            [
                [20, 20, 20, 20, 20],
                [0, 0, 0, 49, 51],
                [0, 1, 36, 0, 63],
                [0, 0, 49, 51, 0],
            ]
        )
        components = {
            name: population([row])
            for name, row in zip(["H", "C", "TA", "TB"], candidates)
        }
        three, diagnostics_three = finite_reasoning(
            components,
            candidates,
            np.random.default_rng(173),
            depth=3,
            screen=16,
            check=32,
        )
        four, diagnostics_four = finite_reasoning(
            components,
            candidates,
            np.random.default_rng(173),
            depth=4,
            screen=16,
            check=32,
        )
        self.assertEqual(len(three), 3)
        self.assertEqual(len(four), 4)
        for earlier, extended in zip(three, four[:3]):
            np.testing.assert_array_equal(
                earlier["allocations"], extended["allocations"]
            )
            np.testing.assert_array_equal(earlier["weights"], extended["weights"])
        self.assertEqual(diagnostics_three, diagnostics_four[: len(diagnostics_three)])
        self.assertTrue(
            all(
                item["level"] == 4
                for item in diagnostics_four[len(diagnostics_three) :]
            )
        )

    def test_first_three_population_support_and_secondary_mass(self):
        anchors = {
            (33, 33, 34, 0, 0),
            (17, 33, 50, 0, 0),
            (15, 30, 55, 0, 0),
            (20, 25, 55, 0, 0),
        }
        for setting, zero_mass, bound in [
            ("zero", 1, 0),
            ("small", 0.5, 3),
            ("shifted", 0.2, 5),
        ]:
            generated = first_three_population(80, seed=37, secondary=setting)
            rows, weights = generated["allocations"], generated["weights"]
            self.assertTrue(anchors.issubset(set(map(tuple, rows))))
            self.assertTrue(np.all(rows[:, :3] > 0))
            self.assertTrue(np.all(rows[:, 3:] >= 0))
            self.assertTrue(np.all(rows[:, 3:] <= bound))
            np.testing.assert_array_equal(rows.sum(axis=1), np.full(len(rows), 100))
            np.testing.assert_array_equal(rows, rows.astype(int))
            no_secondary = np.all(rows[:, 3:] == 0, axis=1)
            self.assertAlmostEqual(weights[no_secondary].sum(), zero_mass)
            self.assertAlmostEqual(weights.sum(), 1)


class Game2FieldTests(unittest.TestCase):
    def test_world_uncertainty_differs_from_pooling_opponent_types(self):
        first = np.array([0, 1, 36, 0, 63])
        second = np.array([0, 0, 49, 51, 0])
        pure_worlds = np.array([[first] * 3, [second] * 3])
        world_scores = evaluate_candidates(
            [first], prepare_triples(pure_worlds), return_samples=True
        )
        np.testing.assert_array_equal(world_scores[0], [3.75, 9])
        weighted_world_score = summarize_scores(world_scores, [0.5, 0.5])[
            "weighted_mean"
        ][0]
        self.assertEqual(weighted_world_score, 6.375)

        anchors = np.array([first, second])
        indices = np.array(list(product(range(2), repeat=3)))
        pooled_score = evaluate_candidates([first], prepare_triples(anchors[indices]))[
            0
        ]
        self.assertEqual(pooled_score, 3.75)

    def test_reasoning_preserves_named_group_masses_in_actual_vectors(self):
        rows = {
            "H": [100, 0, 0, 0, 0],
            "C": [0, 100, 0, 0, 0],
            "Z": [0, 0, 0, 0, 100],
            "F": [0, 0, 100, 0, 0],
            "T": [0, 0, 0, 100, 0],
        }
        components = {name: population([row]) for name, row in rows.items()}
        strategic_row = [1, 2, 3, 4, 90]
        captured = []

        def response(_candidates, opponents, _rng, **_settings):
            captured.append(opponents)
            return population([strategic_row]), {}

        shares = dict(
            zip(["H", "C", "Z", "F", "T", "S"], [0.02, 0.38, 0.10, 0.10, 0.15, 0.25])
        )
        with patch("blotto.game2_field.response_search", side_effect=response):
            levels, _ = _reasoning_levels(
                components,
                np.array([strategic_row]),
                shares,
                np.random.default_rng(32),
                screen=4,
                check=4,
            )
        self.assertEqual(len(captured), 12)
        self.assertEqual(len(levels), 4)
        for index, distribution in enumerate(captured):
            masses = dict(
                zip(map(tuple, distribution["allocations"]), distribution["weights"])
            )
            level, belief = divmod(index, 3)
            self.assertAlmostEqual(masses[tuple(rows["H"])], 0.02)
            self.assertAlmostEqual(masses[tuple(rows["T"])], 0.15)
            self.assertAlmostEqual(masses[tuple(rows["Z"])], [0.05, 0.10, 0.15][belief])
            self.assertAlmostEqual(masses[tuple(rows["F"])], [0.15, 0.10, 0.05][belief])
            response_share = [0.4, 0.6, 0.8][belief] if level else 0
            self.assertAlmostEqual(
                masses[tuple(rows["C"])], 0.63 * (1 - response_share)
            )
            self.assertAlmostEqual(
                masses.get(tuple(strategic_row), 0), 0.63 * response_share
            )

    def test_field_weights_and_structural_counts_include_strategic_players(self):
        strategic_row = [33, 33, 34, 0, 0]
        with patch(
            "blotto.game2_field.response_search",
            return_value=(population([strategic_row]), {}),
        ), redirect_stdout(StringIO()):
            field = build_field([strategic_row], seed=71, samples=20, screen=4, check=4)
        self.assertEqual(len(field["scenarios"]), 90)
        self.assertEqual(len(field["models"]), 10)
        self.assertAlmostEqual(sum(field["weights"].values()), 1)
        families = {item["family"] for item in field["metadata"].values()}
        for family in families:
            mass = sum(
                field["weights"][name]
                for name, item in field["metadata"].items()
                if item["family"] == family
            )
            self.assertAlmostEqual(mass, 0.20)
        for name, distribution in field["scenarios"].items():
            metadata = field["metadata"][name]
            shares = metadata["shares"]
            expected_f = shares["S"]
            expected_z = 0.0
            for group, component in field["models"][metadata["bank"]][
                "components"
            ].items():
                rows, weights = component["allocations"], component["weights"]
                first_three = np.all(rows[:, :3] > 0, axis=1) & np.all(
                    rows[:, 3:] == 0, axis=1
                )
                expected_f += shares[group] * weights[first_three].sum()
                expected_z += shares[group] * weights[rows[:, 4] == 100].sum()
            self.assertAlmostEqual(
                metadata["actual_first_three_only_positive_probability"], expected_f
            )
            self.assertAlmostEqual(
                metadata["actual_exact_100_fifth_probability"], expected_z
            )
            self.assertGreater(
                metadata["actual_first_three_only_positive_probability"], shares["F"]
            )
            self.assertAlmostEqual(distribution["weights"].sum(), 1)


if __name__ == "__main__":
    unittest.main()
