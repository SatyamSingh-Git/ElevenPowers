# PatchProof contributor brief

Status: proposed contribution scope, 2026-10-04. PatchProof is not implemented.
This brief prepares work for a contributor; it records no new verification or
coding-benefit result.

## What is ready, and what is missing

ElevenPowers already records command outcomes and input freshness, exports
portable JSON/Markdown reports, and exposes a fresh ImpactGraph API. These are
enough to start PatchProof without waiting for every graph adapter or automatic
host integration. The missing connection is between a particular patch, the
inputs actually checked, the applicable properties, and explicit evidence gaps.

Build inside ElevenPowers first. Reuse the shared evidence, scanning, redaction
and output policies; keep the CLI and Python API usable without an AI host.
A separate repository would duplicate those policies before the interface is
stable. The full product is an architectural extension; the first contribution
below is a deliberately small part of it.

## Recommended first contribution: exact patch identity

Own a first PR that resolves a requested Git base/head range into a bounded,
read-only patch description. Proposed locations are
`core/patchproof/identity.py` and `tests/test_patchproof_identity.py`; those files
do not exist yet. Keep identity collection independent of report formatting and
check execution so the next PR can consume it without a second Git implementation.

The description should carry resolved commit identities, a content digest of the
chosen base-to-head patch, changed paths and change kinds, whether the checkout
matches the requested head, and explicit completeness issues. Use direct
base-to-head comparison; do not silently substitute merge-base semantics. If an
ancestor relationship is required, state and validate that policy explicitly.
Distinguish an empty patch from failed or truncated collection.

Collect Git facts without staging, refreshing the index, checking out files,
running project commands, invoking external diff/textconv helpers or starting
fsmonitor. Treat refs and paths as data passed in argument arrays; parse paths
without shell splitting. Bound elapsed time and captured output and report any
omission. Keep nested repositories, submodules, linked inputs, binary changes,
deletions and renames explicit; an unsupported item is a gap, not zero impact.

This first PR does not need to interpret API contracts or execute tests. Its
useful result is a stable patch description the evidence layer can bind to.

## Next contribution: a patch-bound evidence report

Wrap the existing portable report rather than replacing its schema or verdicts.
Proposed locations are `core/patchproof/report.py`,
`plugin/bin/ep_patchproof.py` and `tests/test_patchproof_report.py`. Agree the
versioned bundle schema in that PR. Existing `ep_report.py` behavior and its
schema-1 consumers must remain compatible.

Start with reporting a committed range. Associate current receipts only when
the requested head matches the checkout and the relevant inputs can be read
completely. Dirty or untracked inputs, another checked-out head, non-Git roots,
unavailable refs and concurrent changes must prevent an apparently clean
committed-patch binding. They may still produce a useful report with an explicit
unavailable/incomplete binding. Never silently discard dirty changes. A later
working-tree patch mode can support them with its own explicit content identity.

HEAD alone is insufficient. A receipt may have been recorded before that commit
but remain current for its declared observed bytes; conversely, a receipt at the
same HEAD can be stale after an edit. Preserve its actual scope, declaration,
fingerprint, result, execution completeness and current freshness. Do not claim
it executed at the requested commit unless that fact was recorded. Input
freshness does not establish an unchanged external service or environment;
missing producer/environment provenance stays unknown.

A report should explain which properties have evidence, which failed, and which
are absent, stale or incomplete. Preserve result, execution and freshness as
separate fields: a command can have an observed pass and still be stale. A
missing applicable check must remain visible. Recheck identity and relevant
inputs around report collection; a detected concurrent change invalidates the
binding. Bounded reads are not an atomic filesystem transaction.

Reporting executes no checks. A future explicit `verify` command can run
project-owned commands with recorded limits and environment identity after the
read-only bundle is reliable. The current process runner manages lifecycle and
output limits; it must not be advertised as a security sandbox.

## Subsequent independent PRs

