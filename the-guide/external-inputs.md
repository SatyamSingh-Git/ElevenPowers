# External input witnesses

Command-scoped input witnesses extend ordinary receipts, owned verification,
cross-task milestones and PatchProof reuse to selected local dependency/tool
files. A dependency can change at the same
path while source, HEAD, lockfiles and environment values remain unchanged.
With declarations and local approval, such a change prevents reuse of an older
passing execution and schedules the required checks again.

This is shared, language-independent core behavior for any project using the
evidence runtime; explicit PatchProof still requires an eligible Git patch.
Native passive receipt capture and milestone invalidation use the same approved
selections. Existing source-only
receipt freshness remains a separate fact. Matching selected bytes does not
establish a complete environment or universal patch safety.

## Declare the inputs

Create project-owned `elevenpowers.inputs.json` and commit it with the intended
patch. IDs and root labels use 1–64 ASCII letters, digits, underscores or
hyphens, starting with a letter or digit. Up to 32 witnesses and 32 paths each
are supported.

```json
{
  "schema": 1,
  "witnesses": [
    {"id": "parser-dependency", "root": "deps", "paths": ["parser.py"]},
    {"id": "generated-sdk", "root": "sdk", "paths": ["client", "schema.json"]}
  ],
  "limits": {"files": 2048, "bytes": 33554432, "seconds": 10}
}
```

Paths are literal, portable relative paths using forward slashes. There is no
glob expansion; bracketed names such as `types/[slug]/route.d.ts` are literal.
Parent traversal, absolute/drive paths, backslashes, NULs, `*`, `?` and colons
are refused. `.` explicitly selects an approved directory tree. Choose stable
inputs rather than test outputs or caches that a check writes. If an input
changes while a command runs, the observation cannot qualify that command.

Common manifests and lockfiles are already included in supported repository
source selection. Use witnesses for additional bytes that your checks actually
depend on, not as another manifest-only declaration of installed freshness.

## Select inputs for a declared command

Schema 1 keeps every configured witness applicable to every receipt. Opt into
schema 2 to declare a complete nonempty witness set for a specific command:

```json
{
  "schema": 2,
  "witnesses": [
    {"id": "auth-sdk", "root": "sdk", "paths": ["auth"]},
    {"id": "billing-sdk", "root": "sdk", "paths": ["billing"]}
  ],
  "commands": [
    {"command": "npm run test:auth", "witnesses": ["auth-sdk"], "complete": true},
    {"command": "npm run test:billing", "witnesses": ["billing-sdk"], "complete": true}
  ]
}
```

Also declare those exact commands through the ordinary project configuration.
Recognition reuses the runtime's existing declared-command parser, including
supported literal project-directory wrappers. Up to 64 mappings are supported;
empty, unknown, duplicate or ambiguous witness selections are refused.
Commands containing credential values that the runtime redacts cannot qualify
a narrower identity. Put credentials in the environment instead of a declared
command string; distinct secret values must never collapse into one scope.
`complete: false`, unmatched commands and older receipts retain broad coverage.
An assertion of completeness is your project's dependency contract; ImpactGraph
and a missing edge do not infer it or permit skipping a required check.

With unchanged project source, auth SDK drift expires auth evidence while an
independently scoped billing receipt can remain current. Missing selected bytes
leave their scope incomplete. Selected root rebinding, relevant declarations and
scope changes expire the association. Source changes still expire source-scoped
evidence, including edits to this project-owned declaration itself.

Collection budgets apply to the project union, not once per command. Exhausted
coverage stays conservative. Nested PatchProof, ordinary and milestone reports
share opening and closing external observations within one operation; source
snapshots remain independent. No observations are cached across executions or
later report calls. Closing movement keeps overall report coverage incomplete,
even when an independent receipt retains its qualified current state.

This milestone is undergoing final qualification; see the
[design](../docs/design/command-input-scopes.md) and
[implementation plan](../docs/superpowers/plans/2026-10-14-command-input-scopes.md).

## Approve local roots explicitly

A declaration does not authorize external reads. On each machine, bind its root
labels to the intended directories:

