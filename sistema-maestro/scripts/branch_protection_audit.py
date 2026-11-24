#!/usr/bin/env python3
"""Fail-closed audit of GitHub main-branch rules. No settings are changed.

A green contract CI is unrelated to whether main rejects unreviewed merges.
This auditor uses GitHub's authenticated ruleset endpoints and requires
credible enforcement and at least one real independent reviewer.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

REPO = "c2melendez/Academia_Play"
BRANCH = "refs/heads/main"


def rule_targets_main(ruleset):
    target = ruleset.get("target")
    if target != "branch" or ruleset.get("enforcement") != "active":
        return False
    conditions = ruleset.get("conditions") or {}
    branch = conditions.get("ref_name") or {}
    include = branch.get("include") or []
    exclude = branch.get("exclude") or []
    matches = ("~DEFAULT_BRANCH", "~ALL", BRANCH, "main")
    return any(item in include for item in matches) and not any(
        item in exclude for item in (BRANCH, "main", "~DEFAULT_BRANCH")
    )


def audit_rulesets(rulesets, *, default_branch="main", effective_actors=None):
    """Read-only conservative conclusion. Missing data cannot mean protected."""
    errors = []
    if default_branch != "main":
        errors.append("Unexpected default branch")
    active = [r for r in rulesets if rule_targets_main(r)]
    if not active:
        errors.append("No active ruleset demonstrably targeting main")
    rules = [rule for r in active for rule in r.get("rules", [])]
    types = {r.get("type") for r in rules}
    if "pull_request" not in types:
        errors.append("No enforced pull_request rule on main")
    else:
        pr_rules = [r for r in rules if r.get("type") == "pull_request"]
        if not any(
            int((r.get("parameters") or {}).get("required_approving_review_count", 0)) >= 1
            and (r.get("parameters") or {}).get("require_code_owner_review") is True
            and (r.get("parameters") or {}).get("dismiss_stale_reviews_on_push") is True
            for r in pr_rules
        ):
            errors.append("Required approvals, CODEOWNERS and stale-review dismissal not jointly enforced")
    status = [r for r in rules if r.get("type") == "required_status_checks"]
    if not status:
        errors.append("No required_status_checks rule on main")
    else:
        required = [check for r in status for check in (r.get("parameters") or {}).get("required_status_checks", [])]
        if not any("contracts" == c.get("context") for c in required):
            errors.append("Required contracts CI job check not found")
    # Bypass actors are risky even with active rules.
    if any(r.get("bypass_actors") for r in active):
        errors.append("Active ruleset includes bypass actors; verify or remove bypasses before certification")
    # The count of distinct authorized humans cannot be concluded from rulesets.
    if effective_actors is None or len(set(effective_actors)) < 2:
        errors.append("Independent human reviewer capacity not verified")
    return {
        "status": "VERIFIED" if not errors else "BLOCKED",
        "errors": errors,
        "active_rulesets": [r.get("id") for r in active],
        "note": "Static ruleset audit only. Effective rejection tests and independent human review remain separate.",
    }


def fetch_json(url, token):
    if not token:
        raise ValueError("GITHUB_TOKEN missing")
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json",
                 "Authorization": f"Bearer {token}",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "User-Agent": "academia-play-branch-audit"},
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def observe(token, *, verified_human_reviewers=()):
    """Fetch detailed rulesets; a summary alone omits the rule parameters."""
    repo = fetch_json(f"https://api.github.com/repos/{REPO}", token)
    summaries = fetch_json(f"https://api.github.com/repos/{REPO}/rulesets?per_page=100", token)
    if not isinstance(summaries, list):
        raise ValueError("Expected ruleset list")
    if len(summaries) >= 100:
        raise ValueError("Ruleset pagination needs review; do not silently accept partial data")
    details = []
    for item in summaries:
        details.append(fetch_json(f"https://api.github.com/repos/{REPO}/rulesets/{item['id']}", token))
    return audit_rulesets(details, default_branch=repo.get("default_branch"),
                          effective_actors=verified_human_reviewers)


def main():
    p = argparse.ArgumentParser(description="Read-only branch protection verification")
    p.add_argument("--reviewer", action="append", default=[],
                   help="Previously independently VERIFIED human GitHub login; not self-declared")
    args = p.parse_args()
    try:
        result = observe(os.environ.get("GITHUB_TOKEN"), verified_human_reviewers=args.reviewer)
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError, TypeError, KeyError,
            json.JSONDecodeError) as e:
        reason = f"HTTP {e.code}" if isinstance(e, urllib.error.HTTPError) else str(e)
        result = {"status": "BLOCKED", "errors": [reason], "active_rulesets": []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "VERIFIED" else 2


if __name__ == "__main__":
    sys.exit(main())
