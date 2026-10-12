# Plan and explicitly run patch verification

PatchProof can plan the project's declared checks and explicitly collect missing
execution evidence for a clean committed patch. The same workflow applies to any
supported project and host. Reports, plans and installation remain read-only with
respect to project checks; only `--verify` starts the declared commands.

```bash
python plugin/bin/ep_patchproof.py --project PATH --base BASE --head HEAD --plan
python plugin/bin/ep_patchproof.py --project PATH --base BASE --head HEAD --verify --seconds 120 --command-seconds 30
python plugin/bin/ep_patchproof.py --project PATH --base BASE --head HEAD --verify --format json --output verification.json
python plugin/bin/ep_patchproof.py --project PATH --base BASE --head HEAD --plan --impact
python plugin/bin/ep_patchproof.py --project PATH --base BASE --head HEAD --verify --rerun
```

Configure commands through the existing project-owned
[configuration](configuration.md), or use supported manifest discovery. `tests`,
`build`, `typecheck`, `lint` and `benchmark` are recognized. Identical commands can
serve multiple properties with one execution. Grouping uses the original command
digest, so distinct commands with the same redacted display stay separate.
Unsupported properties remain visible and leave execution incomplete. A plan never fabricates a command from
an ImpactGraph candidate file, and never removes required commands or fallbacks.
Impact explanations are advisory even when their input association is bound.

## What the plan means

The plan shows required commands, current evidence states, run/reuse decisions,
qualification issues and budgets. A current legacy receipt can remain informative
without enough provenance to qualify reuse. Duration estimates are unknown;
the configured seconds are limits, not predicted completion times.

Execution requires a complete eligible committed patch at the current head and
complete source coverage. Dirty/staged/nonignored untracked files, linked inputs,
moving refs and unavailable guards leave it incomplete. The `off` profile remains
passive and refuses execution. Commit intended changes before using this path.
Do not delete unrelated work to satisfy the clean-input condition. Requested
named refs are resolved again during execution and final inspection; moving a
ref cannot silently switch the requested patch. JSON execution results retain
the initial `planned_patch` identity as a diagnostic when later qualification fails.

## Durability and reuse

The existing project verification ownership lock prevents overlapping execution.
Before launch, an incomplete attempt is persisted; completed receipts are saved
before the next command starts. Timeout, excessive output, interruption and
unavailable final input inspection remain incomplete. A source/configuration/
policy change stops later commands; earlier evidence remains visible with its
qualifications. Process death leaves the saved attempt incomplete for recovery.
Catchable main-thread cancellation during process creation is deferred until ownership
can clean up the child; existing signal handlers are restored and forwarded.
This does not promise cleanup after uncatchable termination or host death.

`.elevenpowers/patch-verification.json` retains bounded unsigned associations to
existing ledger receipts. Fresh inspection compares the exact patch/tree pair,
source, raw/effective command configuration, repository ignore policy, runtime
producer and environment digests. Environment values and captured outputs are
not exported. Only the latest complete passing associated aggregate can be reused;
a later failed or incomplete receipt supersedes it. A changed command/configuration
or qualified input prevents reuse. New associations store aggregate receipt keys;
individual test results remain in the ledger. Older histories containing leaf
keys remain readable and are retained during recovery. State is bounded to
128 attempts and 1 MiB, with explicit count/byte evictions. Fresh inspection
rechecks saved state and the parent ledger/configuration guard before granting
association; a late real failure cannot preserve an older passing bundle.
Use `--rerun` to execute every declared check again when services or installed
dependencies may have changed: those external bytes are not covered by local reuse.

An ordinary PatchProof bundle reads these saved observations without launching
commands. For qualified new observations, it can report the actual inspected head
at execution and producer/environment identities. Existing legacy receipts keep
their unknown execution provenance.

## Bounds, exits and limitations

Defaults: 120 shared seconds, 30 seconds per command, 64 declared properties,
8 MiB combined command output. Shared seconds range from 0 to 600; command seconds
must be greater than 0 and at most 300. The shared deadline includes planning and
input inspection, with a separate cleanup allowance. These are cooperative limits;
filesystem/system calls and existing parser metadata reads can take additional
time. Interrupted or unavailable final inspection never becomes passing evidence.

Verification exits `0` when all required declared checks are qualified and current,
`1` for a completed qualified failure, and `2` for incomplete/unqualified work.
Planning normally exits `0`; `--require-bound` can gate its patch/input association.
The existing ordinary-report binding gate retains its meaning and is not a safety
or task-completion verdict. Output overwrite requires `--force` as before.

Commands run project code with your account's permissions. Windows Jobs and POSIX
process groups manage descendants; they are not a security sandbox. Deliberate
POSIX group escapes and abrupt host death remain outside cleanup guarantees.
Unsigned local records require trust in the producer and project state. Installed
dependency bytes, services and changes that revert between observations remain
unobserved. A passing command is evidence of that command's result, not proof of
correctness or a demonstrated improvement in AI coding outcomes.

See the [design](../docs/design/patchproof-verification.md),
[implementation plan](../docs/superpowers/plans/2026-10-12-patchproof-verification.md)
and [existing bundle qualifications](patchproof.md).
