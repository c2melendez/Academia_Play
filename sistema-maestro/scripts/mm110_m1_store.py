"""M1 local transactional sessions; trusted learner IDs supplied by caller.
No HTTP exposure or mastery grants. All existing formative pilot work stays assisted.
"""
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4
from mm110_m1_activities import ITEMS, INDEX, public_item, assess, public_assessment

REVISION="bb8efaa1adb12a5181e9dbbc897c02f9ed6ba9e0b12608568fc63219a7c14f53"
MAX_ATTEMPTS=300
MAX_EXAMS=20
FAMILIES=tuple("F%02d"%i for i in range(2,8))

class Store:
    def __init__(self,path):
        self.path=str(Path(path).resolve())
        with closing(self.connect()) as db:
            db.execute("CREATE TABLE IF NOT EXISTS m1_sessions (learner TEXT PRIMARY KEY, payload TEXT NOT NULL)")
    def connect(self):
        return sqlite3.connect(self.path,timeout=10,isolation_level=None)
    def _run(self,learner,fn):
        if not isinstance(learner,str) or not learner or len(learner)>128:
            raise ValueError("invalid learner")
        with closing(self.connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row=db.execute("SELECT payload FROM m1_sessions WHERE learner=?",(learner,)).fetchone()
                state=json.loads(row[0]) if row else {"revision":REVISION,"attempts":{},"exams":{}}
                if state["revision"]!=REVISION:
                    raise ValueError("curriculum mismatch")
                result=fn(state)
                db.execute("INSERT INTO m1_sessions VALUES (?,?) ON CONFLICT(learner) DO UPDATE SET payload=excluded.payload",
                           (learner,json.dumps(state,ensure_ascii=False)))
                db.commit()
                return result
            except BaseException:
                db.rollback()
                raise
    @staticmethod
    def _active(s):
        return next((k for k,v in s["exams"].items() if "review" not in v),None)
    @staticmethod
    def _new(s,item,exam=None):
        if len(s["attempts"])>=MAX_ATTEMPTS:
            raise ValueError("attempt limit")
        key=uuid4().hex
        s["attempts"][key]={"item":item,"exam":exam}
        return key
    @staticmethod
    def _exam_view(s,key):
        e=s["exams"][key]
        return {"exam_id":key,"maximum":len(e["attempts"]),"items":[
            {"attempt_id":a,**public_item(s["attempts"][a]["item"]),
             "recorded":"result" in s["attempts"][a]} for a in e["attempts"]]}
    def start(self,learner,item):
        def run(s):
            if self._active(s) or INDEX[item]["stage"]=="E":
                raise ValueError("unavailable")
            key=self._new(s,item)
            return {"attempt_id":key,**public_item(item)}
        return self._run(learner,run)
    def submit(self,learner,attempt,answer,reason_choice):
        # Bound input even for duplicate replay; null is valid for degree.
        if type(reason_choice) is not int or not 0<=reason_choice<3:
            raise ValueError("reason")
        if not (answer is None or type(answer) is int and 0<=answer<=16 or
                isinstance(answer,str) and len(answer)<=256 or
                isinstance(answer,list) and len(answer)==2 and
                all(isinstance(x,str) and len(x)<=256 for x in answer)):
            raise ValueError("answer format")
        def run(s):
            a=s["attempts"][attempt]
            if self._active(s)!=a["exam"]:
                raise ValueError("active exam boundary")
            submission=[answer,reason_choice]
            if "result" in a:
                if a["submission"]!=submission:
                    raise ValueError("conflicting replay")
                return public_assessment(a["result"])
            result=assess(a["item"],answer,reason_choice,assisted=a["exam"] is None)
            if result["status"] in ("RETRY","INVALID_INPUT"):
                return result
            a.update(result=result,submission=submission)
            return public_assessment(result)
        return self._run(learner,run)
    def start_exam(self,learner):
        def run(s):
            active=self._active(s)
            if active:
                return self._exam_view(s,active)
            if len(s["exams"])>=MAX_EXAMS:
                raise ValueError("exam limit")
            # A single available form is deliberately not reused for the same learner.
            pool=[i for i in ITEMS if i["stage"]=="E"]
            used={a["item"] for a in s["attempts"].values() if a["exam"] is not None}
            selected=[]
            for family in FAMILIES:
                item=next((i["id"] for i in pool if i["family"]==family and i["id"] not in used),None)
                if item is None:
                    raise ValueError("fresh exam bank exhausted")
                selected.append(item)
            key=uuid4().hex
            s["exams"][key]={"attempts":[self._new(s,i,key) for i in selected]}
            return self._exam_view(s,key)
        return self._run(learner,run)
    def active_exam(self,learner):
        def run(s):
            key=self._active(s)
            return self._exam_view(s,key) if key else None
        return self._run(learner,run)
    def finish_exam(self,learner,exam):
        def run(s):
            e=s["exams"][exam]
            if self._active(s) not in (None,exam):
                raise ValueError("active exam boundary")
            if "review" in e:
                return e["review"]
            records=[s["attempts"][a] for a in e["attempts"]]
            if not all(a.get("result",{}).get("status")=="RECORDED" for a in records):
                raise ValueError("incomplete exam")
            review=[{"item_id":a["item"],**a["result"]["private_assessment"],
                     "expected":INDEX[a["item"]]["expected"],
                     "explanation":INDEX[a["item"]]["explanation"],
                     "correct_reason":INDEX[a["item"]]["correct_reason"]} for a in records]
            e["review"]={"exam_id":exam,"maximum":len(review),"score":sum(r["accepted"] for r in review),"reviews":review}
            return e["review"]
        return self._run(learner,run)
    def progress(self,learner):
        def run(s):
            if self._active(s):
                raise ValueError("active exam boundary")
            return {"families":{f:{"completed":sorted({a["item"] for a in s["attempts"].values()
                if a["exam"] is None and INDEX[a["item"]]["family"]==f and a.get("result",{}).get("accepted")})}
                for f in FAMILIES},"mastery":"UNASSESSED","eligible_evidence":0}
        return self._run(learner,run)
