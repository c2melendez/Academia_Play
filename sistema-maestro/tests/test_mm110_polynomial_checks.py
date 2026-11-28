"""Independent fixtures for generic polynomial checks; no student bank."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import mm110_polynomial_checks as c

class PolynomialChecksTests(unittest.TestCase):
    def test_degree(self):
        cases=[
            ("x^4-x^4+x",1,"VERIFIED"),
            ("x-x",None,"VERIFIED"),
            ("7",0,"VERIFIED"),
            ("0",0,"REJECTED"),
            ("x^2+1",1,"REJECTED"),
            ("x",True,"REJECTED"),
            ("x",-1,"REJECTED"),
            ("1/x",1,"REJECTED"),
            ("x^17",17,"INCONCLUSIVE"),
        ]
        for a,b,status in cases:
            with self.subTest(a=a,b=b):
                self.assertEqual(status,c.verify_degree(a,b).status)

    def test_coefficients(self):
        cases=[
            ("(x+2)^2",1,"4","VERIFIED"),
            ("x^3+1",2,"0","VERIFIED"),
            ("x-x",0,"0","VERIFIED"),
            ("(1/3)x^2+(1/6)x^2",2,"1/2","VERIFIED"),
            ("-x^2",2,"1","REJECTED"),
            ("x",1,"x","REJECTED"),
            ("x",True,"1","REJECTED"),
            ("x",-1,"0","REJECTED"),
            ("x",17,"0","INCONCLUSIVE"),
        ]
        for a,e,b,status in cases:
            with self.subTest(a=a,e=e,b=b):
                self.assertEqual(status,c.verify_coefficient(a,e,b).status)

    def test_division(self):
        cases=[
            ("x^2+1","x-1","x+1","2","VERIFIED","EXACT_DIVISION"),
            ("2x^3-3x^2+3x-3","x^2+1","2x-3","x","VERIFIED","EXACT_DIVISION"),
            ("x^2-4","x-2","x+2","0","VERIFIED","EXACT_DIVISION"),
            ("x+1","x^2+1","0","x+1","VERIFIED","EXACT_DIVISION"),
            ("0","x-1","0","0","VERIFIED","EXACT_DIVISION"),
            ("3x+6","3","x+2","0","VERIFIED","EXACT_DIVISION"),
            ("x^2+1","2x","1/2*x","1","VERIFIED","EXACT_DIVISION"),
            ("x^2+1","x-1","x","x+1","REJECTED","REMAINDER_DEGREE"),
            ("x^2+1","x-1","x+1","1","REJECTED","DIVISION_IDENTITY"),
            ("x","x-x","0","x","REJECTED","INVALID_FORMAT_OR_DOMAIN"),
            ("x","x","1/x","0","REJECTED","INVALID_FORMAT_OR_DOMAIN"),
            ("x^16","x^16","x","0","INCONCLUSIVE","COMPUTATION_LIMIT"),
        ]
        for d,v,q,r,status,reason in cases:
            with self.subTest(d=d,v=v,q=q,r=r):
                result=c.verify_division(d,v,q,r)
                self.assertEqual((status,reason),(result.status,result.reason))

    def test_factor_product(self):
        cases=[
            ("x^2-7x+12",["x-3","x-4"],"VERIFIED","EXACT_FACTOR_PRODUCT"),
            ("2x^2+x-6",["x+2","2x-3"],"VERIFIED","EXACT_FACTOR_PRODUCT"),
            ("x^3+8",["x+2","x^2-2x+4"],"VERIFIED","EXACT_FACTOR_PRODUCT"),
            ("2x^2-8",["2","x-2","x+2"],"VERIFIED","EXACT_FACTOR_PRODUCT"),
            ("x^2-4",["x^2-4","1"],"REJECTED","TRIVIAL_FACTORIZATION"),
            ("x^2-4",["x+2","x+2"],"REJECTED","FACTOR_IDENTITY"),
            ("0",["0","x"],"REJECTED","INVALID_FORMAT_OR_DOMAIN"),
            ("x^16",["x^16","x"],"INCONCLUSIVE","COMPUTATION_LIMIT"),
            ("x^2",["x"]*17,"REJECTED","INVALID_FORMAT_OR_DOMAIN"),
        ]
        for a,f,status,reason in cases:
            with self.subTest(a=a,f=f):
                result=c.verify_factor_product(a,f)
                self.assertEqual((status,reason),(result.status,result.reason))

    def test_internal_failure(self):
        with patch.object(c,"normalize",side_effect=RuntimeError("injected")):
            for result in [c.verify_degree("x",1),c.verify_coefficient("x",1,"1"),
                           c.verify_division("x","x","1","0"),
                           c.verify_factor_product("x^2",["x","x"])]:
                self.assertEqual(("INCONCLUSIVE","INTERNAL_FAILURE"),(result.status,result.reason))
