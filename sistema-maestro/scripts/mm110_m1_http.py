"""Loopback-only formative M1 pilot, independent of F01 and its exams."""
import json
from pathlib import Path
from http.cookies import SimpleCookie
from mm110_m1_store import Store, SESSION_TTL
from http.server import HTTPServer, BaseHTTPRequestHandler
from mm110_m1_review import ORGANIZERS, get_organizer, check_prediction
from mm110_m1_activities import ITEMS, INDEX, public_item

class Server(HTTPServer):
    def __init__(self, address, store):
        if address[0] != "127.0.0.1":
            raise ValueError("loopback only")
        self.store=store
        super().__init__(address, Handler)

class Handler(BaseHTTPRequestHandler):
    timeout=5
    def log_message(self,*args):
        pass
    def send_data(self,status,data,kind="application/json",token=None):
        raw=json.dumps(data,ensure_ascii=False).encode("utf-8") if kind=="application/json" else data
        self.send_response(status)
        self.send_header("Content-Type",kind+"; charset=utf-8")
        self.send_header("Content-Length",str(len(raw)))
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Security-Policy","default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        if token:
            self.send_header("Set-Cookie","m1="+token+"; HttpOnly; SameSite=Strict; Path=/; Max-Age="+str(SESSION_TTL))
        self.end_headers()
        self.wfile.write(raw)
    def host_ok(self):
        return self.headers.get_all("Host",[])==["127.0.0.1:"+str(self.server.server_port)]
    def learner(self):
        cookie=SimpleCookie()
        cookie.load(self.headers.get("Cookie",""))
        return self.server.store.learner_for_token(cookie["m1"].value) if "m1" in cookie else None
    def do_GET(self):
        if not self.host_ok():
            return self.send_data(403,{"error":"host"})
        if self.path in ("/","/m1"):
            return self.send_data(200,(Path(__file__).resolve().parents[1]/"pilot"/"mm110_m1.html").read_bytes(),"text/html")
        learner=self.learner()
        if not learner:
            return self.send_data(401,{"error":"session required"})
        if self.path=="/api/m1/exam/active":
            return self.send_data(200,self.server.store.active_exam(learner))
        if self.server.store.active_exam(learner):
            return self.send_data(403,{"error":"active exam"})
        if self.path=="/api/m1/progress":
            return self.send_data(200,self.server.store.progress(learner))
        if self.path=="/api/m1/catalog":
            return self.send_data(200,{"families":[{"id":f,"title":v["title"]} for f,v in ORGANIZERS.items()],
                "items":[public_item(i["id"]) for i in ITEMS if i["stage"]!="E"]})
        if self.path.startswith("/api/m1/review/"):
            family=self.path.split("/")[-1]
            if family in ORGANIZERS:
                data=get_organizer(family)
                # Prediction before worked table reveal.
                data.pop("rows",None)
                return self.send_data(200,data)
        return self.send_data(404,{"error":"not found"})
    def do_POST(self):
        if not self.host_ok() or self.headers.get_all("Origin",[])!=["http://127.0.0.1:"+str(self.server.server_port)]:
            return self.send_data(403,{"error":"origin"})
        if self.headers.get_content_type()!="application/json":
            return self.send_data(415,{"error":"JSON required"})
        try:
            lengths=self.headers.get_all("Content-Length",[])
            if len(lengths)!=1 or self.headers.get("Transfer-Encoding") is not None:
                raise ValueError("framing")
            n=int(lengths[0])
            if not 0<n<=4096:
                raise ValueError("length")
            raw=self.rfile.read(n)
            if len(raw)!=n:
                raise ValueError("body")
            data=json.loads(raw)
            if not isinstance(data,dict):
                raise ValueError("object")
            store=self.server.store
            learner=self.learner()
            if self.path=="/api/m1/session" and not data:
                if learner:
                    return self.send_data(200,{"status":"session active"})
                token=store.create_token()
                if not token:
                    return self.send_data(503,{"error":"session limit"})
                return self.send_data(201,{"status":"session active"},token=token)
            if not learner:
                return self.send_data(401,{"error":"session required"})
            if self.path=="/api/m1/exam/start" and not data:
                try:
                    result=store.start_exam(learner)
                except ValueError as exc:
                    if str(exc)=="fresh exam bank exhausted":
                        return self.send_data(409,{"error":"fresh exam bank exhausted"})
                    raise
            elif self.path=="/api/m1/exam/finish" and set(data)=={"exam_id"}:
                result=store.finish_exam(learner,data["exam_id"])
            elif self.path=="/api/m1/submit" and set(data)=={"attempt_id","answer","reason_choice"}:
                result=store.submit(learner,data["attempt_id"],data["answer"],data["reason_choice"])
            elif store.active_exam(learner):
                return self.send_data(403,{"error":"active exam"})
            elif self.path=="/api/m1/predict" and set(data)=={"family","choice"}:
                result=check_prediction(data["family"],data["choice"])
            elif self.path=="/api/m1/assess" and set(data)=={"item_id","answer","reason_choice"}:
                item=INDEX[data["item_id"]]
                if item["stage"]=="E":
                    return self.send_data(403,{"error":"exam unavailable"})
                result=store.assess_formative(learner,data["item_id"],data["answer"],data["reason_choice"])
            else:
                raise ValueError("request")
            return self.send_data(200,result)
        except (ValueError,KeyError,TypeError,OverflowError,RecursionError):
            return self.send_data(400,{"error":"invalid request"})
        except TimeoutError:
            return self.send_data(408,{"error":"timeout"})
        except Exception:
            return self.send_data(500,{"error":"internal failure"})

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--port",type=int,default=8766)
    p.add_argument("--db",required=True)
    args=p.parse_args()
    with Server(("127.0.0.1",args.port),Store(args.db)) as server:
        print("M1 local formative pilot:",server.server_port,flush=True)
        server.serve_forever()
