"""Independent aggregate assessment contract against real SQLite storage."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_store import Store

ANSWERS = {
    "f01-exam-rational":("-6x+9",0),
    "f01-exam-repair":("12x-19",0),
    "f01-exam-inverse":("6(5x-7)",1),
    "f01-exam-context":("5x+40",2),
    "f01-exam-combined":("-10x+11",0),
}

class ExamSetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"exam.sqlite"
        self.store=Store(self.path)
        self.user="synthetic-exam-set"

    def test_recovery_and_aggregate_result(self):
        exam=self.store.start_exam_set(self.user)
        self.assertEqual(5,exam["maximum"])
        self.assertEqual(set(ANSWERS),{i["item_id"] for i in exam["items"]})
        first=exam["items"][0]
        self.assertEqual({"status":"RECORDED"},self.store.submit(self.user,first["attempt_id"],*ANSWERS[first["item_id"]]))
        self.store=Store(self.path)
        active=self.store.active_exam_set(self.user)
        self.assertEqual(exam["exam_id"],active["exam_id"])
        self.assertEqual([True,False,False,False,False],[a["recorded"] for a in active["items"]])
        for item in active["items"]:
            self.assertFalse({"expected","correct_reason","feedback","answer"} & item.keys())
        with self.assertRaises(ValueError):
            self.store.finish_exam_set(self.user,exam["exam_id"])
        with self.assertRaises(ValueError):
            self.store.finish_exam(self.user,first["attempt_id"])
        self.assertEqual([],self.store.exam_history(self.user))
        for item in active["items"][1:]:
            answer,reason=ANSWERS[item["item_id"]]
            if item["item_id"]=="f01-exam-context":
                answer="5x+8"
            self.assertEqual({"status":"RECORDED"},self.store.submit(self.user,item["attempt_id"],answer,reason))
        result=self.store.finish_exam_set(self.user,exam["exam_id"])
        self.assertEqual((4,5),(result["score"],result["maximum"]))
        self.assertEqual(5,len(result["reviews"]))
        self.assertIsNone(self.store.active_exam_set(self.user))
        self.assertEqual(result,Store(self.path).finish_exam_set(self.user,exam["exam_id"]))
        self.assertEqual([],self.store.snapshot(self.user)["mastery_evidence"])

    def test_isolation_and_review_barriers(self):
        old=self.store.start(self.user,"f01-exam-rational","exam_preparation")["attempt_id"]
        self.store.submit(self.user,old,"-6x+9",0)
        self.store.finish_exam(self.user,old)
        exam=self.store.start_exam_set(self.user)
        self.assertIsNone(self.store.active_exam_set("other"))
        with self.assertRaises(ValueError):
            self.store.finish_exam_set("other",exam["exam_id"])
        with self.assertRaises(KeyError):
            self.store.submit("other",exam["items"][0]["attempt_id"],"-6x+9",0)
        with self.assertRaises(ValueError):
            self.store.start_exam_set(self.user)
        with self.assertRaises(ValueError):
            self.store.start(self.user,"f01-exam-rational","exam_preparation")
        with self.assertRaises(ValueError):
            self.store.finish_exam(self.user,old)
        with self.assertRaises(ValueError):
            self.store.request_hint(self.user,exam["items"][0]["attempt_id"],0)
        self.assertEqual([],self.store.exam_history(self.user))
