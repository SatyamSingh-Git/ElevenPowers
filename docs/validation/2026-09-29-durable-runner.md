# Durable verification runner — 2026-09-29

Implementation delivery for the approved generalized runner, from `8547795`. The user requested six distinct pushes and documentation last. The runtime remains Python 3.11+ standard library code.

## Publication parts

| Part | Commit | Content |
|---|---|---|
| 1 | `ff54475` | Durable journal, project OS lock, recovery and shared budget |
| 2 | `bca5d80` | Contained processes, descendant cleanup and bounded output |
| 3 | `38ae90c` | Immediate receipts, before/after input binding and successful-result reuse |
| 4 | `806c0b0` | Shared Stop/baseline/confirmation deadline, task generation protection, durable confirmation and review corrections |
| 5 | `37acdc0` | Progress reporting, real launcher recovery, legacy receipt compatibility and clean-checkout CI fixes |
| 6 | This documentation commit | Guide, status, validation, journey, plan and rendered architecture |

## Checks actually executed

- Journal/ownership: 7 tests, including actual owner process death and recovery.
- Process runner: 13 tests on Windows; real child/grandchild cleanup after normal exit and timeout, KeyboardInterrupt, SIGTERM unwinding, launch failure, output overflow and failed Job assignment.
- Part 3 focused verification/discovery/scanning/journal checks: 88 passed.
- Shared-budget integration/audit checks: 135 passed, including 21 new shared-budget cases.
- Full local integration suite: **914 passed, 26 skipped, 1 failed in 298.29 seconds**. The failure was `test_a_targeted_reproduction_carries_no_caveat`: selecting only latest receipts initially applied suite counters to a historical named-test receipt. The correction preserves named-test compatibility and rejects superseded successes. Final focused runner/stress/progress/launcher checks: **69 passed in 40.04 seconds**. This is not a claim of a repeated clean full local run.
- Real shipped launcher: first check persisted, owner killed during second check, next Stop reused first and completed second. The concurrent-read Windows atomic-replacement race was observed failing before the bounded retry fix.
- `python -m eval.validate`: all four grader states correct.
- `python plugin/bin/ep_doctor.py --host`: all 11 local seam checks passed. This drives the launcher with payloads; it is not a live installed Claude Code session.
- `python architecture/check.py --render`: 75 nodes, 163 edges, seven planes; **all four tabs draw**. The restricted browser launch initially returned EPERM; the installed browser render passed with the required execution permission.
- Final progress rendering: **5 passed**. Saved-analysis and cleanup compatibility checks: **16 passed**; both raw/curated B8 stdout comparisons were identical (1,165 characters each).
- The final code-head [CI matrix](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/36523624912) passed on Ubuntu and Windows with Python 3.11 and 3.13: 916 passed / 31 skipped on each Ubuntu job and 919 passed / 28 skipped on each Windows job. Separate audit checks passed 102 / 2 skipped on Ubuntu and 104 on Windows.

## Clean-checkout corrections

Earlier delivery-part CI logs reproduced missing B8 run records on both platforms and a Python 3.11-incompatible `rmtree` helper. The local working tree contained ignored analysis runs, so copying the directory was not a clean-checkout test. The final code part adds minimal committed analysis inputs and exercises the fallback without ignored runs, alongside the compatible cleanup callback. These fix existing reproducibility gaps exposed while checking the runner; they do not rerun or revise the underlying paid experiments.

## Snag check

Read-only `source_snapshot(Path('E:/snag'), fresh=True)` covered **4,418 selected files / 81,841,401 bytes**, no coverage issues, fingerprint `61ecd7c9ecd7898c`, **55.66 seconds**. Effective commands were `npm run ci`, `npm run typecheck`, `npm run build`, and `npm run lint`. Snag was not edited, configured or installed into. This full content fingerprint is a different operation from the earlier 1.11-second selection measurement.

## Limits

The 480-second work deadline is shared; commands are capped at 300 seconds. A consistently longer command cannot finish through this automatic path. Filesystem operations, final reporting and bounded cleanup mean this is not a hard real-time wall-clock guarantee. Work resumes only on the next normal completion attempt, with fresh successes reused; there is no daemon. The progress journal is not evidence.

Windows Jobs contain ordinary descendants; POSIX process groups can be escaped deliberately and cannot clean up after an abrupt host SIGKILL. The 8 MiB output threshold is polled, so disk spools can temporarily exceed it. None of this is a security sandbox.

Full Snag CI and a live installed-plugin session remain unverified. No paid agent experiments were launched. Improved patch outcomes remain unproven.
