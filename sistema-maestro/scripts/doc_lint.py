#!/usr/bin/env python3
"""Offline consistency checks for Academia Play's active entrypoint documents."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "sistema-maestro"


def check():
    errors = []
    version = (MASTER / "VERSION").read_text(encoding="utf-8").strip()
    short = ".".join(version.split(".")[:2])
    for rel in ("README.md", "sistema-maestro/README.md"):
        if f"v{short}" not in (ROOT / rel).read_text(encoding="utf-8"):
            errors.append(f"{rel}: canonical version v{short} missing")
    for rel in ("sistema-maestro/AGENTS.md", "sistema-maestro/README.md"):
        data = (ROOT / rel).read_text(encoding="utf-8")
        if (chr(92) + "n") in data:
            errors.append(f"{rel}: literal escaped newline")
    runbook = (MASTER / "RUNBOOK.md").read_text(encoding="utf-8")
    constitution = (MASTER / "CONSTITUCION.md").read_text(encoding="utf-8")
    master = (MASTER / "PROMPT_MAESTRO.md").read_text(encoding="utf-8")
    for i in range(1, 13):
        if not re.search(rf"REQ-{i:03d}\\b", constitution):
            errors.append(f"CONSTITUCION missing REQ-{i:03d}")
    commands = ("INICIAR", "APROBAR_DISEÑO", "CONTINUAR", "AGREGAR_CURSO",
                "AUDITAR", "RECONCILIAR", "REPLANIFICAR", "ESTADO",
                "VALIDAR_LABORATORIOS", "ESCALAR")
    for name in commands:
        if f"`{name}`" not in runbook:
            errors.append(f"RUNBOOK missing command {name}")
    if "CONSTITUCION.md" not in master or "RUNBOOK.md" not in master or "GATES.md" not in master:
        errors.append("PROMPT_MAESTRO: missing canonical authority references")
    gate = (MASTER / "schemas/gate.schema.json").read_text(encoding="utf-8")
    generator = (MASTER / "scripts/build_contracts.py").read_text(encoding="utf-8")
    if '"G-A11Y",' in gate or "'G-A11Y'," in generator:
        errors.append("legacy G-A11Y in active schema generator or enum")
    return errors


if __name__ == "__main__":
    failures = check()
    for problem in failures:
        print("FAIL:", problem)
    if not failures:
        print("PASS: document consistency")
    raise SystemExit(bool(failures))
