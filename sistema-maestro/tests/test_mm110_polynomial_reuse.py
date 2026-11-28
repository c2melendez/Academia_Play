"""Generic algebra regression fixtures, not an approved M1 activity bank."""
import sys
import unittest
from pathlib import Path
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_oracle import compare, normalize

class PolynomialReuseTests(unittest.TestCase):
    def test_reduced_degree(self):
        for expression, expected in [
            ("4x^3-4x^3+2x-1",{1:Fraction(2),0:Fraction(-1)}),
            ("x^2-x^2",{}),
            ("3x-3x+7",{0:Fraction(7)}),
            ("(1/3)x^4+(2/3)x^4",{4:Fraction(1)}),
        ]:
            with self.subTest(expression=expression):
                self.assertEqual(expected,normalize(expression))

    def test_operations_and_identities(self):
        for expression,expected in [
            ("(3x^2-2x+1)-(x^2+4x-5)","2x^2-6x+6"),
            ("(2x-3)(x+4)","2x^2+5x-12"),
            ("(x-5)^2","x^2-10x+25"),
            ("(2x-1)^3","8x^3-12x^2+6x-1"),
            ("(3x+2)(3x-2)","9x^2-4"),
            ("(2x-3)(x+2)","2x^2+x-6"),
            ("(x+2)(x^2-2x+4)","x^3+8"),
            ("(x-3)(x^2+3x+9)","x^3-27"),
            ("(x-1)(x+1)+2","x^2+1"),
            ("(x^2+1)(2x-3)+x","2x^3-3x^2+3x-3"),
        ]:
            with self.subTest(expression=expression):
                self.assertEqual("VERIFIED",compare(expression,expected).status)

    def test_negative_identities_and_domain(self):
        for a,b in [
            ("(x+2)^2","x^2+4"),
            ("(2x-3)(x+4)","2x^2-12"),
            ("(x-3)(x^2+3x+9)","x^3+27"),
            ("(x^2+1)(2x-3)+x","2x^3-3x^2+2x-3"),
            ("1/x","0"),
            ("x^-2","0"),
        ]:
            with self.subTest(a=a):
                self.assertEqual("REJECTED",compare(a,b).status)
        self.assertEqual("INCONCLUSIVE",compare("x^17","0").status)