```sh
python -I -B ElevenPowers/plugin/bin/ep_inputs.py bind --project PROJECT --name deps --path DEPENDENCY_DIRECTORY
python -I -B ElevenPowers/plugin/bin/ep_inputs.py bind --project PROJECT --name sdk --path SDK_DIRECTORY
```

Only this explicit action writes private `.elevenpowers/input-roots.json`.
The file is tied to the current project; copied or Git-tracked approvals do not
qualify. The binding operation preserves other private ignore rules and excludes
its approval, lock and ignore metadata. An imported repository declaration alone
cannot authorize a new directory. Local unsigned state still requires trust in
the caller and filesystem; this is not independent authentication.

Use `--replace` to deliberately change an existing binding. Missing old roots
can be repaired through that explicit replacement. Unused approval entries do
not require current access; an unconfigured project does not inspect approval
state. If existing ignore rules are tracked, review and commit their requested
changes before verification's clean-source requirement.

Approved roots must be unlinked directories. The project itself, ancestors
containing it, `.git` and `.elevenpowers` state cannot be input roots. An ignored
dependency directory inside a project or an independent directory outside it
can be approved. Selected symlinks, junction redirects, multiply linked files
and special files remain incomplete. Some package caches use hard links; narrow
to supported inputs or use a copied installation rather than treating them as
observed automatically.

## Inspect without running checks

```sh
python -I -B ElevenPowers/plugin/bin/ep_inputs.py inspect --project PROJECT
python -I -B ElevenPowers/plugin/bin/ep_inputs.py inspect --project PROJECT --seconds 10 --check
```

Inspection prints JSON with witness labels, collection state, fingerprints,
counts, budgets and issues. It writes no project state and runs no package
imports, version commands, installations, remote probes or model calls. Bounded
read-only Git metadata checks can verify that approval is not tracked. Cold CLI
imports suppress Python bytecode, including in isolated mode.

Ordinary inspection exits 0 for a diagnostic result; `--check` exits 1 unless
collection is available. Invalid CLI/binding requests exit 2 with controlled
diagnostics. `not_configured` means no declaration, not a qualified environment.
Missing approval retains the declared labels so the required root can be found.

## Verification and reuse

After approval, the existing workflow performs witness collection automatically:

```sh
python ElevenPowers/plugin/bin/ep_patchproof.py --project PROJECT --base BASE --head HEAD --plan
python ElevenPowers/plugin/bin/ep_patchproof.py --project PROJECT --base BASE --head HEAD --verify
```

No separate capture command is required. Schema 1 and unmapped commands require
all declared witnesses; schema 2 complete mappings qualify their selected set.
Complete unchanged observations can qualify reuse;
changed bytes, filenames, directory structure, additions/deletions, declaration or binding identity
prevent reuse. Missing approval, empty selected scope, unreadable inputs or
partial inspection leave the plan incomplete and block launch/reuse. Changes
during execution preserve the result as stale/incomplete and defer later work.
Final source, checkout, configuration and ignore-policy guards extend through
collection; a persistent edit during the scan prevents reuse or launch.

The original receipt outcome is retained. A historical pass is not rewritten to
a failed command. `source_freshness` remains separate from current `freshness`
and the receipt's `external_inputs` association. Source can remain fresh while
external qualification becomes stale or incomplete. Earlier eight-field execution
witnesses remain readable; they cannot acquire a newly required external
observation. Without declarations, their existing semantics remain unchanged.
The new optional fingerprint does not certify every installed dependency.

## Ordinary sessions and retained behavior

After declaring inputs and explicitly approving roots, recognized native commands
observe inputs automatically before and after execution. Qualification requires
the same platform, nonempty session and tool-use IDs, task, invocation, directory,
source, configuration and producer. Command-text similarity cannot supply a
missing identity. Existing adapters preserve supplied IDs; unavailable callbacks
or fields remain incomplete. A post-only result cannot invent its before-state.

