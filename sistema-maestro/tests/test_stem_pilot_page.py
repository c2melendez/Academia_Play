import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_pilot_page import render_pilot_page,MARKER

class SharedPilotPageTests(unittest.TestCase):
    def test_both_pilots_load_same_renderer(self):
        for name in ("mm110_f01.html","mm110_m1.html"):
            html=render_pilot_page(name).decode()
            self.assertEqual(html.count("function renderStemAreaGrid("),1)
            self.assertNotIn(MARKER,html)
    def test_reject_unknown_template(self):
        with self.assertRaises(ValueError):
            render_pilot_page("../continuity.json")
