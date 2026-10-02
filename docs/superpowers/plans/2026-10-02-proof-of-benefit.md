# Proof of Benefit Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline, then one fresh whole-branch review.

**Goal:** Trace native delivery and measure a completion intervention against identical coding controls.
**Architecture:** Reuse native setup and subscription/process runners. Add an explicit evaluation recorder and frozen two-case protocol, separate from automatic product hooks and the original pilot.
**Tech Stack:** Python 3.11+ standard library, pytest, installed subscription CLI.
**Spec:** `docs/design/proof-of-benefit.md`.

## Global constraints

- Project-independent runtime behavior; no Snag special cases.
- Exact subscription models/medium effort, no API fallback or host trust bypass.
- Eight calls maximum, 240 seconds each, two tasks/arms/repeats, one working host.
- Freeze before calls; retain failures and neutral/worse outcomes.
- Recorder: at most 32 explicit files, 512 KiB total, 16 proposals; no links.
- No candidate source or raw transcript in ordinary product reports.
- Focused controls per change; broad suite and rendered architecture at delivery.

## Review focus

1. Recorder failures, moving files and index changes must not manufacture evidence.
2. Agent changes to tests, configuration or protocol must invalidate evaluation.
3. A successful host response without native intervention is not a tool benefit.
4. Quota, auth and setup failures must remain visible without API/model fallback.
5. Neither control selection nor repeated calls may select only favorable results.

## Task 1 — Diagnose the actual native boundary

Interfaces: existing setup invocation, installed CLI stdin/stdout and callback registry.
Files: affected `core/hosts/` or launcher only if cause demonstrated; regression tests and dated validation.

- [ ] Observe native startup in the owned disposable fixture; inspect producer errors.
- [ ] Reproduce any runtime cause with a real launcher control; watch RED.
- [ ] Fix the smallest generalized boundary and watch GREEN; preserve ordinary trust.
- [ ] Run affected host/launcher tests. Expected: legitimate callbacks accepted, malformed events remain incomplete.
- [ ] Commit and push descriptive diagnosis/fix. Record external limits separately.

## Task 2 — Neutral bounded proposed-completion capture

Interfaces: explicit task file allowlist -> bounded snapshot -> append-only proposal history.
Files: `eval/proposals.py`, `tests/test_proposals.py`.

- [ ] Write forward/adversarial controls for index neutrality, deletion, bounded bytes, links and unavailable history; observe RED.
- [ ] Implement recorder using ordinary host Stop input, always advisory, no Git writes.
- [ ] Seal contract and source identity; snapshot only frozen task files before intervention.
- [ ] Run `python -m pytest tests/test_proposals.py -q`. Expected: complete/control and incomplete/error cases distinguishable.
- [ ] Commit and push recorder.

## Task 3 — Frozen comparison and native evidence

Interfaces: two frozen cases + proposals + exact CLI observations -> complete per-run journal and qualified summary.
Files: `eval/benefit.py`, frozen task/evaluator module, tests.

- [ ] Write free gold/wrong candidates and scheduling/failure controls; observe RED.
- [ ] Reuse subscription auth/command and contained processes; record setup before launch.
- [ ] Run free controls and native acceptance. Expected: startup/edit/command/Stop processed before batch.
- [ ] Freeze protocol; run eight counterbalanced calls only on the working host.
- [ ] Independently grade initial/proposed/final snapshots; retain all attempts and exact limits.
- [ ] Commit and push harness and whitelisted artifacts as they become reviewable.

## Task 4 — Publish the evidence boundary

Interfaces: reproducible artifacts -> docs/status/PLAN/guide/README/journey and all architecture views.

- [ ] Update plan, status, guide, clean README feature area, journey and validation index.
- [ ] Update architecture GRAPH/DF/ARCH/WF and regenerate mirror.
- [ ] Run full regression, audit, doctor and `python architecture/check.py --render`.
  Expected: green controls, actual outcome counts, graph renders all tabs.
- [ ] Obtain one fresh whole-branch review, resolve important findings RED→GREEN.
- [ ] Push descriptive delivery commits; after exact-head CI passes update main.
