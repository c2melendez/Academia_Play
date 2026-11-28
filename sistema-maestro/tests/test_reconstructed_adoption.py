"""Regression tests for reconstructed curriculum adoption; no invented official syllabus."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import validate_academia_play as validator

class ReconstructedAdoptionTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / 'examples/manifest.json').read_text(encoding='utf8'))
        self.docs = ROOT / 'docs/mm110'
        self.dossier = self.docs / 'MM110_RECONSTRUCCION_CURRICULAR.json'
        self.approval = self.docs / 'MM110_REVISION_F01.json'
        self.revision = json.loads(self.approval.read_text(encoding='utf8'))['design_revision_id']
        self.source = {
            'source_id': 'mm110-reconstruction',
            'kind': 'RECONSTRUCTED',
            'edition': 'reconstructed proposal, not official',
            'license_status': 'STRUCTURE_ONLY',
            'sha256': hashlib.sha256(self.dossier.read_bytes()).hexdigest(),
            'inspected_pages': [],
            'verification': 'OPENED',
            'reconstruction': {
                'dossier_path': str(self.dossier.relative_to(ROOT.parent)),
                'approval_path': str(self.approval.relative_to(ROOT.parent)),
                'design_revision_id': self.revision,
            },
        }
        # The legacy demo remains a synthetic fixture; only its course-source
        # linkage is exercised here. It is NOT the real MM110 manifest.
        self.manifest['institutions'][0]['name'] = 'Universidad Nacional Autónoma de Honduras'
        self.manifest['sources'].append(self.source)
        self.manifest['courses'][0]['syllabus_source_id'] = self.source['source_id']

    def test_legacy_manifest(self):
        old = json.loads((ROOT / 'examples/manifest.json').read_text(encoding='utf8'))
        self.assertEqual([], validator.validate_manifest(old))

    def test_pinned_real_adoption(self):
        self.assertEqual([], validator.validate_manifest(self.manifest))

    def assert_rejected(self, fragment):
        errors = validator.validate_manifest(self.manifest)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_dossier_hash_mutation(self):
        self.source['sha256'] = '0' * 64
        self.assert_rejected('dossier SHA-256 mismatch')

    def test_revision_mutation(self):
        self.source['reconstruction']['design_revision_id'] = '0' * 64
        self.assert_rejected('missing approved design revision')

    def test_missing_dossier(self):
        self.source['reconstruction']['dossier_path'] = 'sistema-maestro/docs/nonexistent.json'
        self.assert_rejected('artifact must exist')

    def test_path_outside_docs(self):
        self.source['reconstruction']['approval_path'] = 'continuity.json'
        self.assert_rejected('artifact must exist')

    def test_wrong_institution(self):
        self.manifest['institutions'][0]['name'] = 'Otra institución'
        self.assert_rejected('institution mismatch')

    def test_no_approval_metadata(self):
        del self.source['reconstruction']
        self.assert_rejected('schema:')

    def test_fictitious_pages(self):
        self.source['inspected_pages'] = [1]
        self.assert_rejected('schema:')

    def test_unopened(self):
        self.source['verification'] = 'NOT_VERIFIED'
        self.assert_rejected('schema:')

    def test_wrong_license(self):
        self.source['license_status'] = 'OWNED'
        self.assert_rejected('schema:')

    def test_mutated_approval_or_design(self):
        # Redirect the artifact root to a temporary sandbox; schema and dossier
        # validator retain their actual repository paths.
        with tempfile.TemporaryDirectory() as tmp:
            fake_root = Path(tmp) / 'sistema-maestro'
            fake_docs = fake_root / 'docs/mm110'
            fake_docs.mkdir(parents=True)
            for p in self.docs.iterdir():
                if p.is_file():
                    (fake_docs / p.name).write_bytes(p.read_bytes())
            ap = fake_docs / self.approval.name
            original = ap.read_bytes()
            data = json.loads(original)
            data['approval_status'] = 'PENDING_HUMAN_APPROVAL'
            ap.write_text(json.dumps(data), encoding='utf8')
            with patch.object(validator, 'ROOT', fake_root):
                self.assert_rejected('missing approved design revision')
                ap.write_bytes(original)
                design = fake_root.parent / data['design_path']
                design.write_text(design.read_text(encoding='utf8') + '\nCambio material\n', encoding='utf8')
                self.assert_rejected('design SHA-256 mismatch')

if __name__ == '__main__':
    unittest.main()
