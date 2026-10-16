# Installed Multi-Stage Verification v1 — proposed design

Status: proposed next milestone; planning only. No new model sessions approved
or launched. This is a delivery and measurement milestone, not a claim that
ElevenPowers already improves coding outcomes.

## Intent and choice

Reliable declared-check execution has qualified real subprocess controls. The
remaining question is whether an installed agent uses that mechanism during
ordinary development, and whether the combined workflow preserves earlier
behavior while adding features. Previous two-stage comparisons tied on
correctness; the last installed scope pilot did not qualify failure capture
because shell trailers prevented exact command attribution.

My recommendation is to extend the existing installed pilot and staged
comparison, rather than add a producer or another independent evaluation
framework. Further one-shot coding puzzles cannot answer the cross-task
question. Additional producers remain useful contributor work, after this
workflow has evidence. These are proposed engineering choices, not recorded
user approval of the design or its session budget.

Builder check completed. The choices about time allocation and missing native
delivery below are my engineering recommendations; they do not spend an allowance.

## Built on

Reuse this repository's subscription launcher, native setup, process containment,
`eval/input_scope_pilot.py`, `eval/preservation.py`, independent oracle/archival
helpers, `core/checks.py`, milestone reports and PatchProof exports. The repository
declares Apache-2.0 in its README; no new third-party runtime dependency or agent
workflow engine is proposed. Existing launchers support the required subscription
authentication but native tools are not an OS-level closed-book boundary.
The addition is a qualified path from installed runner adoption to a frozen,
cross-language, four-stage comparison.

## Gate 0: release health

Inspect the final-main automatic CI repeat before live sessions. Investigate any
actual failure using retained component diagnostics and witness a regression
before a justified repair. A successful repeat does not close the unexplained
older Windows advice incident. Do not spend model allowance against a known
failing release. Free preparation and deterministic controls can proceed while
CI completes; runtime changes require fresh fingerprints and affected gates.

## Gate 1: installed declared-check adoption

Extend the existing two-consumer Python/JavaScript pilot with an opt-in
`declared-runner` protocol; preserve its existing exact-command protocol.
Each new disposable project gets one persistent installed Claude conversation
with three task turns: repair the initial behavior and verify it; observe an
independently changed dependency and retain the affected failure; then verify
again after the controller restores the dependency. Keep the other consumer's
inputs unchanged. Host prompts must not supply a literal `ep_check.py` invocation:
the shipping startup/recheck/completion guidance must make it discoverable.

Qualification requires the shipped runner to be observed in native command
events, correct owned receipts, native task transitions, affected milestone
CURRENT -> STALE -> FAILED -> CURRENT, unchanged independent milestone CURRENT,
preserved configuration/check seals, and an independent final behavior grade.
CLI adoption must not be inferred merely from a final answer or a controller
invocation. Interrupted/timeout controls leave incomplete rather than current
evidence. Synthetic callbacks qualify only deterministic rehearsal.

Proposed live allowance, requiring a fresh specific approval: **two Claude Code
subscription conversations, Sonnet 5.5 medium, 240 seconds total per conversation
across all three turns** (eight minutes maximum), no API fallback or model
retry. Bounded process cleanup is separate (at most five seconds per turn).
Allocate each turn `remaining model-process allowance / remaining turns`, carrying
unused time forward. Deduct observed process wall time conservatively, including
cleanup; deterministic controller/grading time is logged separately and does not
consume the model allowance. A timed-out turn ends that conversation's attempt.
The legacy exact-command protocol keeps its existing deadline behavior.
If either language fails adoption, retain the result and repair the demonstrated
integration boundary before the benefit comparison. No silent favorable rerun;
any requalification needs a new allowance and recorded runtime identity.

## Gate 2: independent multi-stage comparison

Extend the existing preservation controller with a versioned four-stage suite.
Keep the archived two-stage queue/inventory cases and their reproducer unchanged.
New cases are authored portable systems, not representative upstream samples:

| Case | Stage 1 | Stage 2 | Stage 3 | Stage 4 |
|---|---|---|---|---|
| `workflow-queue-py` | Expiring leases, retry limits and stale-token fencing | Versioned snapshot/restart retaining queue/lease semantics | Batch transitions and dead-letter handling | Backward format migration and idempotent replay |
| `workflow-orders-js` | Expiring inventory holds and idempotent requests | Partial fulfillment/refunds with exact integer accounting | Versioned snapshot/restart preserving holds and request identities | Event replay and atomic rejection of invalid batches |

