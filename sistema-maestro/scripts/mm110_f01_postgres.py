"""PostgreSQL persistence with the same domain operations as SQLite Store."""
import hashlib
import json
import secrets
import time
from contextlib import closing
from mm110_f01_store import Store, SESSION_LIMIT, SESSION_TTL
from mm110_f01_session import Session, RULE
from progress_policy import validate_invariants

class PostgresStore(Store):
    def __init__(self, dsn):
        if not isinstance(dsn,str) or not dsn:
            raise ValueError("Database connection required")
        self._dsn = dsn

    def _connect(self):
        import psycopg
        db=psycopg.connect(self._dsn, connect_timeout=10, sslmode="verify-full",
                          prepare_threshold=None)
        return db

    def _run(self, learner, operation):
        if not isinstance(learner,str) or not learner or len(learner)>128:
            raise ValueError("Invalid learner identifier")
        with closing(self._connect()) as db, db.transaction():
            db.execute("SET LOCAL lock_timeout = '10s'")
            db.execute("SET LOCAL statement_timeout = '15s'")
            # Transaction-scoped lock also protects first insertion for a learner.
            db.execute("SELECT pg_advisory_xact_lock(410110, hashtext(%s))",(learner,))
            row=db.execute("SELECT payload FROM academia_private.f01_sessions WHERE learner=%s",(learner,)).fetchone()
            session=Session(learner)
            if row:
                data=json.loads(row[0])
                session._state=data["state"]
                session._attempts=data["attempts"]
                if session._state["user_id"]!=learner:
                    raise ValueError("Stored learner mismatch")
                if (session._state["institution_id"],session._state["course_version"],session._state["node_id"])!=("unah","f01-r3","mm110-f01"):
                    raise ValueError("Stored curriculum mismatch")
                for attempt in session._attempts.values():
                    if "submission" in attempt:
                        attempt["submission"]=tuple(attempt["submission"])
                validate_invariants(session._state,RULE)
            result=operation(session)
            validate_invariants(session._state,RULE)
            payload=json.dumps({"state":session._state,"attempts":session._attempts},ensure_ascii=False)
            db.execute("INSERT INTO academia_private.f01_sessions(learner,payload) VALUES (%s,%s) ON CONFLICT(learner) DO UPDATE SET payload=excluded.payload",(learner,payload))
            return result

    def create_token(self):
        token=secrets.token_urlsafe(32)
        digest=hashlib.sha256(token.encode("ascii")).hexdigest()
        with closing(self._connect()) as db, db.transaction():
            db.execute("SET LOCAL lock_timeout = '10s'")
            db.execute("SET LOCAL statement_timeout = '15s'")
            db.execute("SELECT pg_advisory_xact_lock(410111,0)")
            now=int(time.time())
            db.execute("DELETE FROM academia_private.f01_tokens WHERE expires<=%s",(now,))
            if db.execute("SELECT COUNT(*) FROM academia_private.f01_tokens").fetchone()[0]>=SESSION_LIMIT:
                return None
            db.execute("INSERT INTO academia_private.f01_tokens(digest,learner,expires) VALUES (%s,%s,%s)",(digest,secrets.token_hex(16),now+SESSION_TTL))
        return token

    def learner_for_token(self,token):
        if not isinstance(token,str) or len(token)!=43 or not token.isascii():
            return None
        digest=hashlib.sha256(token.encode("ascii")).hexdigest()
        with closing(self._connect()) as db:
            row=db.execute("SELECT learner FROM academia_private.f01_tokens WHERE digest=%s AND expires>%s",(digest,int(time.time()))).fetchone()
            return row[0] if row else None

    def token_count(self):
        with closing(self._connect()) as db:
            return db.execute("SELECT COUNT(*) FROM academia_private.f01_tokens WHERE expires>%s",(int(time.time()),)).fetchone()[0]
