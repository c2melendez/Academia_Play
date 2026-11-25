"""Integration checks for the approved real MM110 F01 planned manifest."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_academia_play import validate_manifest

class MM110ManifestTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'docs/mm110/MM110_MANIFEST.json').read_text(encoding='utf8'))

    def test_real_manifest(self):
        self.assertEqual([], validate_manifest(self.data))

    def test_course_scope_and_provenance(self):
        course, = self.data['courses']
        self.assertEqual('unah-mm110', course['course_id'])
        self.assertEqual(['mm110-f01'], course['objective_ids'])
        source = next(s for s in self.data['sources'] if s['source_id'] == course['syllabus_source_id'])
        self.assertEqual('RECONSTRUCTED', source['kind'])
        self.assertEqual([], source['inspected_pages'])

    def test_exam_is_independent(self):
        for a in self.data['activities']:
            ids = a['mode_item_ids']
            self.assertFalse(set(ids['exam_preparation']) & set(ids['learning_path'] + ids['practice_tutor']))
        self.assertEqual([], validate_manifest(self.data))

    def test_no_uninspected_textbook_page(self):
        self.data['objectives'][0]['source_refs'][0]['pages'].append(999999)
        self.assertTrue(any('pages not inspected' in e for e in validate_manifest(self.data)))

    def test_approval_revision_mutation(self):
        self.data['sources'][0]['reconstruction']['design_revision_id'] = '0' * 64
        self.assertTrue(any('missing approved design revision' in e for e in validate_manifest(self.data)))
