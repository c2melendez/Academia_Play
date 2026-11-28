"""Credential lifecycle tests using real SQLite and a deterministic clock."""
import hashlib
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_store import Store, SESSION_TTL

class TokenTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/"tokens.sqlite"
        self.store=Store(self.path)

    def test_digest_only_and_distinct_learners(self):
        a,b=self.store.create_token(),self.store.create_token()
        self.assertNotEqual(a,b)
        self.assertNotEqual(self.store.learner_for_token(a),self.store.learner_for_token(b))
        with sqlite3.connect(self.path) as db:
            digests={r[0] for r in db.execute("SELECT digest FROM f01_tokens")}
        self.assertEqual({hashlib.sha256(x.encode("ascii")).hexdigest() for x in (a,b)},digests)
        self.assertNotIn(a.encode(),self.path.read_bytes())
        self.assertNotIn(b.encode(),self.path.read_bytes())

    def test_expiration_boundary_and_reclamation(self):
        with patch("mm110_f01_store.time.time",return_value=1000000):
            token=self.store.create_token()
        with patch("mm110_f01_store.time.time",return_value=1000000+SESSION_TTL-1):
            self.assertIsNotNone(self.store.learner_for_token(token))
            self.assertEqual(1,self.store.token_count())
        with patch("mm110_f01_store.time.time",return_value=1000000+SESSION_TTL):
            self.assertIsNone(self.store.learner_for_token(token))
            self.assertEqual(0,self.store.token_count())
            self.assertIsNotNone(self.store.create_token())
            with sqlite3.connect(self.path) as db:
                self.assertEqual(1,db.execute("SELECT COUNT(*) FROM f01_tokens").fetchone()[0])

    def test_invalid_credentials(self):
        for token in (None,123,"","a"*43,"é"*43,"a"*44):
            with self.subTest(token=token):
                self.assertIsNone(self.store.learner_for_token(token))

    def test_atomic_cap_under_concurrency(self):
        with patch("mm110_f01_store.SESSION_LIMIT",3):
            with ThreadPoolExecutor(max_workers=8) as pool:
                tokens=list(pool.map(lambda _:self.store.create_token(),range(12)))
            self.assertEqual(3,sum(t is not None for t in tokens))
            self.assertEqual(3,self.store.token_count())
