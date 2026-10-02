# Native Validation Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline, then one fresh whole-branch review.

**Goal:** Produce qualified versioned compatibility/performance reports and a
bounded subscription-CLI outcome pilot on challenging work.

**Architecture:** Extend existing acceptance and native observations with runtime
identity. Compose explicit reports from those inspectors; keep experiment work
under `eval/`, outside automatic plugin hooks. Reuse contained process execution
and atomic report writing.

**Tech Stack:** Python 3.11+ standard library, pytest, installed native CLIs.
**Spec:** `docs/design/native-validation.md`.

## Global constraints

- Generalize every path and command; no Snag runtime policy.
- No automatic model call, host launch, paid API fallback or engine install.
- User approved subscription sign-ins; API keys are never used for this pilot.
- Runtime identity: at most 512 eligible files, 8 MiB total, reject links.
- Reports: schema version 1, at most 128 KiB input; explicit atomic output.
- Performance: 3 reads by default, 1–20 allowed; 60 seconds default, 120 maximum.
- Pilot: at most 8 runs, 240 seconds each, 2 replicates per host/arm; frozen inputs.
- Exact models: `gpt-6.1-sol` medium; `claude-sonnet-5-5` medium. No model fallback.
- Task size is not a pass criterion; assess coding outcomes and engaged mechanisms.
- Complete histories are not authentication, production correctness or effect proof.

## Review focus

1. Old/runtime-mismatched observations must not qualify a new release.
2. Malformed, duplicated or contradictory matrix entries must not inflate success.
3. Failed/slow performance samples and moving inputs must remain visible.
4. Subscription execution must not fall back to API credentials or persist secrets.
5. Agent edits to visible tests, the grader or run identity must invalidate evaluation.

## Task 1 — Bind compatibility to runtime and installed version

Files: new `core/hosts/provenance.py`, `core/hosts/probes.py`,
`core/hosts/validation.py`; modify readiness/diagnostics/acceptance.
Interfaces: `fingerprint(source=None) -> str`; `probe(host, timeout=5) -> dict`;
`capture(host, root, timeout=10, observe_version=False) -> dict`.

- [ ] Write `test_runtime_identity_changes_only_for_shipped_code`, link/budget
  controls and observe import/missing-behavior RED before implementation.
- [ ] Implement deterministic bounded runtime hashing; bind actual startup and
  preparation. Verify stale runtime and legacy unbound evidence cannot qualify.
- [ ] Write actual Python child `--version` producer controls for success, nonzero,
  timeout and ambiguous versions; never retain raw output. Watch RED then GREEN.
- [ ] Capture one existing acceptance read; whitelist export fields and recheck
  runtime identity after read. Probe only with explicit operator request.
- [ ] Run `python -m pytest tests/test_native_validation.py tests/test_native_acceptance.py -q`.
  Expected: all controls pass; prepared/replayed exercises remain waiting.

## Task 2 — Compatibility matrix and performance reports

Files: `core/hosts/validation.py`, new `core/hosts/performance.py`,
new `plugin/bin/ep_validate.py`; tests `test_native_validation.py`,
`test_performance.py`, `test_validation_cli.py`.
Interfaces: `matrix(records) -> dict`, `render(value) -> str`;
`measure(host, root, repeats=3, timeout=60) -> dict`.

- [ ] Write missing-host, duplicates, invalid JSON/nonfinite/malformed hash controls;
  create ten explicit host/language cells. Watch RED, implement conservative grouping.
- [ ] Implement Markdown/JSON rendering and reuse `core.export.write` for explicit
  atomic output. No output write when only reading or printing.
- [ ] Write performance controls with finite deterministic clocks: every attempted
  read retained, deadline stops scheduling, health failure not omitted, readonly bytes
  unchanged. Watch RED, implement repeated health reads and sample summaries.
- [ ] Qualify retained callbacks separately; Stop includes command time. Recheck
  source/software movement and retain source counts/health state per sample.
- [ ] Add argparse subcommands `capture`, `matrix`, `performance`; require explicit
  host/project/input paths and refuse conflicting/unknown flags.
- [ ] Run `python -m pytest tests/test_native_validation.py tests/test_performance.py tests/test_validation_cli.py -q`.
  Expected: all pass; invalid options exit 2, unqualified `--check` exits 1.

## Task 3 — Frozen challenging task and subscription runner

