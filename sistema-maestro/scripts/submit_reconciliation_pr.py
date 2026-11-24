#!/usr/bin/env python3
"""Propose an authenticated reconciliation with a GitHub pull request.

No direct writes to protected main, no force push, no bypass, no autonomous
approval/merge. The observed commit is the pre-PR main HEAD, not the commit
that will eventually be merged. Safe retries fail closed rather than overwrite.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

from persist_reconciliation import (
    ConcurrentUpdate, PersistenceBlocked, api_request, build_change,
    event_paths, existing_event, read_text_content,
)
from provider_evidence import observe

SHA = re.compile(r"^[0-9a-f]{40}$")
REPO = "c2melendez/Academia_Play"


def proposal_branch(expected_head, run_id):
    event_paths(expected_head, str(run_id))  # validates both values
    return f"p0/reconcile-{expected_head}-{run_id}"


def current_main(token):
    ref = api_request("GET", "git/ref/heads/main", token)
    return (ref.get("object") or {}).get("sha")


def submit(expected_head, run_id, github_token, render_token, *, dry_run=False):
    """Use provider evidence and a single branch commit, then open an unmerged PR."""
    run_id = str(run_id)
    branch = proposal_branch(expected_head, run_id)
    if not github_token:
        raise PersistenceBlocked("GITHUB_TOKEN required")
    if not render_token:
        raise PersistenceBlocked("RENDER_API_KEY required")
    event_path, _ = event_paths(expected_head, run_id)
    earlier = existing_event(event_path, github_token)
    if earlier is not None:
        raise PersistenceBlocked(
            "Evidence event already exists on main; inspect historical record, do not repeat")
    head = current_main(github_token)
    if head != expected_head:
        raise ConcurrentUpdate(f"main moved from {expected_head} to {head}")
    checkpoint_text, _ = read_text_content("continuity.json", github_token)
    observation = observe(expected_head, run_id, github_token, render_token)
    changes = build_change(json.loads(checkpoint_text), observation, run_id)
    if dry_run:
        return {
            "result": "DRY_RUN",
            "observed_sha": expected_head,
            "branch": branch,
            "files": sorted(changes),
            "note": "Authenticated provider observations; no commits/branches/PRs created",
        }

    # Prevent publishing a proposal based on a stale main, but still verify
    # current main again immediately before creating the new ref.
    if current_main(github_token) != expected_head:
        raise ConcurrentUpdate("main changed during observation")
    try:
        existing_branch = api_request("GET", f"git/ref/heads/{branch}", github_token)
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        existing_branch = None
    if existing_branch is not None:
        raise PersistenceBlocked("Proposal branch already exists; review its PR, never overwrite")

    parent = api_request("GET", f"git/commits/{expected_head}", github_token)
    tree_sha = (parent.get("tree") or {}).get("sha")
    if not SHA.fullmatch(tree_sha or ""):
        raise PersistenceBlocked("Missing valid parent tree SHA")
    tree = api_request("POST", "git/trees", github_token, {
        "base_tree": tree_sha,
        "tree": [
            {"path": path, "mode": "100644", "type": "blob", "content": data}
            for path, data in sorted(changes.items())
        ],
    })
    commit = api_request("POST", "git/commits", github_token, {
        "message": f"chore(p0): propose observed provider checkpoint {expected_head[:12]}",
        "tree": tree["sha"], "parents": [expected_head],
    })
    if current_main(github_token) != expected_head:
        raise ConcurrentUpdate("main changed before creating proposal branch")
    # Create branch directly at the fully composed commit (no partial branch).
    api_request("POST", "git/refs", github_token, {
        "ref": f"refs/heads/{branch}", "sha": commit["sha"],
    })
    # A PR may fail due to permissions or policy. Existing branch is retained
    # for manual inspection/recovery; no silent retry or direct-main fallback.
    pr = api_request("POST", "pulls", github_token, {
        "title": f"chore(p0): reconcile CI/Render observation for {expected_head[:12]}",
        "head": branch, "base": "main",
        "body": (
            "Automated proposal from authenticated GitHub/Render observations. "
            f"Observed pre-PR SHA: {expected_head}; run: {run_id}. "
            "The new commit is not itself certified or deployed. "
            "Requires regular CI, review, protected-branch checks and normal squash merge. "
            "No curriculum or academic approval implied."
        ),
        "draft": False,
    })
    return {
        "result": "PROPOSED_NOT_MERGED",
        "branch": branch,
        "commit_sha": commit["sha"],
        "observed_sha": expected_head,
        "pr_number": pr.get("number"),
        "pr_url": pr.get("html_url"),
        "note": "No changes made to main; no CI/Render claim for proposal commit",
    }


def main():
    parser = argparse.ArgumentParser(description="Prepare and submit protected-branch reconciliation PR")
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = submit(args.expected_head, args.run_id,
                        os.environ.get("GITHUB_TOKEN"),
                        os.environ.get("RENDER_API_KEY"), dry_run=args.dry_run)
    except (PersistenceBlocked, ConcurrentUpdate, ValueError, TypeError, KeyError,
            urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        reason = f"Provider API HTTP {exc.code}" if isinstance(exc, urllib.error.HTTPError) else str(exc)
        print(json.dumps({"result": "BLOCKED", "reason": reason}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
