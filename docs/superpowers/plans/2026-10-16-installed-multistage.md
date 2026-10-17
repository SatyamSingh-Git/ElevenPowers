# Installed Multi-Stage Verification v1 Implementation Plan

Current follow-on: later shared guidance/batch qualification cleared both
controlled installed trials. The separately authorized
[fresh matched comparison](../../../results/matched-workflow/README.md) now
completes all four conversations and reproduces sixteen snapshots, retaining
two correctness ties, higher assisted time and mixed native adoption. The
[current execution checklist](2026-10-17-matched-workflow-comparison.md) supersedes
the earlier blocked status and per-trial permission proposal below; original
contracts, oracles and negative attempts remain unchanged.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Qualify installed declared-check adoption, then measure cross-task behavior preservation with a frozen ordinary-versus-assisted comparison.

**Architecture:** Extend the existing installed scope pilot and preservation controller. Reuse the shipping runner, native event records, independent oracle/archival helpers and evidence exports. Deterministic controls, installed acceptance and outcome comparison remain separate gates.

**Tech Stack:** Python 3.11+ standard-library harness, Node.js built-in test runner, existing pytest/CI and subscription Claude CLI.

**Spec:** `docs/superpowers/specs/2026-10-16-installed-multistage-design.md`

**Status:** Shared repairs remain source-qualified with 70 affected controls, 2,519 local passes/3 skips and all four hosted cells. Both original native trials and both separately approved requalification conversations completed but failed acceptance. Distinct task identities are now present in both fresh trials; owned-runner adoption remains incomplete. Both two-conversation allowances are consumed. The larger comparison is blocked, unapproved and unrun.

## Global Constraints

- Runtime behavior generalized for any project; authored cases/faults only in eval/tests/results.
- Reuse existing controllers; no third-party runtime dependency or new workflow engine.
- Gate 0 inspects actual final-main CI; known failing release blocks model runs, not free preparation.
- Gate 1: proposed two Sonnet 5.5 medium subscription conversations, 240 seconds each across three turns; no API fallback/retry.
- Gate 2: proposed four Sonnet 5.5 medium subscription conversations, 720 seconds each across four turns, only after installed acceptance.
- Both live gates require fresh specific approval; this document authorizes zero model sessions.
- Same public inputs, requirements, model, effort, customization policy and time per matched arm; optional strength disabled.
- New protocols allocate each turn the remaining model-process allowance divided by remaining turns, carry unused time forward, exclude controller/grading time and conservatively deduct observed call wall time. Stop after a timeout; keep legacy exact-command deadline behavior.
- Grade cumulative 4/6/8/10 groups; retain incomplete/scope/setup/timeout states and all scheduled attempts.
- Preserve existing archived two-stage protocols/reproduction and their 480-second default; new suite opts into schema 2 and 720-second cap.
- No new completion gate/default activation; no population, complete-environment or OS-isolation claim.
- Frequent descriptive pushes during approved implementation; qualify then integrate main and refresh docs/journey/all five maps.

## Review Focus

- Echo trailers or successful outer wrappers must not erase owned failure; test Gate 1 at receipt and obligation level (Task 1).
- Adoption must originate in native agent events, not a controller-run CLI or an explicit runner hint in prompts (Task 1).
- Runtime/configuration/oracle drift or cross-arm differences must invalidate qualification without deleting attempts (Task 3).
- A later timeout/missing/setup stage cannot hide earlier regressions; failed delivery cannot selectively remove an outcome-comparable pair (Task 4).
- Existing two-stage archives and correct forward controls must still reproduce after generalizing stage/language dispatch (Tasks 2–4).

### Task 1: Qualify installed runner adoption without literal command coaching

**Files:** Modify `eval/input_scope_pilot.py`; create `tests/test_declared_workflow_pilot.py`; reuse `tests/test_declared_check_protocol.py`, `core/checks.py`, `eval/subscription.py`.

