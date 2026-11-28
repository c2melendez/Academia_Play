import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"stem"))
from mm110_inventory import INVENTORY,validate
class MM110ReuseInventoryTests(unittest.TestCase):
    def setUp(self): self.data=json.loads(INVENTORY.read_text(encoding="utf-8"))
    def test_all_seven_families(self): self.assertEqual(validate(self.data),[f"F{i:02d}" for i in range(1,8)])
    def test_missing_family(self):
        self.data["entries"].pop()
        with self.assertRaises(ValueError): validate(self.data)
    def test_unpinned_source(self):
        self.data["sources"][0]["commit"]="main"
        with self.assertRaises(ValueError): validate(self.data)
    def test_unknown_source(self):
        self.data["entries"][0]["source_ids"].append("missing")
        with self.assertRaises(ValueError): validate(self.data)
    def test_external_pass_transfer(self):
        self.data["entries"][0]["certification_transfer"]=True
        with self.assertRaises(ValueError): validate(self.data)
    def test_external_reuse_without_review(self):
        self.data["entries"][0]["decision"]="REUSE_LOCAL"
        with self.assertRaises(ValueError): validate(self.data)
