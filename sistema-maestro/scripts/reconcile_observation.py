#!/usr/bin/env python3
"""Compare a provider-observed result with a checkpoint without altering history.

Input observations are trusted ONLY when collected by the authenticated
provider_evidence.py program. This script does not turn arbitrary JSON into E1.
"""
import argparse
import json
from pathlib import Path

from validate_academia_play import validate_continuity

def differences(checkpoint, observation):
    errors = validate_continuity(checkpoint)
    if errors:
        return {"status": "INVALID_CHECKPOINT", "errors": errors, "differences": []}
    if observation.get("result") != "VERIFIED_OBSERVATION":
        return {"status": "BLOCKED", "errors": ["Provider observation was not verified"],
                "differences": []}
    if observation.get("repository") != checkpoint.get("repository_full_name"):
        return {"status": "BLOCKED", "errors": ["Repository mismatch"],
                "differences": []}
    if observation.get("service_id") != checkpoint.get("render_service_id"):
        return {"status": "BLOCKED", "errors": ["Render service mismatch"],
                "differences": []}
    comparison = {
        "repo_head_sha": observation.get("target_sha"),
        "qa_ci_verified_sha": observation.get("target_sha"),
        "last_verified_deploy_sha": observation.get("target_sha"),
        "last_observed_at": observation.get("observed_at"),
        "active_branch": "main",
    }
    diff = [
        {"field": name, "checkpoint": checkpoint.get(name), "observed": expected}
        for name, expected in comparison.items()
        if checkpoint.get(name) != expected
    ]
    return {"status": "STALE" if diff else "CONSISTENT", "errors": [],
            "differences": diff,
            "note": "Read-only snapshot comparison; no approval or gate PASS inferred"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--continuity", type=Path, default=Path("continuity.json"))
    parser.add_argument("--observation", type=Path, required=True)
    args = parser.parse_args()
    result = differences(json.loads(args.continuity.read_text(encoding="utf-8")),
                         json.loads(args.observation.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
