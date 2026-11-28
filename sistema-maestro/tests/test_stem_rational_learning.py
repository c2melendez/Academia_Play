import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"stem"))
from rational_learning import ASSET,verify

class RationalLearningTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(ASSET.read_text(encoding="utf-8"))
    def test_five_original_candidates(self):
        self.assertEqual(len(verify(self.data)),5)
    def test_wrong_key(self):
        task=self.data["route"]["lessons"][0]
        task["answer"]=task["options"][0]
        with self.assertRaises(ValueError): verify(self.data)
    def test_equivalent_distractor(self):
        task=self.data["route"]["lessons"][0]
        task["options"][0]=str(2*int(task["answer"].split("/")[0]))+"/"+str(2*int(task["answer"].split("/")[1]))
        with self.assertRaises(ValueError): verify(self.data)
    def test_transfer_cannot_leak_hint(self):
        self.data["route"]["transfer"][0]["hint"]="answer"
        with self.assertRaises(ValueError): verify(self.data)
    def test_no_automatic_certification(self):
        self.data["status"]="PASS"
        with self.assertRaises(ValueError): verify(self.data)
    def test_missing_error_explanation(self):
        self.data["route"]["lessons"][0]["errors"].clear()
        with self.assertRaises(ValueError): verify(self.data)
