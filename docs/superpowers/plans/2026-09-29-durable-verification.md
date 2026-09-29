# Durable verification runner implementation plan

> Use the executing-plans workflow for integration and a narrowly scoped parallel worker for process containment. User approved the runner design and requested six pushes, documentation last.

**Goal:** Preserve every completed verification result, bound completion work, expose progress, clean subprocess trees and reject evidence collected across source changes.

**Architecture:** Keep the synchronous host flow. A project-local run journal and OS-backed lock track queued/running/completed/deferred checks. A shared monotonic deadline spans verification, baseline checks and confirmation. A contained subprocess primitive enforces per-command timeouts. Receipts are persisted after each command and bound to complete snapshots before and after execution.

**Constraints:** Python 3.11+ standard library runtime; Windows and POSIX; passive mode remains passive; no background daemon; preserve existing ledger format and declaration semantics. Do not install or modify Snag without the required filesystem authorization. No paid experiments.

## Six delivery parts

- [x] 1. Durable run journal, atomic writes, project lock, recovery, deadline and unit tests (`core/jobs.py`, `tests/test_jobs.py`).
- [x] 2. Contained process execution and real process-tree tests (`core/process.py`, `tests/test_process.py`).
- [x] 3. Persist receipts per check, state-change detection and fresh-result reuse (`core/verify.py`, `core/parsers.py`, `core/evidence.py`, verification tests).
- [x] 4. Share the completion budget with baseline and confirmation, preserve partial results, guard concurrent completion (`core/hook.py`, `core/stress.py`, integration tests).
- [x] 5. Visible progress/recovery reporting and end-to-end validation (`core/status.py`, `core/report.py`, launcher tests); address independent review findings.
- [x] 6. Update architecture source/mirror, guide, status, validation and journey; render all views and publish final documentation.

## Review focus

- A hook dies after the first check: its completed evidence must remain usable and the unfinished attempt must be visible.
- A second hook arrives concurrently: no duplicate verification and no false verified response.
- A source file changes during a successful command, including same-length edits: no fresh receipt for the changed tree.
- Budget exhausted before or during a command: clear deferred/incomplete status, no unrelated extra processes.
- Timeout, parent exit and interruption: clean ordinary descendant processes; report platform containment limits honestly.
- Output exceeds the capture budget or contains credentials: explicit incomplete outcome and scrubbed persisted state.

## Validation

Observe regression failures before implementation. Run focused tests per part; one complete regression run at the integration boundary, followed only by checks justified by changes or failures. Exercise the real launcher and real child/grandchild cleanup. Verify a read-only Snag plan first; full Snag CI/installed-session claims require actual execution and host evidence.

## Delivery outcome

Parts 1–5 published as `ff54475`, `bca5d80`, `38ae90c`, `806c0b0`, and `37acdc0`. Part 6 is the documentation commit containing this record. See [the dated validation](../../validation/2026-09-29-durable-runner.md) for regression counts, review corrections and CI evidence. The six-part scope expanded only to fix compatibility and reproducibility failures actually exposed by the integration checks. Full Snag CI and a live installed host session remain outside the evidence collected here.
