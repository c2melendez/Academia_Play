"""Read-only STEM-06 extension to provider reconciliation (branch-local evidence).
Never updates checkpoints, merges, deploys, skips tests or assigns PASS.
"""
import base64
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import quote, urlencode
from provider_evidence import REPOSITORY, get_json
from validate_academia_play import validate_continuity

BRANCHES=("main","curriculum/mm110")
SHA=re.compile(r"[0-9a-f]{40}")
CONTRACTS=".github/workflows/academia-play-contracts.yml"
CURRICULUM_WORKFLOWS=(CONTRACTS,".github/workflows/f01-browser.yml",".github/workflows/f01-postgres-qa.yml")

def valid_sha(value):
    if not isinstance(value,str) or not SHA.fullmatch(value):
        raise ValueError("invalid observed SHA")
    return value

def branch_head(get,branch):
    return valid_sha(get("git/ref/heads/"+quote(branch,safe="/"))["object"]["sha"])

def checkpoint(get,sha):
    item=get("contents/continuity.json?"+urlencode({"ref":sha}))
    if item["encoding"]!="base64":
        raise ValueError("unsupported checkpoint encoding")
    data=json.loads(base64.b64decode(item["content"]).decode("utf-8"))
    if validate_continuity(data) or data["repository_full_name"]!=REPOSITORY:
        raise ValueError("invalid checkpoint identity")
    return data

def run_report(get,sha,branch):
    payload=get("actions/runs?"+urlencode({"head_sha":sha,"per_page":100}))
    rows=payload["workflow_runs"]
    if payload["total_count"]>len(rows):
        raise ValueError("incomplete workflow run page")
    required=(CONTRACTS,) if branch=="main" else CURRICULUM_WORKFLOWS
    results=[]
    for path in required:
        candidates=[r for r in rows if r.get("head_sha")==sha and r.get("head_branch")==branch and r.get("path","").split("@",1)[0]==path and r.get("event") in ("push","pull_request","workflow_dispatch") and (r.get("repository") or {}).get("full_name")==REPOSITORY]
        candidates.sort(key=lambda r:(r.get("created_at",""),r["id"]),reverse=True)
        if not candidates:
            results.append({"workflow":path,"state":"NO_CURRENT_RUN"})
            continue
        r=candidates[0]
        status=r.get("status")
        conclusion=r.get("conclusion")
        state=("PENDING" if status!="completed" else "FAILED_OR_NON_SUCCESS" if conclusion!="success" else "PR_RESULT_REQUIRES_CHECKOUT_VERIFICATION" if r["event"]=="pull_request" else "SUCCESS_REPORTED_REQUIRES_STEP_VERIFICATION")
        results.append({"workflow":path,"run_id":r["id"],"attempt":r.get("run_attempt"),"event":r["event"],"state":state})
    return results

def audit(get):
    heads={b:branch_head(get,b) for b in BRANCHES}
    main,work=(heads[b] for b in BRANCHES)
    compare=get("compare/"+main+"..."+work)
    ahead,behind=compare["ahead_by"],compare["behind_by"]
    if type(ahead) is not int or type(behind) is not int or min(ahead,behind)<0 or compare["base_commit"]["sha"]!=main:
        raise ValueError("invalid comparison")
    valid_sha(compare["merge_base_commit"]["sha"])
    branch_reports=[]
    for branch,sha in heads.items():
        cp=checkpoint(get,sha)
        branch_reports.append({"branch":branch,"head":sha,"checkpoint_branch":cp["active_branch"],"checkpoint_sha":cp["repo_head_sha"],"checkpoint_state":"CURRENT_POINTER" if cp["active_branch"]==branch and cp["repo_head_sha"]==sha else "HISTORICAL_OR_STALE_POINTER","qa_evidence_sha":cp["qa_ci_verified_sha"],"qa_pointer_matches_head":cp["qa_ci_verified_sha"]==sha,"deployment_evidence_sha":cp["last_verified_deploy_sha"],"course_design_status":cp["course_design_status"],"active_module_id":cp["active_module_id"],"module_states":cp["module_states"],"runs":run_report(get,sha,branch)})
    if any(branch_head(get,b)!=sha for b,sha in heads.items()):
        return {"status":"INCONCLUSIVE","reason":"branch moved during observation","certification_transfer":False}
    return {"status":"RECONCILE_REQUIRED" if behind else "CURRICULUM_CONTAINS_MAIN","main_commits_missing":behind,"curriculum_commits_ahead":ahead,"branches":branch_reports,"certification_transfer":False,"render_status":"NOT_QUERIED_USE_EXISTING_P0_PROVIDER_RECONCILIATION","observed_at":datetime.now(timezone.utc).isoformat()}

def main():
    token=os.environ.get("GITHUB_TOKEN")
    try:
        result=audit(lambda path:get_json("https://api.github.com/repos/"+REPOSITORY+"/"+path,token))
    except Exception as exc:
        result={"status":"INCONCLUSIVE","reason":type(exc).__name__,"certification_transfer":False}
    output=json.dumps(result,indent=2,ensure_ascii=False)
    print(output)
    summary=os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as stream:
            stream.write("\n### STEM-06 — observación de continuidad (solo lectura)\n\n```json\n"+output+"\n```\n")
    # Advisory: no false gate PASS and no new blocking dependency on provider availability.
    return 0

if __name__=="__main__":
    raise SystemExit(main())
