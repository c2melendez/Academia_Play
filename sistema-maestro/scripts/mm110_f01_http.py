"""Local-only F01 HTTP pilot. No public hosting or institutional authentication."""
import argparse
import hmac
import re
from urllib.parse import urlsplit
import json
import threading
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from http.cookies import SimpleCookie
from mm110_f01_store import Store, SESSION_TTL
from mm110_f01_activities import ITEMS

MAX_CONNECTIONS = 16
SOCKET_TIMEOUT = 5

class PilotServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, store, *, staging_origin=None, staging_access=None, commit_sha=None):
        if staging_origin is None:
            if address[0] != "127.0.0.1" or staging_access is not None:
                raise ValueError("Pilot must bind to loopback")
        else:
            parsed = urlsplit(staging_origin)
            if (parsed.scheme != "https" or not parsed.hostname or parsed.netloc != parsed.hostname
                    or parsed.path or parsed.query or parsed.fragment
                    or not re.fullmatch(r"[a-z0-9.-]+", parsed.hostname)
                    or not isinstance(staging_access,str) or not re.fullmatch(r"[A-Za-z0-9_-]{43,128}",staging_access)):
                raise ValueError("Invalid restricted staging configuration")
        if commit_sha is not None and not re.fullmatch(r"[a-f0-9]{40}",commit_sha):
            raise ValueError("Invalid deployment commit")
        self.commit_sha = commit_sha
        self.staging_origin = staging_origin
        self.staging_access = staging_access
        self.store = store
        self.connection_slots = threading.BoundedSemaphore(MAX_CONNECTIONS)
        super().__init__(address, Handler)

    def process_request(self, request, client_address):
        if not self.connection_slots.acquire(blocking=False):
            try:
                request.settimeout(0.25)
                request.sendall(b'HTTP/1.0 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\nRetry-After: 1\r\n\r\n')
            except OSError:
                pass
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.connection_slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.connection_slots.release()

class Handler(BaseHTTPRequestHandler):
    timeout = SOCKET_TIMEOUT

    def log_message(self, *args):
        pass

    def _send(self, status, payload, cookie=None):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if cookie:
            self.send_header("Set-Cookie", "f01="+cookie+"; HttpOnly; SameSite=Strict; Path=/; Max-Age="+str(SESSION_TTL)+("; Secure" if self.server.staging_origin else ""))
        self.end_headers()
        self.wfile.write(raw)

    def _host_ok(self):
        return self.headers.get_all("Host",[]) == [urlsplit(self.server.staging_origin).netloc if self.server.staging_origin else "127.0.0.1:"+str(self.server.server_port)]

    def _access_ok(self):
        if not self.server.staging_origin:
            return True
        import base64
        expected = "Basic "+base64.b64encode(("reviewer:"+self.server.staging_access).encode("ascii")).decode("ascii")
        return hmac.compare_digest(self.headers.get("Authorization","").encode("utf8"),expected.encode("ascii"))

    def _challenge(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="F01 restricted staging", charset="UTF-8"')
        self.send_header("Cache-Control","no-store")
        self.send_header("Content-Length","0")
        self.end_headers()

    def _learner(self):
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie",""))
        token = cookie.get("f01")
        return self.server.store.learner_for_token(token.value) if token else None

    def do_GET(self):
        if not self._host_ok():
            return self._send(403,{"error":"host"})
        if self.path == "/api/f01/health":
            return self._send(200,{"status":"restricted-staging" if self.server.staging_origin else "local-pilot", "commit_sha":self.server.commit_sha})
        if not self._access_ok():
            return self._challenge()
        if self.path in ("/", "/f01"):
            raw = (Path(__file__).resolve().parents[1] / "pilot" / "mm110_f01.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(raw)
            return
        learner = self._learner()
        if not learner:
            return self._send(401,{"error":"session required"})
        if self.path == "/api/f01/items":
            return self._send(200,[{"item_id":i.item_id,"mode":i.mode,"family":i.family} for i in ITEMS])
        if self.path == "/api/f01/exam/set/active":
            return self._send(200,self.server.store.active_exam_set(learner))
        if self.path == "/api/f01/exam/history":
            return self._send(200,self.server.store.exam_history(learner))
        if self.path == "/api/f01/guided":
            return self._send(200,self.server.store.guided_progress(learner))
        if self.path == "/api/f01/progress":
            s = self.server.store.snapshot(learner)
            return self._send(200,{"mastery_estimate":s["mastery_estimate"],"evidence_count":len(s["mastery_evidence"]),"access_granted":bool(s["access_grants"])})
        return self._send(404,{"error":"not found"})

    def do_POST(self):
        origin = self.server.staging_origin or "http://127.0.0.1:"+str(self.server.server_port)
        if not self._host_ok() or self.headers.get("Origin") != origin:
            return self._send(403,{"error":"origin"})
        if not self._access_ok():
            return self._challenge()
        if self.headers.get_content_type() != "application/json":
            return self._send(415,{"error":"JSON required"})
        try:
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) != 1 or self.headers.get("Transfer-Encoding") is not None:
                return self._send(400,{"error":"invalid body framing"})
            n = int(lengths[0])
            if not 0<n<=4096:
                return self._send(400,{"error":"body size"})
            raw = self.rfile.read(n)
            if len(raw) != n:
                return self._send(400,{"error":"incomplete body"})
            data = json.loads(raw)
            if not isinstance(data,dict):
                raise ValueError("object required")
            if self.path == "/api/f01/session":
                if data:
                    raise ValueError("empty object required")
                token = self.server.store.create_token()
                if token is None:
                    return self._send(503,{"error":"pilot session limit"})
                return self._send(201,{"status":"session created"},token)
            learner = self._learner()
            if not learner:
                return self._send(401,{"error":"session required"})
            store = self.server.store
            if self.path == "/api/f01/start" and set(data)=={"item_id","mode"}:
                result = store.start(learner,data["item_id"],data["mode"])
            elif self.path == "/api/f01/guided/start" and set(data)=={"item_id"}:
                result = store.start_guided(learner,data["item_id"])
            elif self.path == "/api/f01/hint" and set(data)=={"attempt_id","index"}:
                result = store.request_hint(learner,data["attempt_id"],data["index"])
            elif self.path == "/api/f01/exam/set/start" and not data:
                result = store.start_exam_set(learner)
            elif self.path == "/api/f01/exam/set/finish" and set(data)=={"exam_id"}:
                result = store.finish_exam_set(learner,data["exam_id"])
            elif self.path == "/api/f01/exam/finish" and set(data)=={"attempt_id"}:
                result = store.finish_exam(learner,data["attempt_id"])
            elif self.path == "/api/f01/submit" and set(data)=={"attempt_id","answer","reason_choice"}:
                result = store.submit(learner,data["attempt_id"],data["answer"],data["reason_choice"])
            else:
                return self._send(400,{"error":"unsupported request"})
            return self._send(200,result)
        except socket.timeout:
            self.close_connection = True
            return self._send(408,{"error":"request timeout"})
        except (ValueError,KeyError,TypeError,OverflowError,RecursionError):
            return self._send(400,{"error":"invalid request or attempt"})
        except Exception:
            return self._send(500,{"error":"internal failure"})

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",required=True)
    p.add_argument("--port",type=int,default=8765)
    args=p.parse_args()
    with PilotServer(("127.0.0.1",args.port),Store(args.db)) as server:
        print("Local pilot:",server.server_port,flush=True)
        server.serve_forever()

if __name__=="__main__":
    main()
