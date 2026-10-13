# External Input Witnesses v1

This remains the historical explicit-PatchProof foundation. The
[v2 design](external-input-sessions.md) extends its approval and collection
contract to ordinary identified native receipts, completion-owned checks and
retained milestone history; it does not silently upgrade old execution provenance.

Approved purpose, 2026-10-13: detect declared local dependency/tool inputs that
change while project source, commits and environment values stay unchanged.
Build generalized shared core behavior, qualify legitimate reuse and drift,
push coherent parts, update the docs/journey/architecture and deliver on main.

Existing source selection already covers supported manifests and lockfiles.
The explicit verification witness already hashes environment values and runtime
identity. This extension observes selected installed or external file bytes;
it does not infer a complete environment from a package manifest.

## Scope and borrowed components

Reuse the existing source/evidence model, PatchProof ownership and lifecycle,
atomic state replacement and public export redaction (repository Apache-2.0).
Use Python standard-library JSON, pathlib, stat and SHA-256, with actual Python
and Node exercises. Add declared external-byte association rather than another
runner or package installer. No new runtime dependency, model, package import,
version command or remote probe runs during collection/reporting. Read-only Git
metadata inspection may check that local approval is not tracked.

The shared module is `core/inputs/`. V1 integrates with explicit PatchProof
verification, reuse and exports. Native passive receipt capture, per-command
invalidation, package-manager introspection, remote-service witnesses and
authenticated attestation are subsequent adapters, not delivered by this scope.

## Declarations and local approval

Project-owned `elevenpowers.inputs.json` uses schema 1, strict JSON, maximum
64 KiB. It declares up to 32 witnesses with unique ASCII IDs, a root label and
1–32 literal relative paths. Paths use portable forward slashes, with no
absolute/drive paths, parent traversal, backslashes, NULs or glob interpretation.
`.` explicitly selects an approved root tree. IDs/root labels are 1–64 ASCII
letters, digits, underscores or hyphens, starting with a letter or digit.

Example:

```json
{"schema":1,"witnesses":[{"id":"dependencies","root":"deps","paths":["parser.py"]}]}
```

Private `.elevenpowers/input-roots.json` maps root labels to canonical approved
absolute directories and binds the file to the current project identity. Only
an explicit `ep_inputs bind --project PATH --name ROOT --path DIRECTORY` writes
approval. `--replace` is required to replace an existing binding. Binding adds
the private filename to `.elevenpowers/.gitignore` without replacing other rules.
Tracked approvals in Git projects are refused; an imported project declaration
cannot authorize a new external root. Copying approval to another project does
not qualify. Unsigned local approval is not authentication against an adversary
who can forge local state with the same account.

Approved roots must be unlinked directories; an ancestor containing the project,
the project root itself, `.git` or `.elevenpowers` state is unsupported. Ignored
dependency directories inside a project, and independent directories outside it,
are eligible. All selected paths must stay inside their approved root. Symlinks,
junction redirects, multiply linked files and special files remain incomplete.
No contents outside the approved root may be followed. Bindings are optional;
without a declaration, existing users retain their current behavior and limits.

## Collection and bounds

`capture(root, deadline)` freshly reads policy and local approval, then selected
regular files/trees. Return schema/state/fingerprint, witness labels and states,
counts and controlled issues. Public results omit contents, private paths,
per-file digests, raw exception bodies and environment values.

Default aggregate limits per capture: 2,048 files, 4,096 directory entries,
32 MiB, ten cooperative seconds and depth 32. Project limits may lower or raise
files to 16,384, bytes to 256 MiB and seconds to 60; entries are twice the file
allowance. The caller's existing shared deadline is always the earlier bound.
No per-witness multiplication of these aggregate limits. Configurations outside
these finite ranges, duplicate/unknown fields, non-finite values and malformed
state are incomplete. Zero seconds permits diagnostic incomplete collection.

Hash content, relative file and directory names/types, and witness scope
deterministically. Empty-directory additions/deletions must change a selected
tree fingerprint when it also contains regular file bytes; an entirely empty
selection remains incomplete. Shared files
are read once within a capture. Descriptor metadata must match the selected
unlinked regular file before/after reading; directory inventories and policy/
approval bytes are checked again. Missing, unreadable, moving, truncated or
over-budget data cannot produce a qualifying aggregate fingerprint. Filesystem
calls remain cooperative; these checks are not an atomic snapshot and cannot
detect a change that reverts between observations.

## Execution and reuse

All configured witnesses are required for the verification attempt as a whole.
Collect before and after command execution and freshly during reuse inspection.
Recheck source, checkout, configuration and repository policy after external
collection; persistent changes during the scan cannot retain earlier association
or launch a command. Read both new state files through the same safe reader.
Complete matching observations augment the existing eight-field execution
witness with an optional external-input fingerprint. The saved-state reader
accepts old eight-field witnesses and the new qualified variant. An old record
cannot satisfy newly declared inputs. Without declarations, old records keep
their existing association semantics; no additional freshness is implied.

External drift invalidates reuse and schedules required commands again. Missing
approval or incomplete current collection blocks launch/reuse with an explained
incomplete state. During-execution drift leaves the attempt stale/incomplete and
defers later commands. Preserve original receipt outcomes/history; never rewrite
a historical pass to a failed command or discard a newer incomplete observation.

Reports expose a separate external-input view and saved execution associations.
Source-only receipt freshness remains its original fact. Do not call the entire
environment fresh because selected local inputs matched. The plan remains
read-only and must not infer safe exclusions from missing witnesses or graph data.

## Acceptance and delivery

Actual unrelated Python and CommonJS dependency exercises must establish:
unchanged source/HEAD/environment with changed dependency behavior; baseline
reuse gap; independent current check failure; repaired refusal to reuse; actual
new failed result; and unchanged witnessed inputs permitting legitimate reuse.
Record counters and every outcome. This is mechanism acceptance, not population
AI coding benefit, installed-host acceptance or a latency-improvement claim.

Add traversal, copied/tracked approvals, symlink/junction/hard-link, empty tree,
addition/deletion, metadata replacement, unreadable/special inputs, budget,
configuration drift, malformed saved state and old-reader compatibility controls.
CLI cold imports and reporting must preserve inspected source bytes. Export must
not leak known credentials, contents or private roots. Whole-attempt invalidation
must preserve every required command, aliases and fallback verification.

Push each qualified part. Perform one fresh whole-branch review and one repair
pass with witnessed failures. Final gates: full suite, named audits, independent
grader/source reproduction, doctor, stdlib imports, all four hosted cells,
actual dependency exercise, all five rendered architecture views and local links.
Update roadmap, guides, validation and journey 78. Fast-forward main normally,
preserve qualified runtime bytes, verify remote identity and published map bytes;
report automatic main repeats separately.
