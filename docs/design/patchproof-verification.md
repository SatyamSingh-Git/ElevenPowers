# Explicit PatchProof verification

The approved milestone helps any supported project obtain missing evidence for
an exact committed patch. Repair execution reliability first, then compose the
existing configuration, source scanner, parser, ledger, ownership journal and
PatchProof bundle. No project name or coding-agent host changes the policy.

## Decisions

Use a read-only `ep_patchproof.py --plan`, and a separate explicit `--verify`.
The existing report and installation paths never launch these checks. Every
recognized project-declared command remains required; identical commands may
share one execution. Impact candidates are advice, not generated shell commands
or exclusions. Unrecognized declaration properties remain visible but unsupported.
Plans show current/failed/stale/absent/incomplete evidence, reasons, provenance,
shared/per-command budgets and unknown cost. They contain no latency estimate
without measured samples. Do not invent commands from candidate file names.

Reuse the project-owned commands and existing local evidence components under
the repository license; add exact-patch orchestration and qualifications rather
than another runner. Shell commands execute project code with the caller's
permissions. POSIX process groups and Windows Jobs manage descendants, not a
security sandbox. The patch must be a complete, clean, eligible committed pair
at the current head. A before/after qualification is not an atomic snapshot.

## Execution and saved evidence

An explicit invocation uses the existing project verification ownership lock,
with a shared cooperative deadline (default 120 seconds, maximum 600), a command
cap (default 30 seconds, maximum 300), at most 64 declarations and the existing
8 MiB combined output cap. Cleanup may consume its separately documented bound.
Persist an incomplete receipt before launch and completed receipts before the
next command. Keep interrupted/deferred work visible. A profile of `off` remains
passive and refuses execution. Dirty, moving, incomplete or linked inputs refuse
launch/reuse. Source/configuration/policy/patch/producer/environment guards are
checked before and after execution and freshly when reading saved evidence.

Save bounded local execution associations in `.elevenpowers/patch-verification.json`.
Each observation links exact patch/tree identities and existing receipt keys,
command/configuration/source/policy/producer/environment digests, exit status,
execution state and limits. No outputs or environment values enter exports.
Reuse only the latest complete passing associated aggregate for an unchanged
command and qualified inputs; later failed/incomplete attempts supersede success.
External services, installed dependency bytes and intervening reverted changes
remain unobserved. Saved local records are unsigned and require producer trust.
Original named selectors are re-resolved at each witness boundary. Final bundle
guards cover execution inspection as well as receipt collection. New records
use aggregate keys computed from persisted redacted identities; old leaf-key
histories stay readable within the byte bound. Raw command digests, not redacted
display strings, define command grouping. Catchable main-thread launch signals
are deferred until process cleanup ownership is established, then forwarded.

## Reliability and acceptance

First investigate retained Linux interrupt cleanup and Windows quoted-launch
timeouts, preserving deadlines and legitimate controls. Use actual process trees,
bounded hosted POSIX repetitions and diagnostic process identities. Do not call
unreproduced historical incidents fixed. Investigate earlier SQLite reference
failures separately; repair only established causes.

Acceptance uses unrelated actual Python and JavaScript commands, independently
known passing/faulty behavior, failed aggregates, stale source/configuration,
duplicate declarations, timeout/output limits, interruption, exact-patch drift,
read-only defaults and fresh-result reuse. Full regressions, named audit probes,
independent grader, doctor and rendered architecture are delivery gates. No model
session or causal coding-quality/speed claim is part of this milestone.
