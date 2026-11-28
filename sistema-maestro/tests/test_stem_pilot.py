import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"stem"))
from pilot import PILOT, reference, validate, canonical_fingerprint

class StemPilotTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(PILOT.read_text(encoding="utf-8"))
    def test_frozen_cases(self):
        for case in self.data["cases"]:
            with self.subTest(id=case["id"]):
                self.assertEqual(str(reference(case["stimulus"])),case["expected"])
        self.assertEqual(len(validate(self.data)),3)
    def test_mutants_rejected(self):
        for field,value in [("expected","99"),("expression","sqrt(0)"),("stimulus","Calcula √(2/3) + 7/17 − 12/17.")]:
            with self.subTest(field=field):
                mutant=copy.deepcopy(self.data)
                mutant["cases"][0][field]=value
                with self.assertRaises(ValueError):
                    validate(mutant)
        mutant=copy.deepcopy(self.data)
        mutant["cases"].append(mutant["cases"][0])
        with self.assertRaises(ValueError):
            validate(mutant)
    def test_zero_denominator_rejected(self):
        with self.assertRaises(ValueError):
            reference("Calcula √(9/0) + 7/17 − 12/17.")
    def test_fingerprint_changes_per_dependency(self):
        inputs=dict(repository="p",scope="s",criterion_revision="1",oracle_revision="1",source_hash="a"*64,dependency_hash="b"*64,environment="python")
        original=canonical_fingerprint(inputs)
        self.assertEqual(original,canonical_fingerprint(dict(reversed(list(inputs.items())))))
        for field in inputs:
            changed=dict(inputs)
            changed[field]="c"*64 if field.endswith("_hash") else "changed"
            self.assertNotEqual(original,canonical_fingerprint(changed))
        del inputs["environment"]
        with self.assertRaises(ValueError):
            canonical_fingerprint(inputs)
