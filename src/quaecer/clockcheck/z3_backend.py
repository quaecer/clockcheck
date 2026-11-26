# SPDX-License-Identifier: Apache-2.0
"""Optional exact real-difference solver."""

from fractions import Fraction
from typing import Any

from .solver import Assignment, Problem, Variable, _variables


def solve_z3(problem: Problem) -> Assignment | None:
    """Return an exact assignment using the optional real-difference backend."""
    import z3

    names = tuple(name for name in _variables(problem) if name is not None)
    symbols = {name: z3.Real(f"t_{i}") for i, name in enumerate(names)}
    variables: dict[Variable, Any] = dict(symbols.items())
    variables[None] = z3.RealVal(0)
    solver = z3.SolverFor("QF_RDL")
    for clause in problem:
        alternatives = []
        for bound in clause:
            difference = variables[bound.left] - variables[bound.right]
            limit = z3.RealVal(str(bound.limit))
            alternatives.append(difference < limit if bound.strict else difference <= limit)
        solver.add(z3.Or(*alternatives))

    status = solver.check()
    if status == z3.unsat:
        return None
    if status != z3.sat:
        raise RuntimeError(f"backend did not decide: {solver.reason_unknown()}")
    model = solver.model()
    assignment = {
        name: Fraction(model.eval(symbol, model_completion=True).as_fraction())
        for name, symbol in symbols.items()
    }
    if not all(any(bound.holds(assignment) for bound in clause) for clause in problem):
        raise RuntimeError("backend assignment does not satisfy the input")
    return assignment
