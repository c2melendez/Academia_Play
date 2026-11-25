#!/usr/bin/env python3
"""v4.3 curricular research dossier: fail closed on fake provenance or source duplication.

Structure does not prove a source is genuinely institutional; independent
human/source inspection is still needed. Approval is separate from this artifact.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "reconstructed_curriculum.schema.json"
READABLE = {"OPENED", "PARTIAL"}

def validate_dossier(data: dict) -> list[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = [str(e.message) for e in Draft202012Validator(schema).iter_errors(data)]
    if errors:
        return errors
    sources = {}
    for source in data["sources"]:
        sid = source["source_id"]
        if sid in sources:
            errors.append(f"Duplicate source_id {sid}")
        sources[sid] = source
        if source["access_status"] == "NOT_ACCESSIBLE" and source["inspected_sections"]:
            errors.append(f"{sid}: inaccessible source cannot claim inspected sections")
        if source["access_status"] in READABLE and not source["inspected_sections"]:
            errors.append(f"{sid}: opened/partial source needs actual inspected sections")
    seen = set()
    for claim in data["claims"]:
        cid = claim["claim_id"]
        if cid in seen:
            errors.append(f"Duplicate claim_id {cid}")
        seen.add(cid)
        refs = [sources.get(sid) for sid in claim["source_ids"]]
        if any(ref is None for ref in refs):
            errors.append(f"{cid}: references unknown source")
            continue
        inspected = [ref for ref in refs if ref["access_status"] in READABLE and ref["inspected_sections"]]
        origins = {ref["origin_id"] for ref in inspected}
        category = claim["classification"]
        if category == "INSTITUTIONALLY_CONFIRMED" and not any(
            ref["source_type"] == "INSTITUTIONAL" for ref in inspected
        ):
            errors.append(f"{cid}: institutional confirmation lacks inspected institutional source")
        if category == "DOCUMENT_CORROBORATED" and len(origins) < 2:
            errors.append(f"{cid}: corroboration requires two independently originated inspected sources")
        if category in ("INSTITUTIONALLY_CONFIRMED", "DOCUMENT_CORROBORATED") and not inspected:
            errors.append(f"{cid}: no inspected source")
        if category == "ACADEMICALLY_INFERRED" and not claim["confidence_rationale"].strip():
            errors.append(f"{cid}: inference requires rationale")
    for unit in data["units"]:
        for cid in unit["claim_ids"]:
            if cid not in seen:
                errors.append(f"{unit['unit_id']}: unknown claim {cid}")
    if data["provenance"] == "OFFICIAL_VERIFIED" and not any(
        c["classification"] == "INSTITUTIONALLY_CONFIRMED" for c in data["claims"]
    ):
        errors.append("OFFICIAL_VERIFIED requires confirmed institutional claim")
    if data["provenance"] != "RESEARCH_INSUFFICIENT":
        if not data["units"] or not data["claims"]:
            errors.append("Proposed or official curriculum must have units and claims")
        if not any(c["is_core"] and c["classification"] not in ("ACADEMICALLY_INFERRED", "UNRESOLVED")
                   for c in data["claims"]):
            errors.append("Curricular core must include corroborated or institutionally confirmed claims")
    return errors

def main():
    parser = argparse.ArgumentParser(description="Validate provenance of reconstructed curriculum dossier")
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.file.read_text(encoding="utf-8"))
        failures = validate_dossier(data)
    except (OSError, ValueError, TypeError) as exc:
        print(f"BLOCKED: {exc}")
        return 2
    for failure in failures:
        print("FAIL:", failure)
    if not failures:
        print("PASS research dossier: structure and internal provenance checks only; NOT official validation")
    return 1 if failures else 0

if __name__ == "__main__":
    sys.exit(main())
