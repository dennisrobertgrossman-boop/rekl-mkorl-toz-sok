"""Összeállítja a weboldalt: a sablonba beilleszti a térkép geometriáját.

Használat:
    python3 tools/build_page.py [artifact_kimenet.html]

Kimenet: index.html (önálló HTML-dokumentum a tárhely gyökerében), és ha meg van
adva, egy keret nélküli változat a claude.ai Artifact-közzétételhez.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NBSP = " "


def tidy_text(segment):
    """Az ezres számcsoportok közé nem törhető szóköz kerül."""
    return re.sub(r"(?<=\d) (?=\d{3}(?!\d))", NBSP, segment)


def build_fragment():
    template = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
    geo = json.loads((ROOT / "data" / "geometry.json").read_text(encoding="utf-8"))
    parts = re.split(r"(<script\b.*?</script>|<style\b.*?</style>)", template, flags=re.S)
    template = "".join(p if p.startswith(("<script", "<style")) else tidy_text(p) for p in parts)
    template = template.replace("≈ ", "≈" + NBSP)
    geo_json = json.dumps(geo, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    assert template.count("__GEO__") == 1
    return template.replace("__GEO__", geo_json)


def main():
    fragment = build_fragment()
    # Az önálló oldalon a sablon eleje (title, meta, style) a fejlécbe kerül
    head_end = fragment.index("</style>") + len("</style>")
    head, body = fragment[:head_end], fragment[head_end:].lstrip("\n")
    page = (
        "<!doctype html>\n<html lang=\"hu\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
        + head + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n"
    )
    (ROOT / "index.html").write_text(page, encoding="utf-8")
    print("index.html", len(page.encode("utf-8")), "bájt")
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(fragment, encoding="utf-8")
        print(sys.argv[1], len(fragment.encode("utf-8")), "bájt")


if __name__ == "__main__":
    main()
