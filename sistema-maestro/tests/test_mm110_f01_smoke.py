"""Smoke runner contract tests; simulated transport, not remote TLS evidence."""
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_smoke import run

SHA="a"*40
SECRET="b"*43
ORIGIN="https://review.example.invalid"

class Response:
    def __init__(self,status,body=None,headers=None):
        self.status=status
        self.raw=json.dumps(body).encode() if body is not None else b""
        self.headers=headers or {}
    def read(self,n): return self.raw[:n]
    def getheaders(self): return list(self.headers.items())

def fixtures():
    return [
        Response(200,{"status":"restricted-staging","commit_sha":SHA}),
        Response(401),Response(401),Response(403),Response(200),
        Response(201,{},{"Set-Cookie":"f01="+"c"*43+"; Secure; HttpOnly; SameSite=Strict"}),
        Response(201,{},{"Set-Cookie":"f01="+"d"*43+"; Secure; HttpOnly; SameSite=Strict"}),
        Response(200,{"attempt_id":"test"}),
        Response(200,{"accepted":True}),
        Response(200,{"evidence_count":1}),Response(200,{"evidence_count":0})
    ]

class SmokeTests(unittest.TestCase):
    def execute(self,responses):
        with patch("mm110_f01_smoke.http.client.HTTPSConnection") as factory:
            factory.return_value.getresponse.side_effect=responses
            out=io.StringIO()
            with redirect_stdout(out):
                run(ORIGIN,SECRET,SHA)
            self.assertEqual("F01_SMOKE PASS "+SHA,out.getvalue().strip())
            self.assertEqual(11,factory.call_count)
            self.assertEqual(11,factory.return_value.close.call_count)
            for call in factory.call_args_list:
                self.assertEqual("review.example.invalid",call.args[0])
                self.assertTrue(call.kwargs["context"].check_hostname)
            return factory.return_value.request.call_args_list

    def test_positive_contract_and_no_anonymous_auth(self):
        calls=self.execute(fixtures())
        for idx in (1,2):
            self.assertNotIn("Authorization",calls[idx].args[3])
        self.assertEqual("https://invalid.example",calls[3].args[3]["Origin"])
        self.assertNotEqual(calls[9].args[3]["Cookie"],calls[10].args[3]["Cookie"])

    def test_negative_contracts(self):
        for idx,response,label in [
            (0,Response(200,{"status":"restricted-staging","commit_sha":"f"*40}),"deployed SHA"),
            (1,Response(200),"anonymous UI"),
            (2,Response(201),"anonymous session"),
            (3,Response(201),"foreign origin"),
            (5,Response(201,{},{"Set-Cookie":"f01=x; HttpOnly; SameSite=Strict"}),"cookie flags"),
            (7,Response(200,{"attempt_id":"test","expected":"leak"}),"no answer disclosure"),
            (8,Response(200,{"accepted":False}),"exact oracle"),
            (10,Response(200,{"evidence_count":1}),"progress isolation")
        ]:
            with self.subTest(label=label):
                responses=fixtures()
                responses[idx]=response
                with patch("mm110_f01_smoke.http.client.HTTPSConnection") as factory:
                    factory.return_value.getresponse.side_effect=responses
                    out=io.StringIO()
                    with redirect_stdout(out),self.assertRaisesRegex(RuntimeError,label):
                        run(ORIGIN,SECRET,SHA)
                    self.assertNotIn("PASS",out.getvalue())
                    self.assertEqual(idx+1,factory.call_count)

    def test_invalid_configuration_never_connects(self):
        with patch("mm110_f01_smoke.http.client.HTTPSConnection") as factory:
            for origin,secret,sha in [("http://review.example.invalid",SECRET,SHA),(ORIGIN,"short",SHA),(ORIGIN,SECRET,"bad")]:
                with self.assertRaises(RuntimeError):
                    run(origin,secret,sha)
            factory.assert_not_called()
