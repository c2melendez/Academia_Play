"""Transactional local persistence for F01. No HTTP authentication or deployment policy.
Caller must supply a trusted, authenticated learner identifier. Use a durable
volume in production; the default ephemeral hosting filesystem is unsuitable.
"""
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from mm110_f01_session import Session, RULE
from progress_policy import validate_invariants

class Store:
    def __init__(self, path):
        self.path = str(Path(path).resolve())
        with closing(self._connect()) as db:
            db.execute("CREATE TABLE IF NOT EXISTS f01_sessions (learner TEXT PRIMARY KEY, payload TEXT NOT NULL)")
            db.commit()

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def _run(self, learner, operation):
        if not isinstance(learner, str) or not learner or len(learner)>128:
            raise ValueError("Invalid learner identifier")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute("SELECT payload FROM f01_sessions WHERE learner=?", (learner,)).fetchone()
                session = Session(learner)
                if row:
                    data = json.loads(row[0])
                    session._state = data["state"]
                    session._attempts = data["attempts"]
                    if session._state["user_id"] != learner:
                        raise ValueError("Stored learner mismatch")
                    if (session._state["institution_id"], session._state["course_version"], session._state["node_id"]) != ("unah","f01-r3","mm110-f01"):
                        raise ValueError("Stored curriculum mismatch")
                    for attempt in session._attempts.values():
                        if "submission" in attempt:
                            attempt["submission"] = tuple(attempt["submission"])
                    validate_invariants(session._state,RULE)
                result = operation(session)
                validate_invariants(session._state,RULE)
                payload = json.dumps({"state":session._state,"attempts":session._attempts},ensure_ascii=False)
                db.execute("INSERT INTO f01_sessions(learner,payload) VALUES (?,?) ON CONFLICT(learner) DO UPDATE SET payload=excluded.payload",(learner,payload))
                db.commit()
                return result
            except BaseException:
                db.rollback()
                raise

    def snapshot(self, learner):
        return self._run(learner,lambda s:s.snapshot())

    def guided_progress(self, learner):
        return self._run(learner,lambda s:s.guided_progress())

    def start_guided(self, learner, item_id):
        return self._run(learner,lambda s:s.start_guided(item_id))

    def start(self, learner, item_id, mode):
        return self._run(learner,lambda s:s.start(item_id,mode))

    def request_hint(self, learner, attempt_id, index):
        return self._run(learner,lambda s:s.request_hint(attempt_id,index))

    def submit(self, learner, attempt_id, answer, reason_choice):
        if not isinstance(answer,str) or len(answer)>256 or type(reason_choice) is not int or not 0<=reason_choice<=2:
            raise ValueError("Invalid submission format")
        return self._run(learner,lambda s:s.submit(attempt_id,answer,reason_choice))

    def finish_exam(self, learner, attempt_id):
        return self._run(learner,lambda s:s.finish_exam(attempt_id))
