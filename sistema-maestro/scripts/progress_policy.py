"""Progreso Academia Play v4.1: eventos, dominio derivado y unión idempotente.

Los grants son derechos irreversibles. La estimación de dominio se obtiene
de evidencias + regla aprobada; jamás de timestamps de dispositivos.
El sistema de producción debe obtener la mastery_rule del manifiesto confiable.
"""
from __future__ import annotations
from copy import deepcopy


class ProgressConflict(ValueError):
    pass


def _index(items, key):
    result = {}
    for item in items:
        identifier = item[key]
        if identifier in result and result[identifier] != item:
            raise ProgressConflict(f"conflicting {key} {identifier}")
        result[identifier] = item
    return result


def _validate_events(state):
    evidence = _index(state["mastery_evidence"], "evidence_id")
    grants = _index(state["access_grants"], "grant_id")
    keys = {}
    for e in evidence.values():
        k = e["idempotency_key"]
        if k in keys and keys[k] != e["evidence_id"]:
            raise ProgressConflict(f"duplicate idempotency_key {k}")
        keys[k] = e["evidence_id"]
    for grant in grants.values():
        if any(ref not in evidence for ref in grant["evidence_ids"]):
            raise ProgressConflict(f"grant {grant['grant_id']} references unknown evidence")
    reviews = _index(state["review_events"], "event_id")
    opened = {e["review_id"] for e in reviews.values() if e["kind"] == "OPEN"}
    for e in reviews.values():
        if e["kind"] == "RESOLVE" and e["review_id"] not in opened:
            raise ProgressConflict(f"resolve without open: {e['review_id']}")
    return evidence, grants, reviews


def derive_mastery(state, rule):
    """Pure projection; only VERIFIED unassisted unique semantic families count.

    A transfer must be an explicitly marked transfer event, not merely an exam.
    """
    evidence, _, reviews = _validate_events(state)
    eligible = [e for e in evidence.values()
                if e["oracle_result"] == "VERIFIED" and not e["assisted"]]
    families = {e["variant_family"] for e in eligible if e["role"] == "PRACTICE"}
    transfers = [e for e in eligible if e["role"] == "TRANSFER"]
    required = rule["distinct_variant_families"]
    mastered = len(families) >= required and (
        not rule["requires_transfer"] or bool(transfers))
    if not mastered:
        return "DEVELOPING" if evidence else "UNASSESSED"
    opened = {e["review_id"] for e in reviews.values() if e["kind"] == "OPEN"}
    resolved = {e["review_id"] for e in reviews.values() if e["kind"] == "RESOLVE"}
    return "NEEDS_REVIEW" if opened - resolved else "MASTERED"


def validate_invariants(state, rule=None):
    evidence, grants, reviews = _validate_events(state)
    effective_rule = rule or state["mastery_rule"]
    if rule is not None and effective_rule != state["mastery_rule"]:
        raise ProgressConflict("snapshot mastery_rule mismatches trusted route")
    expected = derive_mastery(state, effective_rule)
    if state["mastery_estimate"] != expected:
        raise ProgressConflict(
            f"mastery_estimate={state['mastery_estimate']} should be {expected}")
    return True


def merge_progress(a, b):
    """Join-semilattice of grant/evidence/review events.

    Conflicting IDs or conflicting policy cause an explicit error.
    No device clock can revoke an unlock or determine mastery.
    """
    for field in ("user_id", "institution_id", "course_version", "node_id"):
        if a[field] != b[field]:
            raise ProgressConflict(f"cannot merge distinct {field}")
    if a["mastery_rule"] != b["mastery_rule"]:
        raise ProgressConflict("cannot merge distinct mastery policies")
    _validate_events(a)
    _validate_events(b)
    out = deepcopy(a)
    for field, key in (("access_grants", "grant_id"),
                       ("mastery_evidence", "evidence_id"),
                       ("review_events", "event_id")):
        left = _index(a[field], key)
        right = _index(b[field], key)
        for identity, value in right.items():
            if identity in left and left[identity] != value:
                raise ProgressConflict(f"conflicting {key} {identity}")
            left[identity] = value
        out[field] = [left[i] for i in sorted(left)]
    _validate_events(out)
    out["mastery_estimate"] = derive_mastery(out, out["mastery_rule"])
    out["updated_at"] = max(a["updated_at"], b["updated_at"])
    return out
