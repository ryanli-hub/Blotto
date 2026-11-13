"""Independent checks for Game 1 scoring, optimization, and certificates."""

import unittest

import numpy as np
from scipy.optimize import linprog

from blotto.game import (
    best_response,
    expected_rewards,
    marginals,
    payoff,
    payoff_matrix,
)
from blotto.dynamics import (
    double_oracle,
    finite_reasoning_population,
    near_best_responses,
    pure_response_path,
)
from blotto.opponents import (
    considered_population,
    concentrated_population,
    focused_245_population,
    heuristic_population,
    independent_soldiers,
    mixture,
    uniform_allocations,
)
from blotto.robust import allocation_blocks, minimax_regret


def all_allocations(budget, castles):
    """Enumerate a tiny game's legal allocations, only for independent checks."""
    if castles == 1:
        yield (budget,)
        return
    for first in range(budget + 1):
        for rest in all_allocations(budget - first, castles - 1):
            yield (first,) + rest


def direct_score(own, opponent, values):
    """Read the scoring rule literally, without the production implementation."""
    result = 0.0
    for own_count, other_count, value in zip(own, opponent, values):
        if own_count > other_count:
            result += value
        elif own_count == other_count:
            result += value / 2
    return result


class ScoringTests(unittest.TestCase):
    def test_ties_and_constant_sum(self):
        allocations = np.array(
            [[0, 0, 0, 0, 100], [1, 1, 1, 1, 96], [20, 20, 20, 20, 20]]
        )
        values = np.arange(1, 6)
        scores = payoff_matrix(allocations, allocations, values)
        np.testing.assert_allclose(scores + scores.T, 15)
        np.testing.assert_allclose(np.diag(scores), 7.5)
        self.assertEqual(payoff(allocations[1], allocations[0]), 10)
        for i, own in enumerate(allocations):
            for j, opponent in enumerate(allocations):
                self.assertEqual(scores[i, j], direct_score(own, opponent, values))

    def test_correlated_opponents_need_only_marginals(self):
        # Coordinates are strongly dependent: each row still spends exactly 7.
        opponents = np.array([[7, 0, 0], [0, 7, 0], [0, 0, 7], [2, 3, 2]])
        weights = np.array([0.1, 0.2, 0.3, 0.4])
        values = np.array([1, 2, 4])
        distribution = marginals(opponents, weights, budget=7)
        self.assertEqual(distribution.shape, (3, 8))
        np.testing.assert_allclose(distribution.sum(axis=1), 1)
        rewards = expected_rewards(distribution, values)
        for own in all_allocations(7, 3):
            joint_score = sum(
                weight * direct_score(own, other, values)
                for weight, other in zip(weights, opponents)
            )
            marginal_score = sum(rewards[i, count] for i, count in enumerate(own))
            self.assertAlmostEqual(joint_score, marginal_score)


