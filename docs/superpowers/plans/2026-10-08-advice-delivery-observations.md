# Advice delivery observations implementation plan

> For agentic workers: use superpowers:executing-plans inline, with one fresh
> whole-branch review after the implementation.

**Goal:** Distinguish generated advice, native context emission and subsequent
matching native checks without claiming comprehension or causal benefit.

**Architecture:** Extend the existing advice reservation state and launcher
transports. Read-only readiness joins bounded hashes with existing native links
and fresh portable evidence. Diagnostics remain separate from verification.

**Tech stack:** Python standard library, pytest, actual Python/Node commands.

**Spec:** [design](../../design/advice-delivery-observations.md).

## Global constraints

- Generalized behavior for every project and five hosts; no special repository.
- No model calls, dependencies, new default activation or completion blockers.
- Preserve legacy advice rows and earlier experimental archives.
- Advice state remains ignored, atomic and bounded to 64 KiB, 20 tasks and ten
  attempts per task; only hashes/counters/times/outcome metadata persist.
- Use default system test fixtures outside repository Git boundaries.
- Push meaningful verified increments; use standing main authorization after
  final compatibility qualification.

## Review focus

Response fields that mention advice but do not deliver context; failed flushes
and dropped adapter fields; replay/library/native distinctions; cross-task,
session, generation and runtime joins; older, controller-produced or stale
receipts and corrupted/moving diagnostic state.

### Task 1: Observable launcher emission

Files: `core/milestones/delivery.py`, advice worker/reservation modules,
`core/hosts/readiness.py`, transport and the two plugin launchers;
`tests/test_advice_emission.py`.

- [ ] Write failing controls using an opted disposable project. The real worker
  context alone must not count as emitted; full flushed native context must;
  replay, partial context, no session and failing stdout must not.
- [ ] Add `delivery.collect()` / `prepare(...)` / `emitted(response)` with
  launcher-local context. Worker recommendation hashes describe visible checks.
  Emission writes validate current attempt, scope and configuration generation.
- [ ] Verify all five launcher contracts, existing advice budgets and native
  diagnostics. Commit and push the emission increment.

### Task 2: Read-only follow-up view

Files: `core/milestones/delivery.py`, `core/health.py`;
`tests/test_advice_followup.py`.

- [ ] Observe missing readiness diagnostics before implementing
  `inspect(root, host, task, activation, receipts)`.
- [ ] Join current emitted recommendations to later native receipt keys and
  fresh outcomes. Witness rejection of old/controller receipts, wrong task or
  session, changed runtime/wiring, corruption, absent context and moving state.
- [ ] Add informational readiness JSON/text without changing required stages,
  gates or evidence. Run health compatibility checks, commit and push.

### Task 3: Repeatable acceptance and delivery

Files: disposable evaluation exercise, installed instructions, guides,
results/validation/journey, plan/status and architecture.

- [ ] Run model-free actual commands and all five replay transports in unrelated
  disposable projects. Preserve qualification and failure observations; never
  label these as installed model-session acceptance.
- [ ] Prepare an explicit optional installed exercise with supported wrappers,
  bounded advice and independently inspectable outputs. Make no model call
  without a specific new allowance.
- [ ] Fresh whole-branch review; repair Important findings with failing/passing
  controls. Refresh docs/map and render all five architecture views.
- [ ] Run appropriate final compatibility checks, push, qualify hosted CI,
  integrate verified main and check the published architecture.
