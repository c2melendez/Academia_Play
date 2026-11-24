#!/usr/bin/env python3
"""Read-only independent audit of authenticated GitHub reviews for normative PRs.

This checks GitHub-supplied review identities, state, and exact head revision.
It cannot configure branch protection or authenticate conversational curriculum
approvals. It never grants the agent authority to approve its own work.
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

REPO = "c2melendez/Academia_Play"
REVIEWERS = frozenset({"c2melendez"})
NORMATIVE_EXACT = {
    "PROMPT_EJECUTOR_REPOSITORIO.md",
    "continuity.json",
    ".github/CODEOWNERS",
}
NORMATIVE_PREFIX = (
    "sistema-maestro/",
    "infra/",
    ".github/workflows/",
)
SHA = re.compile(r"^[0-9a-f]{40}$")


def normative_paths(paths):
    """Return sensitive paths; documentation and executable contracts are included."""
    return sorted(set(
        p for p in paths
        if p in NORMATIVE_EXACT or any(p.startswith(prefix) for prefix in NORMATIVE_PREFIX)
    ))


def review_result(pr, changed_paths, reviews, *, approved_accounts=REVIEWERS):
    """Consume GitHub API observations only; no caller-provided JSON counts as attestation."""
    failures = []
    sensitive = normative_paths(changed_paths)
    if not sensitive:
        return {"result": "NOT_APPLICABLE", "errors": [], "paths": [], "reviewers": []}
    head = ((pr.get("head") or {}).get("sha"))
    author = ((pr.get("user") or {}).get("login"))
    if (pr.get("base") or {}).get("ref") != "main":
        failures.append("Expected main as base branch")
    if not SHA.fullmatch(head or ""):
        failures.append("PR has no valid exact head SHA")
    if not author:
        failures.append("PR author identity missing")
    if pr.get("draft"):
        failures.append("PR remains draft")
    if pr.get("state") != "open":
        failures.append("PR is not open")
    if ((pr.get("base") or {}).get("repo") or {}).get("full_name") != REPO:
        failures.append("PR target repository mismatch")
    # Last submitted review per user controls; dismissed or changes-requested
    # after an approval revoke that reviewer's approval.
    latest = {}
    for review in reviews:
        actor = (review.get("user") or {}).get("login")
        if not actor or review.get("state") == "PENDING":
            continue
        when = review.get("submitted_at") or ""
        rid = review.get("id") or 0
        if actor not in latest or (when, rid) >= latest[actor][0]:
            latest[actor] = ((when, rid), review)
    effective = []
    for actor, (_, review) in latest.items():
        if actor not in approved_accounts or actor == author:
            continue
        if review.get("state") == "APPROVED" and review.get("commit_id") == head:
            effective.append(actor)
    if not effective:
        failures.append("No independent authorized APPROVED review for exact PR head SHA")
    return {
        "result": "VERIFIED_REVIEW" if not failures else "BLOCKED",
        "errors": failures,
        "paths": sensitive,
        "reviewers": sorted(effective),
        "head_sha": head,
        "note": "PR governance review only; not APROBAR_DISEÑO or academic approval",
    }


def github_json(path, token):
    if not token:
        raise ValueError("GITHUB_TOKEN is missing")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "academia-play-governance-review",
        })
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def fetch_all_pages(path, token):
    """Fail closed on pagination or API failures; no silent truncation."""
    rows = []
    for page in range(1, 101):
        sep = "&" if "?" in path else "?"
        values = github_json(f"{path}{sep}per_page=100&page={page}", token)
        if not isinstance(values, list):
            raise ValueError("Expected paginated list")
        rows.extend(values)
        if len(values) < 100:
            return rows
    raise ValueError("Review/file collection exceeded pagination safety limit")


def observe_pr(number, token):
    if not str(number).isdigit() or int(number) < 1:
        raise ValueError("Invalid pull request number")
    pr = github_json(f"pulls/{number}", token)
    files = fetch_all_pages(f"pulls/{number}/files", token)
    reviews = fetch_all_pages(f"pulls/{number}/reviews", token)
    return review_result(pr, [file["filename"] for file in files], reviews)


def main():
    parser = argparse.ArgumentParser(description="Check independent GitHub review for governance PR")
    parser.add_argument("--pr", type=int, required=True)
    args = parser.parse_args()
    try:
        result = observe_pr(args.pr, os.environ.get("GITHUB_TOKEN"))
    except (ValueError, KeyError, TypeError, urllib.error.URLError, urllib.error.HTTPError,
            json.JSONDecodeError) as error:
        detail = f"HTTP {error.code}" if isinstance(error, urllib.error.HTTPError) else str(error)
        print(json.dumps({"result": "BLOCKED", "errors": [detail]}))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] in ("VERIFIED_REVIEW", "NOT_APPLICABLE") else 1


if __name__ == "__main__":
    sys.exit(main())
