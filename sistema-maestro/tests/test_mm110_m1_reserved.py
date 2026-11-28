"""Reserved bank: independent mathematical fixtures, first-exposure controls."""
import sys
import tempfile
import unittest
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_m1_activities import INDEX, RESERVED, RESERVED_INDEX, assess_reserved, public_item
from mm110_m1_store import Store

# Independent answer / incorrect answer / canonical conceptual option.
FIXTURES = {
"F02": [(3,5,1),(None,0,2),("-2","2",0),("0","1",2),(0,None,1),(1,3,0)],
"F03": [("2x^3+5x^2+6","2x^3+5x^2+8x+6",2),("x^2-3x+2","1/2x^2-3x+2",0),("-x^3+3x^2+5","-x^3-7x^2-3",1),("3x^2-5x-5","3x^2+5x-9",2),("5x^2+6x+5","5x^2-2x+5",0),("5x^3+5x-3","5x^3+5x+19",1)],
"F04": [("-6x^4+2x^3-8x^2","-6x^4-2x^3-8x^2",2),("3x^3-6x^2+9x","3x^2-6x+9",1),("2x^2-11x-21","2x^2-17x-21",0),("x^3+4x^2+x-6","x^3+4x^2+3x-6",2),("2x^2+13x+20","2x^2+20",1),("3x^2+17x-6","3x^2+19x-6",0)],
"F05": [("16x^2-8x+1","16x^2+1",1),("x^2-81","x^2+81",2),("x^3+12x^2+48x+64","x^3+64",0),("27x^3-27x^2+9x-1","27x^3-1",1),("28x","14x",2),("6x+9","9",0)],
"F06": [(["5x","x+3"],["5x","x-3"],1),(["3x-5","3x+5"],["3x-5","3x-5"],2),(["3x+1","2x+3"],["3x+3","2x+1"],0),(["x+5","x^2+4"],["x+5","x^2-4"],1),(["x+4","x+7"],["x+2","x+14"],2),(["2x","x+5"],["2x","x-5"],0)],
"F07": [(["x^2+x-6","7"],["x^2+x-6","-7"],1),(["2x^2-x","-5"],["2x^2-x","5"],2),(["x^2+1","5"],["x^2","x^2+7"],0),(["0","3x^2+2"],["1","3x^2+2"],1),(["2x^2+x+2","2"],["2x^2+x+2","-2"],2),(["x^2","x+5"],["x^2+1","-x^2-x+5"],0)]
}

def key_for(item):
    slot=RESERVED_INDEX[item["id"]]["slot"]
    n=int(item["id"].rsplit("-",1)[1])-1
    correct,wrong,canonical=FIXTURES[item["family"]][("C1","C2","T").index(slot)*2+n]
    return correct,wrong,item["choices"].index(RESERVED_INDEX[item["id"]]["choices"][canonical])

class ReservedTests(unittest.TestCase):
    def test_inventory_and_isolation(self):
        self.assertEqual(len(RESERVED),36)
        self.assertEqual(len(RESERVED_INDEX),36)
        self.assertFalse(set(INDEX)&set(RESERVED_INDEX))
        for family in FIXTURES:
            self.assertEqual(Counter(i["slot"] for i in RESERVED if i["family"]==family),{"C1":2,"C2":2,"T":2})
        for item in RESERVED:
            with self.assertRaises(KeyError):
                public_item(item["id"])

    def test_all_reserved_items(self):
        for family,fixtures in FIXTURES.items():
            for k,(answer,wrong,key) in enumerate(fixtures):
                item=f"m1-{family.lower()}-reserve-{('c1','c2','t')[k//2]}-{k%2+1}"
                with self.subTest(item=item):
                    self.assertEqual(RESERVED_INDEX[item]["correct_reason"],key)
                    self.assertTrue(assess_reserved(item,answer,key)["eligible_evidence"])
                    self.assertTrue(assess_reserved(item,RESERVED_INDEX[item]["expected"],key)["accepted"])
                    self.assertFalse(assess_reserved(item,wrong,key)["eligible_evidence"])
                    self.assertFalse(assess_reserved(item,answer,(key+1)%3)["eligible_evidence"])

    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path=Path(temp.name)/"m1.sqlite"
        self.store=Store(self.path)

    def finish_route(self,learner):
        for item,answer,key in [
            ("m1-f03-a-1","5x^2",0),("m1-f03-b-2","3x^2+3x-5",1),
            ("m1-f03-c-3","3x^2-7x+10",2),("m1-f03-c-4","6x-1",0),
            ("m1-f03-t-5","4x^2+5x-8",1)
        ]:
            a=self.store.guided_start(learner,"F03",item)
            self.assertTrue(self.store.submit(learner,a["attempt_id"],answer,key)["accepted"])

    def test_reserved_resume_first_exposure_and_slot_sequence(self):
        with self.assertRaises(ValueError):
            self.store.reserved_start("a","F03")
        self.finish_route("a")
        a=self.store.reserved_start("a","F03")
        self.assertNotIn("expected",a)
        self.assertNotIn("correct_reason",a)
        self.assertEqual(a,Store(self.path).reserved_active("a"))
        self.assertEqual(a,Store(self.path).reserved_start("a","F03"))
        with self.assertRaises(KeyError):
            self.store.reserved_submit("b",a["attempt_id"],"0",0)
        with self.assertRaises(ValueError):
            self.store.start_exam("a")
        with self.assertRaises(ValueError):
            self.store.assess_formative("a","m1-f03-a-1","5x^2",0)
        good,wrong,key=key_for(a)
        result=self.store.reserved_submit("a",a["attempt_id"],wrong,key)
        self.assertFalse(result["eligible_evidence"])
        with self.assertRaises(ValueError):
            self.store.reserved_submit("a",a["attempt_id"],good,key)
        b=self.store.reserved_start("a","F03")
        self.assertNotEqual(a["id"],b["id"])
        for slot in ("C1","C2","T"):
            b=self.store.reserved_start("a","F03")
            self.assertEqual(RESERVED_INDEX[b["id"]]["slot"],slot)
            good,wrong,key=key_for(b)
            result=self.store.reserved_submit("a",b["attempt_id"],good,key)
            self.assertTrue(result["eligible_evidence"])
            self.assertEqual(result,self.store.reserved_submit("a",b["attempt_id"],good,key))
        view=self.store.reserved_progress("a","F03")
        self.assertEqual(view["credited_slots"],["C1","C2","T"])
        self.assertEqual(view["status"],"EVIDENCE_COLLECTED")
        self.assertEqual(view["mastery"],"UNASSESSED")

    def test_exhaustion_does_not_award_credit(self):
        self.finish_route("a")
        for _ in range(2):
            a=self.store.reserved_start("a","F03")
            good,wrong,key=key_for(a)
            self.assertFalse(self.store.reserved_submit("a",a["attempt_id"],wrong,key)["eligible_evidence"])
        view=self.store.reserved_progress("a","F03")
        self.assertEqual(view["status"],"EXHAUSTED")
        self.assertEqual(view["credited_slots"],[])
        with self.assertRaises(ValueError):
            self.store.reserved_start("a","F03")
