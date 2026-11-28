"""STEM-05 shadow comparison. No dispatch, skip, or PASS transfer."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import yaml

SNAPSHOT=Path(__file__).with_name("frontend-run-observations.json")
PHASES=("install","typecheck","test","build")
RECORD=re.compile(r"STEM frontend phase=(install|typecheck|test|build) checkout=([0-9a-f]{40}) node=(\S+) npm=(\S+)$")
LOCK=re.compile(r"Lockfile SHA256: ([0-9a-f]{64})\s+package-lock.json$")
def blob(text):
    raw=text.encode("utf-8")
    return hashlib.sha1(("blob %d"%len(raw)).encode()+bytes([0])+raw).hexdigest()

def observed(row):
    if row["status"]!="completed" or row["conclusion"]!="success" or row["job"]["conclusion"]!="success" or row["job"]["status"]!="completed":
        raise ValueError("unsuccessful or incomplete run/job")
    if not re.fullmatch(r"[0-9a-f]{40}",row["head_sha"]) or not isinstance(row["attempt"],int) or row["attempt"]<1:
        raise ValueError("invalid run identity")
    if blob(row["workflow_yaml"])!=row["workflow_blob"]:
        raise ValueError("workflow blob mismatch")
    spec=yaml.load(row["workflow_yaml"],Loader=yaml.BaseLoader)
    job=spec["jobs"][row["job"]["name"]]
    declared=[]
    exclusive=[]
    for step in job["steps"]:
        command=step.get("run","")
        match=re.fullmatch(r"bash (?:\.\./)?scripts/certification/frontend-runner\.sh (install|typecheck|test|build)",command)
        if match:
            matches=[s for s in row["job"]["steps"] if s["name"]==step.get("name")]
            if len(matches)!=1 or matches[0]["conclusion"]!="success" or matches[0]["status"]!="completed":
                raise ValueError("required phase not executed")
            declared.append((match[1],step.get("working-directory",job.get("defaults",{}).get("run",{}).get("working-directory",".")),step.get("env",{}),step.get("shell")))
        elif "run" in step:
            exclusive.append(step.get("name",command))
    if tuple(x[0] for x in declared)!=PHASES:
        raise ValueError("missing or duplicate declared phase")
    phases=[]
    current=None
    images=[]
    versions=[]
    counts=[]
    for line in row["log_excerpt"]:
        line=line.split(" ",1)[-1].strip()
        m=RECORD.fullmatch(line)
        if m:
            if current is not None:
                raise ValueError("missing lockfile record")
            current=m.groups()
            continue
        m=LOCK.fullmatch(line)
        if m:
            if current is None:
                raise ValueError("unbound lockfile record")
            phases.append((*current,m[1]))
            current=None
        if line.startswith("Image: "): images.append(line)
        if line.startswith("Version: "): versions.append(line)
        if re.match(r"(Test Files|Tests)\s+\d+ passed",line): counts.append(line)
    if current is not None or tuple(p[0] for p in phases)!=PHASES or len(set(p[1:] for p in phases))!=1:
        raise ValueError("incomplete or inconsistent phase identity")
    if len(images)!=1 or len(versions)!=1 or len(counts)!=2:
        raise ValueError("missing runner image or test summary")
    checkout,node,npm,lock=phases[0][1:]
    context={"repository":row["repository"],"checkout":checkout,"node":node,"npm":npm,"lockfile":lock,"image":images[0],"image_version":versions[0],"test_summary":counts,"phases":declared,"runner":job.get("runs-on"),"setup":[s for s in job["steps"] if str(s.get("uses","")).startswith(("actions/checkout@","actions/setup-node@"))],"workflow_env":spec.get("env",{}),"job_env":job.get("env",{})}
    return {"context":context,"exclusive_steps":exclusive,"run_id":row["run_id"],"workflow":row["workflow"],"head_sha":row["head_sha"],"event":row["event"]}

def compare(left,right):
    a,b=observed(left),observed(right)
    if a["run_id"]==b["run_id"] or a["workflow"]==b["workflow"]:
        raise ValueError("comparison requires separate workflows")
    differences=[k for k in a["context"] if a["context"][k]!=b["context"][k]]
    return {"repository":a["context"]["repository"],"runs":[a["run_id"],b["run_id"]],"actual_checkouts":[a["context"]["checkout"],b["context"]["checkout"]],"head_shas":[a["head_sha"],b["head_sha"]],"differences":differences,"exclusive_steps":[a["exclusive_steps"],b["exclusive_steps"]],"decision":"RUN" if differences else "REVIEW","reuse_authorized":False,"reason":"Different observed execution inputs" if differences else "Matching observed inputs; independent completeness, artifact integrity and gate equivalence still require proof"}

def audit(data):
    rows=data["observations"]
    if data["schema_version"]!=1 or len({(r["repository"],r["run_id"]) for r in rows})!=len(rows):
        raise ValueError("invalid or duplicate observations")
    groups={}
    for r in rows: groups.setdefault(r["repository"],[]).append(r)
    if not groups or any(len(v)!=2 for v in groups.values()):
        raise ValueError("expected exactly two observations per repository")
    return [compare(*v) for v in groups.values()]

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("snapshot",nargs="?",type=Path,default=SNAPSHOT)
    args=parser.parse_args()
    print(json.dumps(audit(json.loads(args.snapshot.read_text(encoding="utf-8"))),indent=2,ensure_ascii=False))
