# SPDX-License-Identifier: Apache-2.0
"""Compare independently implemented exact backends on seeded formulas."""

import random
from fractions import Fraction

import pytest

from quaecer.clockcheck import Bound, solve
from quaecer.clockcheck.z3_backend import solve_z3


def test_seeded_rational_formulas() -> None:
    pytest.importorskip("z3")
    rng = random.Random(44219)
    names = ("a", "b", "c", None)
    status = set()
    for _ in range(600):
        problem = tuple(
            tuple(
                Bound(
                    rng.choice(names),
                    rng.choice(names),
                    Fraction(rng.randrange(-3, 4), rng.randrange(1, 5)),
                    bool(rng.randrange(2)),
                )
                for _ in range(rng.randrange(1, 4))
            )
            for _ in range(rng.randrange(1, 12))
        )
        native, optional = solve(problem), solve_z3(problem)
        assert (native is None) == (optional is None), problem
        status.add(native is None)
        if native is not None:
            assert all(any(bound.holds(native) for bound in clause) for clause in problem)
    assert status == {False, True}
