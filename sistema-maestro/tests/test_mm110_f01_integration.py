"""Integration tests for F01 activities, oracle and session mastery."""
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from mm110_f01_activities import ITEMS, assess, public_item
from mm110_f01_session import Session
from mm110_f01_oracle import Verdict

class F01IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.s=Session("synthetic-test-user")
    def attempt(self,item,answer,reason,mode="learning_path",assisted=False):
        key=self.s.start(item,mode)["attempt_id"]
        if assisted:self.s.request_hint(key,0)
        return self.s.submit(key,answer,reason)
    def test_all_items(self):
        for i in ITEMS:
            with self.subTest(item=i.item_id):
                self.assertTrue(assess(i.item_id,i.expected,i.correct_reason)["accepted"])
                self.assertNotIn("expected",public_item(i.item_id))
                self.assertNotIn("correct_reason",public_item(i.item_id))
    def test_mastery(self):
        self.attempt("f01-route-expand","14x-21",1)
        self.attempt("f01-route-repair","5x-20",0)
        self.assertEqual("DEVELOPING",self.s.snapshot()["mastery_estimate"])
        self.attempt("f01-route-transfer","8x+48",1)
        state=self.s.snapshot()
        self.assertEqual("MASTERED",state["mastery_estimate"])
        self.assertEqual(1,len(state["access_grants"]))
    def test_repeated_family_not_mastery(self):
        for _ in range(3):self.attempt("f01-route-expand","14x-21",1)
        self.attempt("f01-route-transfer","8x+48",1)
        self.assertEqual("DEVELOPING",self.s.snapshot()["mastery_estimate"])
    def test_assisted_not_eligible(self):
        self.assertFalse(self.attempt("f01-route-expand","14x-21",1,assisted=True)["eligible_evidence"])
        self.assertEqual([],self.s.snapshot()["mastery_evidence"])
    def test_wrong_reason(self):
        self.assertFalse(self.attempt("f01-route-expand","14x-21",0)["accepted"])
    def test_wrong_form(self):
        r=self.attempt("f01-route-expand","7(2x-3)",1)
        self.assertEqual("VERIFIED",r["oracle_status"])
        self.assertFalse(r["accepted"])
    def test_omission_and_sign(self):
        for answer,code in [("14x-3","f01-omit"),("14x+21","f01-sign")]:
            self.assertEqual(code,self.attempt("f01-route-expand",answer,1)["diagnostic_hypothesis"])
    def test_invalid_not_diagnostic(self):
        self.assertIsNone(self.attempt("f01-route-expand","1/x",1)["diagnostic_hypothesis"])
    def test_exam_separation(self):
        with self.assertRaises(ValueError):self.s.start("f01-exam-rational","learning_path")
        key=self.s.start("f01-exam-rational","exam_preparation")["attempt_id"]
        with self.assertRaises(ValueError):self.s.request_hint(key,0)
        self.assertEqual({"status":"RECORDED"},self.s.submit(key,"-6x+9",0))
        self.assertEqual([],self.s.snapshot()["mastery_evidence"])
    def test_inconclusive_retry(self):
        key=self.s.start("f01-route-expand","learning_path")["attempt_id"]
        with patch("mm110_f01_activities.compare",return_value=Verdict("INCONCLUSIVE","INTERNAL_FAILURE")):
            self.assertEqual("RETRY",self.s.submit(key,"14x-21",1)["status"])
        self.assertEqual([],self.s.snapshot()["mastery_evidence"])
        self.assertTrue(self.s.submit(key,"14x-21",1)["accepted"])
    def test_concurrent_replay(self):
        key=self.s.start("f01-route-expand","learning_path")["attempt_id"]
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda _:self.s.submit(key,"14x-21",1),range(20)))
        self.assertTrue(all(r==results[0] for r in results))
        self.assertEqual(1,len(self.s.snapshot()["mastery_evidence"]))
        with self.assertRaises(ValueError):self.s.submit(key,"14x+21",1)
    def test_snapshot_isolation(self):
        state=self.s.snapshot()
        state["mastery_rule"]["distinct_variant_families"]=1
        self.assertEqual(2,self.s.snapshot()["mastery_rule"]["distinct_variant_families"])
