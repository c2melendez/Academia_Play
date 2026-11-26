"""Real subprocess and failure-path certification for the F01 worker."""
import sys
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import mm110_f01_oracle_worker as w
from mm110_f01_oracle import Verdict
from mm110_f01_session import Session

class WorkerTests(unittest.TestCase):
    def test_real_exact_worker(self):
        for a,b in [("7(2x-3)","14x-21"),("(1/3)(6x-9)","2x-3"),("(x+2)(x-2)","x^2-4")]:
            with self.subTest(a=a):
                self.assertEqual(Verdict("VERIFIED","EXACT_IDENTITY"),w.compare_isolated(a,b))
    def test_real_false_identity(self):
        self.assertEqual(Verdict("REJECTED","UNEQUAL_COEFFICIENTS"),w.compare_isolated("x^2","x"))
    def test_real_invalid_domain(self):
        for a in ("1/x","1/0","__import__(x)","x^-1"):
            with self.subTest(a=a):
                self.assertEqual(Verdict("REJECTED","INVALID_FORMAT_OR_DOMAIN"),w.compare_isolated(a,"0"))
    def test_real_computation_limits(self):
        for a in ("x^17","9"*100,"("*30+"x"+")"*30):
            with self.subTest(a=a):
                self.assertEqual(Verdict("INCONCLUSIVE","COMPUTATION_LIMIT"),w.compare_isolated(a,"0"))
    def test_preflight_rejects_without_spawn(self):
        with patch.object(w.subprocess,"run") as run:
            self.assertEqual("REJECTED",w.compare_isolated(None,"0").status)
            self.assertEqual("INCONCLUSIVE",w.compare_isolated("x"*257,"0").status)
            run.assert_not_called()
    def test_timeout_fail_closed(self):
        with patch.object(w.subprocess,"run",side_effect=subprocess.TimeoutExpired("worker",3)):
            self.assertEqual(Verdict("INCONCLUSIVE","COMPUTATION_LIMIT"),w.compare_isolated("x","x"))
    def test_signal_and_nonzero_fail_closed(self):
        for rc in (-9,-24,1):
            with patch.object(w.subprocess,"run",return_value=subprocess.CompletedProcess([],rc,"","")):
                self.assertEqual(Verdict("INCONCLUSIVE","WORKER_FAILURE"),w.compare_isolated("x","x"))
    def test_invalid_worker_protocol(self):
        for output in ("garbage",'["VERIFIED","UNTRUSTED"]','{"status":"VERIFIED"}','[]'):
            with patch.object(w.subprocess,"run",return_value=subprocess.CompletedProcess([],0,output,"")):
                self.assertEqual(Verdict("INCONCLUSIVE","WORKER_FAILURE"),w.compare_isolated("x","x"))
    def test_spawn_failure(self):
        with patch.object(w.subprocess,"run",side_effect=OSError("injected failure")):
            self.assertEqual(Verdict("INCONCLUSIVE","WORKER_FAILURE"),w.compare_isolated("x","x"))
    def test_failure_no_mastery_and_retry(self):
        s=Session("synthetic-worker")
        key=s.start("f01-route-expand","learning_path")["attempt_id"]
        with patch.object(w.subprocess,"run",side_effect=subprocess.TimeoutExpired("worker",3)):
            self.assertEqual("RETRY",s.submit(key,"14x-21",1)["status"])
        self.assertEqual([],s.snapshot()["mastery_evidence"])
        self.assertEqual([],s.snapshot()["access_grants"])
        self.assertTrue(s.submit(key,"14x-21",1)["eligible_evidence"])
        self.assertEqual(1,len(s.snapshot()["mastery_evidence"]))
