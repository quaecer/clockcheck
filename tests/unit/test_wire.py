# SPDX-License-Identifier: Apache-2.0
"""Check the rational wire grammar."""

import unittest
from fractions import Fraction

from quaecer.clockcheck import Bound
from quaecer.clockcheck.cli import parse_problem


class WireTest(unittest.TestCase):
    def test_exact_rational(self) -> None:
        raw = (
            b'{"format":"clock-problem@1","clauses":'
            b'[[{"left":"e","right":null,"limit":"1/3","strict":true}]]}'
        )
        self.assertEqual(parse_problem(raw), ((Bound("e", None, Fraction(1, 3), True),),))
        for bad in (b'""', b'"1e3"', b'"1/0"', b'"01"', b"1.0"):
            with self.assertRaises(ValueError):
                parse_problem(raw.replace(b'"1/3"', bad))

    def test_duplicate_members(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_problem(b'{"format":"clock-problem@1","clauses":[],"clauses":[]}')