**Interfaces:** Preserve `pilot(destination, language, source, *, seconds=180, rehearse=False)` behavior. Add keyword `protocol='exact-command'`; `declared-runner` permits at most 240 seconds and emits schema-2 result with `qualified`, `native_runner_adoption`, `task_boundaries`, three `turns`, milestone transitions, seals and qualification predicates. Add CLI `--protocol exact-command|declared-runner` and `--seconds` (default 180); default protocol remains existing behavior. Live acceptance selects 240 explicitly.

- [x] Inspect final-main CI and retained logs; record real failures/open incident. Repair only demonstrated runtime defects with witnessed RED/GREEN controls before live runs.
- [x] Write RED controls for three-turn rehearsal, unchanged legacy behavior, zero model calls in rehearsal, absent native runner usage, outer-success failure preservation, missing seals, shared allowance exhaustion and incomplete receipt retention.
- [x] Pin `test_receipts_without_native_runner_usage_do_not_qualify` (`result['qualified'] is False`) and `test_rehearsal_never_launches_models` (`result['model_calls'] == 0`); verify failure before implementation.
- [x] Extend the pilot using shipping guidance and native event/ledger inspection. Persist an attempt before every model launch; refuse unapproved execution via the implementation's explicit live-run handoff, not automatic installation or CI.
- [x] Run `python -m pytest tests/test_declared_workflow_pilot.py tests/test_declared_check_protocol.py -q`; require forward/adversarial controls green. Rehearse both languages without model calls and retain exact producer identity.
- [x] Commit/push the inspected acceptance protocol. Request the separate two-conversation/eight-minute allowance only when it is executable and reviewable; do not launch in this task without it.

### Task 2: Freeze two cross-language four-stage cases and independent oracles

**Files:** Create `eval/workflow_cases.py`, `eval/workflow_oracles.py`, `tests/test_workflow_cases.py`; modify registry/dispatch in `eval/preservation_cases.py`, `eval/preservation_oracles.py`.

**Interfaces:** `workflow_cases.case(name: str) -> dict` resolves only `workflow-queue-py` / `workflow-orders-js`, returning `id`, `language`, `files`, `public_command`, `production`, `new_test_paths`, `milestones` and four `requests`. `workflow_oracles.grade(value: dict, stage: int, candidate: Path, *, seconds: float=15) -> dict` accepts stages 0..4 and returns existing graded/setup/incomplete state plus `groups` rows (`id`, `introduced_stage`, `state` passed/failed), passed/failed counts and input identity. Stages have 2/4/6/8/10 cumulative groups. Existing case names/oracles remain unchanged.

- [x] Write RED reference/fault controls: valid behavior accepted, stale lease/replay/expiry/accounting/restart/atomicity breaks rejected at the intended group, unchanged utility accepted, deterministic clocks, malformed saved state explicit, both runtimes available/absent handled.
- [x] Pin `test_four_stage_group_counts_are_cumulative` (`[len(grade(value,s,reference)['groups']) for s in range(5)] == [2,4,6,8,10]`) and require each named fault to fail its intended group without counting a setup error as detection.
- [x] Implement public contracts, reference solutions and independently calculated observable oracles. Reference implementations, faults and grading files live outside model project trees. Public documents fully define promised semantics before case freezing.
- [x] Run `python -m pytest tests/test_workflow_cases.py tests/test_preservation_cases.py -q`; require all gold/fault directions and legacy controls green. Record no-model case rehearsal and freeze the suite before any live comparison.
- [x] Commit/push the cases with limitations that they are authored systems, not independently sampled upstream repositories.

### Task 3: Extend the existing staged controller without breaking archived protocols

**Files:** Modify `eval/preservation.py`, `eval/preservation_archive.py`; create `tests/test_workflow_controller.py`; reuse `tests/test_preservation.py`, `tests/test_preservation_archive.py`, `tests/test_subscription.py`.

**Interfaces:** Preserve `prepare(destination, *, names=('queue','inventory'), seconds=480)` defaults and schema-1 behavior. Add `model=None`, choosing legacy model for schema 1 and `claude-sonnet-5-5` for schema 2; only supported subscription models allowed. New case selection produces schema 2 with four immutable requests, language-specific public commands, per-stage oracle hashes and allowance cap 720. Existing `verify(batch, slot, *, initial=False)`, `execute(batch, slot, executable)` and `summarize(batch)` consume both schemas explicitly; neither infers stages from a result count.

