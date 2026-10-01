# Project health implementation plan

> For agentic workers: use superpowers:executing-plans inline, with one fresh
> whole-branch reviewer after implementation. Steps use checkbox tracking.

Goal: deliver staged, fresh project health and a repeatable native acceptance
workflow across all five hosts, for any repository.

Architecture: extend existing callback state with bounded receipt/timing metadata;
compose a read-only health view from the existing exporter and diagnostics;
prepare disposable native exercises only on explicit invocation.

Stack: Python 3.11+ standard library; pytest; Python unittest and Node TAP fixtures.
Spec: `docs/design/project-health.md`. Base: `5b245f9`.
Branch: `codex/project-health`. The user approved implementation; retain inline
execution and incremental publication from the current working arrangement.

## Seventeen incremental pushes

1. Design/plan (already published).
2. Bounded native diagnostics and receipt links.
3. Shared report freshness/receipt metadata and timings.
4. Staged project-health composition.
5. Diagnostic safety, task/session correlation and incomplete-state controls.
6. Readiness CLI health/budget/check options.
7. Non-executing optional-engine/environment diagnostics.
8. Disposable Python/JavaScript exercise preparation.
9. Strict read-only acceptance evaluation.
10. Doctor CLI acceptance workflow.
11. Actual producer and five-adapter contract acceptance.
12. Measured timing/history and larger-project controls.
13. Independent review corrections and integration evidence.
14. Rendered architecture.
15. All six guides.
16. Status, roadmap, development, validation and journey.
17. README/provenance and complete main publication.

## Global constraints

- No project-specific runtime branches, hardcoded acceptance paths or commands.
- No ordinary health write, test/engine execution, package install or host launch.
- One fresh exporter view; default 10-second, maximum 120-second cooperative deadline.
- At most 64 native receipt links and 32 timing samples per canonical phase.
- No raw session, prompt, input, output, source or mutant metadata in diagnostics.
- Configuration and task changes invalidate relevant observed stages.
- Replay never activates the native pipeline; observations are not authentication.
- Disposable preparation refuses existing/linked destinations; no paid call without approval.

## Review focus

1. Earlier tasks/configurations must not establish current native completion.
2. Complete/fail and incomplete receipts must not be counted as project success.
3. Corrupt state, symlinks and exhausted read budgets must remain explicit.
4. A health read must not execute commands, import optional engines or write state.
5. A replay or prepared exercise must not become native installed-session acceptance.

## Task 1 — Bounded native observation and timing

Files: `core/hosts/readiness.py`, `core/hook.py`, `tests/test_project_health.py`.
Interfaces: `callback(platform, root, event, payload=None)`,
`record_receipts(records, task)`; existing callers remain valid.

- [x] Write controls: real ingress stores per-phase timing/receipt hashes;
  replay stores none; startup does not imply Stop; settings reset history;
  history/sample caps disclose eviction; processing errors preserve counts.
- [x] Run tests and watch missing fields/helper fail.
- [x] Add bounded diagnostics within existing callback transaction and call receipt
  capture only after the ledger successfully records parsed command receipts.
- [x] Run these controls plus onboarding tests; commit and push the working part.

## Task 2 — Shared fresh health and readiness CLI

Files: new `core/health.py`, `core/export.py`, `core/hosts/onboarding.py`,
`plugin/bin/ep_ready.py`, same test file.
Interfaces: `health.inspect(host, root, timeout=10) -> dict`,
`health.render(value) -> str`; existing readiness report/keys preserved.

- [x] Write forward/adversarial controls around real stored receipts: fresh/stale,
  fail/incomplete, old task, missing events, unreadable state, scan budget and
  read-only behavior. Sample assertion: `inspect('codex', root)['latest_receipt']
  ['freshness'] == 'stale'` after editing a source file.
- [x] Watch RED, then compose one bounded exporter view, stage interpretation,
  retained timing summaries and optional engine metadata without importing engines.
- [x] Add `--seconds` and opt-in `--check`; render stage-specific next actions.
- [x] Run health/onboarding/export tests; commit and push the working part.

## Task 3 — Disposable native acceptance

Files: new `core/hosts/acceptance.py`, `plugin/bin/ep_doctor.py`,
new `tests/test_native_acceptance.py`.
Interfaces: `prepare(host, destination, language, source, version='') -> dict`,
`inspect(host, root, timeout=10) -> dict`.

- [x] Write controls for actual unittest/Node fail-to-pass producers, isolated
  setup, existing/linked path refusal and untouched original project.
- [x] Write acceptance controls: prepared/replayed exercise is waiting; real
  receipt diagnostics require pass/fail/incomplete plus fresh native completion;
  changed configuration/task/missing history is not accepted.
- [x] Watch RED, implement preparation and bounded read-only inspection, add strict
  doctor CLI preparation/inspection modes while preserving old diagnostic flags.
- [x] Run actual producers and all five normalized launcher contract controls;
  commit and push the working part.

## Task 4 — Integration and independent review

- [x] Run full suite, audit probes, grader, stdlib imports and doctor replay.
- [x] Dispatch one fresh reviewer with base/head, spec, plan, ledger and focus.
- [x] Reproduce important findings RED, fix, then run relevant and broad checks.
- [x] Probe installed host versions without model calls; exercise free native
  startup where available and qualify unavailable/live model-dependent steps.
- [x] Record exact checks, limits and decisions; push corrections as ready.

## Task 5 — Documentation and publication

- [ ] Update all six guides, README, PLAN/status/postponed/development, provenance,
  dated validation and journey.
- [ ] Update architecture graph and structured views; run `check.py --render`.
- [ ] Check links and diff whitespace, publish completed main without rewriting
  history; check exact-head hosted CI and final remote/local cleanliness.
- [ ] Preserve decisions in validation/final handoff; safely remove only this
  plan's scratch directory.
