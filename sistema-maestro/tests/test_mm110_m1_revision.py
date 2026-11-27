"""Check the pending design reference against exact canonical bytes."""
import hashlib
import json
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "docs" / "mm110"

class M1RevisionTests(unittest.TestCase):
    def test_design_digest_and_pending_approval(self):
        record = json.loads((ROOT / "MM110_REVISION_M1_PROPUESTA.json").read_text(encoding="utf-8"))
        design = (ROOT / "MM110_M1_DISENO_PROPUESTO.md").read_text(encoding="utf-8")
        canonical = unicodedata.normalize("NFC", design).replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n"
        self.assertEqual(hashlib.sha256(canonical.encode("utf-8")).hexdigest(), record["design_revision_id"])
        self.assertEqual("DESIGN_PROPOSED", record["status"])
        self.assertEqual("PENDING_HUMAN_APPROVAL", record["approval_status"])
        self.assertIsNone(record["approval"])
        self.assertIn("No M1 curricular implementation authorized", record["limitations"])
