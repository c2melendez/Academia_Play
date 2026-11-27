"""Real isolated worker checks and adversarial protocol fixtures."""
import sys
import unittest
import subprocess
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import mm110_polynomial_worker as w

class PolynomialWorkerTests(unittest.TestCase):
    def test_real_worker(self):
        cases=[
            ("degree",("x^3-x^3+2x",1),"VERIFIED","EXACT_DEGREE"),
            ("degree",("0",None),"VERIFIED","EXACT_DEGREE"),
            ("degree",("x^2",1),"REJECTED","INCORRECT_DEGREE"),
            ("coefficient",("(x+2)^2",1,"4"),"VERIFIED","EXACT_COEFFICIENT"),
            ("coefficient",("x",1,"2"),"REJECTED","INCORRECT_COEFFICIENT"),
            ("division",("x^2+1","x-1","x+1","2"),"VERIFIED","EXACT_DIVISION"),
            ("division",("x^2+1","x-1","x","x+1"),"REJECTED","REMAINDER_DEGREE"),
            ("division",("x","0","0","x"),"REJECTED","INVALID_FORMAT_OR_DOMAIN"),
            ("factor_product",("x^2-4",["x-2","x+2"]),"VERIFIED","EXACT_FACTOR_PRODUCT"),
            ("factor_product",("x^2-4",["1","x^2-4"]),"REJECTED","TRIVIAL_FACTORIZATION"),
            ("degree",("x^17",1),"INCONCLUSIVE","COMPUTATION_LIMIT"),
        ]
        for op,args,status,reason in cases:
            with self.subTest(op=op,args=args):
                result=w.verify_isolated(op,*args)
                self.assertEqual((status,reason),(result.status,result.reason))

    def test_preflight(self):
        cases=[
            ("unknown",(), "REJECTED"),
            ("degree",("x",True),"REJECTED"),
            ("degree",("x",17),"INCONCLUSIVE"),
            ("degree",("x"*257,1),"INCONCLUSIVE"),
            ("coefficient",("x",1,1.0),"REJECTED"),
            ("factor_product",("x^2",["x"]*17),"REJECTED"),
            ("division",("x",),"REJECTED"),
        ]
        with patch.object(w.subprocess,"run") as run:
            for op,args,status in cases:
                with self.subTest(op=op,args=args):
                    self.assertEqual(status,w.verify_isolated(op,*args).status)
            run.assert_not_called()

    def test_worker_failure_closed(self):
        for stdout,code in [
            ('["VERIFIED","EXACT_DIVISION"]',0),
            ('["VERIFIED",{}]',0),
            ('not-json',0),
            ('["VERIFIED","EXACT_DEGREE"]',1),
            ('x'*257,0),
        ]:
            with self.subTest(stdout=stdout,code=code):
                with patch.object(w.subprocess,"run",return_value=subprocess.CompletedProcess([],code,stdout,"")):
                    result=w.verify_isolated("degree","x",1)
                    self.assertEqual(("INCONCLUSIVE","WORKER_FAILURE"),(result.status,result.reason))

    def test_timeout(self):
        with patch.object(w.subprocess,"run",side_effect=subprocess.TimeoutExpired("worker",3)):
            self.assertEqual(("INCONCLUSIVE","COMPUTATION_LIMIT"),
                             tuple(vars(w.verify_isolated("degree","x",1)).values()))
