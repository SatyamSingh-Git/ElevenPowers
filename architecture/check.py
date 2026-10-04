"""Regenerate the graph mirror and validate the page.

`index.html` is the live source: its inlined `GRAPH` is what renders.
`graph-data.js` is a generated, human-readable mirror — never hand-edited.

    python architecture/check.py            # regenerate + validate
    python architecture/check.py --render   # also prove all five tabs work

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
        for path in sorted((HERE.parent / folder).rglob("*.py")):
            rel = path.relative_to(HERE.parent).as_posix()
            if path.name == "__init__.py":
                continue
            if not any(rel == c or rel in c for c in covered):
                out.append(f"{rel} is not on the graph")
    return out


def planned(html: str) -> tuple[list[dict], list[str]]:
    """Keep contributor links and dependency paths usable as the roadmap grows."""
    match = re.search(r"const PLANNED = (\[.*?\n\]);\n", html, re.S)
    if not match:
        return [], ["missing contributor roadmap data"]
    try:
        items = json.loads(match.group(1))
    except json.JSONDecodeError as error:
        return [], [f"invalid contributor roadmap JSON: {error}"]
    problems = []
    ids = [item.get("id") for item in items]
    if not items or len(set(ids)) != len(ids):
        problems.append("contributor roadmap is empty or has duplicate ids")
    for item in items:
        name = item.get("id", "unnamed")
        if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
            problems.append(f"invalid roadmap id: {name}")
        for key in ("title", "area", "status", "summary", "why", "remaining", "first"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                problems.append(f"{name}: missing {key}")
        if item.get("status") not in {"Open milestone", "Planned research", "Conditional", "Proposed"}:
            problems.append(f"{name}: unknown commitment status")
        if not item.get("acceptance") or not item.get("sources"):
            problems.append(f"{name}: missing acceptance criteria or source links")
        if item.get("status") == "Conditional" and not item.get("trigger"):
            problems.append(f"{name}: conditional work needs a trigger")
        for dependency in item.get("dependsOn", []):
            if dependency not in ids or dependency == name:
                problems.append(f"{name}: unknown/self dependency {dependency}")
        for source in item.get("sources", []):
            path = source.split("#", 1)[0]
            if path.startswith(("/", "\\")) or ".." in Path(path).parts or not (HERE.parent / path).is_file():
                problems.append(f"{name}: missing or unsafe source {source}")
    return items, problems


def main() -> int:
    html = PAGE.read_text(encoding="utf-8")
    g = graph()

    ids = {n["id"] for n in g["nodes"]}
    dangling = [f'{e["source"]}->{e["target"]}' for e in g["edges"]
                if e["source"] not in ids or e["target"] not in ids]
    unknown = sorted({n["plane"] for n in g["nodes"]} - set(g["planes"]))

    _, problems = planned(html)
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
        return ["render unavailable: install playwright and its Chromium browser before claiming visual verification"]

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

        if not page.locator('.tab[data-view="planned"]').count():
            bad.append("planned tab is missing")
        else:
            page.click('.tab[data-view="planned"]')
            cards = page.locator("#planned-grid details")
            items, _ = planned(PAGE.read_text(encoding="utf-8"))
            if cards.count() != len(items) or not cards.count():
                bad.append(f"planned tab drew {cards.count()} cards, expected {len(items)}")
            else:
                card = cards.first
                card.locator("summary").click()
                if not card.evaluate("e => e.open") or not card.locator(".planned-body").is_visible():
                    bad.append("planned card does not expand on click")
                card.locator("summary").focus()
                page.keyboard.press("Enter")
                if card.evaluate("e => e.open"):
                    bad.append("planned card does not collapse with the keyboard")
                page.fill("#planned-search", "ImpactGraph")
                if page.locator("#planned-grid details:visible").count() != 1:
                    bad.append("planned search did not isolate ImpactGraph")
                page.fill("#planned-search", "a-query-with-no-roadmap-match")
                if page.locator("#planned-grid details:visible").count() or not page.locator("#planned-empty").is_visible():
                    bad.append("planned search does not explain an empty result")
                page.fill("#planned-search", "")
                page.select_option("#planned-status", "Conditional")
                if not page.locator("#planned-grid details:visible").count() or page.locator('#planned-grid details:not([data-status="Conditional"]):visible').count():
                    bad.append("planned commitment filter mixes conditional work with promises")
                page.select_option("#planned-status", "")
                page.select_option("#planned-area", "Project graph")
                if not page.locator("#planned-grid details:visible").count() or page.locator('#planned-grid details:not([data-area="Project graph"]):visible').count():
                    bad.append("planned topic filter is incorrect")
                page.select_option("#planned-area", "")
                page.goto(PAGE.as_uri() + "#planned/impact-graph")
                if not page.locator("#view-planned").is_visible() or not page.locator("#planned-impact-graph").evaluate("e => e.open"):
                    bad.append("planned item cannot be opened from its shared link")
                page.fill("#planned-search", "OpenCodeMap")
                page.locator("#planned-open-code-map summary").click()
                page.locator('#planned-open-code-map a[href="#planned/impact-graph"]').click()
                if page.locator("#planned-search").input_value() or not page.locator("#planned-impact-graph").is_visible():
                    bad.append("a prerequisite link to the current hash leaves its target hidden by a filter")
                if page.locator("#planned-impact-graph summary").evaluate("e => e !== document.activeElement"):
                    bad.append("planned item navigation does not move keyboard focus to its target")
                page.click("#theme")
                if page.locator("html").get_attribute("data-theme") != "light":
                    bad.append("theme toggle did not switch the initial dark page to light")
                if not page.locator("#planned-impact-graph").evaluate("e => e.open"):
                    bad.append("theme switching discarded the expanded planned card")
                low_contrast = page.eval_on_selector_all(
                    ".planned-badge, .planned-body a",
                    """elements => {
                      const luminance = color => {
                        const rgb = color.match(/[\\d.]+/g).slice(0, 3).map(Number);
                        const linear = rgb.map(n => {const s=n/255; return s<=0.04045?s/12.92:((s+0.055)/1.055)**2.4;});
                        return linear[0]*0.2126+linear[1]*0.7152+linear[2]*0.0722;
                      };
                      return elements.filter(e => {
                        const foreground=luminance(getComputedStyle(e).color);
                        const background=luminance(getComputedStyle(e.closest('.planned-card')).backgroundColor);
                        return (Math.max(foreground,background)+0.05)/(Math.min(foreground,background)+0.05)<4.5;
                      }).map(e => e.textContent);
                    }""")
                if low_contrast:
                    bad.append(f"small planned text lacks 4.5:1 light-theme contrast: {low_contrast[:5]}")
                page.set_viewport_size({"width": 390, "height": 844})
                overflow = page.locator("#view-planned .scroll").evaluate("e => e.scrollWidth > e.clientWidth + 1")
                if overflow:
                    bad.append("planned view overflows a narrow screen")
        b.close()

    for e in errors[:5]:
        bad.append(f"page error: {e}")
    if not bad:
        print("render  all five tabs work; cards, filters, keyboard, shared links and narrow layout verified")
    return bad


if __name__ == "__main__":
    raise SystemExit(main())
