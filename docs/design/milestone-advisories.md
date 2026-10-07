# Bounded milestone advice

The approved milestone makes exact milestone rechecks useful during development
in any project. It extends the existing ledger, ImpactGraph and report rather
than introducing another verification engine. Advice remains separate from
evidence, command execution and completion decisions.

Three approaches were considered: graph work on every edit would multiply scan
cost; completion-only output would miss hosts without an ordinary Stop context;
a bounded worker at the common edit boundary supports all five transports and
isolates expensive inspection. The third approach is selected.

Projects explicitly opt in through `milestone_advice` in their existing config.
The feature also requires `elevenpowers.milestones.json`; the off profile is
silent. Default automatic activation waits for installed-session qualification.
An edit callback saves attribution first, then requests read-only advice using
the accumulated task paths. A subprocess has a finite wall timeout, bounded
output and no project command execution. Context contains only a bounded list
of exact declared checks, their evidence states, relationship explanations,
omissions and incomplete coverage. It never says a fallback is safe to skip.

A separate ignored atomic state records reservations before inspection, avoiding
duplicate concurrent work. Deduplication, cooldown and a per-task attempt cap
bound repeated edits and failures. New tasks receive their own allowance. Only
digests, counters, timings and outcome metadata are retained; this cache grants
no receipt or verification status. Unavailable/corrupt state declines advice
with a visible bounded diagnostic rather than bypassing limits.

Process relationships use existing `impactgraph.json` file-to-file declared
edges. A CLI test can explicitly `uses` an entry-point file. This is a project
assertion with provenance, not inferred runtime observation; invalid endpoints
reject the whole declaration. No new subprocess execution or heuristic parser
is needed.

Acceptance freezes selected consumer/test and unrelated references from at least
two independent cached upstream repositories before running the evaluator.
Reuse of prior labels is disclosed. Source pins, file hashes, declarations,
negative references, misses, unknown candidates and operation costs remain
reproducible. Existing authored subprocess controls must recover the declared
relationship without claiming automatic subprocess inference.

Automatic worker budget defaults to one second plus a 0.5-second process grace,
with 30-second cooldown and at most three attempts per task. Configuration may
choose 0.1–5 seconds, cooldown 0–3600 seconds and one–ten attempts. Output is at
most 6000 characters, six commands and three reasons per command; omissions are
explicit. These are engineering limits, not promises about overall host delay.

Controls cover legitimate output and timeout, malformed output/state/config,
duplicates, concurrent reservations, source/task changes, off/unconfigured
projects, native patch attribution and all transport contracts. Read-only
inspection cannot run checks or modify evidence. Installed launch measurements
without a model are reported separately from replay and full coding sessions.
A paid end-to-end comparison is outside this delivery.