class OptimizationTests(unittest.TestCase):
    def test_dp_matches_exhaustive_search(self):
        rng = np.random.default_rng(20261103)
        for budget, values in [(0, [1, 2, 3]), (5, [1, 1]), (7, [1, 2, 4])]:
            values = np.asarray(values)
            allocations = np.array(list(all_allocations(budget, len(values))))
            for trial in range(6):
                weights = rng.dirichlet(np.ones(len(allocations)))
                if trial == 0:
                    weights[:] = 0
                    weights[-1] = 1
                distribution = marginals(allocations, weights, budget=budget)
                own, score = best_response(distribution, values=values, budget=budget)
                exhaustive_scores = [
                    sum(
                        weight * direct_score(candidate, other, values)
                        for weight, other in zip(weights, allocations)
                    )
                    for candidate in allocations
                ]
                self.assertEqual(sum(own), budget)
                self.assertTrue(np.all(np.asarray(own) >= 0))
                self.assertTrue(np.all(np.asarray(own) == np.asarray(own, dtype=int)))
                self.assertAlmostEqual(score, max(exhaustive_scores), places=11)
                direct_own_score = sum(
                    weight * direct_score(own, other, values)
                    for weight, other in zip(weights, allocations)
                )
                self.assertAlmostEqual(score, direct_own_score, places=11)

    def test_double_oracle_against_full_toy_game(self):
        budget = 6
        values = np.array([1, 2, 4])
        actions = np.array(list(all_allocations(budget, len(values))))
        full_payoffs = np.array(
            [[direct_score(x, y, values) for y in actions] for x in actions]
        )
        size = len(actions)
        # Maximize a guaranteed score against every enumerated opponent action.
        objective = np.r_[np.zeros(size), -1]
        inequalities = np.column_stack((-full_payoffs.T, np.ones(size)))
        normalization = np.r_[np.ones(size), 0][None, :]
        solution = linprog(
            objective,
            A_ub=inequalities,
            b_ub=np.zeros(size),
            A_eq=normalization,
            b_eq=[1],
            bounds=[(0, None)] * size + [(None, None)],
            method="highs",
        )
        self.assertTrue(solution.success, solution.message)
        result = double_oracle(
            initial_allocations=[[6, 0, 0], [0, 6, 0], [0, 0, 6]],
            values=values,
            budget=budget,
            tolerance=1e-9,
            max_iterations=200,
        )
        self.assertTrue(result["converged"])
        support = np.asarray(result["allocations"])
        weights = np.asarray(result["weights"])
        np.testing.assert_allclose(weights.sum(), 1)
        self.assertTrue(np.all(weights >= -1e-12))
        scores_against_mixture = np.array(
            [
                sum(w * direct_score(x, y, values) for w, y in zip(weights, support))
                for x in actions
            ]
        )
        guaranteed_score = min(
            sum(w * direct_score(x, y, values) for w, x in zip(weights, support))
            for y in actions
        )
        value = values.sum() / 2
        self.assertAlmostEqual(solution.x[-1], value, places=8)
        self.assertAlmostEqual(
            result["best_response_score"], scores_against_mixture.max()
        )
        self.assertAlmostEqual(
            result["exploitability"], scores_against_mixture.max() - value
        )
        self.assertAlmostEqual(result["worst_case_score"], guaranteed_score)
        self.assertGreaterEqual(guaranteed_score, solution.x[-1] - 1e-8)

    def test_every_pure_strategy_has_a_profitable_counter(self):
        rng = np.random.default_rng(20261103)
        allocations = list(rng.multinomial(100, np.full(5, 0.2), size=50))
        allocations.extend(np.eye(5, dtype=int) * 100)
        for opponent in allocations:
            abandoned = np.argmax(opponent)
            response = np.asarray(opponent).copy() + 1
            response[abandoned] -= 5
            self.assertEqual(response.sum(), 100)
            self.assertTrue(np.all(response >= 0))
            self.assertGreaterEqual(
                direct_score(response, opponent, np.arange(1, 6)), 10
            )

    def test_pure_response_path_closes_a_valid_cycle(self):
        result = pure_response_path([0, 0, 0, 0, 100], max_steps=10000)
        allocations = result["allocations"]
        self.assertIsNotNone(result["cycle_start"])
        self.assertGreaterEqual(result["cycle_length"], 3)
        successors = allocations[1:] + [allocations[result["cycle_start"]]]
        for own, response in zip(allocations, successors):
            self.assertEqual(sum(own), 100)
            self.assertEqual(sum(response), 100)
            _, optimum = best_response(marginals([own]))
            self.assertAlmostEqual(payoff(response, own), optimum)

    def test_marginals_reject_invalid_allocations(self):
        for allocation in [[0, 0, 0, 0, 99], [-1, 1, 0, 0, 100], [0.5, 0.5, 0, 0, 99]]:
            with self.subTest(allocation=allocation):
                with self.assertRaises(ValueError):
                    marginals([allocation])

    def test_background_equilibrium_against_full_toy_game(self):
        budget = 6
        values = np.array([1, 2, 4])
        actions = np.array(list(all_allocations(budget, len(values))))
        background_actions = np.array([[0, 6, 0], [2, 2, 2]])
        background_weights = np.array([0.4, 0.6])
        background = marginals(background_actions, background_weights, budget)
        direct_payoffs = np.array(
            [[direct_score(x, y, values) for y in actions] for x in actions]
        )
        fixed_scores = np.array(
            [
                sum(
                    w * direct_score(x, y, values)
                    for w, y in zip(background_weights, background_actions)
                )
                for x in actions
            ]
        )
        baseline = values.sum() / 2
        action_indices = {tuple(x): i for i, x in enumerate(actions)}
        for fraction in [0.35, 0.8, 1.0]:
            with self.subTest(background_weight=fraction):
                result = double_oracle(
                    values=values,
                    budget=budget,
                    tolerance=1e-9,
                    max_iterations=200,
                    background=background,
                    background_weight=fraction,
                )
                self.assertTrue(result["converged"])
                weights = np.zeros(len(actions))
                for action, weight in zip(result["allocations"], result["weights"]):
                    weights[action_indices[tuple(action)]] = weight
                population_scores = (1 - fraction) * (
                    direct_payoffs @ weights
                ) + fraction * fixed_scores
                current_score = weights @ population_scores
                deviation_gap = population_scores.max() - current_score
                transformed = (1 - fraction) * (direct_payoffs - baseline)
                transformed += fraction * (
                    fixed_scores[:, None] - fixed_scores[None, :]
                )
                np.testing.assert_allclose(
                    transformed @ weights, population_scores - current_score, atol=1e-12
                )
                self.assertAlmostEqual(
                    result["best_response_score"], population_scores.max()
                )
                self.assertAlmostEqual(result["population_score"], current_score)
                self.assertAlmostEqual(
                    result["population_exploitability"], deviation_gap
                )
                self.assertLessEqual(deviation_gap, 1e-8)
                smart_scores = direct_payoffs @ weights
                self.assertAlmostEqual(
                    result["exploitability"], smart_scores.max() - baseline
                )
                self.assertAlmostEqual(
                    result["worst_case_score"], (weights @ direct_payoffs).min()
                )


