"""Negative tests for v4.3 curricular provenance, independent of live web access."""
import copy
import sys
import unittest
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from validate_reconstructed_curriculum import validate_dossier

class ReconstructionTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((ROOT/"examples/reconstructed_curriculum_synthetic.json").read_text(encoding="utf-8"))

    def test_synthetic_fixture_passes_structure_not_official_claim(self):
        self.assertEqual(validate_dossier(self.data), [])
        self.assertEqual(self.data["adoption_status"],"PENDING_HUMAN_APPROVAL")

    def test_correlated_duplicates_cannot_corroborate(self):
        self.data["sources"][1]["origin_id"]=self.data["sources"][0]["origin_id"]
        self.assertTrue(any("independently" in e for e in validate_dossier(self.data)))

    def test_inaccessible_document_cannot_count_as_read(self):
        self.data["sources"][1]["access_status"]="NOT_ACCESSIBLE"
        self.assertTrue(validate_dossier(self.data))

    def test_uninspected_official_mention_not_confirmation(self):
        self.data["claims"][0]["classification"]="INSTITUTIONALLY_CONFIRMED"
        self.assertTrue(any("institutional" in e for e in validate_dossier(self.data)))

    def test_official_result_requires_institutional_claim(self):
        self.data["provenance"]="OFFICIAL_VERIFIED"
        self.assertTrue(any("OFFICIAL_VERIFIED" in e for e in validate_dossier(self.data)))

    def test_other_university_without_two_sources_is_not_core_corroboration(self):
        self.data["claims"][0]["source_ids"]=["s2"]
        self.assertTrue(validate_dossier(self.data))

    def test_unknown_source_reference_rejected(self):
        self.data["claims"][0]["source_ids"]=["missing","s2"]
        self.assertTrue(any("unknown source" in e for e in validate_dossier(self.data)))

    def test_inferred_without_independent_core_evidence_cannot_propose(self):
        self.data["claims"][0]["classification"]="ACADEMICALLY_INFERRED"
        self.assertTrue(any("Curricular core" in e for e in validate_dossier(self.data)))

    def test_unapproved_program_cannot_self_approve(self):
        self.data["adoption_status"]="APPROVED"
        self.assertTrue(validate_dossier(self.data))

    def test_missing_unit_claim_rejected(self):
        self.data["units"][0]["claim_ids"]=["unknown"]
        self.assertTrue(any("unknown claim" in e for e in validate_dossier(self.data)))

    def test_research_insufficient_may_have_no_core(self):
        self.data["provenance"]="RESEARCH_INSUFFICIENT"
        self.data["claims"]=[]
        self.data["units"]=[]
        self.assertEqual(validate_dossier(self.data),[])

if __name__=="__main__":
    unittest.main()