Before execution, the ledger retains an incomplete provisional receipt.
`.elevenpowers/input-attempts.json` keeps private identified pending/consumed
attempts: private schema 2, at most 1 MiB, 128 pending and 256 consumed details,
with one-hour pending expiry. A fixed 256 KiB monotone seen-ID filter retains
eligibility history after details are evicted. Filter collisions conservatively
leave attempts incomplete; they never admit a previously seen ID. Earlier
experimental private state without this memory stays incomplete rather than
being silently reset. Terminal callbacks consume once, including post-only
results; unfinished callbacks retain
incomplete history. Duplicate, overlapping, mismatched, replayed or evicted
attempts cannot qualify an old result. Removing the declaration during an active
call preserves its required before observation. Native commands are observed,
not blocked by this observer. Each native capture has ten cooperative seconds,
further limited by declared budgets.

Provisional ledger writes validate the task under the same short write lock;
an old before callback cannot replace a newer task. An unidentified active
provisional receipt remains incomplete if its policy is removed. A fresh owned
check or a new task resolves that ambiguity without inventing an identity.

Completion-owned verification and targeted confirmations also record paired
observations, refuse launch when required inputs are incomplete, and preserve
their existing shared deadlines. Selected external changes expire result reuse
and baseline cache identities. A fresh identified retry can recover qualification.
No declarations preserve the earlier unconfigured behavior and serialization.

[Milestone history](milestones.md) retains this optional metadata across tasks.
Old or malformed records stay incomplete when selected inputs are required;
current reads cannot upgrade their execution provenance. Reports distinguish
bound, stale, incomplete and not-configured external association, keep source
facts separate, and retain required recheck commands. Reports run no checks.
Closing inspection guards source, command configuration and selected external
inputs. Persistent movement invalidates receipt, claim and milestone
qualifications together; the original command result remains unchanged.
Ordinary reports and nested PatchProof bundles share opening and closing external
collections within one operation. Each selected file is read once per phase;
paired execution phases and later operations always collect independently.

## Command-specific qualification

Schema 2 can map an exact declared command to a complete list of required
witness IDs. Partial maps, unmatched commands and historical broad receipts
retain all configured witnesses. Command spellings that redact, or contain
the reserved `REDACTED` replacement marker, cannot authorize narrowing; supply
credentials through the environment. Selected dependency drift expires that
command's evidence without expiring an independent complete scope.

An unavailable unused witness remains visible in overall scan coverage. It does
not prevent a required command with a complete, available scope from running or
reusing qualified execution. An unavailable required witness still prevents a
complete verification result. Every declared check remains required; scopes
never authorize skipping a check. Source edits and configuration changes retain
their independent invalidation rules.

The collector still reads the configured union under aggregate budgets. This
feature narrows qualification, not the files collected for each execution.
Malformed shared state, opaque late movement and exhausted collection budgets
can conservatively leave several scopes incomplete.

## Collection bounds

Defaults per capture are 2,048 files, 4,096 enumerated entries, 32 MiB, ten
cooperative seconds and depth 32. Directory inventories are checked again within
the same aggregate allowance; shared files are read once per capture. Project
limits support 1–16,384 files, 1 byte–256 MiB and 0–60 seconds; entry allowance is
twice the file limit. The caller's existing shared deadline remains the earlier
bound. Scope/byte/time exhaustion produces incomplete coverage, not a truncated
qualifying fingerprint. An empty selected scope cannot qualify reuse.

Policy and approval JSON are each bounded to 64 KiB and parsed strictly. No
contents, per-file digests, private absolute paths, environment values or raw
exception bodies are exported. Public known-credential redaction is retained;
hashes are unsigned observations, not encrypted secret storage or attestation.

[PatchProof bundles](patchproof.md) and [GitHub summaries](patchproof-github.md)
show the separate current external-input view, gaps and saved execution
associations. Reports remain read-only. Before/after observations and descriptor
guards are not an atomic snapshot; reverted changes and unobserved dependencies,
remote services or runtime behavior stay outside the claim. Filesystem calls are
cooperative, so an in-flight call can return after the allowance.

See [design](../docs/design/external-input-witnesses.md),
[validation](../docs/validation/2026-10-13-external-inputs.md) and
[journey 78](../journey/78-the-dependency-can-change-without-the-patch.md).
