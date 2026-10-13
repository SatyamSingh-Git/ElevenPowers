# GitHub evidence presentation

[Declared external inputs](external-inputs.md) appear as current collection,
root labels and selected fingerprints alongside saved execution qualifications.
Successful current collection cannot replace absent or unavailable execution
association. Source-only receipt facts and unobserved environment gaps remain
visible; the public bundle contains no approved absolute root paths or input bytes.

PatchProof can present a fresh, read-only evidence bundle in an Actions job
summary and upload its JSON and Markdown files. It keeps exact patch identity,
check outcomes, input freshness and coverage gaps visible. A successful export
means the presentation was produced; it does **not** certify patch safety.

This works for any eligible Git project. The project owns its commands and
receipts; the presentation never runs project checks, installs dependencies or
calls a model. To create new receipts, use the separately explicit
[verification workflow](patchproof-verification.md) before presenting them.

## Local use

```sh
python -I -B ElevenPowers/plugin/bin/ep_github.py --project PROJECT \
  --repository OWNER/REPOSITORY --base BASE --head HEAD \
  --output-dir NEW_EXTERNAL_DIRECTORY
```

Use Python 3.11 or newer and Git. The runtime needs only the standard library.
The destination must be a new directory outside the inspected project, with an
existing parent and no linked path components. Omit `--output-dir` to create a
new external temporary directory. Existing output is never overwritten.
The fixed files are `evidence.json` and `summary.md`. Standard output is JSON
containing their paths, the artifact name, canonical bundle digest and patch ID.

`--base` defaults to `HEAD~1`, `--head` to `HEAD`, `--timeout` to 120 seconds
(finite 0–600). `--impact` includes advisory graph enrichment without running
checks. `--event EVENT_JSON` validates declared GitHub context: a PR's base and
head must match the requested commits, including a fork's separately declared
head repository. The synthetic merge SHA is not silently substituted for the
PR head. Wrong subjects are refused. Missing patch inputs remain unavailable.
Exit 0 means an informational export; invalid context or publication exits 2.

## Reusable GitHub cloud Action

Check out the desired project head and make the base commit available. Use a
trusted immutable ElevenPowers revision; never run an Action implementation from
an untrusted PR checkout. This example pins the delivered Action revision and
uses the PR's explicit base/head rather than the workflow merge commit:

```yaml
name: Patch evidence
on: pull_request
permissions:
  contents: read
jobs:
  evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          fetch-depth: 0
          persist-credentials: false
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      # Explicitly obtain project-owned receipts in a trusted workflow if wanted.
      # A fresh CI checkout otherwise correctly reports absent evidence.
      - uses: SatyamSingh-Git/ElevenPowers/github/patchproof@b7627614dcc48ed048ba1647aedbadd433cd346f
        with:
          project: '.'
          base: ${{ github.event.pull_request.base.sha }}
          head: ${{ github.event.pull_request.head.sha }}
          retention-days: '7'
```

The pinned revision includes the runtime and review repairs; its final
qualification is recorded in the [delivery record](../docs/validation/2026-10-13-github-evidence.md).
Pin checkout and Python setup according to your repository's policy too.
For fork PRs, ensure the requested base object is available; a missing object is
an explicit collection gap. This milestone qualified actual hosted transport in
a disposable declared context and PR-shaped subject controls. It did not run a
live fork/PR publication session.

Inputs are `project`, required `base`/`head`, optional `repository` (caller
repository by default), `seconds`, `impact` (`true` or `false`) and
`retention-days`. Outputs are `artifact-url`, `artifact-digest`,
`bundle-sha256` and `evidence-directory`. The uploader's archive digest and the
canonical JSON bundle digest identify different bytes. The pinned official
MIT-licensed v4 uploader needs GitHub cloud; GitHub Enterprise Server is not
supported by that uploader. Download links require appropriate login and remain
subject to artifact retention.

The Action reads `GITHUB_EVENT_PATH`, explicitly appends to runner-provided
summary/output files, uploads only the two public files and attaches the
validated download link. It uses no write token, PR comment or Check Run
publisher. Keep this informational job separate from your correctness gates and
branch protection: absent or failed evidence may still export successfully.

## Direct Actions file mode and link mode

`--actions` explicitly enables `GITHUB_STEP_SUMMARY` and `GITHUB_OUTPUT` writes.
Targets must be distinct, bounded regular files outside inspected source, with
unlinked paths and exactly one hard link. Opened descriptors are checked again
before appending. Without this flag, these environment files are untouched.

After an upload, attach its URL without collecting a second bundle:

```sh
python -I -B ElevenPowers/plugin/bin/ep_github.py --project PROJECT \
  --repository OWNER/REPOSITORY --actions --run-id RUN_ID \
  --link-artifact https://github.com/OWNER/REPOSITORY/actions/runs/RUN_ID/artifacts/ARTIFACT_ID
```

Only the canonical HTTPS URL for the declared repository and run is accepted;
query strings, fragments, foreign repositories/runs and credentials are refused.
Link mode cannot be combined with event collection, impact or new output.
Cold CLI imports suppress bytecode even with Python isolated mode.

## Evidence and trust limits

The envelope contains the unchanged PatchProof bundle, declared subject and a
SHA-256 of its canonical public JSON. Public exports scrub known credential
formats in keys and values; colliding redacted keys cause controlled refusal
instead of losing a record. Private configuration and ledger identities stay
unchanged. Raw diffs, source contents, prompts, transcripts and captured command
outputs are excluded. Scrubbing is not universal secret detection; review
project command text before sharing it.

The event read is limited to 2 MiB; duplicate keys, excessive nesting and
non-finite values are rejected. JSON output is limited to 8 MiB. The summary is
limited to 64 KiB, 64 rows per category and 384 characters per free-text cell.
Escaping makes command text literal; omissions and truncations are named. Full
patch identities, check-state counts and coverage counts survive fallback. The
artifact retains the complete accepted bundle, not just the displayed rows.

Repository/event names are declared context, not independent authentication or
ownership attestation. A matching hash detects byte changes against that hash;
an author could replace both payload and hash. Upload success does not create
new passing receipts. Freshness applies to observed inputs at collection time,
not to later edits, remote services or unrecorded environment changes.
Before/after reads are not an atomic snapshot. The execution runner manages
lifecycle; it is not a security sandbox for untrusted project commands.

See [design](../docs/design/patchproof-github.md),
[qualification](../docs/validation/2026-10-13-github-evidence.md) and
[journey 77](../journey/77-the-upload-is-not-the-evidence.md).
