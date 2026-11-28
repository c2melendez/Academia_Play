import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"stem"))
from workflow_overlap import SNAPSHOT,audit,seconds

class StemWorkflowOverlapTests(unittest.TestCase):
    def setUp(self):
        self.observations=json.loads(SNAPSHOT.read_text(encoding="utf-8"))["observations"]
    def test_real_observations(self):
        result=audit(self.observations)
        self.assertEqual(len(result["candidates"]),8)
        self.assertFalse(result["reuse_authorized"])
        self.assertTrue(all(not c["reuse_authorized"] for c in result["candidates"]))
        self.assertTrue(all(c["classification"]=="CONTEXT_DIFF_REVIEW" for c in result["candidates"] if c["repository"].endswith("lite")))
        self.assertTrue(all(c["classification"]=="SAME_DECLARED_CONTEXT_REVIEW" for c in result["candidates"] if c["repository"].endswith("plus")))
        self.assertGreater(result["paired_runner_seconds_lower_bound"],0)
    def test_sha_separation(self):
        observations=copy.deepcopy(self.observations)
        observations[1]["commit"]="f"*40
        self.assertEqual(len(audit(observations)["candidates"]),4)
    def test_corrupt_workflow_fails(self):
        observations=copy.deepcopy(self.observations)
        observations[0]["workflow_yaml"]+="\n# mutated"
        with self.assertRaises(ValueError):
            audit(observations)
    def test_duplicate_run_fails(self):
        with self.assertRaises(ValueError):
            audit(self.observations+[self.observations[0]])
    def test_skipped_not_counted(self):
        self.assertIsNone(seconds({"conclusion":"skipped","started_at":"2026-11-28T00:00:00Z","completed_at":"2026-11-28T00:00:10Z"}))
