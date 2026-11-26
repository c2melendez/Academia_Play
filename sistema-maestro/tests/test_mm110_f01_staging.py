"""Restricted staging transport and configuration tests, with real loopback HTTP."""
import base64
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
from mm110_f01_staging import configuration, deployment_commit

class StagingTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.store=Store(self.root/"test.sqlite")
        self.origin="https://review.example.invalid"
        self.secret="a"*43
        self.auth="Basic "+base64.b64encode(("reviewer:"+self.secret).encode()).decode()
        self.server=PilotServer(("127.0.0.1",0),self.store,staging_origin=self.origin,staging_access=self.secret,commit_sha='a'*40)
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={"poll_interval":0.02},daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)
    def request(self,path,data=None,auth=True,headers=None):
        h={"Host":"review.example.invalid","Origin":self.origin}
        if auth:h["Authorization"]=self.auth
        if data is not None:h["Content-Type"]="application/json"
        h.update(headers or {})
        c=http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=5)
        try:
            c.request("GET" if data is None else "POST",path,None if data is None else json.dumps(data),h)
            r=c.getresponse()
            return r.status,r.read(),dict(r.getheaders())
        finally:c.close()
    def test_health_and_review_access(self):
        status,body,_=self.request("/api/f01/health",auth=False)
        self.assertEqual(200,status)
        self.assertEqual({"status":"restricted-staging","commit_sha":"a"*40},json.loads(body))
        status,body,h=self.request("/",auth=False)
        self.assertEqual(401,status)
        self.assertIn("Basic",h["WWW-Authenticate"])
        self.assertEqual(b"",body)
        self.assertEqual(401,self.request("/",headers={"Authorization":"Basic invalid"})[0])
        self.assertEqual(200,self.request("/")[0])
    def test_session_requires_review_and_secure_cookie(self):
        self.assertEqual(401,self.request("/api/f01/session",{},auth=False)[0])
        self.assertEqual(0,self.store.token_count())
        status,_,h=self.request("/api/f01/session",{})
        self.assertEqual(201,status)
        for flag in ("Secure","HttpOnly","SameSite=Strict"):
            self.assertIn(flag,h["Set-Cookie"])
        cookie=h["Set-Cookie"].split(";")[0]
        self.assertEqual(401,self.request("/api/f01/progress",auth=False,headers={"Cookie":cookie})[0])
        self.assertEqual(200,self.request("/api/f01/progress",headers={"Cookie":cookie})[0])
    def test_host_and_origin_rejection(self):
        self.assertEqual(403,self.request("/",headers={"Host":"evil.invalid","X-Forwarded-Host":"review.example.invalid"})[0])
        self.assertEqual(403,self.request("/api/f01/session",{},headers={"Origin":"http://review.example.invalid"})[0])
        self.assertEqual(0,self.store.token_count())
    def test_invalid_staging_configuration(self):
        for origin,secret in [("http://review.example.invalid",self.secret),(self.origin,"short"),(self.origin+"/",self.secret),("https://user@review.example.invalid",self.secret)]:
            with self.subTest(origin=origin):
                with self.assertRaises(ValueError):
                    PilotServer(("127.0.0.1",0),self.store,staging_origin=origin,staging_access=secret)
    def test_launcher_requires_explicit_storage_and_credentials(self):
        env={"F01_DATA_DIR":str(self.root),"F01_STAGING_ORIGIN":self.origin,"F01_STAGING_ACCESS":self.secret,"PORT":"12345"}
        self.assertEqual((12345,self.root/"f01.sqlite",self.origin,self.secret),configuration(env))
        for key in ("F01_DATA_DIR","F01_STAGING_ORIGIN","F01_STAGING_ACCESS"):
            with self.assertRaises(ValueError):
                configuration({k:v for k,v in env.items() if k!=key})
        with self.assertRaises(ValueError):
            configuration({**env,"RENDER":"true"})
        with self.assertRaises(ValueError):
            configuration({**env,"PORT":"0"})

    def test_deploy_commit_validation(self):
        self.assertIsNone(deployment_commit({}))
        self.assertEqual("a"*40,deployment_commit({"RENDER":"true","RENDER_GIT_COMMIT":"a"*40}))
        for invalid in ("", "abc", "A"*40, "z"*40):
            with self.assertRaises(ValueError):
                deployment_commit({"RENDER":"true","RENDER_GIT_COMMIT":invalid})
        with self.assertRaises(ValueError):
            deployment_commit({"RENDER":"true"})
