# Portable verification report — 2026-10-01

Scope: generalized local Markdown/versioned-JSON exports for any project and host.
Uses the ledger verdict engine; no project commands or model calls during export.
This delivery follows the ten onboarding pushes, rather than being one of them.

## Focused controls

Environment: Windows, Python 3.13.2, standard-library runtime, pinned development
pytest. The first attempt under the restricted account could not use a previous
user's pytest temporary/cache directories; it was an environment failure, not a
product result. The controls were rerun with authorized temporary-directory access.

The fresh review identified six issues. Added controls initially produced
**8 failures / 12 passes**: explicit timestamp-preserving freshness and budget,
Markdown interpretation, ambient journal writes for same/different projects,
receipt timestamps, missing caveats and repeated verdict/deadline handling.
Each was corrected. A subsequent nested snapshot control also failed before
the inner view was isolated. An outside-project explicit input is rejected.

Final focused report/scanner command:

```sh
python -m pytest tests/test_portable_report.py tests/test_repository_scan.py -q
```

Result: **36 passed in 10.58 seconds**. This covers 22 report controls and 14
repository-selection controls. Neither partial coverage nor absent task claims
can certify completed work. Output tests check atomic no-overwrite and forced
replacement. Known-token controls check omission/redaction of session material.

## Delivery-boundary verification

Full local suite, with the virtual environment first on PATH:
**1,084 passed / 28 skipped in 385.33 seconds**. This is the report delivery
suite, distinct from the onboarding delivery's 1,062 passes / 28 skips.
`architecture/check.py --render` passed with **86 nodes / 186 edges / 7 planes**;
all four views drew. The graph includes the report API/CLI and local artifact
data flow, while mutation findings remain in the planned lane.
`python -m eval.validate` returned **all 4 known-answer cases correct**.
The actual Snag JSON export succeeded; `--require-verified` returned **1** for
its UNVERIFIED state, as documented.

## Actual Snag export

Command: `ep_report.py --project E:/snag --output` a local ignored report file,
with `--force` for the reviewed replacement. No Snag project command ran.
The report records:

- Revision `1906da4576f29b02131ff50a29204529b8bcbb5e`.
- Complete selection: **4,417 files / 81,841,184 bytes**.
- The real relayed `npm run ci` receipt: **fail / complete / fresh**.
- Task state **UNVERIFIED**, with no active claim and an action to inspect CI.

That receipt refers to the actual external 14/15-check CI run in the
[onboarding record](2026-10-01-live-onboarding.md). It is not a native installed-host
command capture. Account-specific ignore policy can change selected inputs and
conservatively stale an existing receipt; the export above used the relay's account.

## Limits

The report is unsigned local observation. It does not authenticate the ledger,
prove absence of unrelated side effects, establish independent patch outcomes,
or implement PLAN §5.17's mutation findings. The deadline is cooperative rather
than filesystem preemption. Defaults are 120 seconds, 1,024 latest receipts and
the project's source file/byte budgets; omissions make coverage incomplete.
Known-pattern scrubbing does not classify every possible confidential value.
Live sessions on the four added hosts remain separate acceptance work.

## Fifteen publication parts

The user requested fifteen separate pushes for this new report work, following
the earlier ten onboarding pushes. Parts 1–14 advance `codex/portable-report`;
part 15 publishes that branch and main atomically. Each part has its own detailed
commit. The implementation was preserved in a local backup while splitting the
unpublished history; runtime and test contents match the broadly tested version.

| Part | Change | Commit |
|---|---|---|
| 1 | Generalized report specification and plan | `91199fc` |
| 2 | Fresh bounded source/explicit observations | `45cecbf` |
| 3 | Capability-discovery deadline | `4242212` |
| 4 | Report engine, fidelity and atomic writer | `62903f9` |
| 5 | Markdown/JSON CLI | `b9ee0ba` |
| 6 | Twenty-two report controls | `d07e0ee` |
| 7 | Commands and guide index | `00cf9a4` |
| 8 | Installation and all-platform availability | `f04637a` |
| 9 | Configuration and recovery | `5aaf63f` |
| 10 | Rendered architecture and generated mirror | `39e0886` |
| 11 | PLAN and postponed research scope | `6d84252` |
| 12 | Current status and development checks | `04e88a6` |
| 13 | Journey 51 and chronological index | `199520c` |
| 14 | Validation records and publication accounting | this record |
| 15 | Final README and completed main publication | final delivery commit |
