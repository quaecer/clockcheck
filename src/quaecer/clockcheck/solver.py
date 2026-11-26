# SPDX-License-Identifier: Apache-2.0
"""Exact satisfiability for finite disjunctions of rational difference bounds."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from itertools import pairwise

type Variable = str | None
type Assignment = dict[str, Fraction]


@dataclass(frozen=True)
class Bound:
    """Constrain left minus right. None names the fixed zero."""

    left: Variable
    right: Variable
    limit: Fraction
    strict: bool = False

    def holds(self, values: Mapping[str, Fraction]) -> bool:
        """Test the original inequality on an exact assignment."""
        left = values[self.left] if self.left is not None else Fraction(0)
        right = values[self.right] if self.right is not None else Fraction(0)
        difference = left - right
        return difference < self.limit if self.strict else difference <= self.limit


type Clause = tuple[Bound, ...]
type Problem = tuple[Clause, ...]


def clock_bounds(readings: Mapping[str, Fraction], accuracy: Fraction) -> Problem:
    """Constrain one shared nondecreasing clock, including equal readings.

    >>> constraints = clock_bounds({"a": Fraction(0), "b": Fraction(2)}, Fraction(1))
    >>> solve(constraints) is not None
    True
    """
    if accuracy < 0:
        raise ValueError("clock accuracy must be nonnegative")

    result: list[Clause] = []
    for name, reading in readings.items():
        result.extend(
            (
                (Bound(name, None, reading + accuracy),),
                (Bound(None, name, accuracy - reading),),
            )
        )
    ordered = sorted(readings, key=lambda name: (readings[name], name))
    for earlier, later in pairwise(ordered):
        result.append((Bound(earlier, later, Fraction(0)),))
        if readings[earlier] == readings[later]:
            result.append((Bound(later, earlier, Fraction(0)),))
    return tuple(result)


def _variables(problem: Problem) -> tuple[Variable, ...]:
    names = {
        name
        for clause in problem
        for bound in clause
        for name in (bound.left, bound.right)
        if name is not None
    }
    return (None, *sorted(names))


def _conjunction(bounds: tuple[Bound, ...], names: tuple[Variable, ...]) -> Assignment | None:
    # Distances a + b*epsilon are compared lexicographically for positive infinitesimal epsilon.
    distance = dict.fromkeys(names, (Fraction(0), 0))
    for _ in names:
        changed = False
        for bound in bounds:
            rational, coefficient = distance[bound.right]
            candidate = rational + bound.limit, coefficient - bound.strict
            if candidate < distance[bound.left]:
                distance[bound.left] = candidate
                changed = True
        if not changed:
            break
    else:
        return None

    # Pick one rational epsilon small enough to preserve all positive rational slack.
    epsilon = Fraction(1)
    for bound in bounds:
        left, left_slope = distance[bound.left]
        right, right_slope = distance[bound.right]
        slack = right + bound.limit - left
        slope = left_slope - right_slope + bound.strict
        if slack > 0 and slope > 0:
            epsilon = min(epsilon, slack / (2 * slope))
    root, root_slope = distance[None]
    return {
        name: distance[name][0] - root + (distance[name][1] - root_slope) * epsilon
        for name in names
        if name is not None
    }


def solve(problem: Problem) -> Assignment | None:
    """Find a satisfying assignment, or return None when the problem is incompatible.

    A problem conjoins clauses. Each clause disjoins its bounds, and an empty
    clause is false. An empty problem has the empty assignment.
    """
    if any(not clause for clause in problem):
        return None

    names = _variables(problem)
    fixed = tuple(clause[0] for clause in problem if len(clause) == 1)
    choices = tuple(clause for clause in problem if len(clause) > 1)
    stack = [(0, fixed)]
    while stack:
        depth, bounds = stack.pop()
        values = _conjunction(bounds, names)
        if values is None:
            continue
        if all(any(bound.holds(values) for bound in clause) for clause in choices[depth:]):
            return values
        for alternative in reversed(choices[depth]):
            stack.append((depth + 1, (*bounds, alternative)))
    return None


def minimal_conflict(
    problem: Problem, *, solver: Callable[[Problem], Assignment | None] = solve
) -> tuple[int, ...] | None:
    """Find an inclusion-minimal set of incompatible clause indices.

    The subset is deterministic in input order. It need not have minimum
    cardinality among all possible conflicting subsets.
    """
    if solver(problem) is not None:
        return None
    remaining = list(range(len(problem)))
    for index in range(len(problem)):
        candidate = [other for other in remaining if other != index]
        if solver(tuple(problem[other] for other in candidate)) is None:
            remaining = candidate
    return tuple(remaining)
