"""Validate the scoped reuse inventory, not a certification decision."""
import json
import re
from pathlib import Path
INVENTORY=Path(__file__).with_name("mm110-reuse-inventory.json")
FAMILIES={f"F{i:02d}" for i in range(1,8)}
REPOS={"c2melendez/Academia_Play","c2melendez/desafio-gramatical","c2melendez/precision-lab-lite","c2melendez/precision-lab-plus"}
def validate(data):
    if data["schema_version"]!=1 or data["course"]!="unah-mm110" or data["status"]!="STATIC_INVENTORY_REVIEW":
        raise ValueError("unsupported inventory or claimed approval")
    refs={}
    for s in data["sources"]:
        if s["id"] in refs or s["repository"] not in REPOS or any(not re.fullmatch(r"[0-9a-f]{40}",s[k]) for k in ("commit","blob")):
            raise ValueError("invalid or duplicate pinned source")
        if not s["path"] or s["path"].startswith("/") or ".." in s["path"].split("/"):
            raise ValueError("invalid source path")
        refs[s["id"]]=s
    seen=set()
    for e in data["entries"]:
        family=e["family"]
        if family not in FAMILIES or family in seen or e["module"]!=("M0" if family=="F01" else "M1"):
            raise ValueError("invalid family/module coverage")
        seen.add(family)
        ids=e["source_ids"]
        if not ids or len(set(ids))!=len(ids) or not set(ids)<=refs.keys():
            raise ValueError("missing or invalid source reference")
        if not any(refs[i]["repository"]=="c2melendez/Academia_Play" for i in ids):
            raise ValueError("missing local contract")
        if e["decision"] not in ("ADAPT","REUSE_LOCAL") or e["certification_transfer"] is not False or not e["limits"].strip():
            raise ValueError("unapproved transfer or missing limits")
        if e["decision"]=="REUSE_LOCAL" and any(refs[i]["repository"]!="c2melendez/Academia_Play" for i in ids):
            raise ValueError("external reuse requires adaptation review")
    if seen!=FAMILIES:
        raise ValueError("incomplete family coverage")
    return sorted(seen)
if __name__=="__main__":
    print(json.dumps({"families":validate(json.loads(INVENTORY.read_text(encoding="utf-8"))),"certification_transfer":False}))
