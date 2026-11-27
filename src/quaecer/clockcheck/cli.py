# SPDX-License-Identifier: Apache-2.0
"""Solve a finite JSON problem using exact rational arithmetic."""

import argparse
import json
import re
import sys
from fractions import Fraction
from typing import Any

from .solver import Bound, Problem, minimal_conflict, solve
from .z3_backend import solve_z3

_RATIONAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?")
_MAX_BYTES = 2 * 1024 * 1024


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = dict(pairs)
    if len(result) != len(pairs):
        raise ValueError("duplicate JSON member")
    return result


def parse_problem(raw: bytes) -> Problem:
    """Read closed clause and bound records from a JSON problem."""
    if len(raw) > _MAX_BYTES:
        raise ValueError("problem is too large")
    document = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
    if (
        not isinstance(document, dict)
        or document.keys() != {"format", "clauses"}
        or document["format"] != "clock-problem@1"
        or not isinstance(document["clauses"], list)
    ):
        raise ValueError("invalid problem document")

    def parse_bound(fields: Any) -> Bound:
        if not isinstance(fields, dict) or fields.keys() != {"left", "right", "limit", "strict"}:
            raise ValueError("invalid bound fields")
        left, right, limit, strict = (fields[key] for key in ("left", "right", "limit", "strict"))
        for symbol in (left, right):
            if symbol is not None and (not isinstance(symbol, str) or not symbol):
                raise ValueError("variables must be nonempty strings or null")
        if not isinstance(limit, str) or not _RATIONAL.fullmatch(limit):
            raise ValueError("limit must be a rational string")
        if not isinstance(strict, bool):
            raise ValueError("strict must be a boolean")
        return Bound(left, right, Fraction(limit), strict)

    result = []
    for clause in document["clauses"]:
        if not isinstance(clause, list):
            raise ValueError("clause must be an array")
        result.append(tuple(parse_bound(fields) for fields in clause))
    return tuple(result)


def main() -> int:
    """Read one problem from standard input and write a status and certificate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=["native", "z3"], default="native")
    args = parser.parse_args()
    solver = solve if args.backend == "native" else solve_z3
    try:
        problem = parse_problem(sys.stdin.buffer.read(_MAX_BYTES + 1))
        assignment = solver(problem)
        if assignment is None:
            result: dict[str, object] = {
                "status": "incompatible",
                "clauses": minimal_conflict(problem, solver=solver),
            }
        else:
            result = {
                "status": "compatible",
                "assignment": {key: str(value) for key, value in assignment.items()},
            }
    except (ValueError, OSError, ImportError, RecursionError, RuntimeError) as error:
        parser.exit(2, f"clockcheck: {error}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
