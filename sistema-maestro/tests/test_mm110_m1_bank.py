"""Independent explicit answer fixtures for all initial M1 items."""
import sys
import unittest
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_m1_activities import ITEMS, INDEX, assess_math, public_item, reduced_form, assess, public_assessment

# Authored independently of the bank's expected field; positive and negative answers.
CASES = (
("m1-f02-a-1",3,2),
("m1-f02-b-2","-5","5"),
("m1-f02-c-3",2,4),
("m1-f02-c-4","0","1"),
("m1-f02-t-5",1,3),
("m1-f02-e-6",None,0),
("m1-f03-a-1","5x^2","5x^4"),
("m1-f03-b-2","3x^2+3x-5","3x^2+3x+5"),
("m1-f03-c-3","3x^2-7x+10","3x^2+3x+4"),
("m1-f03-c-4","6x-1","-2x-1"),
("m1-f03-t-5","4x^2+5x-8","4x^2+5x+8"),
("m1-f03-e-6","2x-2","14x^3+2x-2"),
("m1-f04-a-1","-6x^3","-6x^2"),
("m1-f04-b-2","2x^2+6x","2x^2+3"),
("m1-f04-c-3","2x^2+7x-15","2x^2+13x-15"),
("m1-f04-c-4","x^3-5x+2","x^3-5x-2"),
("m1-f04-t-5","2x^2+5x+2","2x^2+2"),
("m1-f04-e-6","3x^2-10x-8","3x^2-8"),
("m1-f05-a-1","x^2+6x+9","x^2+9"),
("m1-f05-b-2","x^2-49","x^2+49"),
("m1-f05-c-3","4x^2-12x+9","4x^2+9"),
("m1-f05-c-4","x^3-6x^2+12x-8","x^3-8"),
("m1-f05-t-5","20x","10x"),
("m1-f05-e-6","9x^2+12x+4","9x^2+4"),
("m1-f06-a-1",["x","x+3"],["1","x^2+3x"]),
("m1-f06-b-2",["x+4","x-4"],["x+4","x+4"]),
("m1-f06-c-3",["x+3","2x+1"],["2x+3","x+1"]),
("m1-f06-c-4",["x+2","x^2-9"],["x+2","x^2+9"]),
("m1-f06-t-5",["x+3","x+5"],["x+1","x+15"]),
("m1-f06-e-6",["x-3","x^2+3x+9"],["x-3","x^2-3x+9"]),
("m1-f07-a-1",["x+3","0"],["x+2","0"]),
("m1-f07-b-2",["x+3","1"],["x+2","1"]),
("m1-f07-c-3",["x^2+x-1","0"],["x^2-1","0"]),
("m1-f07-c-4",["x^2+1","2"],["x^2","x^2+3"]),
("m1-f07-t-5",["x^2-x+5","-2"],["x^2-x+5","2"]),
("m1-f07-e-6",["2x^2-x+1","-6"],["2x^2-x+1","6"]),
)

class M1BankTests(unittest.TestCase):
    def test_inventory(self):
        self.assertEqual(len(ITEMS),36)
        self.assertEqual(set(INDEX),{x[0] for x in CASES})
        for family in ("F02","F03","F04","F05","F06","F07"):
            self.assertEqual(Counter(i["stage"] for i in ITEMS if i["family"]==family),
                             Counter({"A":1,"B":1,"C":2,"T":1,"E":1}))
    def test_public_fields(self):
        for item in ITEMS:
            with self.subTest(id=item["id"]):
                self.assertEqual(set(public_item(item["id"])),{"id","family","stage","operation","prompt","reasoning_prompt","choices"})
    def test_required_form(self):
        cases=[("m1-f04-c-3","(2x-3)(x+5)"),
               ("m1-f04-c-3","2x^2+10x-3x-15"),
               ("m1-f03-a-1","8x^2-3x^2"),
               ("m1-f05-c-4","(x-2)^3"),
               ("m1-f07-c-4",["x^2+2-1","2"])]
        for item,answer in cases:
            with self.subTest(item=item,answer=answer):
                v=assess_math(item,answer)
                self.assertEqual((v.status,v.reason),("REJECTED","REQUIRED_REDUCED_FORM"))
    def test_alternative_forms(self):
        for item,answer in [("m1-f04-c-3","-15+7x+2x^2"),
                            ("m1-f04-c-3","2*x^2+7*x-15"),
                            ("m1-f06-b-2",["2x-8","1/2x+2"])]:
            with self.subTest(item=item,answer=answer):
                self.assertEqual(assess_math(item,answer).status,"VERIFIED")
    def test_limits_and_invalid(self):
        for item,answer,status in [
            ("m1-f02-a-1",True,"REJECTED"),
            ("m1-f02-b-2","x-x-5","REJECTED"),
            ("m1-f04-c-3","x"*257,"INCONCLUSIVE"),
            ("m1-f07-c-4",["x^2+1"],"REJECTED"),
            ("m1-f06-b-2",["x-4","x+4","1"],"REJECTED")]:
            with self.subTest(item=item,answer=answer):
                self.assertEqual(assess_math(item,answer).status,status)

def make_test(item,correct,wrong):
    def test(self):
        self.assertEqual(assess_math(item,correct).status,"VERIFIED")
        self.assertEqual(assess_math(item,INDEX[item]["expected"]).status,"VERIFIED")
        self.assertEqual(assess_math(item,wrong).status,"REJECTED")
    return test

for item,correct,wrong in CASES:
    setattr(M1BankTests,"test_"+item.replace("-","_"),make_test(item,correct,wrong))

class M1ReasoningTests(unittest.TestCase):
    def test_all_items_reasoning(self):
        # Independently specified correct option indices for the current 36 items.
        keys=(0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2,0,1,2)
        for (item,correct,wrong),key in zip(CASES,keys):
            with self.subTest(item=item):
                data=INDEX[item]
                self.assertEqual(data["correct_reason"],key)
                self.assertEqual(len(set(data["choices"])),3)
                good=assess(item,correct,key)
                bad_reason=assess(item,correct,(key+1)%3)
                bad_math=assess(item,wrong,key)
                if data["stage"]=="E":
                    for result in (good,bad_reason,bad_math):
                        self.assertEqual(public_assessment(result),{"status":"RECORDED"})
                    self.assertTrue(good["private_assessment"]["accepted"])
                    self.assertFalse(bad_reason["private_assessment"]["accepted"])
                    self.assertFalse(bad_math["private_assessment"]["accepted"])
                else:
                    self.assertTrue(good["accepted"])
                    self.assertFalse(bad_reason["accepted"])
                    self.assertFalse(bad_math["accepted"])
                    self.assertEqual(good["eligible_evidence"],data["stage"] in ("C","T"))
                    self.assertFalse(assess(item,correct,key,True)["eligible_evidence"])
    def test_reasoning_input(self):
        for reason in (True,None,"0",-1,3):
            with self.assertRaises(ValueError):
                assess("m1-f02-a-1",3,reason)
        with self.assertRaises(ValueError):
            assess("m1-f02-e-6",None,2,True)
    def test_retry_and_invalid_do_not_reveal_solution(self):
        self.assertEqual(assess("m1-f04-c-3","x"*257,2),{"status":"RETRY"})
        self.assertEqual(assess("m1-f02-a-1",True,0),{"status":"INVALID_INPUT"})
