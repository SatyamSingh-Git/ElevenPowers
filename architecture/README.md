# ElevenPowers — living architecture graph

Five views of the system and its unfinished work — the runtime, plugin seam,
durable ledger, evaluation harness and contributor roadmap — in one
self-contained HTML file.

### ▶ **[Open the live graph](https://satyamsingh-git.github.io/ElevenPowers/architecture/)**

Or open [`index.html`](index.html) from a local clone — double-click it. No
server or build. The viewer works offline; choosing a source link opens its
document on GitHub.

> **Why clicking the file on github.com shows code.** github.com is a source
> browser: it renders `.md` and shows every other file as text. That is its
> viewer, not a problem with the page. The live link above is the same file
> served by GitHub Pages, where it renders. All five views and the contributor
> interactions were checked locally and over HTTPS. The served HTML matched the
> published source; see the [dated validation](../docs/validation/2026-10-04-contributor-roadmap.md).

## The five views (tabs across the top)

| Tab | What it shows | How it's drawn |
|---|---|---|
| **Overview** | Every module, event and service as a coloured node; every import and data flow as an edge. Draggable, zoomable, click-to-inspect. | canvas force-directed graph |
| **Data flow** | One task from request to verdict, as numbered **request → / response ←** pairs. | SVG swimlanes |
| **Architecture** | The system in tiers: host surface → the plugin seam → `core/` → durable state → `eval/` → external. | SVG layered lanes |
| **Workflow** | Shipped runtime, evaluation, native validation and v0.8 mechanisms, with their limits. | SVG numbered steps |
| **Planned** | Forty-one unfinished milestones, research questions, conditional extensions and proposals. Search and filter, then expand a card for requirements, acceptance criteria, a first contribution, prerequisites and sources. | responsive HTML cards using native `details` |

## Files

| File | Role |
|---|---|
| `index.html` | **Live source and self-contained viewer.** Its inlined `GRAPH`, three structured-view datasets and `PLANNED` contributor dataset drive all five tabs. |
| `graph-data.js` | **Generated mirror** of the Overview graph (`window.ELEVENPOWERS_GRAPH`). Regenerated from `index.html`; never hand-edited. |
| `check.py` | Regenerates the mirror, validates roadmap sources/dependencies and checks the page. `--render` exercises all five tabs and the contributor interactions. |

The three structured views are driven by small hand-curated datasets inlined in
`index.html` — `DF_ACTORS`/`DF_STEPS`, `ARCH_LAYERS`/`ARCH_LINKS`, and
`WF_LANES`. They are deliberately summaries rather than auto-derived from the
node graph, so each view stays readable.

The contributor view is driven by the inlined JSON array `PLANNED`. A card has a
stable `id`, title, topic, commitment status, summary, rationale, remaining work,
acceptance criteria, a small first contribution and repository source paths.
Optional `dependsOn` ids link to other cards; conditional cards require a
`trigger`. Share `#planned` for the whole view or `#planned/impact-graph` for an
expanded item. Search checks all card fields and combines with topic/status
filters. Several cards can remain open; keyboard activation and both themes work.

The statuses are substantive:

- **Open milestone** finishes a delivered capability's unmet exit.
- **Planned research** represents remaining master-plan experiments.
- **Conditional** waits for the documented measurement trigger.
- **Proposed** records a direction for design discussion, including
  PatchProof, OpenCodeMap, TestMiner and three additional contribution ideas.

The current 41 cards comprise 4 open milestones, 17 planned research items,
14 conditional extensions and 6 proposals. This view consolidates the remaining
work in `PLAN.md`, `docs/status.md`, `docs/postponed.md` and the readable roadmap.
Completed deliveries are context inside cards, not presented as future work.
The view does not approve model runs or supersede research/defer conditions.

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

Current size: **122 nodes / 278 edges** across 7 planes (as of 2026-10-04),
including changed-region targets, schema-2 command qualifications and completed
corrected regrades alongside frozen original producer identities,
four hard interacting task graders, every-attempt regrading,
unstarted-only recovery and separately versioned visible/shutdown audits,
the controlled completion comparison and neutral proposal recorder,
including runtime-bound validation, readonly performance and a frozen subscription pilot,
fresh staged health, bounded native diagnostics, disposable acceptance,
onboarding, native edits, portable reports and optional changed-file test strength.
The fifth tab adds contributor content. ImpactGraph now has real runtime source
nodes, an explicit CLI query workflow and an open acceptance card. Static paths,
declared contracts, current unsigned observations and historical associations
retain separate qualifications. Optional virtual TypeScript compiler, offline
actual Python/Node coverage and frozen independent fault/reference evaluation
now have explicit source and workflow nodes. The process-fault miss and broad
candidate sets kept that acceptance exit unqualified. The relevance repair now
adds source-only literal imports, context-bound pytest fixtures and independent
focused/fallback/support tiers. Saved report reclassification preserves original
producer identity; broader noise and native cost still keep hooks unqualified.
Source maps, live traces,
framework adapters and further relevance work remain open; see
[ImpactGraph acceptance](../docs/validation/2026-10-04-impact-acceptance.md).

The **Workflow** tab's third lane now identifies built v0.8 mechanisms and their
limits. Mutation findings are optional human review observations; missing engines,
failed baselines, import redirection and sampling are explicit. There is no new
verdict and no raw mutant target in automatic agent feedback.

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
   - a planned item got **built** → reconcile or remove its `PLANNED` card and
     update the shipped graph/workflow as appropriate. Preserve any genuinely
     unmet acceptance criterion as remaining work, with current sources;
   - unfinished work or a proposal changed → update its `PLANNED` card, source
     links, prerequisites and status. Conditional work keeps its actual trigger.
   Keep `sub:` text **at most ~42 characters** — the boxes are fixed width and
   longer text overlaps its neighbours. Long-form detail belongs in the node's
   `desc`, which the Overview inspector renders properly.
3. **Bump `meta.updated`** to today and prepend a one-line `meta.changelog` entry.
4. **Regenerate and validate:**

```bash
python architecture/check.py --render
```

Expect `OK` and `render  all five tabs work; cards, filters, keyboard, shared
links and narrow layout verified`.

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
inspector, the theme toggle — is **reused from an earlier architecture graph of
the author's**, which is where the four-view design and the update rule above
come from. This repository borrowed it rather than writing a fourth
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

## Current product flow

The 2026-09-29 graph includes automatic startup health and coverage, root-manifest command discovery with project overrides, bounded Git-aware source selection, and pass/fail/incomplete receipts. Completion runs missing checks; baseline execution requires relevant matching evidence. Codex, Gemini CLI, Cursor Agent and GitHub Copilot CLI adapters join Claude Code through the shared runtime. Per-test dependency invalidation and live installed-session acceptance remain separate work.

Readiness now delegates to `core/health.py` and one fresh exporter view, showing
native stages, every declared command's current aggregate outcome and retained
timing samples. The automatic callback registry stores hashed correlation and
bounded receipt/phase history. Explicit `core/hosts/acceptance.py` preparation
creates a new Python/Node exercise; inspection rechecks its immutable contract
and requires native pass/fail/incomplete history plus fresh completion.

The graph has 122 nodes and 278 edges. [Current status](../docs/status.md) and
[validation records](../docs/validation/README.md) describe which product paths
were exercised. The Planned tab exposes unfinished work separately from those
delivered paths. See [journey 59](../journey/59-a-roadmap-contributors-can-open.md)
for the contributor view and its verification boundary.
