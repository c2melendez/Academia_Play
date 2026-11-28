"""STEM-08: measured work, connected reuse and potential overlap, not PASS."""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from workflow_overlap import audit as overlap_audit
from frontend_evidence import audit as evidence_audit

ROOT=Path(__file__).resolve().parent
REPO="c2melendez/Academia_Play"
WORKFLOWS={
    "contracts":(".github/workflows/academia-play-contracts.yml","Run positive and negative contract tests"),
    "browser":(".github/workflows/f01-browser.yml","Run real browser pilot suite"),
    "postgres":(".github/workflows/f01-postgres-qa.yml","Run python sistema-maestro/tests/postgres_f01_integration.py"),
}
SHA=re.compile(r"[0-9a-f]{40}")

def load(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))

def interval(row):
    a,b=(datetime.fromisoformat(row[k].replace("Z","+00:00")) for k in ("started_at","completed_at"))
    if a.tzinfo is None or b.tzinfo is None or a>b:
        raise ValueError("invalid execution timestamps")
    return a,b

def summarize(data):
    if data["schema_version"]!=1 or data["repository"]!=REPO or data["scope"]!="MM110-F01-F05":
        raise ValueError("unsupported snapshot scope")
    groups={"before":{},"after":{}}
    runs=set()
    jobs=set()
    for row in data["observations"]:
        phase,suite=row["phase"],row["suite"]
        if phase not in groups or suite not in WORKFLOWS or suite in groups[phase]:
            raise ValueError("duplicate or unknown suite")
        if row["repository"]!=REPO or row["event"]!="pull_request" or not all(SHA.fullmatch(row[k]) for k in ("head_sha","checkout_sha")):
            raise ValueError("repository/event/sha mismatch")
        if row["run_id"] in runs or row["job"]["id"] in jobs or type(row["run_attempt"]) is not int or row["run_attempt"]<1:
            raise ValueError("duplicate or invalid execution identity")
        runs.add(row["run_id"]);jobs.add(row["job"]["id"])
        if any(x["status"]!="completed" or x["conclusion"]!="success" for x in (row,row["job"])) or row["step"]["conclusion"]!="success":
            raise ValueError("non-success observation")
        if (row["workflow"],row["step"]["name"])!=WORKFLOWS[suite]:
            raise ValueError("workflow/step mismatch")
        counts=re.fullmatch(r"Ran (\d+) tests in ([\d.]+)s",row["test_summary"])
        if not counts or int(counts[1])<=0:
            raise ValueError("missing test count")
        a,b=interval(row["job"])
        s,e=interval(row["step"])
        if not a<=s<=e<=b:
            raise ValueError("step outside job")
        groups[phase][suite]={"run_id":row["run_id"],"head":row["head_sha"],"checkout":row["checkout_sha"],"tests":int(counts[1]),"job_seconds":int((b-a).total_seconds()),"test_step_seconds":int((e-s).total_seconds())}
    result={}
    for phase,rows in groups.items():
        if set(rows)!=set(WORKFLOWS) or len({r["head"] for r in rows.values()})!=1 or len({r["checkout"] for r in rows.values()})!=1:
            raise ValueError("incomplete or mixed checkout")
        result[phase]={"suites":rows,"tests_executed_in_successful_suites":sum(r["tests"] for r in rows.values()),"job_seconds":sum(r["job_seconds"] for r in rows.values()),"test_step_seconds":sum(r["test_step_seconds"] for r in rows.values())}
    if next(iter(groups["after"].values()))["head"]!=data["asset_commit"] or next(iter(groups["before"].values()))["head"]==data["asset_commit"]:
        raise ValueError("asset revision mismatch")
    assets={}
    for asset in data["assets"]:
        raw=asset["content"].encode("utf-8")
        blob=hashlib.sha1(("blob %d"%len(raw)).encode()+b"\0"+raw).hexdigest()
        if asset["path"] in assets or blob!=asset["blob"]:
            raise ValueError("asset blob mismatch or duplicate")
        assets[asset["path"]]=asset["content"]
    renderer="sistema-maestro/pilot/stem_area_grid.js"
    loader="sistema-maestro/scripts/mm110_pilot_page.py"
    pages=["sistema-maestro/pilot/mm110_f01.html","sistema-maestro/pilot/mm110_m1.html"]
    if set(assets)!={renderer,loader,*pages} or assets[renderer].count("function renderStemAreaGrid(")!=1 or "stem_area_grid.js" not in assets[loader]:
        raise ValueError("missing shared renderer/loader")
    for page in pages:
        if assets[page].count("/* STEM_AREA_GRID */")!=1 or "renderStemAreaGrid(" not in assets[page] or Path(page).name not in assets[loader]:
            raise ValueError("consumer not connected")
    prior,after=result["before"],result["after"]
    return {"status":"OBSERVED_ONLY","MM110":result,
            "change":{"tests":after["tests_executed_in_successful_suites"]-prior["tests_executed_in_successful_suites"],"job_seconds":after["job_seconds"]-prior["job_seconds"],"test_step_seconds":after["test_step_seconds"]-prior["test_step_seconds"]},
            "reuse":{"shared_renderers":1,"connected_templates":len(pages),"source_revision":data["asset_commit"]},
            "actual_time_saved_seconds":None,"certified_curricular_ids":None,"empirical_learning_gain":None,"certification_transfer":False}

def report():
    result=summarize(load("productivity-observations.json"))
    overlap=overlap_audit(load("workflow-observations.json")["observations"])
    evidence=evidence_audit(load("frontend-run-observations.json"))
    result["precision_overlap"]={"candidate_groups":len(overlap["candidates"]),"potential_runner_seconds_lower_bound":overlap["paired_runner_seconds_lower_bound"],"observed_pairs":[{"repository":r["repository"],"decision":r["decision"],"reuse_authorized":r["reuse_authorized"]} for r in evidence],"actual_time_saved_seconds":None}
    return result

if __name__=="__main__":
    print(json.dumps(report(),ensure_ascii=False,indent=2))
