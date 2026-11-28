import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stem"))
from productivity import load, report
from cross_repo_productivity import summarize_cross_repo

class CrossRepoProductivityTests(unittest.TestCase):
    def setUp(self):
        self.data = load("cross-repo-productivity-observations.json")

    def test_observed_and_potential_separated(self):
        r = report()["cross_repo"]
        self.assertEqual(96.313, r["phuma"]["observed_vitest_reduction_seconds"])
        self.assertEqual(1, r["phuma"]["removed_executions"])
        self.assertIsNone(r["phuma"]["causally_attributed_savings_seconds"])
        self.assertEqual(110, r["precision"]["lite"]["observed_repeated_phase_seconds"])
        self.assertEqual(88, r["precision"]["plus"]["observed_repeated_phase_seconds"])
        self.assertFalse(r["precision"]["lite"]["reuse_authorized"])
        self.assertIsNone(r["precision"]["plus"]["actual_time_saved_seconds"])
        self.assertEqual(10, r["precision"]["lite"]["profiles"]["ci"]["expected_fail"])
        self.assertEqual(28, r["precision"]["plus"]["profiles"]["ci"]["todo"])
        self.assertFalse(r["certification_transfer"])

    def test_invalid_evidence_fails_closed(self):
        variants = [
            lambda d: d["precision"][0]["phases"][2].update(conclusion="skipped"),
            lambda d: d["precision"][1].update(job_id=d["precision"][0]["job_id"]),
            lambda d: d["precision"][0]["log_excerpt"].pop(),
            lambda d: d["precision"][0]["phases"][0].update(completed_at="2000-01-01T00:00:00Z"),
            lambda d: d["phuma"][1]["report"]["groups"][0]["calls"][1].update(execution_complete=True),
            lambda d: d["phuma"][1]["report"]["groups"][0]["calls"][0].update(status="FAIL"),
            lambda d: d["phuma"][1]["report"]["groups"][0]["calls"][1].update(shared_execution_from="other"),
            lambda d: d["phuma"][1]["rdg"].update(new_pass=135),
            lambda d: d["precision"].pop(),
        ]
        for i, mutate in enumerate(variants):
            with self.subTest(i=i):
                data = copy.deepcopy(self.data)
                mutate(data)
                with self.assertRaises(ValueError):
                    summarize_cross_repo(data)
