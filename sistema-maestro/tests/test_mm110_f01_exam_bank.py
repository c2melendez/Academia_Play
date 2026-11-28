"""Independent F01 exam fixtures; no formative mastery or hints."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_activities import INDEX, assess, public_item
from mm110_f01_session import Session

CASES = (
    ("f01-exam-rational","-6x+9",0,"-6x-9"),
    ("f01-exam-repair","12x-19",0,"12x-23"),
    ("f01-exam-inverse","6(5x-7)",1,"6(5x+7)"),
    ("f01-exam-context","5x+40",2,"5x+8"),
    ("f01-exam-combined","-10x+11",0,"-10x-19"),
    ("f01-exam-rational-b","10x-15",1,"10x+15"),
    ("f01-exam-repair-b","-10x-5",2,"-10x+11"),
    ("f01-exam-inverse-b","6(-7x+4)",0,"6(7x+4)"),
    ("f01-exam-context-b","-3x-12",1,"-3x+12"),
    ("f01-exam-combined-b","8x-19",2,"8x+8"),
)

class ExamBankTests(unittest.TestCase):
    def test_bank_matches_independent_fixtures(self):
        self.assertEqual({i for i,*_ in CASES},{i for i,v in INDEX.items() if v.mode=="exam_preparation"})
        for item,answer,reason,wrong in CASES:
            with self.subTest(item=item):
                self.assertTrue(assess(item,answer,reason)["accepted"])
                self.assertFalse(assess(item,wrong,reason)["accepted"])
                self.assertFalse(assess(item,answer,(reason+1)%3)["accepted"])
                self.assertFalse(assess(item,answer,reason)["eligible_evidence"])
                self.assertFalse({"expected","correct_reason","explanation","hints"} & public_item(item).keys())

    def test_deferred_review_and_no_formative_credit(self):
        s=Session("synthetic-exam-bank")
        for item,answer,reason,wrong in CASES:
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    s.start(item,"learning_path")
                attempt=s.start(item,"exam_preparation")["attempt_id"]
                with self.assertRaises(ValueError):
                    s.request_hint(attempt,0)
                with self.assertRaises(ValueError):
                    s.finish_exam(attempt)
                self.assertEqual({"status":"RECORDED"},s.submit(attempt,answer,reason))
                self.assertNotIn(attempt,[r["attempt_id"] for r in s.exam_history()])
                review=s.finish_exam(attempt)
                self.assertEqual(1,review["score"])
                self.assertEqual(answer,review["expected"])
                self.assertEqual(review,s.finish_exam(attempt))
        self.assertEqual([],s.snapshot()["mastery_evidence"])
        self.assertEqual([],s.snapshot()["access_grants"])
        self.assertEqual(len(CASES),len(s.exam_history()))