Each starts with functioning core behavior plus an independent utility. Use
injected clocks and deterministic event histories rather than timing sleeps.
Public contracts define boundary semantics, data formats and allowed files
before the run. Independent oracles check observable behavior, never source
spelling or a preferred implementation. Two base contract groups plus two new
groups per stage produce 4/6/8/10 cumulative groups; repeated groups are not
counted as distinct contracts. Oracle groups cover stale/repeated operations,
restart boundaries, conservation and rejection without partial mutation.

Rehearsal must show valid reference solutions pass all applicable groups and
known contract-breaking variants fail their intended groups. Freeze case,
request, grader, configuration, runtime and scheduling identities before any
model calls. Reference solutions and oracle fixtures stay outside model project
directories. Withholding them is not an OS access guarantee.

Use two matched arms per case: ordinary installed Claude and ElevenPowers guide
workflow. Both get identical initial project files, public commands/contracts,
requirements, permitted edits, host/model effort, customization policy and time
allowance. Only the ElevenPowers integration/configuration differs. Existing
public tests and harness/configuration remain sealed; agents may edit declared
production files and add language-appropriate tests in explicitly allowed paths.
Optional mutation engines remain disabled in both arms. Normal declared commands
remain available to both; the runner and plugin feedback are the intervention.
No evaluator repair, hidden-grade hint, new reference test or manual fault is
injected into a model candidate between stages. Controlled faults belong to
Gate 1/rehearsal and are reported separately.

Proposed second live allowance, requested only after Gate 1 qualifies: **four
Claude subscription conversations, Sonnet 5.5 medium, 720 seconds total each
across four turns** (48 minutes maximum), no API fallback, retries or case
replacement. Alternate arm order by case. Persist/resume each conversation and
record both host conversation identity and actual native task boundaries. The
combined proposed ceiling is six conversations/56 model minutes, not approved
spending. Cleanup and deterministic grading/report time are separate and logged.
Use the same remaining-allowance/remaining-turns allocation as Gate 1: 180 seconds
for the first comparison turn, with unused allowance carried forward. The two
arms use identical rules; this preserves the existing comparison's reservation
policy rather than allowing the first request to consume every later stage.

## Measurement and delivery

Primary: lost earlier behavior and final cumulative correctness, with matched
per-case differences. A regression is a group that passed at the preceding graded
stage and fails now. Separately report all currently failed earlier-required
groups, including features never implemented correctly; those are not all new
regressions. Keep new-feature failures separate. With a missing previous grade,
regression count is unavailable rather than zero. Non-graded results,
timeouts, scope violations, missing stages and incomplete sessions are explicit;
never count them as passes or drop them from the scheduled denominator. A pair
is outcome-comparable only if both arms preserve protocol identity and scope,
complete every scheduled host turn, and have graded output at every stage.
Retain all others with their qualification failures.

Native delivery is a separate qualification. In Gate 2, absent assisted runner
adoption, missing callback/task transitions or unavailable feedback does not
exclude an otherwise outcome-comparable pair: retain it as delivery-failed or
unverified, including any unfavorable outcome. Gate 1 still requires verified
native adoption. No component-specific mechanism claim follows from unverified
delivery. Missing/mismatched frozen protocol or conversation identity remains
an integrity failure. The ordinary arm is not expected to emit plugin callbacks.

Secondary: tool adoption and native delivery, actual owned command outcomes,
verified premature-success attempts where observable, execution counts, feedback
availability, model wall time and deterministic analysis overhead. Record cost
only when the CLI supplies it; subscription wall time is not an API-dollar
estimate. Report selected-file/behavior coverage limits and exact runtime hashes.

Export final source snapshots, reproducible independent grades, aggregate
metadata and redacted evidence/PatchProof bundles where independently eligible.
Commit source/check results only after scope/privacy review; keep captured
session prompts/host output, credentials and machine paths private; frozen
authored requirements and prompt templates may be published. A post-run evidence bundle
does not establish that the agent used PatchProof during development.

Update guides, status, plan, results, journey and all five architecture views
after implementation. Do not turn on optional behavior by default or introduce
a new completion gate as part of this evaluation. Runtime remains generalized;
authored cases, fault variants and project names stay in eval/tests/results.

## Exit and stopping rules

Readiness succeeds only if both installed language sessions meet Gate 1. This
first live gate qualifies Claude Code only; it does not qualify all five hosts.
The
comparison is delivered when every scheduled attempt and grade is accounted
for and reproducible, including negative and incomplete outcomes. An observed
advantage supports only a selected-sample observation; ties do not establish
added correctness benefit, and two cases cannot establish population effects.
Record total host time without asserting speedup from this small sample.
If both arms pass everything, publish that tie and revisit the use case before
expanding cases or launching another sweep. Do not add features merely to make
the assisted arm win.
