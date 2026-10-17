# Declared-check adoption and batches implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline; one fresh review of the whole change. Steps use checkboxes.

**Goal:** Repair observable adoption guidance gaps and add an owned batch entry point for all declared checks.

**Architecture:** Reuse core.checks execution qualification with core.jobs.Session; core.check_batch owns orchestration. Native hooks expose bounded project-aware instructions through existing transports.

**Tech Stack:** Python 3.11+ standard library, existing pytest, Node and subscription Claude.

**Spec:** docs/superpowers/specs/2026-10-17-declared-check-adoption-design.md

## Global constraints

- All runtime behavior generalized; no fixture/project paths or commands in runtime.
- Preserve existing selectors, owned qualification, strict attribution, off and continuation behavior.
- Guidance <=2,000 characters, named omissions; one batch owner and finite positive <=600s total deadline, default120.
- New batch schema2; existing per-property schema1; exits0/1/2/130; no captured output in metadata.
- Failure continues independent checks; unrun/incomplete remains explicit. No automatic batch execution in hooks.
- User standing approval covers needed Sonnet5.5medium subscription sessions; no repeated allowance questions, no API fallback/favorable retries.
- No-model checks before live use; current runtime identity, frozen prompts/oracles and every outcome retained.
- Frequent descriptive pushes; docs/journey/maps; all work on main. No coding-benefit or all-host installed claim from synthetic controls.

## Review focus

- Opaque/very long command paths: readable labels and bound/omissions remain true (Task1).
- No-edit/continuation/off native prompts: advice must neither invent claims nor execute commands (Task1).
- Independent failed/build checks: batch continues, source/input qualifiers remain per check (Task2).
- Task/config movement and competing owner between properties: refuse next execution, retain earlier results (Task2).
- Deadline/interruption: journal, provisional evidence and selected denominator stay explicit (Task2/3).

### Task1: Reproduce and repair guidance boundaries

**Files:** core/checks.py, core/hook.py, tests/test_check_adoption.py, tests/test_installed_workflow_boundaries.py.

**Interfaces:** guidance(root, commands=None, batch=False) stays bounded and executable. Existing dispatch(UserPromptSubmit,payload) emits advice for a distinct explicit verification task through normal host transport; no new claim or child process.

- [x] Write real-producer RED tests for visible property labels, new no-edit verification advice, duplicate/continuation/off refusals and unchanged independent receipts.
- [x] Run targeted tests; witness intended missing guidance/label failures.
- [x] Repair shared guidance and truthful startup wording using existing invocation quoting.
- [x] Run new/legacy guidance and hook controls; compare outputs and commit/push.

### Task2: Add owned declared-check batches

**Files:** core/checks.py, core/check_batch.py, plugin/bin/ep_check.py, tests/test_check_batch.py, tests/test_check_cli.py.

**Interfaces:** core.check_batch.execute(root, seconds=120) -> schema2 selected/results/state/issues/elapsed_seconds. Internal single-check implementation accepts the current Session; public execute remains schema1. CLI adds mutually-exclusive --all.

- [x] Write RED real-process tests: independent pass/failure, continued build, one owner/journal run, off/busy/invalid/empty refusal, task/config movement, deadline and interruption; CLI denominator/exit/privacy/legacy controls.
- [x] Run tests and witness absent batch behavior; implement minimal orchestration and shared single-check body.
- [x] Require exact per-property receipts and no outer wrapper inference. Use actual subprocesses for forward/adversarial controls; controlled clocks/launch boundaries only for races/deadline.
- [x] Run batch/single/CLI/declared workflow controls; commit/push.

### Task3: Integrate one-command guidance and portable acceptance

**Files:** core/checks.py, core/hook.py, eval/check_adoption.py, tests/test_check_adoption.py, .github/workflows/tests.yml.

**Interfaces:** batch=True advertises executable --all and declared list; command-filtered advice stays narrow. No-model exercise retains actual Python/Node transitions and typed model_calls=0 result; no installed claim.

- [x] Write RED for batch guidance and selected-property refusal to broaden, and exercise output if needed.
- [x] Prefer batch at startup and distinct no-edit verification prompts; expose each result independently to existing observers.
- [x] Execute unrelated project pass/fail/drift/recovery, owner/deadline/refusal controls and retain results; add stdlib/CI exercise/artifact coverage.
- [x] Commit/push; run one fresh whole-change review and one witnessed repair pass for actual findings.

### Task4: Qualify, observe installed adoption and deliver

**Files:** results/check-adoption/, docs/status.md, PLAN.md, README.md, guides, validation/research, journey83, architecture/.

- [ ] Run affected/full suite, named audits, grader/legacy source reproduction, doctor and imports; inspect four hosted cells for actual candidate.
- [ ] Under standing user approval run two fresh Sonnet5.5medium conversations,240s each/3turns,noAPI/no retries, only after healthy qualification. Retain every result and original failures.
- [ ] Update docs, journey and all five architecture views; render and validate links. Clearly distinguish implemented, source-qualified, native acceptance and coding benefit.
- [ ] Push semantic parts, integrate main and verify remote/publication identity. Preserve unfinished measurement state if installed acceptance still fails.

## Self-review

Qualification adjustment after the actual local full run: isolated milestone
children could not import user-site-only pytest from the global interpreter.
The existing pinned project virtual environment passes both exercise controls.
Preserve the original 1,474 passes/two skips/one setup failure and complete only
the unexecuted suffix in that environment, with an exact disjoint node-ID
denominator. Local coverage across environments is not a fresh single full-suite
pass. All four hosted cells must still pass complete coherent suites before live
use. This is an environment repair; shipping and evaluation source stay unchanged.
After those four complete hosted suites and independently checked artifacts,
the two live observations may run alongside the remaining local continuation.
The diagnosed exercise repair and 32 new runner controls must already pass in
the corrected environment. Final local coverage and documentation delivery
remain required; no pending or failed invocation becomes a pass by concurrency.

Task1 guidance remains compatible until Task2 supplies batch execution. Task3
consumes both after tested integration; filtered advice cannot broaden. Task2
single-body reuse avoids nested owners. All five review-focus classes have tests.
The user's latest standing model authorization overrides historical per-trial
permission wording; conservative explicit caps and no-model release gates remain.
