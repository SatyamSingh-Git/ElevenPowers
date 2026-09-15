# ElevenPowers — living architecture graph

Four views of the whole system — the runtime, the plugin seam it reaches the
host through, the durable ledger, and the evaluation harness — in one
self-contained HTML file.

### ▶ **[Open the live graph](https://satyamsingh-git.github.io/ElevenPowers/architecture/)**

Or open [`index.html`](index.html) from a local clone — double-click it. No
server, no build, no network either way.

> **Why clicking the file on github.com shows code.** github.com is a source
> browser: it renders `.md` and shows every other file as text. That is its
> viewer, not a problem with the page. The live link above is the same file
> served by GitHub Pages, where it renders. Both are verified — all four tabs
> were confirmed drawing over HTTPS, not just from `file://`.

## The four views (tabs across the top)

| Tab | What it shows | How it's drawn |
|---|---|---|
| **Overview** | Every module, event and service as a coloured node; every import and data flow as an edge. Draggable, zoomable, click-to-inspect. | canvas force-directed graph |
| **Data flow** | One task from request to verdict, as numbered **request → / response ←** pairs. | SVG swimlanes |
| **Architecture** | The system in tiers: host surface → the plugin seam → `core/` → durable state → `eval/` → external. | SVG layered lanes |
| **Workflow** | Three sequences left-to-right: a task as the runtime sees it, one paired evaluation run, and what v0.8 adds. | SVG numbered steps |

## Files

| File | Role |
|---|---|
| `index.html` | **Live source and self-contained viewer.** Its inlined `GRAPH` and the three structured-view datasets drive all four tabs. |
| `graph-data.js` | **Generated mirror** of the Overview graph (`window.ELEVENPOWERS_GRAPH`). Regenerated from `index.html`; never hand-edited. |
| `check.py` | Regenerates the mirror and validates the page. `--render` proves all four tabs actually draw. |

The three structured views are driven by small hand-curated datasets inlined in
`index.html` — `DF_ACTORS`/`DF_STEPS`, `ARCH_LAYERS`/`ARCH_LINKS`, and
`WF_LANES`. They are deliberately summaries rather than auto-derived from the
node graph, so each view stays readable.

## How to read it

- **Nodes** are real files, hook events or services; **colour = plane**
  (host / seam / runtime / state / eval / bundles / external). Ringed nodes are
  engines or apps.
- **Edges** are real imports or data flows; the label is the verb.
- **Click** a node → the right inspector shows its purpose, its real source
  paths, and every edge in and out (click a peer to jump).
- **Click a plane** in the left rail to isolate it; click again to restore.
  **Search** filters by name. **Drag** to pan, **scroll** to zoom, **freeze**
  stops the simulation.

Current size: **60 nodes / 99 edges** across 7 planes (as of 2026-09-15).

One thing the graph says out loud: the **Workflow** tab's third lane is
**planned and not built**. Everything in the Overview tab is real code today.

---

## THE UPDATE RULE (standing instruction — also in `CLAUDE.md`)

> After any work session that changes the **architecture, data flow, or
> workflow**, refresh this graph before finishing.

`index.html` is the live copy; `graph-data.js` is regenerated *from* it. Always
edit `index.html`, then run the check — never hand-edit the two out of sync.

1. **Edit the inlined `GRAPH = {…}` block** near the top of the `<script>`:
   add / remove / relabel `nodes` and `edges`. Every node maps to a real file,
   event or service; every edge to a real import or data flow. Keep `id`s stable
   (edges reference them). Pick the right `plane`.
2. **Update the affected structured view(s)** in the same file:
   - the task lifecycle changed → `DF_STEPS` and/or the `task` lane in `WF_LANES`;
   - a new module, hook event, state file or eval stage → `ARCH_LAYERS` +
     `ARCH_LINKS`;
   - something in the v0.8 lane got **built** → move it out of the "planned, NOT
     built" lane. That lane is a promise, and a stale promise is the worst node
     on the page.
   Keep `sub:` text **at most ~42 characters** — the boxes are fixed width and
   longer text overlaps its neighbours. Long-form detail belongs in the node's
   `desc`, which the Overview inspector renders properly.
3. **Bump `meta.updated`** to today and prepend a one-line `meta.changelog` entry.
4. **Regenerate and validate:**

```bash
python architecture/check.py --render
```

Expect `OK` and `render  all four tabs draw`.

`check.py` also refuses to pass if any `.py` under `core/`, `eval/` or
`plugin/bin` is missing from the graph — a new module nobody drew is exactly how
a graph goes stale while still validating. That check was watched firing on a
throwaway module and clearing when it was removed.

**Do not skip `--render`.** The structural checks — balanced `<script>` tags,
doctype present, no external resources, no dangling edges — *all passed* on a
page that rendered nothing, because one apostrophe inside a single-quoted JS
string had broken the script. That failure was observed deliberately before this
check was trusted: the page was broken, the check failed, the page was restored,
the check passed. A page that parses is not a page that draws.

### What counts as "changes the architecture"

- a new module in `core/` or `eval/` that something else imports;
- a new or removed hook event, or a change to which tools an event matches
  (`core/wiring.py` — and remember `hooks.json` is *generated* from it);
- a new file under `.elevenpowers/`, or a change to what one holds;
- a new external dependency in the data path (a runner, a boundary, a service);
- a stage added to or removed from the evaluation pipeline.

### What does **not** need an update

Pure bug fixes, prose and comment edits, internal refactors that do not change
who-imports-whom, new tests, and plan or journey writing.

---

## Credit

The viewer — the canvas force simulation, the three SVG renderers, the
inspector, the theme toggle — is **reused from the architecture graph in the
author's `snag` project**, whose README defines the four-view design and the
update rule above. This repository borrowed it rather than writing a fourth
diagram tool, which is the standing rule in
[`PLAN.md` §1.5](../PLAN.md) and
[`docs/research/build-on.md`](../docs/research/build-on.md): start from the best
existing implementation, and state the one thing you add.

What was added here: a proper document head (`<!doctype>`, charset, viewport —
the original renders in quirks mode), block-level legend chips so a plane's
label and blurb no longer run together, a Python `check.py` in place of the
shell one-liner, and the render check being **seen to fail** before it was
trusted.

Keep it honest: this graph is only useful if it reflects the code. A stale node
is worse than a missing one.
