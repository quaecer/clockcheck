# SPDX-License-Identifier: Apache-2.0
"""Exercise exact bounds, disjunctions and contradictions."""

import unittest
from fractions import Fraction as F

from quaecer.clockcheck import Bound, clock_bounds, minimal_conflict, solve
from quaecer.clockcheck.solver import Problem


class SolverTest(unittest.TestCase):
    def assert_compatible(self, problem: Problem) -> None:
        result = solve(problem)
        assert result is not None
        self.assertTrue(all(any(bound.holds(result) for bound in clause) for clause in problem))

    def test_empty_and_false_formulas(self) -> None:
        self.assertEqual(solve(()), {})
        self.assertIsNone(solve(((),)))
        self.assertEqual(minimal_conflict(((),)), (0,))

    def test_positive_slack_at_arbitrary_precision(self) -> None:
        small = F(1, 10**60)
        self.assert_compatible(
            (
                (Bound(None, "x", F(0), True),),
                (Bound("x", None, small, True),),
                (Bound("y", "x", F(0), True),),
                (Bound(None, "y", F(0), True),),
            )
        )

    def test_strict_zero_cycle(self) -> None:
        weak = ((Bound("a", "b", F(0)),), (Bound("b", "a", F(0)),))
        self.assert_compatible(weak)
        strict = (*weak, (Bound("b", "a", F(0), True),))
        self.assertIsNone(solve(strict))
        self.assertEqual(minimal_conflict(strict), (0, 2))

    def test_disjunction_and_inclusion_minimal_conflict(self) -> None:
        problem = (
            (Bound("x", None, F(-1), True), Bound(None, "x", F(-1))),
            (Bound("x", None, F(0)),),
            (Bound(None, "x", F(0)),),
            (Bound("z", None, F(5)),),
        )
        self.assertIsNone(solve(problem))
        self.assertEqual(minimal_conflict(problem), (0, 1, 2))
        self.assert_compatible(problem[:2])
        self.assert_compatible((problem[0], problem[2]))

    def test_shared_clock_chain(self) -> None:
        bounds = clock_bounds({"a": F(0), "b": F(1), "c": F(2)}, F(2))
        readings = ((Bound(None, "a", F(-1)),), (Bound("c", None, F(0)),))
        self.assertIsNone(solve((*bounds, *readings)))
        self.assert_compatible((*bounds, readings[0]))
        self.assert_compatible((*bounds, readings[1]))

    def test_same_reading_has_one_value(self) -> None:
        bounds = clock_bounds({"a": F(0), "b": F(0)}, F(2))
        observations = ((Bound("a", None, F(-1)),), (Bound(None, "b", F(-1)),))
        self.assertIsNone(solve((*bounds, *observations)))
        with self.assertRaises(ValueError):
            clock_bounds({}, F(-1))
