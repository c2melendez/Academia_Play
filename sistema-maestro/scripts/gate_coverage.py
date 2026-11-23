"""Evaluate candidate module technical closure, independently of evidence authenticity.

A successful structural check NEVER certifies that remote logs, CI or deployments exist.
Verification of those facts requires trusted provider observations.
"""
import re
from validate_academia_play import validate_gate, validate_continuity

DOCUMENTARY = {"G-SOURCE", "G-CURRICULUM", "G-DESIGN"}
REQUIRED_TECHNICAL = {
    "G-ORACLE", "G-PEDAGOGY", "G-PROGRESS", "G-A11Y-AUTO",
    "G-SECURITY", "G-REGRESSION", "G-DEPLOY"
}
REQUIRED_DOCUMENTARY = DOCUMENTARY
CONDITIONAL = {"G-LAB", "G-A11Y-MANUAL"}

def validate_candidate_closure(checkpoint, gates, module_id, target_sha, applicable=None):
    """Return structural errors only; a clean result is not an E1 verification."""
    errors = [f"continuity: {error}" for error in validate_continuity(checkpoint)]
    if not re.fullmatch(r"[0-9a-f]{40}", target_sha or ""):
        errors.append("target_sha must be a full lowercase Git SHA")
    if checkpoint.get("module_states", {}).get(module_id) != "DONE_TECHNICAL":
        errors.append(f"module {module_id} is not DONE_TECHNICAL")
    required = REQUIRED_TECHNICAL | REQUIRED_DOCUMENTARY
    scope = applicable or {}
    required |= {g for g in CONDITIONAL if scope.get(g, "REQUIRED") == "REQUIRED"}
    allowed_na = {g for g in CONDITIONAL if scope.get(g) == "NOT_APPLICABLE"}
    by_id = {}
    for gate in gates:
        if gate.get("module_id") != module_id:
            continue
        gid = gate.get("gate_id")
        if gid in by_id:
            errors.append(f"duplicate gate for module: {gid}")
        by_id[gid] = gate
        errors.extend(f"{gid}: {e}" for e in validate_gate(gate))
        if gid in REQUIRED_TECHNICAL and gate.get("result") == "PASS":
            if gate.get("commit_sha") != target_sha:
                errors.append(f"{gid}: commit SHA mismatch")
    for gid in sorted(required):
        g = by_id.get(gid)
        if not g:
            errors.append(f"missing required gate {gid}")
            continue
        expected = "DOC_PASS" if gid in DOCUMENTARY else "PASS"
        if g.get("result") != expected:
            errors.append(f"{gid}: requires {expected}")
    for gid in sorted(allowed_na):
        g = by_id.get(gid)
        if not g or g.get("result") != "NOT_APPLICABLE":
            errors.append(f"{gid}: requires justified NOT_APPLICABLE record")
    d = by_id.get("G-DEPLOY")
    if d and d.get("result") == "PASS":
        if d.get("commit_sha") != target_sha or d.get("deployment_sha") != target_sha:
            errors.append("G-DEPLOY: commit/deployment/target SHA mismatch")
    return errors
