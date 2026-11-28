"""P0: negative checks for candidate technical closure."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gate_coverage import validate_candidate_closure

SHA = "a" * 40

class CandidateClosureTests(unittest.TestCase):
    def setUp(self):
        self.continuity = json.loads((ROOT.parents[0] / "continuity.json").read_text())
        self.continuity["module_states"] = {"M0": "DONE_TECHNICAL"}

    def test_design_not_approved_cannot_close(self):
        self.continuity["course_design_status"] = "DESIGN_PROPOSED"
        self.continuity["approved_design_revision"] = None
        errors = validate_candidate_closure(self.continuity, [], "M0", SHA)
        self.assertTrue(any("approved design revision" in e for e in errors), errors)

    def test_no_gates_cannot_close(self):
        errors = validate_candidate_closure(self.continuity, [], "M0", SHA)
        self.assertTrue(any("missing required gate G-DEPLOY" in e for e in errors), errors)

    def test_wrong_sha_cannot_close(self):
        gate = {
            "gate_id": "G-DEPLOY", "module_id": "M0", "input_hash": "synthetic",
            "acceptance_revision": "v4.1", "evidence_level": "E1",
            "result": "PASS", "commands": ["deploy"], "logs": ["synthetic-only"],
            "observed_at": "2026-11-23T00:00:00Z", "reviewer": "ci",
            "limitations": [], "commit_sha": "b"*40,
            "workflow_run_id": "synthetic", "deployment_sha": "b"*40
        }
        errors = validate_candidate_closure(self.continuity, [gate], "M0", SHA)
        self.assertTrue(any("SHA mismatch" in e for e in errors), errors)

    def test_checkpoint_not_done(self):
        self.continuity["module_states"]["M0"] = "IN_PROGRESS"
        errors = validate_candidate_closure(self.continuity, [], "M0", SHA)
        self.assertTrue(any("not DONE_TECHNICAL" in e for e in errors), errors)

    def test_target_sha_is_full(self):
        errors = validate_candidate_closure(self.continuity, [], "M0", "short")
        self.assertTrue(any("full lowercase Git SHA" in e for e in errors), errors)

    def test_not_applicable_must_be_recorded(self):
        errors = validate_candidate_closure(self.continuity, [], "M0", SHA, {"G-LAB": "NOT_APPLICABLE"})
        self.assertTrue(any("justified NOT_APPLICABLE" in e for e in errors), errors)

    def test_duplicate_gates_rejected(self):
        gate = json.loads((ROOT / "examples/gate.json").read_text())
        gate["module_id"] = "M0"
        errors = validate_candidate_closure(self.continuity, [gate, copy.deepcopy(gate)], "M0", SHA)
        self.assertTrue(any("duplicate gate" in e for e in errors), errors)

if __name__ == "__main__":
    unittest.main()
