# Declared-check closure implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make exact declared-check gaps visible at completion and retain bounded, privacy-safe feedback delivery observations before another benefit comparison.

**Architecture:** A pure declared-check read model classifies each configured declaration independently of the existing task verdict. A separate delivery observer connects an already-reserved feedback intent to a successfully flushed native host context and later exact receipt links, preserving the distinction between intent, emission, and subsequent observation.

**Tech Stack:** Existing Python standard-library runtime, pytest, existing ledger/host/readiness transport, and the rendered architecture map.

**Spec:** [Declared-check completion closure](../specs/2026-10-18-declared-check-closure-design.md)

## Global Constraints

- Generalized across every project and the five existing host adapters; test fixtures are not product rules.
- No-model validation first; no automatic declared command, new dependency, new completion blocker, receipt promotion, or verdict change.
- Retain raw feedback only in transit; durable observation holds hashes and bounded metadata only.
- Keep off/guide/strict policy, exact command matching, real failure, interruption, source/configuration/input movement, and current reuse behavior unchanged.
- Update README/status/guides/journey and all five architecture views before delivery; run `python architecture/check.py --render`.
- Push independently verified meaningful slices to `main` frequently.

## Review Focus

- A passing generic receipt must never classify a configured exact declaration as `CURRENT`.
- A current exact failure must remain `FAILED`, while an incomplete late attempt must not be overwritten by an earlier pass.
- Source/configuration/input movement must preserve `STALE`; a missing declaration must remain `ABSENT`.
- A rendered or replay-only response must not create native emission evidence.
- A later matching receipt is temporal correlation only and must not be displayed as model consumption.

### Task 1: Exact declared-check completion model

**Files:**
- Create: `core/declared_completion.py`
- Create: `tests/test_declared_completion.py`

**Interfaces:**
- Produces `rows(ledger) -> list[DeclaredCheck]` and `lines(ledger) -> list[str]`.
- Consumes configured `DECLARED_KINDS`, exact `Evidence` records, and their freshness.

- [ ] Write failing tests for current pass, current failure, stale pass, absent declaration, incomplete latest attempt, and configuration mismatch.
- [ ] Run `python -m pytest tests/test_declared_completion.py -q --basetemp .pytest_cache/declared-completion-red` and observe the missing-module failure.
- [ ] Implement the minimal pure read model; do not import hooks, execute commands, or mutate the ledger.
- [ ] Repeat the focused test with a repository-local base temp and confirm it passes.
- [ ] Commit and push the shared completion-model foundation.

### Task 2: Completion annex and feedback delivery observation

**Files:**
- Create: `core/feedback_delivery.py`
- Modify: `core/check_feedback.py`, `core/hook.py`, `core/hosts/transport.py`, `core/report.py`
- Create: `tests/test_feedback_delivery.py`
- Modify: `tests/test_declared_completion.py`

**Interfaces:**
- `prepare(root, task, properties, text)` retains one in-flight hash-bound candidate only under a host callback.
- `emitted(response)` records a bounded durable emission only after stdout flush; `inspect(ledger)` returns intent/emission/subsequent-receipt observations.
- `end_report(ledger)` appends declared rows and optional delivery observation without changing `ledger.status()`.

- [ ] Write failing native-shaped controls for intent-only, supported emitted context, unsupported/replay/partial context, changed activation, and later current/failed/incomplete exact receipts.
- [ ] Run the controls and watch each fail because the observer/annex is absent.
- [ ] Implement the minimum shared observer and report integration; preserve existing milestone-advice observation behavior.
- [ ] Run affected hook, host, advice, and declared-completion tests with a repository-local base temp.
- [ ] Commit and push the integrated completion/delivery slice.

### Task 3: Generalized no-model qualification and delivery

**Files:**
- Modify: `eval/check_adoption.py` or a focused existing no-model evaluator only if it can retain the new stages without historical reinterpretation
- Modify: `README.md`, `PLAN.md`, `docs/status.md`, `the-guide/declared-checks.md`, `the-guide/platforms.md`, `the-guide/troubleshooting.md`
- Create: `docs/design/declared-check-closure.md`, `docs/research/declared-check-closure.md`, `docs/validation/2026-10-18-declared-check-closure.md`, `journey/86-a-gap-is-visible-at-done.md`, `results/declared-check-closure/README.md`
- Modify: `architecture/index.html`

- [ ] Add actual disposable Python and Node controls for pass/fail/stale/absent/incomplete declaration states and safe host-shaped emission observations.
- [ ] Run no-model qualification, affected regression groups, source/architecture checks, and the appropriate broader suite; retain environment/setup limitations separately.
- [ ] Update public status and roadmap from “planned” to the exact qualified state, including any remaining installed gap.
- [ ] Render all architecture tabs, review the final diff against the spec, commit and push documentation/qualification/delivery work to `main`.
