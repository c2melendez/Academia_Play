#!/usr/bin/env python3
"""Atomic, opt-in reconciliation of authenticated provider observations into GitHub.

The observed SHA is the PRE-RECONCILIATION commit. This write creates a new
commit; it must not be presented as evidence that the new commit is deployed.
Only the trusted observe() call may supply the observation, never a JSON file.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from copy import deepcopy

from provider_evidence import REPOSITORY, SERVICE_ID, observe
from validate_academia_play import validate_continuity, validate_event

SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
API_BASE = f"https://api.github.com/repos/{REPOSITORY}"
EVENT_DIRECTORY = "sistema-maestro/execution-events"


class ConcurrentUpdate(RuntimeError):
    """Another agent changed main; do not overwrite or rebase implicitly."""


class PersistenceBlocked(RuntimeError):
    """Missing permission, invalid input or an unverified observation."""


def api_request(method: str, path: str, token: str, payload=None):
    """Call GitHub API; errors propagate without exposing the token."""
    if not token:
        raise PersistenceBlocked("GITHUB_TOKEN not configured")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "academia-play-p0-reconcile",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(f"{API_BASE}/{path}", data=data,
                                     headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def event_paths(sha: str, run_id: str):
    if not SHA_PATTERN.fullmatch(sha or "") or not str(run_id).isdigit() or int(run_id) <= 0:
        raise PersistenceBlocked("Invalid SHA or workflow run ID")
    basename = f"reconcile-{sha}-{run_id}"
    return (f"{EVENT_DIRECTORY}/{basename}.json",
            f"{EVENT_DIRECTORY}/{basename}.observation.json")


def build_change(checkpoint: dict, observation: dict, run_id: str):
    """Pure transformation; source must be the result of observe() in this process."""
    errors = validate_continuity(checkpoint)
    if errors:
        raise PersistenceBlocked(f"Invalid continuity checkpoint: {errors}")
    if observation.get("result") != "VERIFIED_OBSERVATION" or observation.get("errors"):
        raise PersistenceBlocked("Authenticated provider observation is not verified")
    sha = observation.get("target_sha")
    event_path, snapshot_path = event_paths(sha, run_id)
    if (observation.get("repository") != checkpoint["repository_full_name"]
            or observation.get("repository") != REPOSITORY
            or observation.get("service_id") != checkpoint["render_service_id"]
            or observation.get("service_id") != SERVICE_ID
            or observation.get("workflow_run_id") != str(run_id)
            or not observation.get("deployment_id")
            or not observation.get("observed_at")):
        raise PersistenceBlocked("Provider observation identity or provenance mismatch")
    updated = deepcopy(checkpoint)
    updated["active_branch"] = "main"
    updated["repo_head_sha"] = sha
    updated["qa_ci_verified_sha"] = sha
    updated["last_verified_deploy_sha"] = sha
    # This field means the deployment's actual finished-at time, not when queried.
    updated["last_verified_deploy_at"] = observation.get("deployment_finished_at")
    updated["last_observed_at"] = observation["observed_at"]
    updated["last_verified_commands"] = (updated["last_verified_commands"] + [
        f"RECONCILIAR provider-observed CI run {run_id} deployment {observation['deployment_id']}"
    ])[-20:]
    # Preserve all curriculum approvals, module states, blockers and next action.
    errors = validate_continuity(updated)
    if errors:
        raise PersistenceBlocked(f"Reconciled checkpoint is invalid: {errors}")
    event = {
        "event_id": f"RECONCILIAR-{sha}-{run_id}",
        "timestamp": observation["observed_at"],
        "action": "RECONCILIAR",
        "actor": "authenticated-provider-observer",
        "environment_mode": updated["environment_mode"],
        "evidence_level": "E1",
        "summary": f"Observed CI run {run_id} and Render deploy {observation['deployment_id']} for pre-write SHA {sha}",
        "repo_sha": sha,
        "result": "VERIFIED_OBSERVATION",
    }
    errors = validate_event(event)
    if errors:
        raise PersistenceBlocked(f"Execution event fails contract: {errors}")
    snapshot = {
        "observation": observation,
        "meaning": "Historical pre-write provider observation, not current deployed HEAD",
        "source": "provider_evidence.observe authenticated calls in the same process",
    }
    def serialize(item):
        return json.dumps(item, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    return {
        "continuity.json": serialize(updated),
        event_path: serialize(event),
        snapshot_path: serialize(snapshot),
    }


def read_text_content(path, token):
    """Use the content API for branch-scoped read and blob SHA."""
    import base64
    safe = urllib.parse.quote(path, safe="/")
    info = api_request("GET", f"contents/{safe}?ref=main", token)
    if info.get("encoding") != "base64":
        raise PersistenceBlocked(f"Unsupported content encoding for {path}")
    decoded = base64.b64decode(info["content"]).decode("utf-8")
    return decoded, info["sha"]


def existing_event(path, token):
    try:
        content, _ = read_text_content(path, token)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    return json.loads(content)


def persist_verified_observation(expected_head: str, run_id: str, github_token: str,
                                 render_token: str, *, dry_run=False):
    """Optimistic HEAD lock plus atomic three-file Git commit, never force push."""
    event_path, snapshot_path = event_paths(expected_head, run_id)
    # Idempotence before HEAD precondition permits safe retry after success.
    earlier = existing_event(event_path, github_token)
    if earlier is not None:
        if (earlier.get("event_id") == f"RECONCILIAR-{expected_head}-{run_id}"
                and earlier.get("repo_sha") == expected_head
                and earlier.get("result") == "VERIFIED_OBSERVATION"):
            return {"result": "ALREADY_RECORDED", "event_path": event_path,
                    "note": "Historical event exists; does not prove current LIVE"}
        raise PersistenceBlocked("Event path occupied by nonmatching record")

    ref = api_request("GET", "git/ref/heads/main", github_token)
    current_head = (ref.get("object") or {}).get("sha")
    if current_head != expected_head:
        raise ConcurrentUpdate(f"Expected main {expected_head}; current main {current_head}")
    current_text, _ = read_text_content("continuity.json", github_token)
    checkpoint = json.loads(current_text)
    observation = observe(expected_head, run_id, github_token, render_token)
    changes = build_change(checkpoint, observation, run_id)
    if dry_run:
        return {"result": "DRY_RUN", "observed_sha": expected_head,
                "proposed_paths": sorted(changes),
                "note": "No Git objects or refs were written"}

    # Prevent rewriting a checkpoint if another agent committed during observation.
    latest = api_request("GET", "git/ref/heads/main", github_token)
    if (latest.get("object") or {}).get("sha") != expected_head:
        raise ConcurrentUpdate("main advanced during provider observation")
    parent = api_request("GET", f"git/commits/{expected_head}", github_token)
    base_tree = (parent.get("tree") or {}).get("sha")
    if not base_tree:
        raise PersistenceBlocked("Unable to read parent tree")

    tree = api_request("POST", "git/trees", github_token, {
        "base_tree": base_tree,
        "tree": [
            {"path": path, "mode": "100644", "type": "blob", "content": data}
            for path, data in sorted(changes.items())
        ],
    })
    commit = api_request("POST", "git/commits", github_token, {
        "message": f"chore(p0): record authenticated provider snapshot {expected_head[:12]}",
        "tree": tree["sha"],
        "parents": [expected_head],
    })
    # force=false is mandatory. A concurrent update is not a fast-forward
    # from our old parent. Protected branches can reject this action.
    try:
        api_request("PATCH", "git/refs/heads/main", github_token,
                    {"sha": commit["sha"], "force": False})
    except urllib.error.HTTPError as exc:
        if exc.code in (409, 422):
            raise ConcurrentUpdate("GitHub rejected ref update: concurrent write or protection") from exc
        raise
    return {
        "result": "RECORDED",
        "commit_sha": commit["sha"],
        "observed_sha": expected_head,
        "event_path": event_path,
        "observation_path": snapshot_path,
        "note": "New HEAD is NOT verified CI/Render; reconcile again only after it deploys",
    }


def main():
    parser = argparse.ArgumentParser(description="Persist authenticated CI/Render observation atomically")
    parser.add_argument("--expected-head", required=True, help="Exact pre-write SHA of main")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = persist_verified_observation(
            args.expected_head, args.run_id,
            os.environ.get("GITHUB_TOKEN"), os.environ.get("RENDER_API_KEY"),
            dry_run=args.dry_run)
    except (PersistenceBlocked, ConcurrentUpdate, ValueError, KeyError, TypeError,
            urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        reason = str(exc)
        if isinstance(exc, urllib.error.HTTPError):
            reason = f"GitHub or Render API HTTP {exc.code}"
        print(json.dumps({"result": "BLOCKED", "reason": reason}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
