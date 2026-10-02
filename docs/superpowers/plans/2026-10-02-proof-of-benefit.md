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

- [x] Observe native startup in the owned disposable fixture; inspect producer errors.
- [x] Reproduce any runtime cause with a real launcher control; watch RED.
- [x] Fix the smallest generalized boundary and watch GREEN; preserve ordinary trust.
- [x] Run affected host/launcher tests. Expected: legitimate callbacks accepted, malformed events remain incomplete.
- [x] Commit and push descriptive diagnosis/fix. Record external limits separately.

## Task 2 — Neutral bounded proposed-completion capture

Interfaces: explicit task file allowlist -> bounded snapshot -> append-only proposal history.
Files: `eval/proposals.py`, `tests/test_proposals.py`.

- [x] Write forward/adversarial controls for index neutrality, deletion, bounded bytes, links and unavailable history; observe RED.
- [x] Implement recorder using ordinary host Stop input, always advisory, no Git writes.
- [x] Seal contract and source identity; snapshot only frozen task files before intervention.
- [x] Run `python -m pytest tests/test_proposals.py -q`. Expected: complete/control and incomplete/error cases distinguishable.
- [x] Commit and push recorder.

## Task 3 — Frozen comparison and native evidence

Interfaces: two frozen cases + proposals + exact CLI observations -> complete per-run journal and qualified summary.
Files: `eval/benefit.py`, frozen task/evaluator module, tests.

- [x] Write free gold/wrong candidates and scheduling/failure controls; observe RED.
- [x] Reuse subscription auth/command and contained processes; record setup before launch.
- [x] Run free controls and native acceptance. Expected: startup/edit/command/Stop processed before batch.
- [x] Freeze protocol; run eight counterbalanced calls only on the working host.
- [x] Independently grade initial/proposed/final snapshots; retain all attempts and exact limits.
- [x] Commit and push harness and whitelisted artifacts as they become reviewable.

## Task 4 — Publish the evidence boundary

Interfaces: reproducible artifacts -> docs/status/PLAN/guide/README/journey and all architecture views.

- [x] Update plan, status, guide, clean README feature area, journey and validation index.
- [x] Update architecture GRAPH/DF/ARCH/WF and regenerate mirror.
- [x] Run the audit, doctor and rendered architecture checks; run corrective controls and start the complete regression delivery gate.
  Expected at publication: green full regression, actual outcome counts, graph renders all tabs.
- [x] Obtain one fresh whole-branch review, resolve important findings RED→GREEN.
- [x] Push descriptive implementation commits and stage the exact-head CI/main delivery gate.

Publication exit: the corrected complete regression and all four exact-head
hosted CI jobs must pass before main is fast-forwarded. Git refs and the linked
[tests workflow](https://github.com/SatyamSingh-Git/ElevenPowers/actions/workflows/tests.yml)
carry the final publication state. The eight-run measurement is complete;
demonstrating a patch-correctness improvement remains a separate evidence exit.
