"""Transactional M1 session contracts using actual SQLite and isolated oracles."""
import sys
import tempfile
import unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_m1_store import Store
from mm110_m1_activities import INDEX

def displayed_key(item,canonical):
    return item['choices'].index(INDEX[item['id']]['choices'][canonical])

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
            reason=displayed_key(i,reason)
            if n==1:
                reason=(reason+1)%3
            self.assertEqual(self.store.submit("a",i["attempt_id"],answer,reason),{"status":"RECORDED"})
            self.store=Store(self.path)
            self.assertEqual(sum(i["recorded"] for i in self.store.active_exam("a")["items"]),n+1)
        review=self.store.finish_exam("a",e["exam_id"])
        self.assertEqual((review["score"],review["maximum"]),(5,6))
        self.assertEqual(review,self.store.finish_exam("a",e["exam_id"]))
        self.assertIsNone(self.store.active_exam("a"))
        self.assertTrue(self.store.submit("a",a,"5x^2",0)["accepted"])
        self.assertEqual(self.store.progress("a")["eligible_evidence"],0)

    def test_retry_invalid_and_duplicate_exam(self):
        e=self.store.start_exam("a")
        a=e["items"][0]["attempt_id"]
        key=displayed_key(e["items"][0],2)
        self.assertEqual(self.store.submit("a",a,"not a degree",key),{"status":"INVALID_INPUT"})
        self.assertFalse(self.store.active_exam("a")["items"][0]["recorded"])
        self.assertEqual(self.store.submit("a",a,None,key),{"status":"RECORDED"})
        self.assertEqual(self.store.submit("a",a,None,key),{"status":"RECORDED"})
        with self.assertRaises(ValueError):
            self.store.submit("a",a,0,key)

    def test_concurrent_exam_start(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            result=list(pool.map(lambda _:self.store.start_exam("a"),range(2)))
        self.assertEqual(result[0],result[1])
        self.assertEqual(len(result[0]["items"]),6)

    def test_three_disjoint_forms_and_exhaustion(self):
        used=set()
        for _ in range(3):
            e=self.store.start_exam("rotation")
            self.assertEqual(e,Store(self.path).active_exam("rotation"))
            ids={i["id"] for i in e["items"]}
            self.assertFalse(used & ids)
            used.update(ids)
            for i in e["items"]:
                canonical=INDEX[i["id"]]["correct_reason"]
                key=displayed_key(i,canonical)
                self.assertEqual(self.store.submit("rotation",i["attempt_id"],INDEX[i["id"]]["expected"],key),{"status":"RECORDED"})
            result=self.store.finish_exam("rotation",e["exam_id"])
            self.assertEqual(result["score"],6)
            for i,review in zip(e["items"],result["reviews"]):
                self.assertEqual(i["choices"][review["correct_reason"]],INDEX[i["id"]]["choices"][INDEX[i["id"]]["correct_reason"]])
        self.assertEqual(len(used),18)
        with self.assertRaisesRegex(ValueError,"fresh exam bank exhausted"):
            self.store.start_exam("rotation")

    def test_guided_route_order_and_reload(self):
        learner="guided"
        family="F03"
        self.assertEqual(self.store.guided_progress(learner,family)["stage"],"A")
        with self.assertRaises(ValueError):
            self.store.guided_start(learner,family,"m1-f03-t-5")
        # An ordinary practice result cannot bypass the guided prerequisites.
        self.store.assess_formative(learner,"m1-f03-a-1","5x^2",0)
        self.assertEqual(self.store.guided_progress(learner,family)["stage"],"A")
        cases=[
            ("m1-f03-a-1","5x^2",0,"B"),
            ("m1-f03-b-2","3x^2+3x-5",1,"C"),
            ("m1-f03-c-3","3x^2-7x+10",2,"C"),
            ("m1-f03-c-4","6x-1",0,"T"),
            ("m1-f03-t-5","4x^2+5x-8",1,"COMPLETE"),
        ]
        for item,answer,key,stage in cases:
            a=self.store.guided_start(learner,family,item)
            self.store=Store(self.path)
            self.assertEqual(a,self.store.guided_start(learner,family,item))
            r=self.store.submit(learner,a["attempt_id"],answer,key)
            self.assertTrue(r["accepted"])
            self.assertTrue(r["assisted"])
            self.assertFalse(r["eligible_evidence"])
            self.assertEqual(self.store.guided_progress(learner,family)["stage"],stage)
        self.assertEqual(len(self.store.guided_progress(learner,family)["completed"]),5)
        self.assertEqual(self.store.progress(learner)["mastery"],"UNASSESSED")
        self.assertEqual(self.store.guided_progress("other",family)["stage"],"A")

    def test_guided_wrong_answer_does_not_advance(self):
        a=self.store.guided_start("a","F02","m1-f02-a-1")
        r=self.store.submit("a",a["attempt_id"],2,0)
        self.assertFalse(r["accepted"])
        self.assertEqual(self.store.guided_progress("a","F02")["stage"],"A")
        b=self.store.guided_start("a","F02","m1-f02-a-1")
        self.assertNotEqual(a["attempt_id"],b["attempt_id"])
        self.store.start_exam("a")
        with self.assertRaises(ValueError):
            self.store.guided_progress("a","F02")
        with self.assertRaises(ValueError):
            self.store.submit("a",b["attempt_id"],3,0)
