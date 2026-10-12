# PatchProof verification implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, with one fresh-context whole-branch review at the end.

**Goal:** Obtain and export qualified evidence for an exact patch with generalized,
explicit, bounded execution after investigating execution reliability.

**Architecture:** Reuse `core.process`, `core.jobs.Session`, configuration,
source snapshots, parsers and ledger. Add a planner, executor and saved-association
reader in `core/patchproof`, then compose them into the existing CLI and bundle.

**Tech Stack:** Python standard library, existing optional ImpactGraph adapters,
Git 2.45+, Windows Jobs/POSIX process groups, pytest and hosted matrix.

**Spec:** `docs/design/patchproof-verification.md`

## Global constraints

- All projects/hosts use the same policy; no project-specific paths or commands.
- Reports/plans/installations execute no checks; `--verify` is explicit.
- Defaults: total 120 seconds (0–600), command 30 seconds (>0–300), 64 declarations,
  existing combined output cap 8 MiB. Cleanup allowance is separate and visible.
- Off profile refuses execution. Required commands and fallbacks are never removed by impact advice.
- Receipts are local unsigned observations, not proof of safety or coding benefit.
- Persist incomplete before launch; fresh association before reuse. Unknown external/dependency freshness remains explicit.
- Push independently verified pieces frequently; final qualified code also on main.

## Review focus

1. Cancellation while a process tree is starting or cleaning up must not leak descendants.
2. Changed ignored configuration or selection policy must refuse launch/reuse.
3. A later failed/incomplete command must supersede an older passing receipt.
4. Moving patch refs or command-mutated source must leave associations unavailable.
5. Saved malformed/linked/oversized state must not execute commands or grant freshness.

### Task 1: Reliability investigation and established repairs

Files: `core/process.py`, `tests/test_process.py`, `tests/test_host_setup.py`,
new bounded `.github/workflows/execution-reliability.yml`, dated observations.

- [ ] Read retained CI failures and run actual local quoted launch/tree controls.
- [ ] Add PID/group/process-state diagnostics and repeat real controls in hosted Linux/Windows.
- [ ] For each established defect, add its failing control, observe RED, fix the cause, observe GREEN.
- [ ] Preserve unresolved incidents honestly; no timeout/assertion weakening.
- [ ] Commit/push qualified reliability work before executor implementation.

### Task 2: Read-only exact-patch verification planner

Create `core/patchproof/planning.py`, `tests/test_patchproof_planning.py`.
Consumes `report.build(root, base, head, timeout=..., impact=...)`; produces
`plan(root, base='HEAD~1', head='HEAD', seconds=120, command_seconds=30, impact=False)`.

- [ ] Add real project fixtures and failing assertions for all declared commands,
  absent/stale/incomplete/latest-failure, duplicate commands, unsupported properties.
- [ ] Run RED; implement bounded read-only plan identities/reasons and optional impact advice.
- [ ] Assert byte-for-byte unchanged project state and mandatory-check preservation.
- [ ] Run focused controls, commit/push.

### Task 3: Explicit durable execution and conservative reuse

Create `core/patchproof/execution.py`, `core/patchproof/execution_report.py`,
`tests/test_patchproof_execution.py`; compose saved associations in `report.py`.
Consumes planner and existing Session/parser/ledger; produces
`verify(root, base='HEAD~1', head='HEAD', seconds=120, command_seconds=30, impact=False)`.

- [ ] Actual Python/Node controls: passing/faulty commands, timeout, noisy output,
  source/config drift, passive profile, interrupted latest attempt and clean reuse.
- [ ] Observe RED; implement incomplete-before-launch, per-command shared deadline,
  before/after witnesses and bounded atomic state; record receipt keys.
- [ ] Fresh saved-association inspection rejects malformed/linked/oversized records.
- [ ] Require latest exact aggregate and unchanged producer/environment/inputs for reuse.
- [ ] Run focused controls; commit/push coherent increments.

### Task 4: CLI and independently checked end-to-end exercise

Modify `plugin/bin/ep_patchproof.py`; create `tests/test_patchproof_verification_cli.py`
and portable actual exercise observations.

- [ ] Run failing CLI controls for `--plan`/`--verify`, budgets, JSON/Markdown and exits.
- [ ] Add mutually exclusive flags; exits: 0 all required current, 1 completed failure,
  2 absent/unsupported/unqualified/incomplete; ordinary report gate unchanged.
- [ ] Exercise independent Python/JavaScript assertions and reuse without a model.
- [ ] Verify read-only default, captured-output exclusion, no hidden host execution; push.

### Task 5: Review, delivery qualification and contributor documentation

- [ ] One fresh-context branch review; repair Critical/Important once with RED→GREEN.
- [ ] Full suite, named audit probes, eval.validate, published source graders, doctor,
  standard-library imports and hosted matrix. Preserve every failing attempt/cause.
- [ ] Update README, PLAN/status, command/configuration/feature guides, contributor
  brief, journey/index, all architecture views/card/mirror and dated validation.
- [ ] Run `python architecture/check.py --render`, local links and published bytes.
- [ ] Push verified docs; fast-forward main without force, verify remote identity/CI.
