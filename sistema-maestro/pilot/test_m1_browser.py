"""Real Chromium and axe checks for the local formative M1 pilot."""
import json
import os
import sys
import threading
import tempfile
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_m1_http import Server
from mm110_m1_store import Store

CASES=(
    ("F02",1,3,"m1-f02-c-3",["2"],2),
    ("F03",2,3,"m1-f03-c-3",["3x^2-7x+10"],2),
    ("F04",0,2,"m1-f04-c-3",["2x^2+7x-15"],2),
    ("F05",1,2,"m1-f05-c-3",["4x^2-12x+9"],2),
    ("F06",2,3,"m1-f06-c-3",["2x+1","x+3"],2),
    ("F07",0,2,"m1-f07-c-4",["x^2+1","2"],0),
)

class BrowserM1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmp=tempfile.TemporaryDirectory()
        cls.addClassCleanup(tmp.cleanup)
        cls.server=Server(("127.0.0.1",0),Store(Path(tmp.name)/"m1.sqlite"))
        thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        thread.start()
        def stop():
            cls.server.shutdown()
            cls.server.server_close()
            thread.join(timeout=5)
        cls.addClassCleanup(stop)
        cls.pw=sync_playwright().start()
        cls.addClassCleanup(cls.pw.stop)
        cls.browser=cls.pw.chromium.launch()
        cls.addClassCleanup(cls.browser.close)
        cls.url="http://127.0.0.1:"+str(cls.server.server_port)

    def setUp(self):
        self.context=self.browser.new_context(viewport={"width":390,"height":844})
        self.addCleanup(self.context.close)
        self.page=self.context.new_page()
        self.errors=[]
        self.page.on("pageerror",lambda e:self.errors.append(str(e)))
        self.page.goto(self.url)
        expect(self.page.locator("#review-title")).to_contain_text("F02")
        expect(self.page.locator("#activity")).to_be_enabled()

    def tearDown(self):
        self.assertEqual([],self.errors)

    def family(self,f):
        self.page.locator('button[data-family="'+f+'"]').click()
        expect(self.page.locator("#review-title")).to_contain_text(f)
        expect(self.page.locator("#activity")).to_be_enabled()
        expect(self.page.locator("#worked")).to_be_hidden()
        expect(self.page.locator("#activity option")).to_have_count(7)

    def predict(self,key,count):
        self.page.locator('input[name="prediction-choice"]').nth(key).check()
        self.page.locator("#prediction button").click()
        expect(self.page.locator("#review-feedback")).to_contain_text("Correcto.")
        expect(self.page.locator("#rows tr")).to_have_count(1)
        for i in range(2,count+1):
            self.page.locator("#next-step").click()
            expect(self.page.locator("#rows tr")).to_have_count(i)
        expect(self.page.locator("#next-step")).to_be_disabled()

    def submit(self,item,answers,reason):
        self.page.locator("#activity").select_option(item)
        for i,answer in enumerate(answers):
            self.page.locator("#ans"+str(i)).fill(answer)
        self.page.locator('input[name="reason"]').nth(reason).check()
        self.page.locator("#assessment button").click()
        expect(self.page.locator("#result")).to_be_visible()
        expect(self.page.locator("#assessment button")).to_be_enabled()

    def audit(self,state):
        self.page.evaluate(Path(os.environ["F01_AXE_PATH"]).read_text(encoding="utf8"))
        result=self.page.evaluate("""async () => await axe.run(document, {
            runOnly: {type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}
        })""")
        violations=[v["id"] for v in result["violations"]]
        print("M1_AXE "+json.dumps({"state":state,"passes":len(result["passes"]),
              "incomplete":[v["id"] for v in result["incomplete"]],"violations":violations}),flush=True)
        self.assertGreater(len(result["passes"]),0)
        self.assertEqual([],violations)

    def test_six_families_end_to_end(self):
        for f,key,count,item,answers,reason in CASES:
            with self.subTest(family=f):
                self.family(f)
                self.predict(key,count)
                self.submit(item,answers,reason)
                expect(self.page.locator("#result")).to_contain_text("Correcto.")
                self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
                self.audit(f+"-worked-and-assessed")

    def test_rejected_answer_and_reason(self):
        self.family("F04")
        self.submit("m1-f04-c-3",["(2x-3)(x+5)"],2)
        expect(self.page.locator("#result")).to_contain_text("debes desarrollar")
        self.submit("m1-f04-c-3",["2x^2+7x-15"],0)
        expect(self.page.locator("#result")).to_contain_text("revisa el fundamento")
        self.submit("m1-f04-c-3",["2x^2+7x-15"],2)
        expect(self.page.locator("#result")).to_contain_text("Correcto.")

    def test_api_boundary(self):
        result=self.page.evaluate("""async () => {
          const catalog=await (await fetch('/api/m1/catalog')).json();
          const review=await (await fetch('/api/m1/review/F02')).json();
          const post=async (path,body)=>fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
          const forbidden=await post('/api/m1/assess',{item_id:'m1-f02-e-6',answer:null,reason_choice:2});
          const formative=await (await post('/api/m1/assess',{item_id:'m1-f02-c-3',answer:2,reason_choice:2})).json();
          return {catalog,review,forbidden:forbidden.status,formative};
        }""")
        self.assertEqual(len(result["catalog"]["items"]),42)
        self.assertTrue(all(i["stage"]!="E" and "expected" not in i and "correct_reason" not in i for i in result["catalog"]["items"]))
        self.assertNotIn("rows",result["review"])
        self.assertNotIn("correct",result["review"])
        self.assertEqual(result["forbidden"],403)
        self.assertTrue(result["formative"]["accepted"])
        self.assertTrue(result["formative"]["assisted"])
        self.assertFalse(result["formative"]["eligible_evidence"])

    def test_keyboard_and_initial_accessibility(self):
        self.audit("initial-mobile")
        self.page.locator('button[data-family="F07"]').focus()
        self.page.keyboard.press("Enter")
        expect(self.page.locator("#review-title")).to_contain_text("F07")
        expect(self.page.locator("#activity")).to_be_enabled()
        expect(self.page.locator("#review-title")).to_be_focused()
        self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))

    def test_persistent_progress(self):
        self.family("F04")
        self.submit("m1-f04-c-3",["2x^2+7x-15"],2)
        expect(self.page.locator("#progress")).to_contain_text("1 de 42")
        self.page.reload()
        expect(self.page.locator("#progress")).to_contain_text("1 de 42")
        other=self.browser.new_context()
        self.addCleanup(other.close)
        page=other.new_page()
        page.goto(self.url)
        expect(page.locator("#progress")).to_contain_text("0 de 42")

    def test_exam_reload_and_deferred_review(self):
        self.page.locator("#start-exam").click()
        expect(self.page.locator("#exam-count")).to_contain_text("0 de 6")
        expect(self.page.locator("#review")).to_be_hidden()
        expect(self.page.locator("#practice")).to_be_hidden()
        expect(self.page.locator("#finish-exam")).to_be_hidden()
        self.assertEqual(self.page.evaluate("async () => (await fetch('/api/m1/review/F02')).status"),403)
        self.page.locator("#exam-undefined").check()
        self.page.get_by_label("No queda ningún término de coeficiente no nulo",exact=True).check()
        self.page.locator("#exam-form button").click()
        expect(self.page.locator("#exam-count")).to_contain_text("1 de 6")
        expect(self.page.locator("#exam-review")).to_be_hidden()
        self.page.reload()
        expect(self.page.locator("#exam-count")).to_contain_text("1 de 6")
        self.audit("exam-active-recovered")
        for n,(answers,reason) in enumerate([
            (["2x-2"],"Sus coeficientes son opuestos"),
            (["3x^2-10x-8"],"Los productos cruzados suman -10x"),
            (["9x^2+12x+4"],"Del doble producto de 3x y 2"),
            (["x-3","x^2+3x+9"],"La diferencia de cubos"),
            (["2x^2-x+1","-6"],"Dividendo = divisor por cociente más residuo, con grado del residuo menor")
        ],2):
            for i,answer in enumerate(answers):
                self.page.locator("#exam-ans"+str(i)).fill(answer)
            self.page.locator('input[name="exam-reason"]').nth(2).check()
            self.page.locator("#exam-form button").click()
            expect(self.page.locator("#exam-count")).to_contain_text(str(n)+" de 6")
            expect(self.page.locator("#exam-review")).to_be_hidden()
        expect(self.page.locator("#finish-exam")).to_be_visible()
        self.page.reload()
        expect(self.page.locator("#finish-exam")).to_be_visible()
        self.page.locator("#finish-exam").click()
        expect(self.page.locator("#exam-score")).to_contain_text("6 de 6")
        expect(self.page.locator("#exam-reviews li")).to_have_count(6)
        self.audit("exam-finished")
        self.page.locator("#back-study").click()
        expect(self.page.locator("#review")).to_be_visible()
        self.page.locator("#start-exam").click()
        expect(self.page.locator("#exam-count")).to_contain_text("0 de 6")
        expect(self.page.locator("#exam-prompt")).to_contain_text("3x^3-3x^3+7")