class PopulationTests(unittest.TestCase):
    def test_focused_245_profiles_preserve_bounds_and_budget(self):
        bounds = {
            "local": [(1, 3), (12, 19), (1, 3), (34, 40), (38, 51)],
            "broad": [(0, 4), (10, 22), (0, 4), (30, 43), (35, 55)],
            "shifted": [(1, 4), (16, 22), (1, 4), (38, 43), (32, 48)],
            "overbid": [(2, 5), (12, 21), (2, 5), (34, 42), (33, 52)],
        }
        anchors = [(2, 16, 1, 37, 44), (1, 14, 1, 37, 47)]
        for profile, intervals in bounds.items():
            with self.subTest(profile=profile):
                result = focused_245_population(profile)
                rows, weights = result["allocations"], result["weights"]
                self.assertTrue(np.issubdtype(rows.dtype, np.integer))
                np.testing.assert_array_equal(rows.sum(axis=1), 100)
                self.assertEqual(len(rows), len(np.unique(rows, axis=0)))
                for castle, (lower, upper) in enumerate(intervals):
                    self.assertTrue(np.all(rows[:, castle] >= lower))
                    self.assertTrue(np.all(rows[:, castle] <= upper))
                self.assertTrue(np.all(weights > 0))
                self.assertAlmostEqual(weights.sum(), 1)
                np.testing.assert_allclose(result["marginals"].sum(axis=1), 1)
                if profile != "shifted":
                    np.testing.assert_allclose(weights, 1 / len(rows))
                if profile in ["local", "broad"]:
                    support = set(map(tuple, rows))
                    self.assertTrue(all(anchor in support for anchor in anchors))

    def test_focused_245_shifted_weight_ratios(self):
        result = focused_245_population("shifted")
        weights = dict(zip(map(tuple, result["allocations"]), result["weights"]))
        center = weights[(1, 18, 1, 40, 40)]
        self.assertAlmostEqual(weights[(1, 20, 1, 40, 38)] / center, np.exp(-0.5))
        self.assertAlmostEqual(
            weights[(1, 18, 1, 41, 39)] / center, np.exp(-0.5 / 1.5**2)
        )
        # Low bids have equal weight when the main-castle bids agree.
        self.assertAlmostEqual(weights[(3, 18, 2, 40, 37)], center)

    def test_focused_245_weighted_matchups_agree_with_marginals(self):
        candidates = [
            [8, 9, 10, 11, 62],
            [2, 16, 1, 37, 44],
            [1, 14, 1, 37, 47],
            [12, 0, 2, 38, 48],
            [2, 18, 2, 39, 39],
        ]
        values = np.arange(1, 6)
        for profile in ["local", "broad", "shifted", "overbid"]:
            result = focused_245_population(profile)
            rewards = expected_rewards(result["marginals"])
            for candidate in candidates:
                direct = sum(
                    weight * direct_score(candidate, opponent, values)
                    for opponent, weight in zip(
                        result["allocations"], result["weights"]
                    )
                )
                marginal_score = sum(
                    rewards[i, amount] for i, amount in enumerate(candidate)
                )
                self.assertAlmostEqual(direct, marginal_score)

    def test_uniform_marginals_match_enumeration(self):
        for budget, castles in [(0, 2), (4, 3), (5, 5)]:
            actions = list(all_allocations(budget, castles))
            exact = np.zeros((castles, budget + 1))
            for action in actions:
                for castle, amount in enumerate(action):
                    exact[castle, amount] += 1 / len(actions)
            np.testing.assert_allclose(uniform_allocations(budget, castles), exact)

    def test_independent_soldiers_preserve_expected_budget(self):
        for budget, castles in [(0, 3), (7, 3), (100, 5)]:
            distribution = independent_soldiers(budget, castles)
            np.testing.assert_allclose(distribution.sum(axis=1), 1)
            expected_counts = distribution @ np.arange(budget + 1)
            np.testing.assert_allclose(expected_counts, budget / castles)
            self.assertAlmostEqual(expected_counts.sum(), budget)

    def test_generated_populations_and_mixture_preserve_budget(self):
        heuristics = heuristic_population(samples=80, seed=42)
        concentrated = concentrated_population(samples=80, seed=43)
        populations = [
            heuristics,
            concentrated,
            mixture([heuristics, concentrated], [1, 3]),
        ]
        for distribution in populations:
            self.assertEqual(distribution.shape, (5, 101))
            self.assertTrue(np.all(distribution >= 0))
            np.testing.assert_allclose(distribution.sum(axis=1), 1)
            self.assertAlmostEqual((distribution @ np.arange(101)).sum(), 100)
        np.testing.assert_allclose(
            populations[-1], 0.25 * heuristics + 0.75 * concentrated
        )
        np.testing.assert_array_equal(
            heuristics, heuristic_population(samples=80, seed=42)
        )
        np.testing.assert_array_equal(
            concentrated, concentrated_population(samples=80, seed=43)
        )

    def test_considered_population_is_legal_and_reproducible(self):
        for profile in ["base", "overbid", "avoid_high"]:
            with self.subTest(profile=profile):
                result = considered_population(samples=160, seed=43, profile=profile)
                repeated = considered_population(samples=160, seed=43, profile=profile)
                allocations = result["allocations"]
                self.assertEqual(allocations.shape, (160, 5))
                self.assertTrue(np.issubdtype(allocations.dtype, np.integer))
                self.assertTrue(np.all(allocations >= 0))
                np.testing.assert_array_equal(allocations.sum(axis=1), 100)
                np.testing.assert_array_equal(allocations, repeated["allocations"])
                np.testing.assert_allclose(result["marginals"].sum(axis=1), 1)
                self.assertAlmostEqual(
                    (result["marginals"] @ np.arange(101)).sum(), 100
                )
                # Recover the empirical histogram directly from the saved rows.
                for castle in range(5):
                    histogram = np.bincount(allocations[:, castle], minlength=101) / 160
                    np.testing.assert_allclose(result["marginals"][castle], histogram)

    def test_considered_secondary_castles_keep_the_requested_small_bids(self):
        for small_bid in [1, 2, 3]:
            probabilities = [0] * small_bid + [1]
            result = considered_population(
                samples=80,
                seed=44,
                overrides={
                    "active_count_probabilities": [1, 0, 0],
                    "small_bid_probabilities": probabilities,
                    "noise_sigma": 0,
                },
            )
            allocations = result["allocations"]
            # Exactly two castles receive the main budget; three keep the small bid.
            np.testing.assert_array_equal((allocations == small_bid).sum(axis=1), 3)
            self.assertTrue(np.all(allocations > 0))
            np.testing.assert_array_equal(allocations.sum(axis=1), 100)


