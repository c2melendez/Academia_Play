"""Real PostgreSQL integration; run only against disposable CI database."""
import os
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
import psycopg
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_postgres import PostgresStore
from mm110_f01_store import Store

class LocalPostgresStore(PostgresStore):
    def _connect(self):
        # Only for disposable loopback CI, never the production adapter's TLS path.
        return psycopg.connect("host=127.0.0.1 port=5432 dbname=f01_test user=academia_f01_app password=ci_only sslmode=disable",connect_timeout=5)

class Equivalence(unittest.TestCase):
    def setUp(self):
        self.pg=LocalPostgresStore("ci-only")
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.sqlite=Store(Path(self.tmp.name)/"f01.sqlite")
        with psycopg.connect("host=127.0.0.1 dbname=f01_test user=postgres password=ci_only") as db:
            db.execute("TRUNCATE academia_private.f01_sessions, academia_private.f01_tokens")
    def test_progress_equivalence_and_restart(self):
        for store in (self.sqlite,self.pg):
            learner="synthetic-learner"
            for item,answer,reason in [("f01-route-expand","14x-21",1),("f01-route-repair","5x-20",0),("f01-route-transfer","8x+48",1)]:
                attempt=store.start(learner,item,"learning_path")
                self.assertTrue(store.submit(learner,attempt["attempt_id"],answer,reason)["accepted"])
            self.assertEqual("MASTERED",store.snapshot(learner)["mastery_estimate"])
            self.assertEqual(3,len(store.snapshot(learner)["mastery_evidence"]))
            self.assertEqual(0,len(store.snapshot("other")["mastery_evidence"]))
        self.assertEqual("MASTERED",LocalPostgresStore("ci-only").snapshot("synthetic-learner")["mastery_estimate"])
    def test_concurrent_tokens(self):
        with patch("mm110_f01_postgres.SESSION_LIMIT",3):
            with ThreadPoolExecutor(max_workers=8) as pool:
                tokens=list(pool.map(lambda _:self.pg.create_token(),range(12)))
        valid=[t for t in tokens if t is not None]
        self.assertEqual(3,len(valid))
        self.assertEqual(3,len(set(self.pg.learner_for_token(t) for t in valid)))
        self.assertEqual(3,self.pg.token_count())
    def test_expiration_and_hash(self):
        with patch("mm110_f01_postgres.time.time",return_value=1000):
            token=self.pg.create_token()
            self.assertIsNotNone(self.pg.learner_for_token(token))
        with patch("mm110_f01_postgres.time.time",return_value=605800):
            self.assertIsNone(self.pg.learner_for_token(token))
        with self.pg._connect() as db:
            digest=db.execute("SELECT digest FROM academia_private.f01_tokens").fetchone()[0]
            self.assertEqual(64,len(digest))
            self.assertNotEqual(digest,token)
    def test_rollback_and_concurrent_attempts(self):
        learner="same"
        def bad(session):
            session.start("f01-route-expand","learning_path")
            raise RuntimeError("rollback")
        with self.assertRaises(RuntimeError):
            self.pg._run(learner,bad)
        with self.pg._connect() as db:
            self.assertIsNone(db.execute("SELECT payload FROM academia_private.f01_sessions WHERE learner=%s",(learner,)).fetchone())
        with ThreadPoolExecutor(max_workers=6) as pool:
            attempts=list(pool.map(lambda _:self.pg.start(learner,"f01-route-expand","learning_path"),range(6)))
        self.assertEqual(6,len({a["attempt_id"] for a in attempts}))
        with self.pg._connect() as db:
            import json
            payload=json.loads(db.execute("SELECT payload FROM academia_private.f01_sessions WHERE learner=%s",(learner,)).fetchone()[0])
        self.assertEqual(6,len(payload["attempts"]))
    def test_permissions(self):
        with self.pg._connect() as db:
            self.assertEqual("academia_f01_app",db.execute("SELECT current_user").fetchone()[0])
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with self.pg._connect() as db:
                db.execute("DELETE FROM academia_private.f01_sessions")
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with self.pg._connect() as db:
                db.execute("UPDATE academia_private.f01_tokens SET expires=1")

if __name__=="__main__":
    unittest.main(verbosity=2)
