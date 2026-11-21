"""Additional v4.1 negative tests for gate semantics and checkpoint validation."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_academia_play import validate_continuity, validate_event, validate_gate


def fixture(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


class TestV41Operational(unittest.TestCase):
    def test_valid_continuity(self):
        root = ROOT.parents[0] / "continuity.json"
        self.assertEqual(validate_continuity(json.loads(root.read_text())), [])

    def test_design_approval_requires_revision(self):
        root = ROOT.parents[0] / "continuity.json"
        x = json.loads(root.read_text())
        x["course_design_status"] = "DESIGN_APPROVED"
        x["approved_design_revision"] = None
        self.assertTrue(validate_continuity(x))

    def test_valid_event(self):
        self.assertEqual(validate_event(fixture("execution_event.json")), [])

    def test_invalid_event_level(self):
        x = fixture("execution_event.json")
        x["evidence_level"] = "E99"
        self.assertTrue(validate_event(x))

    def test_lab_not_applicable_needs_reason(self):
        x = fixture("gate.json")
        x["gate_id"] = "G-LAB"
        x["result"] = "NOT_APPLICABLE"
        x["limitations"] = []
        self.assertTrue(validate_gate(x))
        x["limitations"] = ["No se requiere laboratorio en objetivo textual sin simulacion."]
        self.assertEqual(validate_gate(x), [])

    def test_oracle_not_applicable_disallowed(self):
        x = fixture("gate.json")
        x["gate_id"] = "G-ORACLE"
        x["result"] = "NOT_APPLICABLE"
        self.assertTrue(validate_gate(x))

    def test_manual_a11y_pass_needs_reviewer(self):
        x = fixture("gate.json")
        x.update({"gate_id": "G-A11Y-MANUAL",
                  "result": "PASS", "evidence_level": "E1",
                  "commands": ["manual acceptance"],
                  "logs": ["evidence/a11y-test.json"],
                  "reviewer": "unassigned"})
        self.assertTrue(validate_gate(x))

    def test_human_certification_not_automatic(self):
        x = fixture("gate.json")
        x.update({"gate_id": "G-ACADEMIC", "result": "PASS",
                  "evidence_level": "E1", "commands": ["self-attest"],
                  "logs": ["synthetic"], "reviewer": "agent"})
        self.assertTrue(validate_gate(x))

    def test_checkpoint_rejects_missing_render_id(self):
        root = ROOT.parents[0] / "continuity.json"
        x = json.loads(root.read_text())
        x["render_service_id"] = None
        self.assertTrue(validate_continuity(x))

if __name__ == "__main__":
    unittest.main()
