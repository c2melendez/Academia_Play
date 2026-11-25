import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import mm110_f01_oracle as o

class F01OracleTests(unittest.TestCase):
    def test_exact_identities(self):
        for a,b in [
            ('7(2x-3)','14x-21'),('-3(2x-5)','-6x+15'),
            ('(1/2)(4x-6)','2x-3'),('(x+2)(x-2)','x^2-4'),
            ('x-x','0'),('0','0'),('-x^2','-(x*x)'),
            ('(x+1)^3','x^3+3x^2+3x+1'),
            ('2/3*x+1/3*x','x'),('8(x+6)','8x+48'),
            ('x²','x*x'),('(-x)^2','x^2')
        ]:
            with self.subTest(a=a,b=b):
                self.assertEqual(o.compare(a,b).status,'VERIFIED')
    def test_false_identities(self):
        for a,b in [('5(x-4)','5x-4'),('x^2','x'),('-3(2x-5)','-6x-15'),('2(x+3)','2x+3')]:
            with self.subTest(a=a,b=b):
                self.assertEqual(o.compare(a,b),o.Verdict('REJECTED','UNEQUAL_COEFFICIENTS'))
    def test_invalid_domain(self):
        for a in ['1/x','0/x','1/(x-x+1)','1/0','x^-1','x^(1/2)','sin(x)','y','2.5','x=1','2 3','(x+1','__import__(x)']:
            with self.subTest(a=a):
                self.assertEqual(o.compare(a,'0'),o.Verdict('REJECTED','INVALID_FORMAT_OR_DOMAIN'))
    def test_limits(self):
        for a in ['x^17','x'*257,'('*30+'x'+')'*30,'9'*100]:
            with self.subTest(a=a):
                self.assertEqual(o.compare(a,'0'),o.Verdict('INCONCLUSIVE','COMPUTATION_LIMIT'))
    def test_injected_failure(self):
        with patch.object(o,'normalize',side_effect=RuntimeError('simulated')):
            self.assertEqual(o.compare('x','x'),o.Verdict('INCONCLUSIVE','INTERNAL_FAILURE'))
    def test_exact_independent_coefficients(self):
        from fractions import Fraction
        self.assertEqual(o.normalize('(2/3)(3x-6)'),{1:Fraction(2),0:Fraction(-4)})
