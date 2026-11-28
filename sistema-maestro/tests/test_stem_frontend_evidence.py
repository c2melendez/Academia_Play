import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"stem"))
from frontend_evidence import SNAPSHOT,audit,observed,compare

class FrontendEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        self.rows=self.data["observations"]
    def test_observed_checkout_not_head(self):
        for row in self.rows:
            evidence=observed(row)
            self.assertNotEqual(evidence["head_sha"],evidence["context"]["checkout"])
    def test_real_pairs_never_authorize_reuse(self):
        results=audit(self.data)
        self.assertEqual(len(results),2)
        self.assertTrue(all(not r["reuse_authorized"] for r in results))
        lite=next(r for r in results if r["repository"].endswith("-lite"))
        self.assertIn("setup",lite["differences"])
        self.assertEqual(lite["decision"],"RUN")
    def test_missing_phase_rejected(self):
        row=copy.deepcopy(self.rows[0])
        row["log_excerpt"]=[s for s in row["log_excerpt"] if "phase=build" not in s]
        with self.assertRaises(ValueError): observed(row)
    def test_skipped_step_rejected(self):
        row=copy.deepcopy(self.rows[0])
        next(s for s in row["job"]["steps"] if s["name"]=="Production build")["conclusion"]="skipped"
        with self.assertRaises(ValueError): observed(row)
    def test_tampered_workflow_rejected(self):
        row=copy.deepcopy(self.rows[0])
        row["workflow_yaml"]+="\n# changed"
        with self.assertRaises(ValueError): observed(row)
    def test_cross_product_never_reused(self):
        result=compare(self.rows[0],self.rows[3])
        self.assertIn("repository",result["differences"])
        self.assertFalse(result["reuse_authorized"])
