"""Read-only workflow overlap audit. Never skips, dispatches or certifies a gate."""
import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import yaml

SNAPSHOT=Path(__file__).with_name("workflow-observations.json")
COMMANDS=("npm ci","npm run typecheck","npm test","npm run build")

def seconds(step):
    if step.get("conclusion")!="success" or not step.get("started_at") or not step.get("completed_at"):
        return None
    a,b=(datetime.fromisoformat(step[k].replace("Z","+00:00")) for k in ("started_at","completed_at"))
    if a.tzinfo is None or b.tzinfo is None or b<a:
        raise ValueError("invalid step timestamps")
    return int((b-a).total_seconds())

def inventory(observations):
    rows=[]
    seen=set()
    for obs in observations:
        raw=obs["workflow_yaml"].encode("utf-8")
        blob=hashlib.sha1(("blob %d"%len(raw)).encode()+bytes([0])+raw).hexdigest()
        if blob!=obs["blob"]:
            raise ValueError("workflow Git blob mismatch")
        key=(obs["repository"],obs["run_id"])
        if key in seen:
            raise ValueError("duplicate run")
        seen.add(key)
        doc=yaml.load(obs["workflow_yaml"], Loader=yaml.BaseLoader)
        for job in obs["jobs"]:
            spec=doc["jobs"].get(job["name"])
            if not spec:
                raise ValueError("unsupported job naming: "+job["name"])
            runtime=next((s for s in spec["steps"] if str(s.get("uses","")).startswith("actions/setup-node@")),None)
            checkout=next((s for s in spec["steps"] if str(s.get("uses","")).startswith("actions/checkout@")),None)
            if not runtime or not checkout:
                continue
            by_name={s["name"]:s for s in job["steps"]}
            for step in spec["steps"]:
                command=step.get("run")
                if command not in COMMANDS:
                    continue
                if step.get("name") not in by_name:
                    continue
                observed=by_name[step["name"]]
                directory=step.get("working-directory",spec.get("defaults",{}).get("run",{}).get("working-directory","."))
                context={"runner":spec.get("runs-on"),"directory":directory,"setup_node":runtime.get("uses"),"setup_with":runtime.get("with",{}),"checkout":checkout.get("uses"),"checkout_with":checkout.get("with",{}),"workflow_env":doc.get("env",{}),"job_env":spec.get("env",{}),"step_env":step.get("env",{}),"shell":step.get("shell",spec.get("defaults",{}).get("run",{}).get("shell"))}
                rows.append({"repository":obs["repository"],"commit":obs["commit"],"workflow":obs["path"],"run_id":obs["run_id"],"job_id":job["id"],"command":command,"context":context,"condition":step.get("if"),"seconds":seconds(observed),"job_conclusion":job["conclusion"]})
    return rows

def audit(observations):
    groups=defaultdict(list)
    for row in inventory(observations):
        groups[(row["repository"],row["commit"],row["command"],row["context"]["directory"])].append(row)
    candidates=[]
    for key,rows in sorted(groups.items()):
        if len({r["workflow"] for r in rows})<2:
            continue
        # A matching command does not establish equivalent acceptance, including
        # earlier steps, action versions, lockfiles, guards and generated inputs.
        matching=all(r["context"]==rows[0]["context"] for r in rows)
        measured=[r["seconds"] for r in rows if r["seconds"] is not None and r["job_conclusion"]=="success"]
        candidates.append({"repository":key[0],"commit":key[1],"command":key[2],"directory":key[3],"classification":"SAME_DECLARED_CONTEXT_REVIEW" if matching else "CONTEXT_DIFF_REVIEW","observations":rows,"paired_runner_seconds_lower_bound":min(measured) if len(rows)==2 and len(measured)==2 else None,"reuse_authorized":False})
    return {"status":"DIAGNOSTIC_ONLY","candidates":candidates,"paired_runner_seconds_lower_bound":sum(c["paired_runner_seconds_lower_bound"] or 0 for c in candidates),"reuse_authorized":False}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("snapshot",nargs="?",type=Path,default=SNAPSHOT)
    args=parser.parse_args()
    print(json.dumps(audit(json.loads(args.snapshot.read_text(encoding="utf-8"))["observations"]),indent=2,ensure_ascii=False))