class FiniteReasoningTests(unittest.TestCase):
    def test_near_best_responses_respect_the_total_score_slack(self):
        budget = 6
        values = np.array([1, 2, 4])
        actions = np.array(list(all_allocations(budget, len(values))))
        rng = np.random.default_rng(45)
        direct_payoffs = np.array(
            [[direct_score(x, y, values) for y in actions] for x in actions]
        )
        for trial in range(3):
            weights = rng.dirichlet(np.ones(len(actions)))
            distribution = marginals(actions, weights, budget)
            optimum = (direct_payoffs @ weights).max()
            for slack in [0, 0.13, 0.7]:
                with self.subTest(trial=trial, slack=slack):
                    samples = near_best_responses(
                        distribution,
                        count=96,
                        slack=slack,
                        seed=46,
                        values=values,
                        budget=budget,
                    )
                    self.assertEqual(samples.shape, (96, len(values)))
                    self.assertTrue(np.issubdtype(samples.dtype, np.integer))
                    self.assertTrue(np.all(samples >= 0))
                    np.testing.assert_array_equal(samples.sum(axis=1), budget)
                    for own in samples:
                        score = sum(
                            weight * direct_score(own, opponent, values)
                            for weight, opponent in zip(weights, actions)
                        )
                        self.assertGreaterEqual(score, optimum - slack - 1e-12)

    def test_zero_slack_samples_multiple_optimal_allocations(self):
        # Against [1, 1, 1], [2, 1, 0] permutations and [1, 1, 1] score 1.5.
        budget = 3
        values = np.ones(3)
        opponent = [1, 1, 1]
        distribution = marginals([opponent], budget=budget)
        options = dict(count=80, slack=0, seed=47, values=values, budget=budget)
        samples = near_best_responses(distribution, **options)
        np.testing.assert_array_equal(
            samples, near_best_responses(distribution, **options)
        )
        optimum = max(
            direct_score(x, opponent, values) for x in all_allocations(budget, 3)
        )
        self.assertGreater(len(set(map(tuple, samples))), 1)
        for sample in samples:
            self.assertEqual(direct_score(sample, opponent, values), optimum)

    def test_finite_reasoning_depths_preserve_normalization_and_budget(self):
        budget = 6
        values = np.array([1, 2, 4])
        backgrounds = [
            marginals([[2, 2, 2], [0, 3, 3]], budget=budget),
            marginals([[1, 0, 5], [0, 4, 2]], budget=budget),
        ]
        for depth in [1, 2, 3]:
            options = dict(
                samples_per_belief=12,
                slack=0.15,
                seed=48,
                depth=depth,
                values=values,
                budget=budget,
            )
            result = finite_reasoning_population(backgrounds, **options)
            self.assertEqual(len(result["depth_marginals"]), depth)
            self.assertEqual(len(result["allocations_by_depth"]), depth)
            for allocations, distribution in zip(
                result["allocations_by_depth"], result["depth_marginals"]
            ):
                self.assertEqual(allocations.shape, (24, 3))
                self.assertTrue(np.issubdtype(allocations.dtype, np.integer))
                self.assertTrue(np.all(allocations >= 0))
                np.testing.assert_array_equal(allocations.sum(axis=1), budget)
                np.testing.assert_allclose(distribution.sum(axis=1), 1)
                self.assertAlmostEqual(
                    (distribution @ np.arange(budget + 1)).sum(), budget
                )
                for castle in range(3):
                    empirical = np.bincount(
                        allocations[:, castle], minlength=budget + 1
                    ) / len(allocations)
                    np.testing.assert_allclose(distribution[castle], empirical)
            np.testing.assert_allclose(
                result["marginals"], np.mean(result["depth_marginals"], axis=0)
            )
            np.testing.assert_array_equal(
                result["allocations"],
                finite_reasoning_population(backgrounds, **options)["allocations"],
            )

    def test_finite_levels_respond_to_the_full_lower_level_population(self):
        budget = 6
        values = np.array([1, 2, 4])
        background_actions = [
            np.array([[2, 2, 2], [0, 3, 3]]),
            np.array([[1, 0, 5], [0, 4, 2]]),
        ]
        backgrounds = [marginals(rows, budget=budget) for rows in background_actions]
        result = finite_reasoning_population(
            backgrounds,
            samples_per_belief=12,
            slack=0.05,
            seed=49,
            depth=3,
            values=values,
            budget=budget,
        )
        actions = list(all_allocations(budget, len(values)))
        for level, allocations in enumerate(result["allocations_by_depth"]):
            gaps = []
            for belief, background in enumerate(background_actions):
                opponents = background
                weights = np.full(len(background), 1 / len(background))
                if level:
                    previous = np.vstack(result["allocations_by_depth"][:level])
                    share = result["parameters"]["response_shares"][belief]
                    opponents = np.vstack([background, previous])
                    weights = np.r_[
                        (1 - share) * weights,
                        np.full(len(previous), share / len(previous)),
                    ]

                def expected_score(own):
                    return sum(
                        weight * direct_score(own, opponent, values)
                        for weight, opponent in zip(weights, opponents)
                    )

                optimum = max(expected_score(action) for action in actions)
                for own in allocations[12 * belief : 12 * (belief + 1)]:
                    gap = optimum - expected_score(own)
                    self.assertLessEqual(gap, 0.05 + 1e-12)
                    gaps.append(gap)
            self.assertAlmostEqual(
                max(gaps),
                result["diagnostics"]["by_depth"][level]["max_optimality_gap"],
            )