| Contribution | Useful output | Boundary |
|---|---|---|
| ImpactGraph enrichment | Changed areas, explained consumer paths, focused/fallback/support test candidates and graph gaps in the bundle | Graph recommendations do not establish passing assertions, safe test exclusion or exhaustive blast radius. Compare graph and report input identities; do not combine incompatible fingerprints by assumption. |
| One contract receipt adapter | Applicable contract, real checker identity/version, exact inputs and configuration, result, limits and freshness | Choose one producer, run it before defining its output parser, and cover legitimate, incompatible and stale cases. An unsupported contract stays absent/unsupported. |
| Explicit verification execution | Project-declared checks with complete/pass, complete/fail and incomplete receipts | No model calls, command execution or installation during ordinary report creation. Preserve existing runner limits; stronger isolation needs a separate design. |
| GitHub presentation | A check summary and downloadable evidence bundle linked to the exact patch | Local unsigned receipts do not become independent attestation by being uploaded. Missing checks must not become a green safety badge. |

Build/type/test receipts are already reusable. API, database-schema, dependency,
security and behavioral compatibility each need their own applicability and
provenance rules. Do not promise all of them in the first PR or invent a single
percentage that claims the patch is safe.

## Acceptance controls

The identity PR should demonstrate these on disposable, independently created
repositories. Observe the relevant regression fail before implementing its fix.

- An ordinary committed change yields the requested full base/head identities
  and a reproducible patch digest; changing the range changes that identity.
- An empty range is reported as empty. Invalid refs, unavailable Git, exhausted
  budgets and failed collection are distinct incomplete/error observations.
- Spaces, Unicode and leading-dash path/ref inputs cannot change command meaning.
  Renames, deletions, binary changes and repository boundaries retain their
  actual qualification rather than disappearing.
- A different checkout, dirty index, dirty tracked input, untracked selected
  input or concurrent edit cannot qualify a clean committed-patch binding.
- Identity collection leaves index, refs and project files unchanged and invokes
  no repository-defined diff/textconv/fsmonitor command.

The report and adapter PRs add these controls:

- A real passing command appears with its observed input scope. A real failing
  command remains failed; timeout/interruption remains incomplete; no receipt
  remains absent. An empty claim set cannot become verified merely from a pass.
- Changing source, a declared command, relevant configuration or a relevant
  dependency input expires the corresponding evidence. If a dependency was not
  recorded, expose that coverage gap instead of inventing freshness.
- Old receipts and unrelated successful checks cannot satisfy a property outside
  their recorded scope. Incomplete scans and changed inputs invalidate binding.
- JSON and Markdown agree on patch identity and qualifications. Reports exclude
  prompts, transcripts and raw captured output, retain redaction, and refuse
  overwriting an output file unless explicitly requested.
- Run controls in at least two unrelated repositories, with supported Python and
  JavaScript command examples. Runtime logic contains no project-specific path,
  manifest name outside supported conventions, or hardcoded command.

## Reading and local workflow

Read [repository rules](../../CLAUDE.md), [the master plan](../../PLAN.md),
[portable report design](portable-report.md) and
[ImpactGraph interfaces and limits](impact-graph.md). The implementation entry
points are [the exporter](../../core/export.py),
[receipt/freshness model](../../core/evidence.py),
[portable report CLI](../../plugin/bin/ep_report.py),
[ImpactGraph API](../../core/impact/__init__.py),
[process runner](../../core/process.py) and
[report regression controls](../../tests/test_portable_report.py).

Use a fork/contribution branch such as `codex/patchproof-identity`, and make a
focused PR with its behavior, validation and limits. A suitable first commit
message is `Bind patch descriptions to exact Git base and head identities`.
Incremental commits should describe their changes rather than a numbered part.
Record any new dependencies, their licenses and the specific gap they fill;
prefer existing components and a standard-library core.

Run the focused tests during development. Before integration, run the required
regressions, update affected guides/status/design and the architecture views,
and run `python architecture/check.py --render`. New modules must be drawn in
the shipped graph only when they exist. Keep the
[PatchProof Planned card](https://satyamsingh-git.github.io/ElevenPowers/architecture/#planned/patch-proof)
honest about remaining work; add a journey and dated validation for delivered
behavior. Paid/model sessions require separate explicit authorization and are
unnecessary for these first contributions.

## What success establishes

The first useful milestone lets a reviewer identify the patch, inspect current
machine observations and see the checks still needed. Independent compatible,
incompatible and stale controls establish that the bundle distinguishes those
states. They do not establish universal patch safety or improved agent-written
code. Measure any later coding benefit against an ordinary workflow on the same
independent checks, preserving neutral, adverse and incomplete results.
