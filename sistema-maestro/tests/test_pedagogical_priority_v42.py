"""Regression: v4.2 mission prioritizes learning while preserving v4.1 safeguards."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "sistema-maestro"

class PedagogicalPriorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prompt = (SYSTEM / "PROMPT_MAESTRO.md").read_text(encoding="utf-8")
        cls.architecture = (SYSTEM / "docs/ARQUITECTURA_PEDAGOGICA_FUNDACIONAL_v4_2.md").read_text(encoding="utf-8")
        cls.runbook = (SYSTEM / "RUNBOOK.md").read_text(encoding="utf-8")
        cls.evidence = (SYSTEM / "docs/EVIDENCE_REGISTER.md").read_text(encoding="utf-8")

    def test_version_and_priority(self):
        self.assertEqual((SYSTEM / "VERSION").read_text(encoding="utf-8").strip(), "4.2.0")
        for word in ("currículo", "Fundamentos", "investigación", "Brilliant.org", "transferencia"):
            self.assertIn(word.casefold(), self.prompt.casefold())

    def test_foundational_contract_and_fallback(self):
        for token in ("FOUNDATION", "CONCEPTUAL_BRIDGE", "CURRICULAR_TARGET", "TRANSFER_EVIDENCE", "SOURCE_MISSING"):
            self.assertIn(token, self.architecture)

    def test_education_evidence_not_replaced_by_ci(self):
        self.assertIn("CI verde", self.prompt)
        self.assertIn("no aumenta", self.architecture.lower())
        self.assertIn("COURSE_PENDING", self.evidence)
        self.assertIn("NOT_VERIFIED", self.evidence)

    def test_preserves_approval_and_command_authority(self):
        self.assertIn("APROBAR_DISEÑO", self.prompt)
        self.assertIn("CONSTITUCION.md", self.prompt)
        self.assertIn("RUNBOOK.md", self.prompt)
        self.assertIn("GATES.md", self.prompt)
        self.assertIn("no altera semántica", self.runbook)

if __name__ == "__main__":
    unittest.main()
