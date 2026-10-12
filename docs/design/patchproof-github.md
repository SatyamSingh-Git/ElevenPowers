# GitHub presentation for qualified PatchProof evidence

Approved purpose, 2026-10-13: reviewers should find the existing exact-patch
evidence, missing checks and qualifications in GitHub, for any eligible project.
The user requested inline implementation, frequent meaningful pushes, final
documentation/architecture updates and all code on main.

This is an architectural extension with a bounded first delivery: a portable
CLI, a composite GitHub Action and a real hosted summary/artifact exercise.
Reports execute no project checks. Installation, publishing and rendering do not
implicitly run verification or a model. Existing PatchProof schemas and verdicts
stay unchanged. Commands continue to be declared by the project.

## Approach and borrowed components

Use Actions job summaries and `actions/upload-artifact@v4` (MIT), the existing
PatchProof report and export/redaction code (repository Apache-2.0), and Python
standard-library filesystem/JSON/HTML helpers. Add a GitHub presentation envelope,
bounded human summary and transport integration, not another evidence producer.
GitHub documents the summary file and PR head semantics:
[summaries](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#adding-a-job-summary),
[PR subjects](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request),
[uploader](https://github.com/actions/upload-artifact/tree/v4).

Alternative direct Check Runs/PR-comment publishing requires write permission
and lifecycle ownership. A standalone saved-JSON renderer would need a new
untrusted-bundle validation/trust contract. Those are subsequent adapters. This
delivery freshly builds the existing read-only bundle from the selected checkout,
then writes an informational summary and downloadable envelope. It needs no
GitHub token for local use, no comments, and no `checks:write` permission.

## Execution baseline defect

The automatic main repeat at `9c713a1` failed the actual creation-handoff survival
assertion on Windows/Python 3.11 and 3.13; Linux passed. The preceding final-code
matrix remains historical passing evidence, not a replacement for the repeat.
An actual local 20-attempt probe reproduced a cached exit code with an unsignalled
process handle. Python's Windows terminate recovery can cache an exit code after
access denied while asynchronous termination is finishing; its cached `wait()`
does not wait on the kernel object. Require the original Windows process handle
to signal within the remaining existing five-second cleanup allowance. Keep
POSIX behavior, survival assertions and deadlines unchanged. This established
boundary is separate from older unexplained cleanup/launcher/SQLite incidents.

## Components and interfaces

- `core/process.py`: finish bounded reaping against the original Windows handle.
- `core/patchproof/github.py`: `build(root, base, head, *, repository,
  event=None, timeout=120, impact=False)` calls existing report collection and
  returns schema-1 `patchproof_github` with declared repository, exact patch IDs,
  inspected qualifications and the unchanged portable bundle. It performs no
  network request and no project-command execution.
- `core/patchproof/github_context.py`: validate declared repository and optional
  bounded GitHub event snapshot. PR events require the base repository and exact
  base/head commit IDs; the fork head repository remains separate. A synthetic
  merge commit cannot substitute for PR head. Local/dispatch context is explicitly
  declared; repository ownership and event authenticity are not independently
  attested. `artifact_link(repository, run_id, url)` accepts only the uploader's
  canonical HTTPS github.com repository/run/artifact URL.
- `core/patchproof/github_output.py`: bounded summary rendering and publication
  files. `publish(value, destination=None, *, project)` writes `evidence.json` and `summary.md`
  in a new directory outside the inspected project, with no overwrite. All hashes
  describe canonical public JSON, not captured outputs or an attestation.
- `plugin/bin/ep_github.py`: portable CLI for generation and explicit Actions
  summary/output-file writing; a separate link mode writes the actual upload URL.
- `github/patchproof/action.yml`: caller-owned project checkout and pinned trusted
  runtime, Python 3.11+, no installs, no `pull_request_target`, no secrets/write
  permission. Generate, upload exact files, then append a validated download link.
- `eval/github_presentation.py`: disposable committed Python project, actual
  independently expected assertion, complete/failed/incomplete observations and
  before/after read-only checks. It prepares hosted acceptance inputs, not product
  verification invoked by presentation.

## Presentation and identity

The summary leads with **informational evidence export, not patch safety** and
full base/head/patch IDs. It preserves declared-check states, receipt outcome,
execution, freshness and association separately; saved associations describe
the inspection time. Missing declarations, unsupported properties, unobserved
paths, contract gaps and graph limitations remain visible. Current task verdicts
do not become a universal safety conclusion. No percentage or invented passing
check is emitted. A successful Action means presentation/transport completed;
projects should not configure that informational job as a correctness gate.

Untrusted names/commands/paths are escaped as literal GFM text. Row/text omissions
are counted and point to the full artifact. Unknown or absent evidence cannot
be hidden behind an otherwise valid export. Optional impact uses the existing
bounded snapshot qualifications; it never excludes checks. Source files and
private prompts/transcripts/outputs are not uploaded. Known credential scrubbing
is defense in depth, not a guarantee against every secret format.

## Bounds, outputs and trust

Existing report timeout: default 120, finite 0–600 seconds. Optional event JSON
is at most 2 MiB, rejects duplicate keys, non-finite numbers and excessive/deep
input. Artifact JSON is at most 8 MiB; summary at most 64 KiB, below GitHub's
1 MiB step allowance. Render at most 64 rows per category and 384 characters per
free-text cell, with explicit omissions and compact fallback if needed.
Output directories are new, unlinked and outside the inspected project; filenames
are fixed. Publication does not change project state. Actions file writing is
explicit (`--actions`); local generation never touches runner environment files.
Existing runner targets and opened descriptors must have exactly one hard link;
preflight validates distinct external bounded regular files. The CLI suppresses
bytecode before imports and the Action uses isolated Python with `-B`, preserving
cold vendored checkouts. Public-only redaction covers dictionary keys and values;
colliding scrubbed keys are a controlled refusal, never silent record loss.
Private ledger/configuration identities are not rewritten. Hostile concurrent
parent replacement and an atomic filesystem transaction are not qualified.
Uploader links are appended only after successful upload and checked against the
declared repository and run ID. Artifact retention/login requirements remain
GitHub conditions; upload hashes do not sign the local evidence.

Exit 0 means a valid presentation was generated, including missing/unavailable
evidence. Invalid context, unreadable event, output failure or malformed identity
returns nonzero with controlled diagnostics. No new completion gate is introduced.
The v4 cloud uploader does not qualify GitHub Enterprise Server support.

## Acceptance

Reproduce the cleanup fault before repair; retain both original CI failures and
kernel-state observations. Test unrelated real Python and JavaScript projects,
absent/failed/stale/incomplete results, exact PR/fork/merge identities, literal
Markdown, size/omission bounds, no-overwrite/unlinked output and byte-for-byte
unchanged project state. Run a real hosted Action, inspect summary and artifact
metadata, download and independently verify its JSON/content hash. Model-free
controls establish presentation and recovery, not AI coding benefit. Full suite,
named audits, independent grader, doctor, rendered architecture and hosted matrix
are final gates, with all historical failures and limits retained.

Delivered controls and actual cloud artifact observations are recorded in
[dated validation](../validation/2026-10-13-github-evidence.md). Broader live PR/
fork publication, additional producers and external-input witnesses remain
separate work; informational export is not authenticated CI import.
