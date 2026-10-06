# Verification across development milestones

Status: first implementation approved on 2026-10-06. This document specifies
the local capability; automatic completion integration and coding-benefit
acceptance are separate, unqualified follow-ups.

## Goal and reuse

Keep user-owned behavior expectations and their latest qualified execution
evidence available as development moves between tasks. A person can inspect
which earlier behaviors have current evidence, failed checks, stale inputs,
incomplete execution or no recorded check. Build inside ElevenPowers for any
project and any host, without executing commands during inspection.

Reuse the existing `Evidence` freshness semantics, locked atomic `Ledger.save`,
portable export redaction/escaping/atomic output, and `core.impact` query API.
No new mandatory dependency, model service, checkpoint store or verdict engine.
The existing task claims and proven snapshots keep their own meaning.

## Project-owned declarations

An optional version-controlled root file `elevenpowers.milestones.json`, schema
1, contains at most 64 milestones. Each has a unique identifier, a human-owned
description, 1-128 normalized repository-relative ordinary input files and
1-16 checks. Each check declares the exact command and aggregate evidence kind:
`test_suite`, `build`, `typecheck`, `lint` or `benchmark`.

```json
{
  "schema": 1,
  "milestones": [{
    "id": "authentication",
    "description": "A valid session permits the authenticated request.",
    "inputs": ["src/auth.py", "tests/test_auth.py", "requirements.txt"],
    "checks": [{"kind": "test_suite", "command": "python -m pytest tests/test_auth.py"}]
  }]
}
```

Descriptions express expectations; a passing command establishes only its
recorded property and observed scope. Runtime behavior is not derived from
example project names. Unsupported command producers remain missing evidence.
No command discovery or execution is added by these declarations. Unknown
schema/fields, duplicate IDs/JSON keys, empty required fields, invalid kinds,
unsafe paths and over-budget input fail closed with explicit issues. The file
is bounded at 128 KiB. Input paths cannot escape the root, cross nested Git
boundaries or follow links. Missing/deleted declared inputs are visible gaps.

## Durable evidence and freshness

Opted-in projects retain a bounded `milestone_history` in the existing ledger
JSON. The same short write lock and atomic replacement commit history together
with current task state. History persists independently across new tasks and
concurrent saves. It never becomes evidence for a new task's claims.

Keep the latest aggregate receipt per kind/exact command using the existing
timestamp and later-entry tie rule. Strip receipt detail and keep no prompts,
transcripts or captured output in history. Preserve its original input scope,
fingerprint, declaration, result and execution state; do not relabel an old run
as executed in the current task. Limit history to 256 command identities and
4 MiB of JSON; eviction or malformed historical state remains an explicit
coverage issue. Report reads also bound the ledger to 8 MiB. Missing declarations
leave existing behavior unchanged and perform no milestone capture work.

A qualifying receipt must match the exact command/kind, have valid recorded
metadata and cover every declared input plus the declaration file. Its recorded
inputs must be fresh now. Empty observations cannot qualify. Source-scoped
receipts retain conservative whole-source invalidation, including declarations,
configuration/dependency files already selected by the scanner. Explicit-path
receipts require the full declared scope and use the existing fresh digest view.
Changing descriptions or declarations invalidates evidence bound to that file.
Unrecorded dependencies and external environment/services remain qualifications,
not claims of freshness. A redacted command identity cannot establish an exact
match. Test receipts that counted zero executed tests cannot qualify.

Do not flatten result, execution and freshness into one fact. Check states are
`CURRENT`, `FAILED`, `STALE`, `INCOMPLETE` and `ABSENT`. A fresh complete pass is
`CURRENT` within its declared scope; incomplete execution and stale observations
cannot certify current behavior. A milestone aggregates with incomplete, failed,
stale and absent taking precedence over current. A view with unresolved coverage
cannot pass its explicit `--check` gate, even if some checks are current.

## Read-only report and impact advice

`core.milestones.build(root, *, seconds=30, changed=None, impact=False)` returns
schema-1 JSON. `python plugin/bin/ep_milestones.py --project PATH` renders
Markdown; `--json`, `--output`, `--force`, `--seconds` and `--check` follow existing
CLI conventions. Exporting is an explicit write; inspection runs no commands or
hosts and creates no project state. An absent file reports `not_configured`.
Invalid declarations, unavailable history, omitted work and concurrent movement
remain incomplete. The cooperative operation budget is 0-120 seconds.

Optional `--impact` builds a fresh graph, using explicitly supplied `--changed`
paths or current task touched paths as change observations. Match explained
affected paths to milestone inputs and show direct/graph leads with separate
coverage gaps. History co-change never becomes causal impact. Graph absence
cannot establish that a milestone is unaffected, safely exclude fallback tests,
or certify behavior. Declared receipt freshness decides check state; advice is
informational. No automatic hook queries or new completion blocker.

Portable `ep_report` includes the milestone section only for opted-in projects.
The section keeps its own schema/state/limits and never changes task verdicts.
The source/ledger/declaration identities read for each report remain explicit;
two bounded observations are not an atomic transaction. Check for movement of
the declaration and ledger across collection and mark detected movement
incomplete. Outputs reuse portable redaction, root substitution and escaping.

## Acceptance

Exercise three stages with independently specified provider, consumer and
worker expectations. Retain passing, later broken, repaired, valid alternative,
unrelated, missing and incomplete controls. Use real Python and Node producers
before interpreting their output, in unrelated disposable layouts. A later
provider change must make earlier evidence stale and the relevant real check
must reject its seeded fault. Refreshing the failed check must show `FAILED`;
the repaired counterpart must show `CURRENT` after fresh checks.

Exercise malformed declarations/history, command/kind/scope mismatch, zero
tests, description/config/dependency edits, unchanged-mtime bytes, deletion,
new tasks, concurrent saves, symlink/nested boundaries and file/time/history
budgets. Explicit declared scopes must preserve an unrelated milestone where
its inputs remain unchanged; broad source receipts conservatively expire and
must disclose that grain. Verify no command execution or state write during
reads, portable JSON/Markdown, standard-library-only import and existing task
verdict compatibility. Update all affected architecture views and render them.

Publish capability outcomes and descriptive local elapsed times. These controls
are not an ordinary-agent comparison and do not establish coding benefit,
universal safety, selective invalidation accuracy or installed-host acceptance.
PatchProof patch binding, hosted provenance and automatic integration remain
separate. New paid/model comparisons require explicit authorization.
