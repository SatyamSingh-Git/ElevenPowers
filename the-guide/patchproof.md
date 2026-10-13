# PatchProof: the patch and its evidence

[External input witnesses](external-inputs.md) can qualify saved explicit
execution with selected approved dependency files and trees. Reports show current
collection separately from saved association; source-only receipt facts remain
visible when an external association becomes unavailable.

[GitHub presentation](patchproof-github.md) shares this read-only bundle through
an informational Actions summary and downloadable artifact, retaining exact
identities, failures, missing checks and coverage gaps. It runs no checks.

PatchProof v1 exports an exact committed Git base/head identity alongside existing
machine receipts. It helps a reviewer see what was checked, whether observed
inputs still match the checkout, and what remains unsupported or unobserved.
It runs independently of any coding host and works with any project using the
shared evidence runtime. Reporting runs no checks, installations or model calls.

```bash
python plugin/bin/ep_patchproof.py --project PATH --base HEAD~1 --head HEAD
python plugin/bin/ep_patchproof.py --project PATH --base BASE --head HEAD --format json --output bundle.json
python plugin/bin/ep_patchproof.py --project PATH --base BASE --head HEAD --require-bound
```

Defaults: current directory, direct `HEAD~1` to `HEAD` comparison, Markdown,
stdout and a 120-second cooperative deadline. `--timeout` accepts 0–600 seconds.
`--force` explicitly permits replacing an output file; otherwise publication
refuses overwrite atomically. Ordinary exit 0 means a bundle was produced, even
with unavailable binding. `--require-bound` exits 1 unless patch/input binding
qualifies. Invalid arguments or output failures exit nonzero. The binding gate
does not mean all checks passed, that work is verified, or that a patch is safe.

Patch identity requires **Git 2.45+**. Older/unknown versions cannot qualify the
lazy-fetch guard and report unavailable identity. Missing partial-clone objects
are never retrieved automatically; fetch needed objects explicitly in your normal
workflow before exporting again. Effective worktree filters and included filter
configurations are disabled along with lazy fetching and transport protocols.
See [the Git source and controls](../docs/research/patchproof-git.md).

Choose the repository root, including a linked worktree root. Subdirectories and
non-Git projects cannot qualify committed-patch identity. Refs resolve to full
commit IDs; comparison does not silently use merge-base semantics. The versioned
SHA-256 patch identity binds the commit pair; the content digest binds the full
base/head tree pair, including unchanged inputs. It is not a formatted diff hash.
Renames retain Git's heuristic similarity and both paths, modes and blob IDs.
Binary files retain identity without exposing contents. Empty patches remain
distinct from failed or incomplete collection.

Saved [declared OpenAPI observations](contracts.md) are now available in an
additive `contracts` section. Result, execution, freshness and exact-patch
association remain separate; compatibility outside those standalone specs is
unsupported. Ordinary bundle export never launches the checker.

Optional [ImpactGraph enrichment](patchproof-impact.md) adds patch-qualified
consumer paths and focused/fallback/support test candidates through `--impact`.
Graph recommendations remain separate from execution receipts and incomplete
semantic coverage stays visible.

[Explicit verification](patchproof-verification.md) adds a read-only `--plan`
and separate `--verify` execution path. Existing bundle export only reads saved
execution associations; new exact-head observations do not upgrade unknown
legacy provenance. All project-declared checks remain required, with incomplete
attempts and an explicit `--rerun` option when external inputs need refreshing.

## Reading the bundle

| Field | What it establishes |
|---|---|
| `patch` | Exact commits, trees, changed paths and collection qualifications. |
| `binding` | Whether the inspected checkout and report inputs qualify association with that committed head. |
| `receipts` | Original outcome, execution completeness and freshness, plus the changed paths in each recorded scope. |
| `checks` | Latest matching project-declared command observations; current, failed, stale, incomplete, no-tests or absent. |
| `verification` | The existing schema-1 task report, with its original verdict and obligations. |
| `contracts` | Declared standalone OpenAPI checks, saved producer/configuration/input identities and current qualifications. |
| `impact` | Optional fresh graph recommendations, exact patch/input identities and coverage qualifications; never passing evidence. |
| `execution` | Saved explicit command associations, freshly inspected exact heads and source/configuration/policy/producer/environment digests; legacy receipts retain unknown provenance. |
| `external_inputs` | Current required selected local file/tree collection, public fingerprints, root labels, budgets and gaps; not a substitute for matching saved execution association. |
| `coverage` | Changed paths without a qualified receipt association and unsupported compatibility categories. |

`bound` is an input association. A fresh failing or interrupted receipt can be
associated with the patch while still reporting failure or incomplete execution.
A passing unrelated check cannot associate with paths it never observed. Declared
check state uses the property's aggregate receipt kind; a passing individual test
cannot replace a failed suite, and timestamp ties use the later aggregate. No
active claim stays `UNVERIFIED`; passing receipts cannot invent task completion.
Check state and patch association are separate: an observed pass may be current
for its own inputs while patch association remains unavailable.

Checkout HEAD must match the requested head. Dirty tracked/index/nonignored
untracked files, hidden `assume-unchanged`/`skip-worktree` entries, configured
clean/process filters, linked inputs/submodules, incomplete scans and observed
changes during collection leave binding unavailable. Commit and tree identity
can still be useful. Working-tree patch identity is a later feature; do not
silently omit dirty changes. Ignored project configuration and receipt state are
also checked before/after collection. Ambient Git redirection/config injection
leaves legacy report enumeration unqualified. Local state read limits are 8 MiB
for the ledger and 1 MiB for configuration; Git output uses the shared 8 MiB cap.

## What it does not prove

This is an unsigned local evidence bundle. It does not establish authenticity,
unchanged external services, producer/environment versions that were never
recorded, or execution at the requested commit for legacy receipts. Separately
qualified explicit execution records retain their inspected head. Before/after bounded reads are
not an atomic snapshot and cannot detect transient changes that revert between
observations. Existing receipt fingerprint and source-selection limits remain.
Unknown API, database, security and behavioral compatibility stay unsupported;
no green suite certifies those properties. There is no patch safety percentage.

Exports reuse credential scrubbing, root substitution and escaped Markdown.
They exclude raw diffs, contents, prompts, transcripts, captured output and receipt
details. Inspect project metadata and command text before sharing: scrubbing
known credential formats is not a guarantee of anonymity.

The standard-library Python API is `core.patchproof.identity.collect` and
`core.patchproof.report.build`/`markdown`. Existing `ep_report.py` schema-1
consumers are unchanged. See [design](../docs/design/patchproof-v1.md),
[contributor next steps](../docs/design/patchproof-contributor-brief.md),
[dated validation](../docs/validation/2026-10-11-patchproof-v1.md) and
[journey 73](../journey/73-a-patch-needs-its-own-identity.md).