- [x] Write RED controls for identical matched source/contracts, alternating arm order, four resumed turns under one allocated model allowance, changed runtime/grader/configuration rejection, protected-public-test tampering, allowed new tests, missing native transitions lowering delivery verification, and partial journal preservation after interruption.
- [x] Pin `test_comparison_reserves_later_turn_allowances`: with a 720-second cap and simulated calls taking 90 seconds, expected caps are `[180,210,270,450]`; no model call occurs in this control. Controller/grading delays must not reduce these caps.
- [x] Replace hardcoded Python/two-stage assumptions with frozen case metadata and schema-aware dispatch. Preserve the existing schema-1 constants and artifacts; seals include stage count, model, order, commands, case/oracle/runtime bytes and allowed path rules. Do not expose independent grades as feedback between stages.
- [x] Run `python -m pytest tests/test_workflow_controller.py tests/test_preservation.py tests/test_preservation_archive.py tests/test_subscription.py -q`; require four-stage forward/adversarial controls and all legacy behavior green.
- [x] Commit/push the controller and documented explicit preparation/run procedure; no model launch required for this deliverable.

### Task 4: Retain independent results and separate readiness from benefit

**Files:** Modify `eval/preservation.py`, `eval/preservation_archive.py`; create `tests/test_workflow_results.py`; later retain `results/installed-multistage/` metadata, frozen manifests and reproducible grade entry point.

**Interfaces:** Schema-2 summary contains `scheduled`, `attempted`, `outcome_comparable`, `delivery_verified`, `readiness`, per-case/per-stage `regressed`, `earlier_failed`, `new_failed`, cumulative grades, paired differences, observed command/feedback delivery and separate model/analysis time. `regressed` names earlier groups that passed at the preceding graded stage and fail now; missing prior grade is null. Outcome comparison requires both paired arms host-completed, graded, identity-valid and scope-valid for all four stages; unqualified attempts remain rows. Missing assisted adoption/native delivery alone sets `delivery_verified=False`, without excluding otherwise comparable outcomes. Reproducer accepts exported source snapshots and verifies the frozen case/grader identities without a model call.

- [x] Write RED outcome controls for assisted advantage, tie, worse result, missing/timeout/setup stage, scope violation, early regression followed by repair, missing receipt, fabricated adoption and post-run fingerprint drift.
- [x] Pin `test_failed_delivery_does_not_drop_a_graded_pair` (`outcome_comparable is True`, `delivery_verified is False`) and `test_previously_failing_feature_is_not_a_new_regression`: an unchanged earlier failing group remains in `earlier_failed` but is absent from `regressed`.
- [x] Implement summaries/reproduction/public export with explicit scheduled denominators and grade provenance. Distinguish observed receipts, contract correctness, installed readiness and causal interpretation. Use existing redacted evidence exports; no raw prompt/transcript/machine paths in public artifacts.
- [x] Run `python -m pytest tests/test_workflow_results.py tests/test_preservation_archive.py -q` and a full no-model four-stage rehearsal; require exact source grades reproduce and all attempt records survive.
- [x] Commit/push the report path and frozen protocol before asking for the separate four-conversation/48-minute comparison allowance.

### Task 5: Installed acceptance, bounded comparison and delivery

**Files:** Relevant guides, `PLAN.md`, `docs/status.md`, `whats-offered/roadmap.md`, dated validation/research, next unused journey, `architecture/index.html` and generated `architecture/graph-data.js`, retained results.

**Interfaces:** Task 1 readiness gates Tasks 3–4 live comparison; all independent controls are runnable without a model. Public status distinguishes designed, rehearsed, installed-qualified and compared.

- [x] Complete one fresh whole-branch review and witness/fix Important findings; inspect current CI and free rehearsal before requesting approved live runs.
- [x] After fresh allowance, run exactly the two installed sessions. If adoption fails, publish the defect/limit and stop live comparison pending repair/requalification; do not spend the larger allowance automatically.
- [ ] After readiness and separate allowance, run the four predeclared comparison conversations. Freeze each source stage before independently grading it; keep all incomplete and negative outcomes. Do not change cases/oracles based on results.
- [ ] Reproduce grades without models; inspect evidence/export privacy. Report selected-sample advantage, tie or worse outcome with exact limits; do not require a favorable result to count as completed measurement.
- [x] Run affected/full regression gates and all five rendered maps; update guides, plan, status, research, results and journey. Push descriptive parts, integrate verified inputs onto main, and verify remote/published identity without describing pending repeats as passed.

