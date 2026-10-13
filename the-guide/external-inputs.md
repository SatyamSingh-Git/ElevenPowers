# External input witnesses

External Input Witnesses v1 extends explicit PatchProof verification and reuse
to selected local dependency/tool files. A dependency can change at the same
path while source, HEAD, lockfiles and environment values remain unchanged.
With declarations and local approval, such a change prevents reuse of an older
passing execution and schedules the required checks again.

This is shared, language-independent core behavior for any eligible Git project.
The initial integration is PatchProof; native passive receipt capture and
milestone invalidation do not yet consume these witnesses. Existing source-only
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

No separate capture command is required. All declared witnesses are required for
the attempt as a whole. Complete unchanged observations can qualify reuse;
changed bytes, filenames, directory structure, additions/deletions, declaration or binding identity
prevent reuse. Missing approval, empty selected scope, unreadable inputs or
partial inspection leave the plan incomplete and block launch/reuse. Changes
during execution preserve the result as stale/incomplete and defer later work.
Final source, checkout, configuration and ignore-policy guards extend through
collection; a persistent edit during the scan prevents reuse or launch.

The original receipt outcome is retained. A historical pass is not rewritten to
a failed command. Source-only receipt states may remain current while saved
external execution association is unavailable. Earlier eight-field execution
witnesses remain readable; they cannot acquire a newly required external
observation. Without declarations, their existing semantics remain unchanged.
The new optional fingerprint does not certify every installed dependency.

## Budgets, output and limits

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
