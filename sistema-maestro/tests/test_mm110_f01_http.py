"""Real loopback HTTP integration tests for the F01 local pilot."""
import http.client
import socket
import time
from contextlib import ExitStack
from unittest.mock import patch
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_http import PilotServer, Handler, MAX_CONNECTIONS
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

    def raw_request(self, headers, body=b"", half_close=True):
        with socket.create_connection(("127.0.0.1",self.port),timeout=8) as sock:
            prefix=("POST /api/f01/session HTTP/1.0\r\nHost: 127.0.0.1:"+
                    str(self.port)+"\r\nOrigin: "+self.origin+
                    "\r\nContent-Type: application/json\r\n").encode()
            sock.sendall(prefix+headers+b"\r\n"+body)
            if half_close:
                sock.shutdown(socket.SHUT_WR)
            response=http.client.HTTPResponse(sock)
            response.begin()
            return response.status,response.read()

    def test_duplicate_content_length_rejected(self):
        status,_=self.raw_request(b"Content-Length: 2\r\nContent-Length: 2\r\n",b"{}")
        self.assertEqual(400,status)
        self.assertEqual(0,self.server.store.token_count())

    def test_transfer_encoding_rejected(self):
        status,_=self.raw_request(b"Content-Length: 2\r\nTransfer-Encoding: chunked\r\n",b"{}")
        self.assertEqual(400,status)
        self.assertEqual(0,self.server.store.token_count())

    def test_truncated_body_rejected(self):
        status,_=self.raw_request(b"Content-Length: 10\r\n",b"{}")
        self.assertEqual(400,status)
        self.assertEqual(0,self.server.store.token_count())
        self.assertEqual(200,self.request("/api/f01/health")[0])

    def test_body_timeout_releases_connection(self):
        with patch.object(Handler,"timeout",0.25):
            status,_=self.raw_request(b"Content-Length: 10\r\n",b"{",half_close=False)
        self.assertEqual(408,status)
        self.assertEqual(0,self.server.store.token_count())
        self.assertEqual(200,self.request("/api/f01/health")[0])

    def test_saturation_and_recovery_real_connections(self):
        entered=threading.Condition()
        count=0
        release=threading.Event()
        original=Handler.do_GET
        def held(handler):
            nonlocal count
            with entered:
                count+=1
                entered.notify_all()
            release.wait(8)
            original(handler)
        with patch.object(Handler,"do_GET",held):
            with ExitStack() as stack:
                held_sockets=[]
                try:
                    for _ in range(MAX_CONNECTIONS):
                        s=stack.enter_context(socket.create_connection(("127.0.0.1",self.port),timeout=5))
                        held_sockets.append(s)
                        s.sendall(("GET /api/f01/health HTTP/1.0\r\nHost: 127.0.0.1:"+str(self.port)+"\r\n\r\n").encode())
                    with entered:
                        self.assertTrue(entered.wait_for(lambda:count==MAX_CONNECTIONS,timeout=5))
                    status,_,headers=self.request("/api/f01/health")
                    self.assertEqual(503,status)
                    self.assertEqual("1",headers["Retry-After"])
                finally:
                    release.set()
                for s in held_sockets:
                    response=http.client.HTTPResponse(s)
                    response.begin()
                    self.assertEqual(200,response.status)
                    response.read()
        deadline=time.monotonic()+5
        while time.monotonic()<deadline:
            if self.request("/api/f01/health")[0]==200:
                break
            time.sleep(0.02)
        else:
            self.fail("server did not recover after saturation")
        self.assertEqual(201,self.request("/api/f01/session",{})[0])

    def test_deferred_exam_review(self):
        c=self.session()
        key=self.start(c,"f01-exam-rational","exam_preparation")
        def finish(cookie=c):
            return self.request("/api/f01/exam/finish",{"attempt_id":key},cookie)
        self.assertEqual(400,finish()[0])
        before=self.request("/api/f01/progress",cookie=c)[1]
        self.assertEqual({"status":"RECORDED"},self.submit(c,key,"-6x+9",0)[1])
        self.assertEqual(400,finish(self.session())[0])
        status,review,_=finish()
        self.assertEqual(200,status)
        self.assertEqual("FINISHED",review["status"])
        self.assertEqual(1,review["score"])
        self.assertEqual("-6x+9",review["expected"])
        self.assertEqual(review,finish()[1])
        self.assertEqual(400,self.submit(c,key,"-6x-9",0)[0])
        self.assertEqual(before,self.request("/api/f01/progress",cookie=c)[1])

    def test_exam_review_wrong_and_non_exam(self):
        c=self.session()
        key=self.start(c,"f01-exam-rational","exam_preparation")
        self.assertEqual({"status":"RECORDED"},self.submit(c,key,"-6x-9",0)[1])
        status,review,_=self.request("/api/f01/exam/finish",{"attempt_id":key},c)
        self.assertEqual(200,status)
        self.assertEqual(0,review["score"])
        self.assertFalse(review["correct"])
        self.assertTrue(review["feedback"])
        practice=self.start(c)
        self.submit(c,practice,"14x-21",1)
        self.assertEqual(400,self.request("/api/f01/exam/finish",{"attempt_id":practice},c)[0])

    def test_session_survives_server_restart(self):
        c=self.session()
        key=self.start(c,"f01-exam-rational","exam_preparation")
        self.assertEqual({"status":"RECORDED"},self.submit(c,key,"-6x+9",0)[1])
        self.assertEqual([],self.request("/api/f01/exam/history",cookie=c)[1])
        review=self.request("/api/f01/exam/finish",{"attempt_id":key},c)[1]
        other=self.session()
        self.stop()
        self.server=PilotServer(("127.0.0.1",0),Store(Path(self.tmp.name)/"test.sqlite"))
        self.port=self.server.server_port
        self.origin="http://127.0.0.1:"+str(self.port)
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={"poll_interval":0.02},daemon=True)
        self.thread.start()
        status,history,_=self.request("/api/f01/exam/history",cookie=c)
        self.assertEqual(200,status)
        self.assertEqual([{"attempt_id":key,**review}],history)
        self.assertEqual([],self.request("/api/f01/exam/history",cookie=other)[1])
        self.assertEqual(401,self.request("/api/f01/exam/history",cookie="f01="+"a"*43)[0])
