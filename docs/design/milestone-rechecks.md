# Explained milestone rechecks

2026-10-07. Extends the approved milestone-verification direction in PLAN.md.

The goal is useful continuity during a multi-stage build: give a developer exact
earlier commands to consider, explain the relationships, and measure irrelevant
leads and inspection cost without changing what passing evidence means.

Reuse ElevenPowers' existing ImpactGraph query/selection and milestone freshness
report (repository MIT license). Add command-level prioritization and independent
evaluation; do not create another dependency graph or claim safe test exclusion.

## Contract

When `ep_milestones --impact` is requested, the versioned report adds `rechecks`.
It contains every declared kind/exact-command identity once, references all its
milestones, retains per-milestone check states, and records explained reasons.
Priorities are `direct`, `dependency`, `fallback`. They describe paths, not failure
probabilities. A matching declared input is direct; a current reverse graph path
to a declared input is dependency; no available path is fallback/unknown.

`needs_refresh` is true if any associated check is not CURRENT. An incomplete
overall report also requires resolving coverage before relying on the list.
CURRENT evidence is never made stale by a ranking, and graph absence never makes
stale evidence current. Shared commands preserve every milestone qualification.
Order refresh-needed checks before current checks, then direct/dependency/fallback,
then exact kind/command. No shell execution, new completion blocker or hook query.

The list contains at most 1,024 checks (64 milestones x 16), each referencing at
most 64 milestones. At most 256 explained leads come from the existing bridge.
Each row has at most 16 reasons with explicit omissions. Retain fallback rows even
if graph time/input/result budgets expire. Direct changed-input matches must
survive an exhausted graph budget. Reject unsafe input paths; show omitted changed
observations, and bound the stored requested list to 256. Existing declared scope
and freshness semantics remain unchanged.

Measure graph build/query and ranking elapsed time separately from the whole
report. Source identities from the receipt view and graph must agree; movement or
missing coverage makes the advisory incomplete. Timings are local descriptive
samples, not guarantees or installed-session latency.

## Independent qualification

Freeze controller-owned Python and Node project sources, assertions, changes and
required/extraneous milestone labels before applying faults. Use multiple unrelated
layouts, including transitive imports, dynamic loading, a subprocess consumer and
configuration changes. Hold out subprocess/config cases from algorithm development.
Grade milestone-specific path witnesses against explicit labels; a shared command's
priority does not supply a relationship to every associated milestone. Preserve fallback misses,
and report false leads only for labelled negatives. Actual tests must fail for a
behavior fault and pass for correct/equivalent code; setup errors never count as
detected faults. No agent/model is launched. New output directory only; save every
attempt, source/oracle identities, output digests and timings. Atomically checkpoint
incomplete overall/case state, each completed read, and requested/finished attempts;
retain a pending attempt identity when interrupted. Do not infer the
precision of all unlabelled relationships or a coding-quality gain.

## Delivery exits

Command prioritization and a reproducible evaluation are this delivery. Automatic
advisory hooks, producer-supported narrow receipts, native session overhead and a
matched agent comparison remain subsequent exits. Publish neutral/adverse outcomes
and update guides, status, journey and all affected architecture views.