## Self-review

Scope matches the spec's release health, installed adoption, four-stage cases,
matched controller, independent measurement, approval and publication gates.
All five review-focus failures have explicit test ownership. Shared signatures,
schema values, stage counts and budgets agree across tasks. Legacy source grades
are regression inputs, never replaced by the new suite. No model run is needed
to implement and rehearse Tasks 1–4; live spending remains separately approved.

## Installed trial repair and requalification

The initial source candidate passed 2,507 local tests and all four hosted cells.
Both native conversations completed within allowance but failed Gate 1. Retain
the original observations and their producer; never relabel them after repair.

- [x] Publish both original attempts, including missing build evidence and recovery task reuse.
- [x] Reproduce missing native task metadata using actual callback ingress rather than fabricated diagnostic fields.
- [x] Repair explicit task declarations, native prompt/tool correlation and independent declared-property guidance for every project/host; 70 affected controls pass.
- [x] Qualify repaired source `8d26185` with full local suite, four hosted cells, standard-library imports, audits, grader/source reproduction, doctor and updated rendered maps.
- [x] After a new specific allowance, run two fresh Sonnet 5.5 medium conversations, 240 seconds each across three turns, no API fallback or retry; keep every result. Both completed but failed acceptance; 94.763s Python and 47.005s JavaScript model-process time.
- [ ] Only if both qualify, freeze a new comparison batch at that producer and request the separate four-conversation allowance. Existing authored contracts/oracles remain unchanged.

The repair changes no completion gate or automatic model activation. Guidance
remains bounded and reports omitted command instructions explicitly. Earlier
CI incident causes remain open; green source qualification does not explain them.

## Qualified source delivery

First main fast-forward `366048d` contains all task work. Remote main and the
feature branch matched with zero feature commits absent. Pages run 38972715986
succeeded; independent HTTPS reads matched committed architecture HTML/data
bytes. The documentation closure preserves qualified source and rendered-map
bytes. Subsequent requalification completed but remained unqualified, with
both original and fresh attempts retained. The larger comparison is still blocked
and unapproved; source delivery does not complete the measurement gate or claim benefit.

## Next acceptance repair after requalification

Both approved requalification conversations completed all three turns. Task
identity is distinct in both; Python records qualified owned calls on first
and recovery turns. Both drift turns use compound ordinary commands with
trailing output. Python stays STALE and JavaScript retains ABSENT evidence.
No new model run is authorized by this plan extension.

Actual native startup/resume inspection already confirms that both encoded
tests/build instructions were emitted in all six turns. Preserve that forward
observation: investigate readable property guidance, prompt/completion context
and subsequent adoption without assuming startup instructions were absent.
Emission alone does not establish model consumption or the cause of non-adoption.

- [ ] Reproduce the real ordinary compound-command and no-edit prompt/Stop
  boundaries without a model; retain command, emitted guidance, child outcome,
  actual native callback shape and owned receipt facts as separate authorities.
- [ ] Determine why shipped runner guidance is not reliably delivered/adopted
  across those turns. Improve bounded project-aware instructions through the
  existing shared path; preserve continuations, unrelated current evidence,
  passive/off behavior and explicit project configuration.
- [ ] Keep arbitrary shell trailers/output as non-owned observations. Do not
  infer per-child exit codes, fabricate receipts or weaken qualification to
  satisfy a fixture. Add real producer forward/adversarial controls for the
  demonstrated boundary before a justified runtime change.
- [ ] Qualify any changed source, update fingerprints and report limits before
  requesting another specific installed allowance. Do not change frozen cases,
  prompts or independent oracles in response to failed outcomes.
- [ ] Run the larger comparison only after installed acceptance and a separate
  specific allowance. Retain all failed/incomplete attempts.
