"""Independent transfer fixtures and real SQLite persistence checks."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_activities import assess
from mm110_f01_store import Store

PRE = [
    ("f01-a-sign-positive","15",0),
    ("f01-a-fraction-negative","-3/2",1),
    ("f01-b-group","28",1),
    ("f01-b-predict","4x+12",2),
    ("f01-route-expand","14x-21",1),
    ("f01-route-repair","5x-20",0),
    ("f01-tutor-inverse","6(3x-2)",0),
]
TRANSFER = [
    ("f01-route-transfer","8x+48",1,"8x+6"),
    ("f01-transfer-perimeter","2x+16",0,"2x+10"),
    ("f01-transfer-discount","3/4x+9",1,"3/4x+12"),
    ("f01-transfer-balance","-3x-12",2,"-3x+12"),
]

RESERVE = [
    ("f01-transfer-reserve-fuel","2x+1",0,"2x+2"),
    ("f01-transfer-reserve-temperature","-4x-8",1,"-4x+8"),
    ("f01-transfer-reserve-scale","2x+3",2,"2x+15"),
    ("f01-transfer-reserve-sharing","2x-3",0,"2x-9"),
]

class TransferTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"test.sqlite"
        self.s=Store(self.path)
        self.user="synthetic-transfer"
    def prep(self):
        for item,answer,reason in PRE:
            key=self.s.start_guided(self.user,item)["attempt_id"]
            self.assertTrue(self.s.submit(self.user,key,answer,reason)["accepted"])
        self.assertEqual("T",self.s.guided_progress(self.user)["stage"])
    def test_independent_math_and_reason(self):
        for item,answer,reason,wrong in TRANSFER+RESERVE:
            with self.subTest(item=item):
                self.assertTrue(assess(item,answer,reason)["accepted"])
                self.assertFalse(assess(item,wrong,reason)["accepted"])
                self.assertFalse(assess(item,answer,(reason+1)%3)["accepted"])
    def test_exposure_in_free_practice_replaces_item(self):
        item,answer,reason,wrong=TRANSFER[0]
        key=self.s.start(self.user,item,"learning_path")["attempt_id"]
        self.s.request_hint(self.user,key,0)
        self.prep()
        self.assertEqual([TRANSFER[1][0]],self.s.guided_progress(self.user)["pending"])
        with self.assertRaises(ValueError):self.s.start_guided(self.user,item)
    def test_failed_transfer_replaced_and_persisted(self):
        self.prep()
        item,answer,reason,wrong=TRANSFER[0]
        key=self.s.start_guided(self.user,item)["attempt_id"]
        self.assertFalse(self.s.submit(self.user,key,wrong,reason)["accepted"])
        self.s=Store(self.path)
        item,answer,reason,wrong=TRANSFER[1]
        self.assertEqual([item],self.s.guided_progress(self.user)["pending"])
        key=self.s.start_guided(self.user,item)["attempt_id"]
        self.assertTrue(self.s.submit(self.user,key,answer,reason)["eligible_evidence"])
        self.assertEqual("COMPLETE",self.s.guided_progress(self.user)["stage"])
    def test_parallel_attempts_do_not_reuse_exposure(self):
        self.prep()
        item,answer,reason,wrong=TRANSFER[0]
        a=self.s.start_guided(self.user,item)["attempt_id"]
        b=self.s.start_guided(self.user,item)["attempt_id"]
        self.s.request_hint(self.user,a,0)
        result=self.s.submit(self.user,b,answer,reason)
        self.assertTrue(result["previously_exposed"])
        self.assertFalse(result["eligible_evidence"])
        self.assertEqual([TRANSFER[1][0]],self.s.guided_progress(self.user)["pending"])
    def test_reserve_recovery_and_persistence(self):
        self.prep()
        self.assertEqual("STANDARD",self.s.guided_progress(self.user)["transfer_status"])
        for item,answer,reason,wrong in TRANSFER:
            key=self.s.start_guided(self.user,item)["attempt_id"]
            self.s.submit(self.user,key,wrong,reason)
        self.s=Store(self.path)
        state=self.s.guided_progress(self.user)
        self.assertEqual("RESERVE",state["transfer_status"])
        self.assertEqual([RESERVE[0][0]],state["pending"])
        item,answer,reason,wrong=RESERVE[0]
        key=self.s.start_guided(self.user,item)["attempt_id"]
        self.assertTrue(self.s.submit(self.user,key,answer,reason)["eligible_evidence"])
        self.assertEqual("COMPLETE",self.s.guided_progress(self.user)["stage"])

    def test_exhaustion_does_not_complete(self):
        self.prep()
        for item,answer,reason,wrong in TRANSFER+RESERVE:
            key=self.s.start_guided(self.user,item)["attempt_id"]
            self.s.submit(self.user,key,wrong,reason)
        state=self.s.guided_progress(self.user)
        self.assertEqual("T",state["stage"])
        self.assertEqual([],state["pending"])
        self.assertEqual("EXHAUSTED",state["transfer_status"])
        for item,_,_,_ in TRANSFER+RESERVE:
            with self.assertRaises(ValueError):self.s.start_guided(self.user,item)
        self.assertNotEqual("MASTERED",self.s.snapshot(self.user)["mastery_estimate"])
