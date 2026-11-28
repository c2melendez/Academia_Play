"""Public/reference algebra contrasts for MM110. No student bank or curricular approval."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_oracle_worker import compare_isolated
from mm110_polynomial_worker import verify_isolated
from mm110_m1_review import get_organizer, check_prediction

class STEMMM110Contrasts(unittest.TestCase):
    def assert_verdict(self, result, expected):
        self.assertEqual(expected,(result.status,result.reason))
    def test_f01_distributivity_and_false_identity(self):
        for left,right,status,reason in [
            ("-3(2x-5)","-6x+15","VERIFIED","EXACT_IDENTITY"),
            ("-3(2x-5)","-6x-15","REJECTED","UNEQUAL_COEFFICIENTS"),
            ("x^2","x","REJECTED","UNEQUAL_COEFFICIENTS"),
        ]:
            with self.subTest(left=left,right=right):
                self.assert_verdict(compare_isolated(left,right),(status,reason))
    def test_f02_degree_after_cancellation(self):
        for expression,degree,status,reason in [
            ("x^4-x^4+x",1,"VERIFIED","EXACT_DEGREE"),
            ("x-x",None,"VERIFIED","EXACT_DEGREE"),
            ("x-x",0,"REJECTED","INCORRECT_DEGREE"),
        ]:
            with self.subTest(expression=expression,degree=degree):
                self.assert_verdict(verify_isolated("degree",expression,degree),(status,reason))
    def test_f03_exact_rational_coefficients(self):
        self.assert_verdict(compare_isolated("(1/3)x^2+(1/6)x^2","(1/2)x^2"),("VERIFIED","EXACT_IDENTITY"))
    def test_f04_expansion(self):
        self.assert_verdict(compare_isolated("(2x-3)(x+4)","2x^2+5x-12"),("VERIFIED","EXACT_IDENTITY"))
    def test_f05_reference_exp01_and_mutant(self):
        # Algebra114 AS-EXP-01; public mathematical identity, not an exam item.
        self.assert_verdict(compare_isolated("(x+1)(x-1)","x^2-1"),("VERIFIED","EXACT_IDENTITY"))
        self.assert_verdict(compare_isolated("(x+1)(x-1)","x^2+1"),("REJECTED","UNEQUAL_COEFFICIENTS"))
    def test_f06_reference_fac01_and_mutant(self):
        # Product identity does not certify irreducibility or completeness.
        self.assert_verdict(verify_isolated("factor_product","x^2-9",["x-3","x+3"]),("VERIFIED","EXACT_FACTOR_PRODUCT"))
        self.assert_verdict(verify_isolated("factor_product","x^2-9",["x+3","x+3"]),("REJECTED","FACTOR_IDENTITY"))
        self.assert_verdict(verify_isolated("factor_product","x^4-1",["x^2-1","x^2+1"]),("VERIFIED","EXACT_FACTOR_PRODUCT"))
    def test_f07_reference_div01_and_domain_boundary(self):
        self.assert_verdict(verify_isolated("division","x^2-4","x-2","x+2","0"),("VERIFIED","EXACT_DIVISION"))
        self.assert_verdict(verify_isolated("division","x^2+1","x-1","x+1","2"),("VERIFIED","EXACT_DIVISION"))
        self.assert_verdict(verify_isolated("division","x^2+1","x-1","x","x+1"),("REJECTED","REMAINDER_DEGREE"))
        self.assert_verdict(compare_isolated("(x^2-4)/(x-2)","x+2"),("REJECTED","INVALID_FORMAT_OR_DOMAIN"))
    def test_computation_limit_is_not_failure_or_pass(self):
        self.assert_verdict(compare_isolated("x^17","0"),("INCONCLUSIVE","COMPUTATION_LIMIT"))

    def test_f04_shared_symbolic_grid_exact_products(self):
        # Use the worked data that feeds the browser, not another copy of its rows.
        organizer = get_organizer("F04")
        worked = check_prediction("F04", 0)
        self.assertTrue(worked["correct"])
        self.assertTrue(worked["assisted"])
        self.assertFalse(worked["eligible_evidence"])
        self.assertNotIn("correct", organizer)
        columns = organizer["columns"][1:]
        rows = worked["rows"]
        def ascii_expr(value):
            return value.replace("−", "-").replace("²", "^2")
        for row in rows:
            for factor, product in zip(columns, row[1:]):
                with self.subTest(row=row[0], column=factor):
                    self.assert_verdict(compare_isolated(
                        "(" + ascii_expr(row[0]) + ")(" + ascii_expr(factor) + ")",
                        ascii_expr(product)), ("VERIFIED", "EXACT_IDENTITY"))
        reconstructed = "+".join("(" + ascii_expr(x) + ")" for row in rows for x in row[1:])
        self.assert_verdict(compare_isolated("(2x-3)(x+4)", reconstructed),
                            ("VERIFIED", "EXACT_IDENTITY"))
        self.assert_verdict(compare_isolated("(2x-3)(x+4)", reconstructed.replace("(-12)", "(12)")),
                            ("REJECTED", "UNEQUAL_COEFFICIENTS"))
        self.assertFalse(check_prediction("F04", 1)["eligible_evidence"])
