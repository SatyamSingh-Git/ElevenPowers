# Behavior Preservation Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline, with one
> fresh whole-branch review after implementation. Keep progress in this plan's
> ignored workspace and push independently verified changes as they finish.

**Goal:** measure installed advice and behavior preservation across two sequential
feature requests from identical ordinary/assisted starting inputs.

**Architecture:** compose existing subscription execution, Claude project hooks,
milestone reports and contained processes. Keep authored cases and independent
grader outside runtime and candidate trees. Record every stage before launching it.

**Tech stack:** Python 3.11+, standard library, existing pytest development tools,
installed Claude subscription CLI.

**Spec:** [behavior preservation](../../design/behavior-preservation.md).

## Global constraints

- Generalized controller; fixture-specific behavior never enters core.
- Four approved sessions; Sonnet 5, medium, 480 seconds total per two-stage session.
- No API fallback, favorable retries, injected hidden feedback or default activation.
- Missing callbacks, changed configuration and incomplete execution remain explicit.
- Configuration and existing tests are immutable; new tests are allowed.

## Review focus

- Grader crashes/timeouts are incomplete, never successful regression detection.
- Candidate edits cannot silently change declarations or grading inputs.
- Session resumption uses one UUID and a shared time allowance.
- Native acceptance requires runtime-bound phases and captured receipt links.
- An observed correctness advantage must not be advertised as causal repair.

### Task 1: Freeze and qualify independent staged cases

Files: `eval/preservation_cases.py`, `eval/preservation_oracles.py`,
`tests/test_preservation_cases.py`.

Interface: `case(name) -> dict` contains files, two stage requests, gold stages
and faulty controls. `grade(name, stage, candidate) -> dict` returns bounded
per-check pass/fail/error outcomes from an isolated private copy.

- [x] Write tests asserting gold passes each stage, base fails new requirements,
  reverting faults fail earlier behavior and equivalent changes remain accepted.
- [x] Witness missing implementation, implement cases/grading and rerun controls.
- [x] Retain source and oracle hashes; push qualified cases and protocol.

### Task 2: Generalized staged controller and immutable preparation

Files: `eval/preservation.py`, `tests/test_preservation.py`.

Interface: `prepare(destination, cases, seconds=480) -> protocol`; stages use
exact frozen public commands and immutable input/config manifests.

- [x] Test equal public inputs, explicit assisted wiring, existing destination
  refusal, unsafe paths and source/config mutation detection before launch.
- [x] Implement preparation, private stage grading and resumable native command
  construction. Test removed no-session-persistence, session UUID/resume and caps.
- [x] Push preparation and controller controls.

### Task 3: Native stage collection and conservative comparison

Files: `eval/preservation.py`, `tests/test_preservation.py`.

Interface: `execute(batch, slot, executable) -> record`; `summarize(batch) -> dict`.

- [x] Test journal-before-launch, interruption retention, scope failures, no
  retry, incomplete grader separation and incomplete-pair aggregation.
- [x] Implement bounded requests, native response archives, report/diagnostic
  capture, independent source snapshots and conservative summary.
- [x] Run free full rehearsal and auth/version/help preflight; push before calls.

### Task 4: Approved installed comparison and evidence publication

Files: `results/behavior-preservation/`, dated validation and journey.

- [x] Freeze source/case/oracle identities and all four slots before calls.
- [x] Run each session once within approved allowance; inspect all outcomes.
- [x] Publish bounded raw captures and explicit native/correctness/cost findings.
  Preserve private full outputs without publishing prompts/transcript secrets.
- [x] Push observations without expanding approval or making unsupported claims.

### Task 5: Review, documentation and integration

Files: plan, status, master plan, guides, architecture and CI import coverage.

- [x] Perform one fresh whole-branch review, repair important findings with
  witnessed failing/passing controls and retain unresolved limits.
- [x] Run affected regression tests, doctor/grader checks and architecture render.
- [x] Update all affected delivery records and Planned card.
- Final integration gate: push the final revision, qualify hosted CI for that
  exact revision and fast-forward main under standing authorization. Integration
  status is verified from Git refs and the linked Actions run at delivery.

## Execution record

Four approved sessions completed without retries; producer revisions and unused
prepared slots are preserved explicitly in the published record. One fresh code
review plus one focused append for the subsequently added archive produced
witnessed repairs. The corrected oracle gives two correctness ties. Native
command-capture acceptance, advice consumption and coding benefit remain open;
the plan's delivery does not close those product exits. See
[observations](../../../results/behavior-preservation/README.md) and
[validation](../../validation/2026-10-08-behavior-preservation.md).
