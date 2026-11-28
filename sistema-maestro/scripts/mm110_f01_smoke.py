"""HTTPS smoke test for restricted staging. No credential or cookie logging."""
import base64
import http.client
import json
import os
import re
import ssl
from urllib.parse import urlsplit
from http.cookies import SimpleCookie

def require(condition, label):
    if not condition:
        raise RuntimeError("Smoke failed: "+label)

def run(origin, access, expected_sha):
    parsed=urlsplit(origin)
    require(parsed.scheme=="https" and parsed.hostname and parsed.netloc==parsed.hostname
            and not parsed.path and not parsed.query and not parsed.fragment, "HTTPS origin")
    require(bool(re.fullmatch(r"[a-f0-9]{40}",expected_sha)), "expected SHA")
    require(bool(re.fullmatch(r"[A-Za-z0-9_-]{43,128}",access)), "review credential")
    auth="Basic "+base64.b64encode(("reviewer:"+access).encode("ascii")).decode("ascii")
    def request(path, data=None, authorized=True, cookie=None, source=origin):
        headers={"Origin":source}
        if authorized: headers["Authorization"]=auth
        if cookie: headers["Cookie"]=cookie
        if data is not None: headers["Content-Type"]="application/json"
        conn=http.client.HTTPSConnection(parsed.hostname,timeout=15,context=ssl.create_default_context())
        try:
            conn.request("GET" if data is None else "POST",path,
                         None if data is None else json.dumps(data),headers)
            response=conn.getresponse()
            raw=response.read(65537)
            require(len(raw)<=65536,"response size")
            return response.status,dict(response.getheaders()),raw
        finally:
            conn.close()
    def api(path,data=None,cookie=None,status=200):
        code,headers,raw=request("/api/f01/"+path,data,cookie=cookie)
        require(code==status,path+" status")
        return json.loads(raw),headers
    health,_=api("health")
    require(health.get("status")=="restricted-staging","staging identity")
    require(health.get("commit_sha")==expected_sha,"deployed SHA")
    require(request("/",authorized=False)[0]==401,"anonymous UI rejected")
    require(request("/api/f01/session",{},authorized=False)[0]==401,"anonymous session rejected")
    require(request("/api/f01/session",{},source="https://invalid.example")[0]==403,"foreign origin rejected")
    require(request("/")[0]==200,"authorized UI")
    def new_session():
        _,headers=api("session",{},status=201)
        cookie=SimpleCookie()
        cookie.load(headers["Set-Cookie"])
        item=cookie["f01"]
        require(item["secure"] and item["httponly"] and item["samesite"].lower()=="strict","cookie flags")
        return "f01="+item.value
    a,b=new_session(),new_session()
    require(a!=b,"separate sessions")
    attempt,_=api("start",{"item_id":"f01-route-expand","mode":"learning_path"},cookie=a)
    require("expected" not in attempt and "correct_reason" not in attempt,"no answer disclosure")
    result,_=api("submit",{"attempt_id":attempt["attempt_id"],"answer":"14x-21","reason_choice":1},cookie=a)
    require(result.get("accepted") is True,"exact oracle")
    first,_=api("progress",cookie=a)
    second,_=api("progress",cookie=b)
    require(first["evidence_count"]==1 and second["evidence_count"]==0,"progress isolation")
    print("F01_SMOKE PASS "+expected_sha,flush=True)

if __name__=="__main__":
    run(os.environ["F01_STAGING_ORIGIN"],os.environ["F01_STAGING_ACCESS"],os.environ["F01_EXPECTED_SHA"])
