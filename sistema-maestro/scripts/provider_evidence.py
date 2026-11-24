#!/usr/bin/env python3
"""Read-only provider verification; never infer E1 from self-reported strings.

Requires explicit provider credentials. A missing token, bad response or mismatch
is an error, never PASS. Does not write repo files or publish a deployment.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

SHA = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY = "c2melendez/Academia_Play"
SERVICE_ID = "srv-dc06lp67bikc739hlghg"
CONTRACTS_WORKFLOW_PATH = ".github/workflows/academia-play-contracts.yml"
CONTRACTS_WORKFLOW_ID = 425123083


def get_json(url, token, *, render=False):
    if not token:
        raise ValueError("provider credential is missing")
    headers = {"Accept": "application/json", "User-Agent": "academia-play-p0-evidence"}
    if render:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def verify_observations(expected_sha, repo, run, render_service, deployments):
    """Validate factual relationships; input provenance is caller's responsibility."""
    errors = []
    if not SHA.fullmatch(expected_sha or ""):
        errors.append("expected SHA is not 40 lowercase hexadecimal characters")
    if repo.get("full_name") != REPOSITORY or repo.get("default_branch") != "main":
        errors.append("GitHub repository identity or default branch mismatch")
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        errors.append("GitHub workflow run not completed successfully")
    if run.get("head_sha") != expected_sha:
        errors.append("GitHub workflow SHA mismatch")
    if (run.get("repository") or {}).get("full_name") != REPOSITORY:
        errors.append("GitHub workflow repository identity mismatch")
    if run.get("workflow_id") != CONTRACTS_WORKFLOW_ID or run.get("path") != CONTRACTS_WORKFLOW_PATH:
        errors.append("GitHub run is not the canonical contracts workflow")
    if run.get("event") != "push" or run.get("head_branch") != "main":
        errors.append("GitHub contracts run must be a push on main")
    if render_service.get("id") != SERVICE_ID:
        errors.append("Render service identity mismatch")
    if render_service.get("repo", "").rstrip("/") != f"https://github.com/{REPOSITORY}":
        errors.append("Render GitHub repository mismatch")
    if render_service.get("branch") != "main":
        errors.append("Render deploy branch mismatch")
    if not isinstance(deployments, list) or not deployments:
        errors.append("No Render deployments observed")
    else:
        # Render's REST endpoint returns entries with a 'deploy' envelope.
        latest = deployments[0]
        deploy = latest.get("deploy", latest) if isinstance(latest, dict) else {}
        if deploy.get("status", "").lower() != "live":
            errors.append("Latest Render deployment is not live")
        if (deploy.get("commit") or {}).get("id") != expected_sha:
            errors.append("Latest Render deployment SHA mismatch")
        if not deploy.get("id"):
            errors.append("Latest Render deployment ID missing")
    return errors


def observe(expected_sha, run_id, github_token, render_token, repo=REPOSITORY, service_id=SERVICE_ID):
    if repo != REPOSITORY or service_id != SERVICE_ID:
        raise ValueError("Only the canonical repository and service are supported")
    if not SHA.fullmatch(expected_sha or ""):
        raise ValueError("Invalid expected SHA")
    if not str(run_id).isdigit() or int(run_id) <= 0:
        raise ValueError("Invalid GitHub workflow run ID")
    github_repo = get_json(f"https://api.github.com/repos/{repo}", github_token)
    workflow = get_json(f"https://api.github.com/repos/{repo}/actions/runs/{run_id}", github_token)
    render_service = get_json(f"https://api.render.com/v1/services/{service_id}", render_token, render=True)
    deployments = get_json(f"https://api.render.com/v1/services/{service_id}/deploys?limit=1",
                           render_token, render=True)
    errors = verify_observations(expected_sha, github_repo, workflow, render_service, deployments)
    result = {
        "result": "VERIFIED_OBSERVATION" if not errors else "REJECTED_OBSERVATION",
        "repository": repo,
        "service_id": service_id,
        "target_sha": expected_sha,
        "workflow_run_id": str(run_id),
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "errors": errors,
        "workflow_url": workflow.get("html_url"),
        "deployment_id": None,
        "deployment_finished_at": None,
    }
    if isinstance(deployments, list) and deployments:
        newest = deployments[0]
        item = newest.get("deploy", newest) if isinstance(newest, dict) else {}
        result["deployment_id"] = item.get("id")
        result["deployment_finished_at"] = item.get("finishedAt")
    return result


def main():
    parser = argparse.ArgumentParser(description="Read-only verification of GitHub CI + Render deployment")
    parser.add_argument("--sha", required=True, help="Exact commit SHA")
    parser.add_argument("--run-id", required=True, help="GitHub Actions run ID for that SHA")
    args = parser.parse_args()
    try:
        result = observe(args.sha, args.run_id, os.environ.get("GITHUB_TOKEN"),
                         os.environ.get("RENDER_API_KEY"))
    except (ValueError, urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"result": "BLOCKED", "reason": type(exc).__name__,
                          "detail": str(exc) if not isinstance(exc, urllib.error.HTTPError)
                          else f"HTTP {exc.code}"}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "VERIFIED_OBSERVATION" else 1


if __name__ == "__main__":
    sys.exit(main())
