# External Input Witnesses v2 Implementation Plan

> For agentic workers: use superpowers:executing-plans inline, witnessed RED→GREEN and one fresh whole-branch review. The user requested build and main delivery.

**Goal:** Make selected approved external inputs qualify ordinary receipts and cross-task behavior evidence.

**Architecture:** Shared optional receipt metadata and fresh inspection; bounded
native attempt pairing; existing owned execution and history/report consumers.

**Tech Stack:** Python stdlib, existing parsers/locks/host adapters, actual Python
and Node checks. No runtime dependency, model or installer.

**Spec:** `docs/design/external-input-sessions.md`

## Global constraints

- Generic project/host core; no named-project policy or new paid/installed runs.
- Preserve v1 approval and aggregate budgets; ten cooperative seconds per native observation.
- Private attempt schema 2: 1 MiB, 128 pending, 256 consumed details, one-hour expiry and 256 KiB monotone seen-ID memory. Collisions conservatively remain incomplete.
- No missing-ID or command-text-only pairing; preserve unavailable provenance.
- Preserve source facts, required commands, fallback verification, profile and cleanup limits.
- Reports run no checks/installers/models and share bounded fresh reads.
- Old Evidence serialization remains unchanged when metadata is absent.

## Review focus

1. Missing/reused IDs, concurrent pre/post and task/session changes cannot pair another attempt.
2. Declaration/root/runtime or source changes during collection cannot leave current qualification.
3. Unfinished attempts, replay and bounded-state eviction cannot resurrect older passing evidence.
4. Legacy/malformed history and post-only capture cannot invent external execution provenance.
5. Repeated receipt inspection must not multiply byte/time budgets or leak private roots/contents.

### Task 1: Reproduce the ordinary-session and cross-task gap

Files: `tests/test_input_sessions_gap.py`; design and this plan.
Consumes real commands and existing hook/ledger/milestone/report APIs.

- [x] Seed unrelated Python/JavaScript dependency checks and project-owned milestones; capture actual native events and results.
- [x] Independently mutate dependencies with source/HEAD unchanged, observe failing checks and current-report gap RED.
- [x] Keep unmodified and read-only positive controls; preserve incorrect fixture attempts separately; push the concrete gap/spec.

### Task 2: Shared receipt metadata and freshness

Files: `core/inputs/receipts.py`, `core/evidence.py`, `core/ledger.py`,
`core/milestones/history.py`, `tests/test_input_receipts.py`.
Produces `metadata(before,after,attempt,issues=()) -> dict`,
`inspect(record,root,current=None) -> dict`, `attach(records,before,after,attempt,issues=())`.

- [x] Watch RED for legacy/no-policy compatibility, configured missing history, bound/drift/incomplete/malformed metadata and unchanged source facts.
- [x] Implement strict bounded metadata and optional Evidence field with stable absent serialization.
- [x] Share fresh captures in freshness views, guard final moving inputs, qualify verdicts and retain metadata in milestone history.
- [x] Run whole task's controls GREEN, note rulings, commit and push.

### Task 3: Native attempt observations

Files: `core/inputs/native.py`, `core/hook.py`, native adapters only where existing
fields need preserving; `tests/test_input_native.py`.
Produces `before(payload,root)` and `after(payload,root,records,terminal=True)`;
safe bounded private pending/consumed state; no inferred IDs.

- [x] Watch RED for actual before/after, post-only, duplicate/replay, overlap, task/session/raw-command/cwd mismatch, interruption, expiry and private-state boundaries.
- [x] Add provisional records and bounded identified pre snapshots; consume terminal post atomically after collection, preserving original outcomes.
- [x] Route ordinary hook records through the shared qualifier; preserve missing IDs and unsupported host callbacks as gaps.
- [x] Run five adapter controls and actual commands GREEN; commit/push parts.

### Task 4: Owned verification and reuse

Files: `core/verify.py`, `core/stress.py`, `core/patchproof/execution.py`, related
tests and actual exercise producers. Uses the Task 2 metadata contract.

- [x] Watch actual RED for unchanged reuse, dependency drift, missing-input launch refusal, during-command changes and confirmation/cache qualification.
- [x] Observe inputs around existing owned commands; persist incomplete first and retain source/parser/profile/cleanup behavior.
- [x] Bind targeted confirmations and baseline cache identities; enrich explicit PatchProof records from existing witnesses.
- [x] Update actual controller-run fixtures to attach observed metadata; never upgrade manually saved history from current reads.
- [x] Run affected controls GREEN; commit/push parts.

### Task 5: Consistent milestone and public views

Files: `core/export.py`, `core/milestones/report.py`, `core/report.py`,
`core/patchproof/report.py`, related advice/GitHub tests and guides.

- [x] Watch RED for cross-task retention, separate source/current external qualification, absent/failed/stale/incomplete states and moving report inputs.
- [x] Expose bounded qualifications and coverage gaps; keep reports read-only and required checks in advice.
- [x] Make Task 1 drift controls GREEN while preserving old unconfigured states and signed/installed/coding-benefit limits; commit/push.

### Task 6: Actual end-to-end acceptance and delivery

Files: `eval/input_sessions.py`, tests, workflow, docs, journey 79 and architecture.

- [x] Run actual multi-task Python/Node controls with independent fault checks, all five synthetic host adapters, owned verification, counters and read costs.
- [x] Add the exercise and stdlib imports to four-cell hosted qualification; push.
- [x] One whole-branch reviewer; regrade and repair Important/Critical findings in one witnessed pass, retain other rulings/minors.
- [ ] Freeze code and run full suite, named audits, independent grader/source reproduction, doctor, stdlib, final hosted matrix, architecture render and added links.
- [ ] Update all affected docs, roadmap, journey/validation and five views; push descriptive parts.
- [ ] Fast-forward main normally, verify refs/raw bytes/published map, and archive only this owned private workspace.
