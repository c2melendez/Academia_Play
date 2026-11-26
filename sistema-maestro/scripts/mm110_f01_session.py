"""F01 session controller. Server-owned in-memory state; persistence adapter pending."""
from copy import deepcopy
from uuid import uuid4
from datetime import datetime, timezone
from threading import RLock
from functools import wraps
from mm110_f01_activities import INDEX, public_item, hint, assess
from progress_policy import derive_mastery, validate_invariants

GUIDED_STAGES = (
    ("f01-a-sign-positive", "f01-a-fraction-negative"),
    ("f01-b-group", "f01-b-predict"),
    ("f01-route-expand", "f01-route-repair", "f01-tutor-inverse"),
    ("f01-route-transfer",),
)

RULE = {"distinct_variant_families":2,"requires_transfer":True,"unassisted_required":True}

def utc_now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')

def locked(method):
    @wraps(method)
    def wrapped(self,*args,**kwargs):
        with self._lock:
            return method(self,*args,**kwargs)
    return wrapped

class Session:
    def __init__(self, user_id):
        self._lock = RLock()
        self._state = {"user_id":user_id,"institution_id":"unah","course_version":"f01-r3",
                       "node_id":"mm110-f01","mastery_rule":dict(RULE),"access_grants":[],
                       "mastery_evidence":[],"review_events":[],"mastery_estimate":"UNASSESSED",
                       "updated_at":utc_now()}
        self._attempts = {}

    @locked
    def snapshot(self):
        return deepcopy(self._state)

    @locked
    def guided_progress(self):
        completed = {a["item"] for a in self._attempts.values()
                     if a.get("guided") and a.get("closed")
                     and a.get("assessment", {}).get("accepted")
                     and not a.get("assisted")}
        for stage, ids in enumerate(GUIDED_STAGES):
            pending = [i for i in ids if i not in completed]
            if pending:
                return {"stage": "ABCT"[stage], "pending": pending, "completed": sorted(completed)}
        return {"stage": "COMPLETE", "pending": [], "completed": sorted(completed)}

    @locked
    def start_guided(self,item_id):
        if item_id not in self.guided_progress()["pending"]:
            raise ValueError("Guided prerequisite not satisfied")
        result = self.start(item_id, INDEX[item_id].mode)
        self._attempts[result["attempt_id"]]["guided"] = True
        return result

    @locked
    def start(self,item_id,mode):
        item = INDEX[item_id]
        if item.mode != mode:
            raise ValueError("Item unavailable in this mode")
        key = uuid4().hex
        self._attempts[key] = {"item":item_id,"assisted":False,"closed":False}
        return {"attempt_id":key,**public_item(item_id)}

    @locked
    def request_hint(self,attempt_id,index):
        a = self._attempts[attempt_id]
        if a["closed"]:
            raise ValueError("Attempt closed")
        result = hint(a["item"],index)
        a["assisted"] = True
        return result

    @locked
    def submit(self,attempt_id,answer,reason_choice):
        a = self._attempts[attempt_id]
        if a["closed"]:
            if a["submission"] != (answer,reason_choice):
                raise ValueError("Conflicting submission")
            return deepcopy(a["result"])
        item = INDEX[a["item"]]
        # A previous completed attempt or hint on this exact item is exposure,
        # including attempts opened in parallel before feedback was disclosed.
        exposed = any(k != attempt_id and other["item"] == item.item_id
                      and (other.get("closed") or other.get("assisted"))
                      for k, other in self._attempts.items())
        result = assess(item.item_id,answer,reason_choice,a["assisted"])
        if exposed:
            result["eligible_evidence"] = False
        result["previously_exposed"] = exposed
        if result["oracle_status"] == "INCONCLUSIVE":
            return {"status":"RETRY","feedback":"No se pudo comprobar; intenta nuevamente."}
        if item.mode == "exam_preparation":
            # No correctness or explanation disclosed before exam review.
            public = {"status":"RECORDED"}
        else:
            public = result
            if result["eligible_evidence"]:
                role = "TRANSFER" if item.family == "contextual" else "PRACTICE"
                self._state["updated_at"] = utc_now()
                self._state["mastery_evidence"].append({
                    "evidence_id":attempt_id,"variant_family":item.family,"role":role,
                    "oracle_result":"VERIFIED","assisted":False,"idempotency_key":attempt_id})
                self._state["mastery_estimate"] = derive_mastery(self._state,RULE)
                if self._state["mastery_estimate"] == "MASTERED" and not self._state["access_grants"]:
                    self._state["access_grants"].append({"grant_id":"f01-completed",
                        "granted_at":self._state["updated_at"],
                        "evidence_ids":[e["evidence_id"] for e in self._state["mastery_evidence"]]})
                validate_invariants(self._state,RULE)
        a.update(closed=True,submission=(answer,reason_choice),result=deepcopy(public),assessment=result)
        return deepcopy(public)
