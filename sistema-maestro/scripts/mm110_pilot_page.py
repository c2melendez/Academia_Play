"""Load one of the two trusted local pilot templates with the shared area renderer."""
from pathlib import Path

PILOT = Path(__file__).resolve().parents[1] / "pilot"
MARKER = "/* STEM_AREA_GRID */"

def render_pilot_page(name):
    if name not in ("mm110_f01.html", "mm110_m1.html"):
        raise ValueError("unknown pilot")
    template = (PILOT / name).read_text(encoding="utf-8")
    script = (PILOT / "stem_area_grid.js").read_text(encoding="utf-8")
    if template.count(MARKER) != 1 or "</script" in script.lower():
        raise ValueError("invalid trusted area renderer template")
    return template.replace(MARKER, script).encode("utf-8")
