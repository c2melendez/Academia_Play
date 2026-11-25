"""F01 persistence tests using only temporary databases and synthetic learners."""
import sys
import unittest
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from mm110_f01_store import Store

class F01StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"test.sqlite3"
        self.store=Store(self.path)
        self.user="synthetic-learner"

    def start(self,item="f01-route-expand",mode="learning_path"):
        return self.store.start(self.user,item,mode)["attempt_id"]

    def test_restart_retains_attempt(self):
        key=self.start()
        reopened=Store(self.path)
        self.assertTrue(reopened.submit(self.user,key,"14x-21",1)["accepted"])
        self.assertEqual(1,len(Store(self.path).snapshot(self.user)["mastery_evidence"]))

    def test_hint_survives_restart(self):
        key=self.start()
        self.store.request_hint(self.user,key,0)
        result=Store(self.path).submit(self.user,key,"14x-21",1)
        self.assertTrue(result["assisted"])
        self.assertEqual([],self.store.snapshot(self.user)["mastery_evidence"])

    def test_replay_after_restart(self):
        key=self.start()
        result=self.store.submit(self.user,key,"14x-21",1)
        self.assertEqual(result,Store(self.path).submit(self.user,key,"14x-21",1))
        self.assertEqual(1,len(self.store.snapshot(self.user)["mastery_evidence"]))
        with self.assertRaises(ValueError):
            self.store.submit(self.user,key,"14x+21",1)

    def test_distinct_learner_isolation(self):
        key=self.start()
        with self.assertRaises(KeyError):
            self.store.submit("another-synthetic",key,"14x-21",1)
        self.assertEqual([],self.store.snapshot("another-synthetic")["mastery_evidence"])

    def test_concurrent_independent_connections(self):
        key=self.start()
        def submit(_):
            return Store(self.path).submit(self.user,key,"14x-21",1)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(submit,range(20)))
        self.assertTrue(all(r==results[0] for r in results))
        self.assertEqual(1,len(self.store.snapshot(self.user)["mastery_evidence"]))

    def test_mastery_and_grant_survive_restart(self):
        for item,answer,reason in [
            ("f01-route-expand","14x-21",1),
            ("f01-route-repair","5x-20",0),
            ("f01-route-transfer","8x+48",1),
        ]:
            self.store.submit(self.user,self.start(item),answer,reason)
        state=Store(self.path).snapshot(self.user)
        self.assertEqual("MASTERED",state["mastery_estimate"])
        self.assertEqual(1,len(state["access_grants"]))

    def test_transaction_rolls_back(self):
        key=self.start()
        original=self.store.snapshot(self.user)
        with patch("mm110_f01_store.json.dumps",side_effect=RuntimeError("injected write failure")):
            with self.assertRaises(RuntimeError):
                self.store.submit(self.user,key,"14x-21",1)
        self.assertEqual(original,Store(self.path).snapshot(self.user))
        self.assertTrue(self.store.submit(self.user,key,"14x-21",1)["accepted"])

    def test_exam_isolation_after_restart(self):
        key=self.start("f01-exam-rational","exam_preparation")
        self.assertEqual({"status":"RECORDED"},Store(self.path).submit(self.user,key,"-6x+9",0))
        self.assertEqual([],self.store.snapshot(self.user)["mastery_evidence"])