Files: new `eval/subscription.py`, `eval/paired.py`, `eval/challenge.py`;
tests `test_subscription.py`, `test_paired.py`, `test_challenge.py`.
Interfaces: `command(host, executable, root, prompt, model, effort) -> list[str]`;
`run_case(...) -> dict`, `summarize(records) -> dict`; `prepare(root) -> dict`,
`grade(root) -> dict` for the frozen original multi-module task.

- [ ] Write CLI producer/auth controls: allowed subscription mode, API-key refusal,
  timeout/setup separation, usage unavailable remains unavailable. Watch RED→GREEN.
- [ ] Freeze task/visible tests/evaluator/prompt IDs before runs; baseline and tool
  roots have identical task bytes. Check legitimate gold behavior and deliberately
  wrong candidates against the actual evaluator before any agent invocation.
- [ ] Add bounded per-run journaling, randomized balanced arm order, equal effort
  and runtime allowance. Agent return code is distinct from grader outcome.
- [ ] Controls: modified visible tests/identity, partial journal, unavailable model,
  interrupted process and grade failure cannot become a resolved task.
- [ ] Run `python -m pytest tests/test_subscription.py tests/test_paired.py tests/test_challenge.py -q`.
  Expected: complete contracts pass; no test starts a real model.

## Task 4 — Actual sessions, measurements and independent review

- [ ] Prepare new owned exercises; run installed Claude/Codex via verified
  subscription auth, preserve actual observations and unavailable-host gaps.
- [ ] Run free performance reads on unrelated small projects and a large acceptance
  repository. Do not write source/config or run its declared commands.
- [ ] Run the frozen eight-run pilot, at most 240 seconds each, same model/effort
  per arm. Preserve every result, including neutral outcomes and setup failures.
- [ ] Dispatch one fresh reviewer; reproduce Important/Critical findings RED before
  one correction pass, then broad suite. No repeated speculative full-suite loops.
- [ ] Run full pytest, audit probes, `python -m eval.validate`, doctor replay and
  stdlib imports. Expected: passing output, skip counts and limits recorded exactly.

## Task 5 — Documentation, architecture and publication

- [ ] Refresh architecture source/mirror and all structured views; run
  `python architecture/check.py --render`. Expected: all tabs draw.
- [ ] Update all six guides, status, postponed work, README feature section,
  roadmap/PLAN and journey. Reconcile original A/B closure and existing modules.
- [ ] Record native gaps, performance protocol/sample sizes and all pilot results;
  no broad improvement claim from a small sample or a ceiling baseline.
- [ ] Check links/whitespace, complete twenty-nine incremental feature pushes,
  then fast-forward verified main with preserved history and exact-head CI.

## Incremental publication boundaries

Publish each as its checks finish; messages describe the actual change:

1. Current plan reconciliation and approved validation/pilot design.
2. Bounded deterministic runtime identity.
3. Automatic startup identity observations.
4. Runtime-bound disposable acceptance.
5. Contained installed-version probes.
6. Whitelisted native compatibility captures.
7. Conservative ten-cell compatibility matrix.
8. Explicit compatibility CLI and atomic reports.
9. Bounded read-only latency sampling.
10. Timing qualification and retained callback distributions.
11. Performance CLI and producer/readonly integration controls.
12. Frozen challenging behavioral task and independent evaluator.
13. Subscription-authenticated CLI command controls.
14. Paired run journaling and equal-budget grading.
15. Outcome protocol/adversarial integration controls.
16. Installed-session/performance/pilot observations and required corrections.
17. Rendered architecture and all six guides.
18. Independent behavior controller/worker and legitimate package imports.
19. Strict outcome summary prerequisites and state/grade consistency.
20. Recorded-protocol summary reproduction after evaluator updates.
21. Explicit read-only archived-pilot inspection and private-field rejection.
22. Original protocol artifact and reproduced outcome summary.
23. Corrected evaluator, archive inspection and native trust guides.
24. Failure-record metadata validation before archived exports.
25. Bounded type-preserving candidate behavior transport.
26. Plan, roadmap, status and journey reconciliation.
27. Dated trusted native-session observations and conservative capture.
28. Delivery validation, review evidence and final repository checks.
29. Clean README feature update and verified main publication.

No empty commits, force pushes, counter suffixes or fabricated positive outcomes.
