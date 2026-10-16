# Installed multi-stage verification

This contributor workflow checks two separate questions: whether an installed
agent uses the declared-check runner across tasks, and whether the combined
workflow preserves behavior while adding features. Installation launches no
model experiment. Runtime behavior remains project-independent; authored queue
and order-system cases exist only in evaluation code.
Run these evaluation commands from an ElevenPowers repository checkout; plugin
installation does not launch them or spend a model allowance.

The first two installed trials completed but did not qualify. After shared
task/provenance/guidance repairs passed full local and four-cell qualification,
two separately approved requalification conversations also completed but did
not qualify. Both now have distinct task identities. Python owns initial and
recovery receipts but leaves the dependency failure stale; JavaScript uses
ordinary compound commands throughout and retains no qualifying receipts.
The larger comparison remains blocked. See the [original attempts](../results/installed-multistage/installed-acceptance.json)
and [repaired-runtime attempts](../results/installed-multistage/repaired/installed-acceptance.json).
Both two-conversation allowances are consumed. Further runs need a new specific
allowance after diagnosing and qualifying the remaining adoption boundary.

## Rehearse without a model

The installed pilot has an opt-in three-task protocol:

```sh
python -m eval.input_scope_pilot --protocol declared-runner --language python --seconds 240 --rehearse --output NEW_DIR
python -m eval.input_scope_pilot --protocol declared-runner --language javascript --seconds 240 --rehearse --output ANOTHER_NEW_DIR
```

Both use actual declared commands and controlled dependency drift/recovery.
Their synthetic task events cannot qualify installed acceptance. The existing
`exact-command` protocol and its 180-second cap remain available as the default.
Real adoption additionally requires completed native runner calls, fresh owned
receipts, current-runtime callback provenance and distinct native task identities.

The four-stage comparison extends the existing controller:

```sh
python -m eval.workflow_rehearsal --output NEW_REHEARSAL_DIR
python -m eval.preservation --prepare NEW_BATCH --case workflow-queue-py --case workflow-orders-js --model claude-sonnet-5-5 --seconds 720
python -m eval.preservation --summary NEW_BATCH
```

Preparation runs actual baseline/public/reference controls and freezes source,
requests, grader identities, configuration, Git head, model and schedule. It
launches no model. The queue covers leases/retries, restart, batching and replay;
the Node case covers holds, exact refunds, restart and atomic event replay. These
are authored systems, not randomly sampled upstream projects.
The integrated rehearsal executes all four reference stages and reproduces all
sixteen source snapshots. Its records explicitly cannot qualify an installed
session or ordinary-versus-assisted coding comparison.

## Live execution is explicit

Before a live pilot, inspect current release health and obtain a specific
subscription-session allowance. The installed gate uses two Claude Code Sonnet
5.5 medium conversations, at most 240 seconds each across three turns. Invoke
the pilot without `--rehearse` only after that approval. It requires a new
unlinked system-temp directory outside Git ancestors. Prompts do not name the
runner; shipping startup/recheck/completion guidance must make it discoverable.

The separate comparison requires installed acceptance and a further allowance:
four matched Sonnet 5.5 medium conversations, 720 seconds each across four turns.
Use `python -m eval.preservation --execute BATCH --slot SLOT --executable CLAUDE`
for each frozen slot. No API fallback, favorable retries or case replacement.
Each turn reserves its share of remaining process time; unused time carries
forward. Controller/grading time is separate, and cleanup is bounded.

## Read outcomes correctly

The source grader checks 2 base groups, then 4/6/8/10 cumulative groups. A new
regression is an earlier group that passed at the previous graded stage and fails
now. A previously failing feature remains an earlier failure, not a new regression.
Absent prior grading produces an unknown regression count, never zero by default.

Outcome comparison requires both arms' complete, identified, scope-valid,
independently graded four-stage output. Missing runner adoption or feedback does
not remove an otherwise comparable unfavorable outcome: delivery is reported
separately. Timeouts, missing stages and scope/setup failures remain scheduled
attempts. The ordinary arm is not expected to emit plugin callbacks.
Earlier source-checked grades and model time remain visible after a later
scope or snapshot failure. Each stage labels `source_grade_valid`; final
integrity failures disqualify the arm without deleting its measured trajectory.
Interrupted native output and diagnostics stay in private attempt files.

The archive extends `eval.preservation_archive` for the new slot names. Retain
every scheduled slot from the same frozen batch. It exports exact source
snapshots, independent regrades, existing redacted evidence reports and explicit
PatchProof eligibility gaps. A dirty uncommitted final result does not acquire
patch binding merely by being exported.

Reproduce a new source archive without a model:

```sh
python -m eval.workflow_results --reproduce ARCHIVE_DIR
```

Reproduction verifies source bytes, public case and generated oracle identities
and grade outcomes. It separately reports whether the historical raw harness
matches; source grading does not replay or authenticate the old installed
session. Runtime evidence freshness never normalizes raw bytes. Review source
privacy before publication; raw host output and captured prompts stay private.

See [design](../docs/superpowers/specs/2026-10-16-installed-multistage-design.md),
[validation](../docs/validation/2026-10-16-installed-multistage.md) and
[journey 82](../journey/82-a-workflow-needs-a-native-trial.md).
