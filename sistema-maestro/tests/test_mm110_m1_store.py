"""Transactional M1 session contracts using actual SQLite and isolated oracles."""
import sys
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_m1_store import Store

EXAM={
    "F02":(None,2),
    "F03":("2x-2",2),
    "F04":("3x^2-10x-8",2),
    "F05":("9x^2+12x+4",2),
    "F06":(["x-3","x^2+3x+9"],2),
    "F07":(["2x^2-x+1","-6"],2),
}

class M1StoreTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path=Path(temp.name)/"m1.sqlite"
        self.store=Store(self.path)

    def test_formative_persistence_and_isolation(self):
        a=self.store.start("a","m1-f04-c-3")["attempt_id"]
        with self.assertRaises(KeyError):
            self.store.submit("b",a,"2x^2+7x-15",2)
        r=self.store.submit("a",a,"2x^2+7x-15",2)
        self.assertTrue(r["accepted"])
        self.assertTrue(r["assisted"])
        self.assertFalse(r["eligible_evidence"])
        restored=Store(self.path)
        self.assertEqual(r,restored.submit("a",a,"2x^2+7x-15",2))
        with self.assertRaises(ValueError):
            restored.submit("a",a,"0",2)
        self.assertEqual(restored.progress("a")["families"]["F04"]["completed"],["m1-f04-c-3"])
        self.assertEqual(restored.progress("b")["families"]["F04"]["completed"],[])
        self.assertEqual(restored.progress("a")["mastery"],"UNASSESSED")

    def test_exam_lifecycle_and_recovery(self):
        a=self.store.start("a","m1-f03-a-1")["attempt_id"]
        e=self.store.start_exam("a")
        self.assertEqual(e["maximum"],6)
        self.assertEqual({i["family"] for i in e["items"]},set(EXAM))
        self.assertTrue(all(not i["recorded"] and "expected" not in i and "correct_reason" not in i for i in e["items"]))
        self.assertEqual(self.store.start_exam("a"),e)
        self.assertIsNone(self.store.active_exam("b"))
        with self.assertRaises(KeyError):
            self.store.finish_exam("b",e["exam_id"])
        with self.assertRaises(ValueError):
            self.store.finish_exam("a",e["exam_id"])
        with self.assertRaises(ValueError):
            self.store.progress("a")
        with self.assertRaises(ValueError):
            self.store.submit("a",a,"5x^2",0)
        with self.assertRaises(ValueError):
            self.store.start("a","m1-f03-a-1")
        for n,i in enumerate(e["items"]):
            answer,reason=EXAM[i["family"]]
            if n==1:
                reason=0
            self.assertEqual(self.store.submit("a",i["attempt_id"],answer,reason),{"status":"RECORDED"})
            self.store=Store(self.path)
            self.assertEqual(sum(i["recorded"] for i in self.store.active_exam("a")["items"]),n+1)
        review=self.store.finish_exam("a",e["exam_id"])
        self.assertEqual((review["score"],review["maximum"]),(5,6))
        self.assertEqual(review,self.store.finish_exam("a",e["exam_id"]))
        self.assertIsNone(self.store.active_exam("a"))
        with self.assertRaisesRegex(ValueError,"fresh exam bank exhausted"):
            self.store.start_exam("a")
        self.assertTrue(self.store.submit("a",a,"5x^2",0)["accepted"])
        self.assertEqual(self.store.progress("a")["eligible_evidence"],0)

    def test_retry_invalid_and_duplicate_exam(self):
        e=self.store.start_exam("a")
        a=e["items"][0]["attempt_id"]
        self.assertEqual(self.store.submit("a",a,"not a degree",2),{"status":"INVALID_INPUT"})
        self.assertFalse(self.store.active_exam("a")["items"][0]["recorded"])
        self.assertEqual(self.store.submit("a",a,None,2),{"status":"RECORDED"})
        self.assertEqual(self.store.submit("a",a,None,2),{"status":"RECORDED"})
        with self.assertRaises(ValueError):
            self.store.submit("a",a,0,2)

    def test_concurrent_exam_start(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            result=list(pool.map(lambda _:self.store.start_exam("a"),range(2)))
        self.assertEqual(result[0],result[1])
        self.assertEqual(len(result[0]["items"]),6)
