"""Reference oracle for a deliberately narrow, frozen cross-project pilot."""
import hashlib
import json
import math
import re
from fractions import Fraction
from pathlib import Path

PILOT = Path(__file__).with_name("arithmetic-pilot.json")
PATTERN = re.compile(r"Calcula √\((\d{1,6})/(\d{1,6})\) \+ (\d{1,6})/(\d{1,6}) − (\d{1,6})/(\d{1,6})\.")
def reference(stimulus):
    match = PATTERN.fullmatch(stimulus)
    if not match:
        raise ValueError("outside pilot scope")
    a,b,c,d,e,f = map(int, match.groups())
    if not b or not d or not f:
        raise ValueError("zero denominator")
    radicand = Fraction(a,b)
    n,q = math.isqrt(radicand.numerator),math.isqrt(radicand.denominator)
    if n*n != radicand.numerator or q*q != radicand.denominator:
        raise ValueError("nonrational root")
    return Fraction(n,q)+Fraction(c,d)-Fraction(e,f)

def canonical_fingerprint(inputs):
    """Identity only; never grants PASS or proves execution."""
    required = {"repository","scope","criterion_revision","oracle_revision","source_hash","dependency_hash","environment"}
    if set(inputs) != required or any(not isinstance(v,str) or not v.strip() for v in inputs.values()):
        raise ValueError("complete explicit scope required")
    for field in ("source_hash","dependency_hash"):
        if not re.fullmatch(r"[0-9a-f]{64}", inputs[field]):
            raise ValueError("invalid hash")
    return hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")).hexdigest()

def validate(data):
    if data["schema_version"] != 1 or not data["cases"]:
        raise ValueError("unsupported or empty pilot")
    seen=set()
    for case in data["cases"]:
        if case["id"] in seen or not re.fullmatch(r"[0-9a-f]{64}",case["content_hash"]):
            raise ValueError("duplicate or invalid identity")
        seen.add(case["id"])
        match=PATTERN.fullmatch(case["stimulus"])
        if not match:
            raise ValueError("outside pilot scope")
        a,b,c,d,e,f=match.groups()
        if case["expression"] != f"sqrt({a}/{b})+{c}/{d}-{e}/{f}":
            raise ValueError("expression does not preserve stimulus")
        if reference(case["stimulus"]) != Fraction(case["expected"]):
            raise ValueError("incorrect expected result: "+case["id"])
    return sorted(seen)

if __name__ == "__main__":
    print(json.dumps({"scope":"reference-only","verified_ids":validate(json.loads(PILOT.read_text(encoding="utf-8"))),"fixture_sha256":hashlib.sha256(PILOT.read_bytes()).hexdigest()},ensure_ascii=False))
