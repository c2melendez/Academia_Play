import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"stem"))
from productivity import load,summarize,report

class ProductivityTests(unittest.TestCase):
    def setUp(self): self.data=load("productivity-observations.json")
    def test_observed_counts_and_no_inferred_savings(self):
        r=report()
        self.assertEqual(426,r["MM110"]["before"]["tests_executed_in_successful_suites"])
        self.assertEqual(437,r["MM110"]["after"]["tests_executed_in_successful_suites"])
        self.assertEqual(11,r["change"]["tests"])
        self.assertEqual(2,r["reuse"]["connected_templates"])
        self.assertIsNone(r["actual_time_saved_seconds"])
        self.assertIsNone(r["certified_curricular_ids"])
        self.assertFalse(r["certification_transfer"])
        self.assertEqual(229,r["precision_overlap"]["potential_runner_seconds_lower_bound"])
        self.assertFalse(any(x["reuse_authorized"] for x in r["precision_overlap"]["observed_pairs"]))
    def test_duplicate_run_rejected(self):
        self.data["observations"][1]["run_id"]=self.data["observations"][0]["run_id"]
        with self.assertRaises(ValueError): summarize(self.data)
    def test_failed_job_rejected(self):
        self.data["observations"][0]["job"]["conclusion"]="failure"
        with self.assertRaises(ValueError): summarize(self.data)
    def test_different_checkout_rejected(self):
        self.data["observations"][0]["checkout_sha"]="a"*40
        with self.assertRaises(ValueError): summarize(self.data)
    def test_missing_suite_rejected(self):
        self.data["observations"].pop()
        with self.assertRaises(ValueError): summarize(self.data)
    def test_tampered_source_rejected(self):
        self.data["assets"][0]["content"]+="\n// changed"
        with self.assertRaises(ValueError): summarize(self.data)
    def test_bad_timestamps_rejected(self):
        self.data["observations"][0]["step"]["completed_at"]="2020-01-01T00:00:00Z"
        with self.assertRaises(ValueError): summarize(self.data)