class RobustnessTests(unittest.TestCase):
    def test_allocation_blocks_enumerate_each_action_once(self):
        for budget in [0, 1, 4, 7]:
            actual = np.concatenate(list(allocation_blocks(budget)))
            rows = [tuple(row) for row in actual]
            expected = set(all_allocations(budget, 5))
            self.assertEqual(len(rows), len(set(rows)))
            self.assertEqual(set(rows), expected)

    def test_minimax_regret_against_exhaustive_direct_scores(self):
        budget = 4
        values = np.arange(1, 6)
        actions = np.array(list(all_allocations(budget, 5)))
        populations = {
            "first": (np.array([[4, 0, 0, 0, 0]]), np.array([1.0])),
            "fourth": (np.array([[0, 0, 0, 4, 0]]), np.array([1.0])),
            "spread": (
                np.array([[0, 1, 1, 1, 1], [1, 1, 1, 1, 0]]),
                np.array([0.3, 0.7]),
            ),
        }
        scenarios = {
            name: marginals(opponents, weights, budget)
            for name, (opponents, weights) in populations.items()
        }
        direct_scores = np.array(
            [
                [
                    sum(
                        w * direct_score(x, y, values)
                        for w, y in zip(weights, opponents)
                    )
                    for opponents, weights in populations.values()
                ]
                for x in actions
            ]
        )
        optimal_scores = direct_scores.max(axis=0)
        maximum_regrets = (optimal_scores - direct_scores).max(axis=1)
        result = minimax_regret(scenarios, budget=budget, values=values)
        chosen_index = next(
            i for i, x in enumerate(actions) if list(x) == result["allocation"]
        )
        self.assertEqual(result["scenarios"], list(populations))
        self.assertEqual(result["allocations_examined"], len(actions))
        np.testing.assert_allclose(result["optimal_scores"], optimal_scores)
        np.testing.assert_allclose(result["scores"], direct_scores[chosen_index])
        self.assertAlmostEqual(result["max_regret"], maximum_regrets.min())
        self.assertAlmostEqual(maximum_regrets[chosen_index], maximum_regrets.min())

    def test_pruning_matches_exhaustive_search_from_different_incumbents(self):
        rng = np.random.default_rng(50)
        for budget, values in [
            (0, np.arange(1, 6)),
            (3, np.ones(5)),
            (5, np.arange(1, 6)),
        ]:
            actions = np.array(list(all_allocations(budget, 5)))
            payoffs = np.array(
                [[direct_score(x, y, values) for y in actions] for x in actions]
            )
            weights = rng.dirichlet(np.ones(len(actions)), size=9).T
            scores = payoffs @ weights
            regrets = (scores.max(axis=0) - scores).max(axis=1)
            expected_index = np.flatnonzero(regrets <= regrets.min() + 1e-12)[0]
            scenarios = {
                str(index): marginals(actions, weights[:, index], budget)
                for index in range(weights.shape[1])
            }
            for incumbent in [actions[0], actions[len(actions) // 2], actions[-1]]:
                with self.subTest(budget=budget, incumbent=incumbent.tolist()):
                    result = minimax_regret(
                        scenarios,
                        budget=budget,
                        values=values,
                        initial_allocation=incumbent,
                    )
                    self.assertEqual(
                        result["allocation"], actions[expected_index].tolist()
                    )
                    self.assertEqual(result["allocations_examined"], len(actions))
                    self.assertAlmostEqual(result["max_regret"], regrets.min())
                    np.testing.assert_allclose(result["scores"], scores[expected_index])

    def test_fixed_population_mixture_regret_is_bounded_by_endpoints(self):
        budget = 4
        values = np.arange(1, 6)
        actions = np.array(list(all_allocations(budget, 5)))
        payoffs = np.array(
            [[direct_score(x, y, values) for y in actions] for x in actions]
        )
        rng = np.random.default_rng(51)
        base_weights = rng.dirichlet(np.ones(len(actions)))
        added_weights = rng.dirichlet(np.ones(len(actions)))
        base_scores = payoffs @ base_weights
        added_scores = payoffs @ added_weights
        shares = [0, 0.03, 0.05, 0.10, 0.15]
        scores = np.column_stack(
            [(1 - share) * base_scores + share * added_scores for share in shares]
        )
        regrets = scores.max(axis=0) - scores
        endpoint_bound = regrets[:, [0, -1]].max(axis=1)
        self.assertTrue(np.all(regrets <= endpoint_bound[:, None] + 1e-12))
        scenarios = {
            str(share): marginals(
                actions, (1 - share) * base_weights + share * added_weights, budget
            )
            for share in shares
        }
        endpoints = {str(share): scenarios[str(share)] for share in [0, 0.15]}
        full = minimax_regret(scenarios, budget=budget, values=values)
        reduced = minimax_regret(endpoints, budget=budget, values=values)
        self.assertEqual(full["allocation"], reduced["allocation"])
        self.assertAlmostEqual(full["max_regret"], reduced["max_regret"])

    def test_score_floor_search_matches_exhaustive_feasible_allocations(self):
        budget = 5
        values = np.arange(1, 6)
        actions = np.array(list(all_allocations(budget, 5)))
        payoffs = np.array(
            [[direct_score(x, y, values) for y in actions] for x in actions]
        )
        rng = np.random.default_rng(52)
        weights = rng.dirichlet(np.ones(len(actions)), size=3).T
        scores = payoffs @ weights
        regrets = (scores.max(axis=0) - scores).max(axis=1)
        unrestricted = int(np.argmin(regrets))
        floor_opponents = [actions[unrestricted], actions[0]]
        floor_scores = payoffs[:, [unrestricted, 0]]
        # Require more than the self-match score against the unconstrained winner.
        first_floor = values.sum() / 2 + 0.25
        first_feasible = floor_scores[:, 0] >= first_floor - 1e-12
        second_floor = np.median(floor_scores[first_feasible, 1])
        minima = np.array([first_floor, second_floor])
        feasible = np.flatnonzero(np.all(floor_scores >= minima - 1e-12, axis=1))
        infeasible = np.flatnonzero(np.any(floor_scores < minima - 1e-12, axis=1))
        self.assertGreater(len(feasible), 1)
        self.assertIn(unrestricted, infeasible)
        expected = feasible[np.argmin(regrets[feasible])]
        scenarios = {
            str(index): marginals(actions, weights[:, index], budget)
            for index in range(3)
        }
        floors = {
            str(index): (marginals([floor_opponents[index]], budget=budget), minimum)
            for index, minimum in enumerate(minima)
        }
        result = minimax_regret(
            scenarios,
            budget=budget,
            values=values,
            initial_allocation=actions[feasible[0]],
            score_floors=floors,
        )
        self.assertEqual(result["allocation"], actions[expected].tolist())
        self.assertAlmostEqual(result["max_regret"], regrets[expected])
        self.assertEqual(result["allocations_examined"], len(actions))
        np.testing.assert_allclose(result["scores"], scores[expected, :3])
        np.testing.assert_allclose(result["optimal_scores"], scores[:, :3].max(axis=0))
        with self.assertRaises(ValueError):
            minimax_regret(scenarios, budget=budget, values=values, score_floors=floors)
        with self.assertRaises(ValueError):
            minimax_regret(
                scenarios,
                budget=budget,
                values=values,
                initial_allocation=actions[infeasible[0]],
                score_floors=floors,
            )


if __name__ == "__main__":
    unittest.main()
