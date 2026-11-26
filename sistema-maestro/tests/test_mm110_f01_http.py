"""Real loopback HTTP integration tests for the F01 local pilot."""
import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_http import PilotServer
from mm110_f01_store import Store

class F01HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.server=PilotServer(("127.0.0.1",0),Store(Path(self.tmp.name)/"test.sqlite"))
        self.port=self.server.server_port
        self.origin="http://127.0.0.1:"+str(self.port)
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={"poll_interval":0.02},daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
    def request(self,path,data=None,cookie=None,headers=None):
        h={"Origin":self.origin}
        if data is not None:h["Content-Type"]="application/json"
        if cookie:h["Cookie"]=cookie
        if headers:h.update(headers)
        conn=http.client.HTTPConnection("127.0.0.1",self.port,timeout=5)
        try:
            conn.request("GET" if data is None else "POST",path,None if data is None else json.dumps(data),h)
            r=conn.getresponse()
            raw=r.read()
            body=json.loads(raw) if r.getheader("Content-Type","").startswith("application/json") else raw.decode()
            return r.status,body,dict(r.getheaders())
        finally:conn.close()
    def session(self):
        status,body,h=self.request("/api/f01/session",{})
        self.assertEqual(201,status)
        self.assertIn("HttpOnly",h["Set-Cookie"])
        self.assertIn("SameSite=Strict",h["Set-Cookie"])
        return h["Set-Cookie"].split(";")[0]
    def start(self,cookie,item="f01-route-expand",mode="learning_path"):
        status,body,_=self.request("/api/f01/start",{"item_id":item,"mode":mode},cookie)
        self.assertEqual(200,status)
        self.assertNotIn("expected",body)
        self.assertNotIn("correct_reason",body)
        return body["attempt_id"]
    def submit(self,cookie,key,answer,reason):
        return self.request("/api/f01/submit",{"attempt_id":key,"answer":answer,"reason_choice":reason},cookie)
    def test_page_and_health(self):
        status,body,h=self.request("/")
        self.assertEqual(200,status)
        self.assertIn("Repaso visual",body)
        self.assertIn("connect-src 'self'",h["Content-Security-Policy"])
        self.assertEqual(200,self.request("/api/f01/health")[0])
    def test_requires_session(self):
        self.assertEqual(401,self.request("/api/f01/items")[0])
        self.assertEqual(401,self.request("/api/f01/progress")[0])
    def test_origin_and_host(self):
        self.assertEqual(403,self.request("/api/f01/session",{},headers={"Origin":"http://example.invalid"})[0])
        self.assertEqual(403,self.request("/",headers={"Host":"example.invalid"})[0])
    def test_mastery_http(self):
        c=self.session()
        for item,answer,reason in [("f01-route-expand","14x-21",1),("f01-route-repair","5x-20",0),("f01-route-transfer","8x+48",1)]:
            key=self.start(c,item)
            status,result,_=self.submit(c,key,answer,reason)
            self.assertEqual(200,status)
            self.assertTrue(result["accepted"])
        self.assertEqual({"mastery_estimate":"MASTERED","evidence_count":3,"access_granted":False},self.request("/api/f01/progress",cookie=c)[1])
    def test_guided_grants_access_http(self):
        c=self.session()
        for item,answer,reason in [("f01-a-sign-positive","15",0),("f01-a-fraction-negative","-3/2",1),("f01-b-group","28",1),("f01-b-predict","4x+12",2),("f01-route-expand","14x-21",1),("f01-route-repair","5x-20",0),("f01-tutor-inverse","6(3x-2)",0),("f01-route-transfer","8x+48",1)]:
            status,body,_=self.request("/api/f01/guided/start",{"item_id":item},c)
            self.assertEqual(200,status)
            self.assertTrue(self.submit(c,body["attempt_id"],answer,reason)[1]["accepted"])
        self.assertTrue(self.request("/api/f01/progress",cookie=c)[1]["access_granted"])
        self.assertEqual("COMPLETE",self.request("/api/f01/guided",cookie=c)[1]["stage"])
    def test_hint_and_replay(self):
        c=self.session()
        key=self.start(c)
        self.assertEqual(200,self.request("/api/f01/hint",{"attempt_id":key,"index":0},c)[0])
        a=self.submit(c,key,"14x-21",1)
        self.assertFalse(a[1]["eligible_evidence"])
        self.assertEqual(a[1],self.submit(c,key,"14x-21",1)[1])
        self.assertEqual(0,self.request("/api/f01/progress",cookie=c)[1]["evidence_count"])
    def test_cross_session_isolation(self):
        a,b=self.session(),self.session()
        key=self.start(a)
        self.assertEqual(400,self.submit(b,key,"14x-21",1)[0])
        self.assertEqual(200,self.submit(a,key,"14x-21",1)[0])
        self.assertEqual(0,self.request("/api/f01/progress",cookie=b)[1]["evidence_count"])
    def test_exam_does_not_disclose(self):
        c=self.session()
        key=self.start(c,"f01-exam-rational","exam_preparation")
        self.assertEqual(400,self.request("/api/f01/hint",{"attempt_id":key,"index":0},c)[0])
        self.assertEqual({"status":"RECORDED"},self.submit(c,key,"-6x+9",0)[1])
        self.assertEqual(0,self.request("/api/f01/progress",cookie=c)[1]["evidence_count"])
    def test_client_cannot_supply_assistance_or_identity(self):
        c=self.session()
        key=self.start(c)
        self.assertEqual(400,self.request("/api/f01/submit",{"attempt_id":key,"answer":"14x-21","reason_choice":1,"assisted":False},c)[0])
        self.assertEqual(400,self.request("/api/f01/session",{"learner":"someone"})[0])
    def test_invalid_payload(self):
        c=self.session()
        self.assertEqual(400,self.request("/api/f01/start",{"item_id":"unknown","mode":"learning_path"},c)[0])
        self.assertEqual(415,self.request("/api/f01/session",{},headers={"Content-Type":"text/plain"})[0])
        self.assertEqual(400,self.request("/api/f01/session",{"data":"a"*5000})[0])
