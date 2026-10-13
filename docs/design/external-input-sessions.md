# External Input Witnesses v2: ordinary sessions and milestones

Approved purpose, 2026-10-13: extend selected approved local input protection to
ordinary agent receipts, completion-owned checks and cross-task milestones.
Build once in the shared core for any project; retain every required command,
source-only facts, old readable history and explicit host observation limits.

## Scope and reuse

Reuse `core/inputs/` v1 selection/approval/verified reads, existing parsers,
native normalization, atomic locked state, verification ownership and milestone
history. No new third-party runtime dependency, package resolver, test generator
or model call. Reports and callbacks observe bytes; only existing explicitly
authorized/project-profile runners execute commands. Native replay controls are
not installed acceptance or population coding benefit.

One optional `external_inputs` metadata object augments Evidence. Old records
with no object keep identical serialization when no inputs are configured.
Once inputs are required, old records cannot acquire execution provenance merely
because a report can read current bytes. Preserve `source_freshness` separately
from combined freshness and the selected external association.

## Receipt qualification

The versioned bounded metadata records before/after selected aggregate digests,
attempt hash, state and controlled issues. `bound` requires complete matching
observations for one identified execution, complete stable source and unchanged
producer. Changed observations are stale; absent, malformed, incomplete or
unpaired observations are incomplete. A historical pass remains a pass; current
qualification changes instead. Optional metadata is unsigned local evidence.

Read-only freshness operations share one bounded current observation across
receipts. Recheck after report collection, invalidate final qualification if it
moves, and propagate gaps to coverage and verdicts. No process-global reuse of
an external snapshot across separate inspections. Existing source selection,
required checks, profiles and fallback verification remain intact.

## Native attempt association

Use the normalized platform (Claude entry point defaults to claude), nonempty
session and tool-use IDs, task identity, raw invocation digest and qualified cwd.
Never join by command text alone or invent missing IDs. Unsupported native fields
stay unsupported; preserve actual available fields through existing adapters.

Before recognized command evidence, retain an incomplete provisional receipt and
a bounded private before observation. Pre observation and post observation use
at most ten cooperative seconds each, further limited by v1 declared budgets.
No configured policy means no new native state/capture work. Unknown command
results can retain their original facts but cannot acquire missing pre evidence.

`.elevenpowers/input-attempts.json` is schema 1, at most 1 MiB, 128 pending
attempts and 256 consumed IDs. Pending expiry is one hour; negative/non-finite
clock intervals are incomplete. Validate safe state reads and private tracking;
use the existing write lock and atomic replacement. Do not hold a lock during
filesystem collection. Revalidate state when consuming it. Duplicate pre,
replayed post, overlapping calls, changed task/session/invocation, changed runtime,
eviction and interrupted/unfinished outcomes cannot create qualified success.
Terminal post consumes once; unfinished callbacks retain explicit incomplete
history. A fresh identified retry can supersede an earlier incomplete check.

## Owned execution and consumers

Completion-owned verification and targeted confirmations capture required inputs
around actual commands, persist incomplete before launch and refuse launch when
required inputs cannot be observed. Their existing budgets/cleanup remain the
earlier deadline. Dependency changes invalidate reuse and baseline-discrimination
cache inputs. Baseline observations never imply current execution provenance.
Explicit PatchProof execution supplies the same receipt metadata from its existing
qualified before/after witnesses, rather than inventing a second execution.

Milestone history retains metadata across tasks under existing bounds. Reports
distinguish current, failed, stale, absent and incomplete observations, and recheck
advice consumes those states without excluding required checks. Ordinary reports,
completion, milestone reports, PatchProof and GitHub expose consistent qualified
facts and gaps. Existing manually captured exercise receipts must be enriched only
from their actual controller-run before/after observations.

## Acceptance and delivery

Actual unrelated Python and JavaScript projects must build and check behavior,
retain it into another task, demonstrate independently failing dependency drift
with unchanged source/HEAD, lose current qualification, rerun and recover after
repair. Positive unchanged-input reuse, missing inputs, callback loss, concurrent
calls, duplicate/replay, declaration movement, malformed state and old records
must have forward/adversarial controls. Count actual command executions and
selected-file reads; report elapsed observations without a speedup claim.

Exercise five normalized hosts using real local commands and explicitly synthetic
callback envelopes. Missing host identity remains unqualified. Run shared owned
verification separately. No paid or installed sessions are included in this task.
Keep each witnessed RED→GREEN part pushed. One fresh whole-branch review, one
repair pass, final full/named/independent/doctor/stdlib gates, four hosted cells,
actual exercise, all five rendered architecture tabs and local links qualify
delivery. Update guides, README, plan/status, contributor roadmap, journey 79
and dated validation; normally fast-forward main preserving qualified bytes.
