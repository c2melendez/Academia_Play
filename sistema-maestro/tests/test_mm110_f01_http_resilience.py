"""Bounded real loopback resilience tests; never targets an external service."""
import http.client
import socket
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mm110_f01_http import PilotServer, Handler, MAX_CONNECTIONS
from mm110_f01_store import Store

class HTTPResilienceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.server=PilotServer(("127.0.0.1",0),Store(Path(self.tmp.name)/"resilience.sqlite"))
        self.port=self.server.server_port
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={"poll_interval":0.01},daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def connect(self):
        sock=socket.create_connection(("127.0.0.1",self.port),timeout=3)
        self.addCleanup(sock.close)
        return sock

    def post(self, headers, body=b"", half_close=False):
        s=self.connect()
        request=(f"POST /api/f01/session HTTP/1.0\r\nHost: 127.0.0.1:{self.port}\r\n"
                 f"Origin: http://127.0.0.1:{self.port}\r\nContent-Type: application/json\r\n"
                 +headers+"\r\n").encode("ascii")+body
        s.sendall(request)
        if half_close:
            s.shutdown(socket.SHUT_WR)
        with http.client.HTTPResponse(s) as response:
            response.begin()
            return response.status,response.read()

    def health(self):
        conn=http.client.HTTPConnection("127.0.0.1",self.port,timeout=3)
        try:
            conn.request("GET","/api/f01/health")
            r=conn.getresponse()
            r.read()
            return r.status
        finally:
            conn.close()

    def test_duplicate_content_length(self):
        status,body=self.post("Content-Length: 2\r\nContent-Length: 2\r\n",b"{}")
        self.assertEqual(400,status)
        self.assertIn(b"invalid body framing",body)

    def test_transfer_encoding_rejected(self):
        status,body=self.post("Content-Length: 2\r\nTransfer-Encoding: chunked\r\n",b"{}")
        self.assertEqual(400,status)
        self.assertIn(b"invalid body framing",body)

    def test_incomplete_body(self):
        status,body=self.post("Content-Length: 10\r\n",b"{}",half_close=True)
        self.assertEqual(400,status)
        self.assertIn(b"incomplete body",body)

    def test_real_socket_timeout_and_recovery(self):
        with patch.object(Handler,"timeout",0.2):
            status,body=self.post("Content-Length: 10\r\n",b"{}")
            self.assertEqual(408,status)
            self.assertIn(b"request timeout",body)
        self.assertEqual(200,self.health())

    def test_actual_concurrency_limit_and_recovery(self):
        sockets=[]
        # Hold handlers before headers are complete. Synchronize through
        # a test-only event instead of relying on timing or private semaphore fields.
        admitted=threading.Condition()
        count=[0]
        original=self.server.process_request_thread
        def tracked(request,address):
            with admitted:
                count[0]+=1
                admitted.notify_all()
            return original(request,address)
        with patch.object(self.server,"process_request_thread",side_effect=tracked):
            try:
                for index in range(MAX_CONNECTIONS):
                    s=self.connect()
                    sockets.append(s)
                    s.sendall(b"GET /api/f01/health HTTP/1.0\r\n")
                    with admitted:
                        self.assertTrue(admitted.wait_for(lambda:count[0]>=index+1,timeout=2))
                self.assertEqual(503,self.health())
            finally:
                for s in sockets:
                    s.close()
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            if self.health()==200:
                break
            time.sleep(0.03)
        else:
            self.fail("Server did not recover after releasing connections")
        self.assertEqual(200,self.health())

    def test_parallel_health(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda _:self.health(),range(24)))
        self.assertEqual([200]*24,results)
