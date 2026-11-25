"""F01 foundation checks: independent expected values and exclusion from mastery."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_activities import assess, INDEX
from mm110_f01_session import Session

CASES = [
    ("f01-a-sign-positive","15",0,"-15","f01-sign"),
    ("f01-a-fraction-negative","-3/2",1,"3/2","f01-sign"),
    ("f01-b-predict","4x+12",2,"4x+3","f01-omit"),
    ("f01-b-group","28",1,"13","f01-omit"),
]

class FoundationTests(unittest.TestCase):
    def test_independent_expected_answers(self):
        for item,answer,reason,wrong,code in CASES:
            with self.subTest(item=item):
                result=assess(item,answer,reason)
                self.assertTrue(result["accepted"])
                self.assertFalse(result["eligible_evidence"])

    def test_diagnostic_hypotheses(self):
        for item,answer,reason,wrong,code in CASES:
            with self.subTest(item=item):
                result=assess(item,wrong,reason)
                self.assertFalse(result["accepted"])
                self.assertEqual(code,result["diagnostic_hypothesis"])

    def test_wrong_justification(self):
        for item,answer,reason,wrong,code in CASES:
            with self.subTest(item=item):
                self.assertFalse(assess(item,answer,(reason+1)%3)["accepted"])

    def test_equivalent_fraction(self):
        self.assertTrue(assess("f01-a-fraction-negative","-18/12",1)["accepted"])

    def test_prediction_requires_expansion(self):
        self.assertFalse(assess("f01-b-predict","4(x+3)",2)["accepted"])

    def test_foundations_cannot_unlock_mastery(self):
        s=Session("synthetic-foundation")
        for item,answer,reason,wrong,code in CASES:
            key=s.start(item,"learning_path")["attempt_id"]
            self.assertTrue(s.submit(key,answer,reason)["accepted"])
        self.assertEqual([],s.snapshot()["mastery_evidence"])
        key=s.start("f01-route-transfer","learning_path")["attempt_id"]
        s.submit(key,"8x+48",1)
        self.assertEqual("DEVELOPING",s.snapshot()["mastery_estimate"])
        self.assertEqual([],s.snapshot()["access_grants"])

    def test_hints_never_count(self):
        s=Session("synthetic-hints")
        for item,answer,reason,wrong,code in CASES:
            key=s.start(item,"learning_path")["attempt_id"]
            s.request_hint(key,0)
            result=s.submit(key,answer,reason)
            self.assertTrue(result["assisted"])
            self.assertFalse(result["eligible_evidence"])
