"""Validate an original candidate learning resource; never a curricular PASS."""
import json
from fractions import Fraction
from pathlib import Path
from pilot import PATTERN,reference
ASSET=Path(__file__).with_name("rational-learning-candidate.json")

def verify(data):
    if data["schema_version"]!=1 or data["status"]!="CANDIDATE" or data["scope"]!="principal-real-root-rational-sum":
        raise ValueError("unsupported asset state/scope")
    route=data["route"]
    if len(route["lessons"])<2 or len(route["transfer"])<3 or len(route["summary"])<3:
        raise ValueError("missing learning stages")
    ids=set()
    stimuli=set()
    for transfer,tasks in ((False,route["lessons"]),(True,route["transfer"])):
        for task in tasks:
            if task["id"] in ids or task["prompt"] in stimuli:
                raise ValueError("duplicate task")
            ids.add(task["id"])
            stimuli.add(task["prompt"])
            answer=reference(task["prompt"])
            values=[Fraction(x) for x in task["options"]]
            if len(values)!=4 or len(set(values))!=4 or answer!=Fraction(task["answer"]) or task["answer"] not in task["options"]:
                raise ValueError("wrong answer or equivalent options")
            if str(answer)!=task["answer"]:
                raise ValueError("noncanonical answer")
            if set(task["errors"])!=set(task["options"])-{task["answer"]} or not all(task["errors"].values()) or not task["explanation"]:
                raise ValueError("incomplete feedback")
            if transfer and ("hint" in task or "bridge" in task):
                raise ValueError("transfer leaks scaffolding")
            if not transfer and (not task.get("hint") or len(task.get("bridge",[]))<3):
                raise ValueError("missing learning scaffolding")
    return sorted(ids)

if __name__=="__main__":
    print(json.dumps({"candidate_ids":verify(json.loads(ASSET.read_text(encoding="utf-8"))),"curricular_pass":False},ensure_ascii=False))
