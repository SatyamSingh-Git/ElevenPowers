"""Regenerate the graph mirror and validate the page.

`index.html` is the live source: its inlined `GRAPH` is what renders.
`graph-data.js` is a generated, human-readable mirror — never hand-edited.

    python architecture/check.py            # regenerate + validate
    python architecture/check.py --render   # also prove all four tabs draw

The render check is the one that matters. Every structural check below passed
on a page that rendered nothing at all, because a single apostrophe inside a
single-quoted JS string had broken the script. A page that parses is not a
page that draws.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = HERE / "index.html"
MIRROR = HERE / "graph-data.js"

BANNER = """/* GENERATED - do not hand-edit.
 * Human-readable mirror of the GRAPH inlined in index.html, which is the live
 * source. Regenerate with:  python architecture/check.py
 */"""


def graph() -> dict:
    html = PAGE.read_text(encoding="utf-8")
    m = re.search(r"const GRAPH = (\{.*?\n\});\n", html, re.S)
    if not m:
        sys.exit("could not find the inlined `const GRAPH = {...};` block")
    return json.loads(m.group(1))


def uncovered(g: dict) -> list[str]:
    """A module nobody drew is the failure this file exists to prevent.

    Every `.py` under core/, eval/ and plugin/bin must appear in some node's
    `files`. A new module that nothing draws is exactly how a graph goes stale
    while still validating.
    """
    covered = {f.replace("\\", "/").rstrip("/") for n in g["nodes"] for f in n["files"]}
    out = []
    for folder in ("core", "eval", "plugin/bin"):
        for path in sorted((HERE.parent / folder).glob("*.py")):
            rel = f"{folder}/{path.name}"
            if path.name == "__init__.py":
                continue
            if not any(rel == c or rel in c for c in covered):
                out.append(f"{rel} is not on the graph")
    return out


def main() -> int:
    html = PAGE.read_text(encoding="utf-8")
    g = graph()

    ids = {n["id"] for n in g["nodes"]}
    dangling = [f'{e["source"]}->{e["target"]}' for e in g["edges"]
                if e["source"] not in ids or e["target"] not in ids]
    unknown = sorted({n["plane"] for n in g["nodes"]} - set(g["planes"]))

    problems = []
    if dangling:
        problems.append(f"dangling edges: {', '.join(dangling)}")
    if len(ids) != len(g["nodes"]):
        problems.append("duplicate node ids")
    if unknown:
        problems.append(f"nodes on undeclared planes: {', '.join(unknown)}")
    if html.count("<script>") != html.count("</script>"):
        problems.append("unbalanced <script> tags - the classic blank-canvas regression")
    for needle in ("<!doctype html>", '<meta charset="utf-8">', "</head>", "<body>", "</body>", "</html>"):
        if needle not in html:
            problems.append(f"missing {needle} - would render in quirks mode")
    external = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    if external:
        problems.append(f"external resources break file:// and strict CSP: {external}")
    # boxed views have fixed-width boxes; long `sub` text overlaps its neighbours
    long_subs = [s for s in re.findall(r"sub:'([^'\n]*)'", html) if len(s) > 42]
    if long_subs:
        problems.append(f"sub text too long for its box: {long_subs}")
    problems += uncovered(g)

    MIRROR.write_text(
        BANNER + "\nwindow.ELEVENPOWERS_GRAPH = " + json.dumps(
            {"meta": g["meta"], "planes": g["planes"], "nodes": g["nodes"], "edges": g["edges"]},
            indent=2) + ";\n",
        encoding="utf-8")

    print(f"nodes {len(g['nodes'])}  edges {len(g['edges'])}  planes {len(g['planes'])}")
    print(f"updated {g['meta']['updated']}")
    print(f"mirror  {MIRROR.name} regenerated")

    if "--render" in sys.argv:
        problems += render()

    if problems:
        print("\nFAIL")
        for p in problems:
            print("  -", p)
        return 1
    print("\nOK" + ("" if "--render" in sys.argv else "  (run with --render to prove the tabs draw)"))
    return 0


def render() -> list[str]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("render  SKIPPED (pip install playwright && playwright install chromium)")
        return []

    bad: list[str] = []
    errors: list[str] = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(PAGE.as_uri())
        page.wait_for_timeout(1400)

        chips = page.eval_on_selector_all("#legend .plane-chip", "e => e.length")
        want = len(graph()["planes"])
        if chips != want:
            bad.append(f"legend drew {chips} plane chips, expected {want}")

        painted = page.evaluate(
            "() => {const c=document.getElementById('c');"
            "const x=c.getContext('2d').getImageData(0,0,c.width,c.height).data;"
            "let n=0; for(let i=3;i<x.length;i+=4) if(x[i]) n++; return n;}")
        if not painted:
            bad.append("overview canvas painted nothing")

        for view, sel in (("dataflow", "#svg-dataflow"),
                          ("architecture", "#svg-architecture"),
                          ("workflow", "#svg-workflow")):
            page.click(f'.tab[data-view="{view}"]')
            page.wait_for_timeout(700)
            drawn = page.eval_on_selector(sel, "e => e.querySelectorAll('*').length")
            if not drawn:
                bad.append(f"{view} tab drew nothing")
        b.close()

    for e in errors[:5]:
        bad.append(f"page error: {e}")
    if not bad:
        print("render  all four tabs draw")
    return bad


if __name__ == "__main__":
    raise SystemExit(main())
