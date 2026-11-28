"""Independent fixtures and persistence tests for C-family remediation."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_activities import assess, INDEX
from mm110_f01_session import Session
from mm110_f01_store import Store

CASES = [
    ("f01-c-expand-negative","-12x+20",1,"-12x-20","f01-sign"),
    ("f01-c-expand-rational","6x+4",2,"6x+6","f01-omit"),
    ("f01-c-repair-sign","-6x+21",0,"-6x-21","f01-sign"),
    ("f01-c-repair-rational","4x+4",1,"4x+8","f01-omit"),
    ("f01-c-inverse-negative","6(-4x+3)",2,"6(-4x+18)","f01-omit"),
    ("f01-c-inverse-rational","6(3/2x-1/2)",0,"6(3/2x+1/2)","f01-sign"),
    ("f01-c-expand-trinomial","-6x+6",0,"-6x-6","f01-sign"),
    ("f01-c-repair-nested","6x-13",1,"6x-3","f01-sign"),
    ("f01-c-inverse-combine","6(3x-3)",2,"6(2x-3)","f01-omit"),
]
PRE=[("f01-a-sign-positive","15",0),("f01-a-fraction-negative","-3/2",1),
     ("f01-b-group","28",1),("f01-b-predict","4x+12",2)]

class RemediationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"test.sqlite"
        self.s=Store(self.path)
        self.user="synthetic-remediation"
    def resolve(self,item,answer,reason):
        key=self.s.start_guided(self.user,item)["attempt_id"]
        return self.s.submit(self.user,key,answer,reason)
    def prep(self):
        for item,answer,reason in PRE:
            self.assertTrue(self.resolve(item,answer,reason)["accepted"])
        self.assertEqual("C",self.s.guided_progress(self.user)["stage"])
    def test_independent_math_diagnostics_and_reasoning(self):
        for item,answer,reason,wrong,code in CASES:
            with self.subTest(item=item):
                self.assertTrue(assess(item,answer,reason)["eligible_evidence"])
                self.assertFalse(assess(item,answer,(reason+1)%3)["accepted"])
                result=assess(item,wrong,reason)
                self.assertFalse(result["accepted"])
                self.assertEqual(code,result["diagnostic_hypothesis"])
                self.assertFalse(assess(item,answer,reason,True)["eligible_evidence"])
    def test_failed_item_replaced_and_full_route_persists(self):
        self.prep()
        self.assertFalse(self.resolve("f01-route-expand","14x-3",1)["accepted"])
        self.s=Store(self.path)
        self.assertIn("f01-c-expand-negative",self.s.guided_progress(self.user)["pending"])
        with self.assertRaises(ValueError):
            self.s.start_guided(self.user,"f01-route-expand")
        self.assertTrue(self.resolve("f01-c-expand-negative","-12x+20",1)["eligible_evidence"])
        self.assertTrue(self.resolve("f01-route-repair","5x-20",0)["eligible_evidence"])
        self.assertTrue(self.resolve("f01-tutor-inverse","6(3x-2)",0)["eligible_evidence"])
        self.assertEqual("T",self.s.guided_progress(self.user)["stage"])
        self.assertTrue(self.resolve("f01-route-transfer","8x+48",1)["eligible_evidence"])
        self.s=Store(self.path)
        self.assertEqual("COMPLETE",self.s.guided_progress(self.user)["stage"])
        self.assertEqual("MASTERED",self.s.snapshot(self.user)["mastery_estimate"])
        self.assertEqual(1,len(self.s.snapshot(self.user)["access_grants"]))
    def test_prior_hint_and_parallel_attempt(self):
        self.prep()
        a=self.s.start_guided(self.user,"f01-route-expand")["attempt_id"]
        b=self.s.start_guided(self.user,"f01-route-expand")["attempt_id"]
        self.s.request_hint(self.user,a,0)
        result=self.s.submit(self.user,b,"14x-21",1)
        self.assertTrue(result["previously_exposed"])
        self.assertFalse(result["eligible_evidence"])
        self.assertIn("f01-c-expand-negative",self.s.guided_progress(self.user)["pending"])
    def test_exhaustion_blocks_transfer(self):
        self.prep()
        for item,wrong,reason in [("f01-route-expand","14x-3",1),
            ("f01-c-expand-negative","-12x-20",1),("f01-c-expand-rational","6x+6",2),("f01-c-expand-trinomial","-6x-6",0)]:
            self.assertFalse(self.resolve(item,wrong,reason)["accepted"])
        self.assertTrue(self.resolve("f01-route-repair","5x-20",0)["accepted"])
        self.assertTrue(self.resolve("f01-tutor-inverse","6(3x-2)",0)["accepted"])
        self.s=Store(self.path)
        state=self.s.guided_progress(self.user)
        self.assertEqual("C",state["stage"])
        self.assertEqual(["expansion"],state["exhausted_families"])
        self.assertEqual([],state["pending"])
        self.assertEqual([],self.s.snapshot(self.user)["access_grants"])
        with self.assertRaises(ValueError):
            self.s.start_guided(self.user,"f01-route-transfer")
    def test_same_family_does_not_inflate_mastery(self):
        s=Session("synthetic-family")
        for item,answer,reason in [("f01-route-expand","14x-21",1),
            ("f01-c-expand-negative","-12x+20",1),("f01-c-expand-rational","6x+4",2),
            ("f01-route-transfer","8x+48",1)]:
            key=s.start(item,INDEX[item].mode)["attempt_id"]
            self.assertTrue(s.submit(key,answer,reason)["eligible_evidence"])
        self.assertEqual("DEVELOPING",s.snapshot()["mastery_estimate"])
        self.assertEqual([],s.snapshot()["access_grants"])

    def test_fourth_variant_recovers_full_guided_route(self):
        self.prep()
        for item,wrong,reason in [("f01-route-expand","14x-3",1),
            ("f01-c-expand-negative","-12x-20",1),("f01-c-expand-rational","6x+6",2)]:
            self.assertFalse(self.resolve(item,wrong,reason)["accepted"])
        self.s=Store(self.path)
        self.assertIn("f01-c-expand-trinomial",self.s.guided_progress(self.user)["pending"])
        self.assertTrue(self.resolve("f01-c-expand-trinomial","-6x+6",0)["eligible_evidence"])
        self.assertTrue(self.resolve("f01-route-repair","5x-20",0)["accepted"])
        self.assertTrue(self.resolve("f01-tutor-inverse","6(3x-2)",0)["accepted"])
        self.assertEqual("T",self.s.guided_progress(self.user)["stage"])
        self.assertTrue(self.resolve("f01-route-transfer","8x+48",1)["accepted"])
        self.assertEqual("COMPLETE",Store(self.path).guided_progress(self.user)["stage"])
