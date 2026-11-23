#!/usr/bin/env python3
"""P0 documentation consistency checks (offline, deterministic)."""
from pathlib import Path
import re
ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "sistema-maestro"

def check():
    errors = []
    version = (MASTER / "VERSION").read_text(encoding="utf-8").strip()
    short = ".".join(version.split(".")[:2])
    for rel in ["README.md", "sistema-maestro/README.md"]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        if f"v{short}" not in text:
            errors.append(f"{rel}: canonical version v{short} missing")
        if re.search(r"\\\\n(?=\\d+\\.\\s)", text):
            errors.append(f"{rel}: literal escaped newline in numbered list")
    for rel in ["sistema-maestro/AGENTS.md", "sistema-maestro/README.md"]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        if re.search(r"\\\\n(?=\\d+\\.\\s)", text):
            errors.append(f"{rel}: literal escaped newline in numbered list")
    runbook = (MASTER / "RUNBOOK.md").read_text(encoding="utf-8")
    master = (MASTER / "PROMPT_MAESTRO.md").read_text(encoding="utf-8")
    for name in re.findall(r"`([A-Z][A-Z_]+)`", master):
        if name in {"SOURCE_MISSING", "PROVISIONING_BLOCKED", "ENVIRONMENT_CONSTRAINED", "NOT_RUN", "INCONCLUSIVE", "PASS"}:
            continue
        if name not in runbook and name in {"INICIAR","CONTINUAR","RECONCILIAR","REPLANIFICAR","AUDITAR","ESTADO","ESCALAR","AGREGAR_CURSO","APROBAR_DISEÑO","VALIDAR_LABORATORIOS"}:
            errors.append(f"RUNBOOK missing command {name}")
    return errors

if __name__ == "__main__":
    failures = check()
    for failure in failures:
        print("FAIL:", failure)
    if not failures:
        print("PASS: document consistency")
    raise SystemExit(bool(failures))
