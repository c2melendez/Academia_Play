"""Real Chromium pilot tests. Run with Python Playwright installed."""
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_http import PilotServer
from mm110_f01_store import Store

class BrowserF01(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.server=PilotServer(("127.0.0.1",0),Store(Path(cls.tmp.name)/"browser.sqlite"))
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        def stop():
            cls.server.shutdown()
            cls.server.server_close()
            cls.thread.join(timeout=5)
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
        expect(self.page.locator("#notice")).to_contain_text("Sesión local activa")
        expect(self.page.locator("#start")).to_be_enabled()

    def tearDown(self):
        self.assertEqual([],self.errors)

    def choose(self,item):
        self.page.locator("#item").select_option(item)
        self.page.locator("#start").click()
        expect(self.page.locator("#exercise")).to_be_visible()
        expect(self.page.locator("#submit")).to_be_enabled()

    def answer(self,expression,reason):
        self.page.get_by_label("Expresión algebraica (usa x, / y ^)").fill(expression)
        self.page.locator('input[name="reason"]').nth(reason).check()
        self.page.locator("#submit").click()
        expect(self.page.locator("#submit")).to_be_disabled()

    def test_mastery_and_reload(self):
        for item,answer,reason in [
            ("f01-route-expand","14x-21",1),
            ("f01-route-repair","5x-20",0),
            ("f01-route-transfer","8x+48",1),
        ]:
            self.choose(item)
            self.answer(answer,reason)
            expect(self.page.locator("#feedback")).to_contain_text("Respuesta aceptada")
        expect(self.page.locator("#progress")).to_contain_text("Dominio inicial acreditado")
        self.page.reload()
        expect(self.page.locator("#progress")).to_contain_text("Dominio inicial acreditado")
        expect(self.page.locator("#progress")).not_to_contain_text("Acceso conservado")

    def test_hint_excludes_evidence(self):
        self.choose("f01-route-expand")
        self.page.locator("#hint").click()
        expect(self.page.locator("#feedback")).to_contain_text("intento asistido")
        expect(self.page.locator("#submit")).to_be_enabled()
        self.answer("14x-21",1)
        expect(self.page.locator("#feedback")).to_contain_text("Respuesta aceptada")
        expect(self.page.locator("#progress")).to_contain_text("Evidencias: 0")

    def test_exam_no_hint_or_feedback(self):
        self.page.locator("#mode").select_option("exam_preparation")
        self.choose("f01-exam-rational")
        expect(self.page.locator("#review")).to_be_hidden()
        expect(self.page.locator("#hint")).to_be_hidden()
        self.answer("-6x+9",0)
        expect(self.page.locator("#feedback")).to_contain_text("No se revela la corrección")
        expect(self.page.locator("#progress")).to_contain_text("Evidencias: 0")

    def test_mobile_keyboard_and_labels(self):
        self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))
        self.page.locator("#start").focus()
        self.page.keyboard.press("Enter")
        expect(self.page.locator("#exercise")).to_be_visible()
        expect(self.page.locator("#prompt")).to_be_focused()
        self.page.keyboard.press("Tab")
        expect(self.page.locator("#answer")).to_be_focused()
        expect(self.page.get_by_role("group",name=self.page.locator("#reason").inner_text())).to_be_visible()
        self.assertTrue(self.page.evaluate("document.documentElement.scrollWidth <= innerWidth"))

    def test_guided_complete_and_reload(self):
        self.page.locator("#mode").select_option("guided")
        expect(self.page.locator("#guided-status")).to_contain_text("Etapa A")
        self.assertEqual(400,self.page.evaluate("""async () => (await fetch('/api/f01/guided/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({item_id:'f01-route-transfer'})})).status"""))
        cases = [
            ("f01-a-sign-positive","15",0,"A"),
            ("f01-a-fraction-negative","-3/2",1,"B"),
            ("f01-b-group","28",1,"B"),
            ("f01-b-predict","4x+12",2,"C"),
            ("f01-route-expand","14x-21",1,"C"),
            ("f01-route-repair","5x-20",0,"C"),
            ("f01-tutor-inverse","6(3x-2)",0,"T"),
            ("f01-route-transfer","8x+48",1,"COMPLETE"),
        ]
        for item,expression,reason,stage in cases:
            self.choose(item)
            self.answer(expression,reason)
            expect(self.page.locator("#feedback")).to_contain_text("Respuesta aceptada")
            expect(self.page.locator("#guided-status")).to_contain_text("Ruta completada" if stage=="COMPLETE" else "Etapa "+stage)
            if stage!="COMPLETE":
                expect(self.page.locator("#start")).to_be_enabled()
        expect(self.page.locator("#start")).to_be_disabled()
        expect(self.page.locator("#progress")).to_contain_text("Acceso conservado")
        self.page.reload()
        expect(self.page.locator("#notice")).to_contain_text("Sesión local activa")
        self.page.locator("#mode").select_option("guided")
        expect(self.page.locator("#guided-status")).to_contain_text("Ruta completada")
        expect(self.page.locator("#progress")).to_contain_text("Acceso conservado")
        expect(self.page.locator("#start")).to_be_disabled()

    def test_guided_assistance_does_not_unlock(self):
        self.page.locator("#mode").select_option("guided")
        self.choose("f01-a-sign-positive")
        self.page.locator("#hint").click()
        expect(self.page.locator("#feedback")).to_contain_text("intento asistido")
        expect(self.page.locator("#submit")).to_be_enabled()
        self.answer("15",0)
        expect(self.page.locator("#feedback")).to_contain_text("Respuesta aceptada")
        expect(self.page.locator("#guided-status")).to_contain_text("0/8")
        expect(self.page.locator("#start")).to_be_enabled()

if __name__=="__main__":
    unittest.main()
