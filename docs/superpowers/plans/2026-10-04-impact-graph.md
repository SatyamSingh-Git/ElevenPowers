# ImpactGraph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build a generalized local graph and explained impact query with bounded, qualified evidence.

**Architecture:** Fresh repository scanning feeds typed source/declaration edges,
optional observations and separately qualified history. A reverse traversal
returns reproducible paths and candidate tests. The CLI shares this API.

**Tech Stack:** Python 3.11+, standard-library AST/JSON/hashlib/Git subprocess;
existing optional tree-sitter adapter for JS/TS.

**Spec:** [ImpactGraph design](../../design/impact-graph.md)

## Global Constraints

- Build for any project, without special-case repository paths or commands.
- No mandatory new dependency; Python works without site packages.
- No implicit state writes or project/host/model execution.
- Default 30-second cooperative deadline, 20,000 files/256 MiB scan defaults;
  project scan overrides apply, file/input cap 4 MiB, rows 10,000, edges 50,000.
- History opt-in, maximum 200 commits/2 MiB/40 selected files per commit.
- Query defaults 6 hops/100 results; maximum 20 hops/1,000 results.
- Separate static, declared, observed and historical evidence; stale/incomplete
  observations never become current paths; no breakage probabilities.

## Review Focus

- Ambiguous package roots and shadowed bindings must not invent call edges.
- Symlink parents, traversal and nested repositories must not escape scope.
- A stale or malformed observation must not contaminate current recommendations.
- Byte/file/deadline/history/query caps must be visible, including exact bounds.
- A test import and co-change must not become passing correctness evidence.

## Task 1: Fresh model and Python relationships

Files: create `core/impact/__init__.py`, `model.py`, `source.py`, `build.py`;
create `tests/test_impact_source.py`.

Interfaces: `build(...) -> Graph`; `Graph.nodes` maps IDs to `Node`;
`Graph.edges` holds `Edge`; `Graph.issues`, `fingerprint`, `coverage`,
`associations`, `quarantined` qualify the snapshot; `to_dict()` serializes it.
Node fields: id, kind, label, path, line. Edge fields: source, target, kind,
origin, path, line, identity. Direction: dependent -> dependency.

- [x] Write controls for aliases, relative/package/src imports, top-level calls,
  same-name unrelated functions, shadows, ambiguity, parser failure, dirty bytes,
  budgets and boundaries; run them before implementation.
- [x] Implement bounded fresh reads around `scan_sources`; parse without importing
  candidate code. Build deterministic node/edge IDs and content fingerprint.
- [x] Implement unique module resolution and conservative Python bindings;
  suppress ambiguous/shadowed imported calls and retain location-qualified gaps.
- [x] Run `.venv/Scripts/python.exe -m pytest tests/test_impact_source.py -q`;
  expected all controls pass. Commit/push the working foundation.

Representative behavioral contract:

```python
graph = build(root)
assert any(e.kind == 'calls' and e.target == 'symbol:session.py#expire'
           for e in graph.edges)
assert not any(e.source == 'file:unrelated.py' and e.kind == 'calls'
               for e in graph.edges)
assert build(root, max_files=1).issues
```

## Task 2: JS/TS repository imports

Files: extend `source.py`; create `tests/test_impact_typescript.py` and
`requirements-impact.txt`. Consumes safe selected source bytes from Task 1;
produces location-qualified `imports` edges using the existing real grammar.

- [x] Write real-parser controls for relative imports, JS-extension substitution,
  barrels, declared workspace main/module/types entry, ambiguity, unknown aliases,
  syntax errors and unavailable grammar. Run before implementation.
- [x] Resolve only selected, in-scope candidates. Read selected package.json;
  duplicate names and unsupported exports/path mappings remain gaps.
- [x] Pin optional acceptance dependencies; run source + TS controls with the
  installed producer. Commit/push validated adapter support.

```python
assert ('file:api.ts', 'file:session.ts') in {
    (e.source, e.target) for e in build(root).edges if e.kind == 'imports'}
```

## Task 3: Declared and observed relationships

Files: create `core/impact/ingest.py`, `tests/test_impact_ingest.py`.
Consumes Graph and safe selected declaration bytes. Produces qualified `depends_on`,
`uses`, `tests`, `observed_call`, `observed_test` edges or quarantined observations.

- [x] Write schema, safe-anchor, missing-endpoint, duplicate-ID, row cap and
  malformed controls plus current/stale/incomplete observation controls.
- [x] Validate declaration graph atomically before adding it; allow logical nodes
  with optional selected file anchors, never executable commands.
- [x] Validate schema-1 observation identity/fingerprint/completion and existing
  endpoints. Keep invalid/stale/incomplete artifacts out of active graph edges.
- [x] Run ingestion/source/TS controls; commit/push qualified contract evidence.

```python
assert build(root, observations=artifact).quarantined  # wrong fingerprint
assert not any(e.origin == 'observed' for e in build(root, observations=artifact).edges)
```

## Task 4: Explained queries, bounded history and CLI

Files: create `query.py`, `history.py`, `plugin/bin/ep_impact.py`,
`tests/test_impact_query.py`, `tests/test_impact_cli.py`.
Consumes Graph; produces schema-1 query dict and `markdown(report) -> str`.

- [x] Write reverse/transitive/multiple-seed/cycle tests, declaration and test
  paths, missing/deleted paths, depth/result cap, stale exclusion and
  history-only association controls. Run before implementation.
- [x] Implement reverse traversal with stable explanations and no co-change
  propagation. Group candidate tests by the existing test-name policy.
- [x] Read opt-in Git file lists with strict subprocess/output/commit-size bounds;
  store current selected file associations separately, not causal edges.
- [x] Add fresh CLI queries and explicit no-overwrite exports. Write/read JSON,
  invalid argument, missing project and standard-library-only CLI tests.
- [x] Run all `tests/test_impact_*.py`; commit/push usable CLI/API.

```python
report = analyze(build(root), ['session.py'])
assert 'tests/test_login.py' in [n['path'] for n in report['tests']]
assert report['tests'][0]['explanation']  # actual path, not name resemblance
```

## Task 5: Acceptance, review and documentation

Files: create `tests/test_impact_acceptance.py`, dated validation, journey 60,
`the-guide/impactgraph.md`; update README/commands/features/roadmap/status/PLAN,
architecture source and its generated mirror.

- [x] Execute an independent cross-component fixture: legitimate behavior passes,
  a seeded expiration regression fails the suggested API/worker test, and a
  valid equivalent repair passes. Retain exact producer and timing qualifications.
- [ ] Run the full regression suite and standard-library import; request one
  independent whole-branch review, fix substantive findings with controls.
- [x] Map every new runtime module in the architecture, reconcile the Planned
  card with remaining limitations, regenerate and run `architecture/check.py
  --render`. Validate local documentation links and report actual measurements.
- [ ] Commit/push docs and validation; integrate to main under standing user
  authorization once required checks pass. Keep later framework/live-trace/type
  adapters and held-out outcome measurements explicitly unfinished.

Execution: inline, following the user's instruction to plan and start building.
Baseline: 41 existing scanner/atlas/radius controls passed, 26 optional grammar
controls skipped before installing the pinned optional acceptance dependencies.
