"""Local-only F01 HTTP pilot. No public hosting or institutional authentication."""
import argparse
import json
import secrets
import threading
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from http.cookies import SimpleCookie
from mm110_f01_store import Store
from mm110_f01_activities import ITEMS

MAX_CONNECTIONS = 16
SOCKET_TIMEOUT = 5

class PilotServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, store):
        if address[0] != "127.0.0.1":
            raise ValueError("Pilot must bind to loopback")
        self.store = store
        self.sessions = {}
        self.session_lock = threading.Lock()
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
            self.send_header("Set-Cookie", "f01="+cookie+"; HttpOnly; SameSite=Strict; Path=/")
        self.end_headers()
        self.wfile.write(raw)

    def _host_ok(self):
        return self.headers.get("Host") == "127.0.0.1:"+str(self.server.server_port)

    def _learner(self):
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie",""))
        token = cookie.get("f01")
        with self.server.session_lock:
            return self.server.sessions.get(token.value) if token else None

    def do_GET(self):
        if not self._host_ok():
            return self._send(403,{"error":"host"})
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
        if self.path == "/api/f01/health":
            return self._send(200,{"status":"local-pilot"})
        learner = self._learner()
        if not learner:
            return self._send(401,{"error":"session required"})
        if self.path == "/api/f01/items":
            return self._send(200,[{"item_id":i.item_id,"mode":i.mode,"family":i.family} for i in ITEMS])
        if self.path == "/api/f01/exam/history":
            return self._send(200,self.server.store.exam_history(learner))
        if self.path == "/api/f01/guided":
            return self._send(200,self.server.store.guided_progress(learner))
        if self.path == "/api/f01/progress":
            s = self.server.store.snapshot(learner)
            return self._send(200,{"mastery_estimate":s["mastery_estimate"],"evidence_count":len(s["mastery_evidence"]),"access_granted":bool(s["access_grants"])})
        return self._send(404,{"error":"not found"})

    def do_POST(self):
        origin = "http://127.0.0.1:"+str(self.server.server_port)
        if not self._host_ok() or self.headers.get("Origin") != origin:
            return self._send(403,{"error":"origin"})
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
                token = secrets.token_urlsafe(32)
                with self.server.session_lock:
                    if len(self.server.sessions)>=1000:
                        return self._send(503,{"error":"pilot session limit"})
                    self.server.sessions[token] = secrets.token_hex(16)
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
