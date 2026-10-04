# ImpactGraph: explained impact across project boundaries

Status: foundation delivered on 2026-10-04. The separately approved
[real-project acceptance milestone](impact-acceptance.md) adds optional compiler
resolution, offline actual coverage conversion and independent evaluation.
Framework extraction, OpenTelemetry, more languages and automatic integration
remain open; this is not the entire ImpactGraph vision.

The user wants a useful graph for end-to-end development in any project, not a
Snag-specific feature or a diagram of imports presented as a prediction of
breakage. A person or coding agent must be able to ask what depends on a file,
follow the reason, find relevant tests and see what the tool cannot establish.

## Approach and reuse

Build a module inside ElevenPowers with a standalone CLI and Python API. A
separate repository would duplicate scanning and evidence policy; extending the
existing name-matching radius alone cannot carry provenance or contracts.

Reuse `core.evidence.scan_sources` for project-owned selection budgets, Git
ignores and repository boundaries; `core.polyglot` for the optional grammar
pack; `core.surface.TEST_NAME` for candidate test classification; and
`core.export.write` for explicit atomic exports. Borrow Aider's graph extraction
approach, not its implementation: its Apache-2.0 repository map selects context
under a token budget. ImpactGraph adds typed, content-bound relationships and
explainable impact paths. Python uses standard-library ASTs; JS/TS import
extraction uses the existing tree-sitter adapter. No mandatory new dependency.

Sources checked on 2026-10-04: [Aider repository map](https://aider.chat/docs/repomap.html),
[Python AST](https://docs.python.org/3/library/ast.html),
[Tree-sitter parsing](https://tree-sitter.github.io/tree-sitter/using-parsers/2-basic-parsing.html).
Optional validation dependencies: tree-sitter-language-pack 1.20.0 and
tree-sitter 0.26.0. The runtime still imports without site packages.

## First delivery

1. A deterministic schema-1 graph contains selected files, top-level Python
   symbols and optional declared component/route/database/config/infrastructure
   nodes. An edge points from a dependent to its dependency and carries its
   kind, origin, source location and evidence qualification. File membership
   does not imply that an unrelated symbol with the same name is called.
2. Resolve Python absolute/relative imports using unique repository module
   candidates, including `src/` layouts and package initializers. Ambiguous
   names remain gaps. Root and conventional `src/` module roots are supported;
   other implicit PYTHONPATH roots are not guessed. Record conservative imported top-level Python callable
   links only where binding is unambiguous; shadowed bindings remain unresolved.
   For JS/TS, resolve relative imports, barrels and uniquely declared workspace
   package entries. Missing grammar, syntax errors, aliases/export maps that
   cannot be resolved and unsupported languages remain explicit. JS/TS calls
   and type-dependent dispatch are not claimed in this first delivery.
3. Automatically read optional project-owned `impactgraph.json`, schema 1.
   It declares logical nodes and dependency/uses/test relationships, with safe
   selected path anchors. This is a declared contract, not observed behavior.
   Framework-specific route/SQL extraction is a later adapter, not string
   guessing over arbitrary applications.
4. Accept an explicit optional observation JSON with schema 1, producer/run
   identity, a complete flag, the graph source fingerprint and typed edges.
   Current, complete observations are useful relationships; stale, incomplete
   and malformed imports cannot enter current impact paths. Observations are
   local unsigned reports, not authenticated coverage or correctness evidence.
   The observation artifact itself is excluded from the source fingerprint.
5. Optionally read a bounded recent Git history. Keep co-change associations in
   a separate section; never propagate them as causal dependencies. Large
   commits, unavailable Git and truncated history have explicit qualifications.
   Read only file lists and commit IDs, never author identities or commit prose.
6. Analyze reverse dependency paths from one or more files, or a declared node
   ID. Return direct/transitive/observed/declared relationships, explanations,
   relevant test candidates and history associations. Categories express
   evidence, not calibrated breakage probabilities. A test import is a candidate
   check, not proof that assertions cover the changed behavior.

## Interfaces and freshness

`core.impact.build(root, *, seconds=30, max_files=None, max_bytes=None,
observations=None, history=0) -> Graph` builds from freshly read bytes on every
query. `Graph.to_dict()` returns a portable schema-1 snapshot.
`core.impact.analyze(graph, files, *, max_depth=6, max_results=100) -> dict`
accepts repository-relative file paths or graph node IDs. It never executes
project code, tests, an AI host or an installer. Missing/deleted selected paths
and query caps produce explicit gaps, rather than a claim of no impact.

No implicit cache or project-state writes. Scan configuration is read separately
under the input cap, without command discovery; Git scans disable fsmonitor so
project monitor scripts cannot run. Content fingerprints include selected
source/configuration/dependency files and the declaration map, not mtimes or
only HEAD. Rebuilding handles dirty edits, additions, removals and renames; an
old observation goes stale when any selected input or selection policy changes.
The graph's selection/adapter coverage is not exhaustive semantic coverage.

Default cooperative build budget: 30 seconds, at most 20,000 selected files and
256 MiB, using project scan overrides. Each file/explicit input is bounded by
4 MiB; declaration/observation rows by 10,000; graph edges by 50,000. Native AST
or filesystem calls can exceed a cooperative deadline. History is opt-in, at
most 200 commits, 2 MiB of accepted output and 40 selected files per commit.
The shared process runner separately caps capture at 8 MiB, with disk spooling
and cooperative polling; neither limit is an OS resource boundary. Queries cap
depth at 20 and results at 1,000. Every cap is reported when it omits work.

## CLI and integration

`python plugin/bin/ep_impact.py --project PATH FILE [FILE ...]` prints explained
Markdown; `--json` returns query JSON, `--graph` exports the graph, `--observations
PATH` imports an explicitly selected artifact and `--history N` enables history.
`--output PATH` is an explicit export; overwrite requires `--force`. `--change`
records user intent without turning its prose into evidence. Exit 0 means a
report was produced; `--check` exits 1 for incomplete requested coverage;
invalid invocation exits 2. Queries read fresh inputs automatically.

The first delivery is available to all hosts through the same CLI/API. Existing
runtime gates and radius behavior stay stable until representative noise and
overhead measurements justify automatic hook integration. The graph is the
shared foundation for later PatchProof/OpenCodeMap/TestMiner adapters; those
features are not part of this delivery.

## Acceptance and measurement

- A cross-component repair fixture links a changed session function to an API,
  worker, declared storage/route contract and candidate tests, with unrelated
  same-name functions excluded. An independently executed repair/regression
  control demonstrates that the suggested test catches the seeded fault.
- Python relative/src/package imports, TypeScript relative/barrel/workspace
  imports, ambiguous imports, binding shadows and malformed source are checked.
- Dirty bytes with identical mtime, addition/deletion/rename, map changes, stale
  and incomplete observations, ignored/generated inputs, nested repositories,
  unsafe/symlink paths and all budgets yield correct updates or visible gaps.
- History-only co-change never becomes an impact path or test-coverage proof.
- CLI JSON/Markdown, explicit exports and standard-library-only import work.
- Existing relevant suites, full regression suite, independent review and
  rendered architecture pass before integration; docs retain actual limits.

These establish graph usefulness and fault sensitivity on bounded controls.
They do not establish improved AI coding outcomes, universal precision/recall,
exhaustive coverage or production safety. Held-out comparisons remain open.
