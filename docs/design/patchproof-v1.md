# PatchProof v1: exact patches and qualified receipts

Approved scope: the user's 2026-10-11 instruction starts implementation of the
existing contributor brief: exact committed patch identity, binding to existing
receipts, and a portable evidence bundle. This extends the shared runtime inside
ElevenPowers, independently of any coding host or particular repository.

## Design decision

Use Git's own object identities and raw tree comparison, plus the existing
exporter, fingerprint model, redaction and atomic output writer. Git (GPL-2.0)
already defines tree contents, modes and object identities; we add a bounded,
read-only description and conservative association with current receipts.
Do not duplicate the portable report schema, introduce a separate repository,
execute checks automatically, or treat an LLM opinion as evidence.

`collect(root, base, head, seconds=30)` resolves full commit and tree identities.
Comparison is direct base-to-head, not an implicit merge base. A versioned SHA-256
identity binds the resolved commit pair; a separate content digest binds the full
tree pair (including unchanged inputs). It is not a hash of a formatted diff.
An identical empty tree pair is explicitly empty. Invalid refs, absent Git,
unsupported roots and exceeded output/time budgets produce unavailable or
incomplete descriptions, never an empty successful patch.

Git 2.45+ is required for the lazy-fetch prohibition; older/unknown versions
produce unavailable identity rather than relying on an unverified setting.
Git is invoked with argument arrays, no shell, optional locks disabled and
external diff, textconv, fsmonitor and effective clean/process filters disabled,
including worktree configuration and includes. Lazy object fetching and transport
protocols are disabled; unavailable local objects stay incomplete.
Raw NUL-delimited output preserves path boundaries. Git's rename detection is
heuristic; modes and old/new blob IDs remain authoritative. Submodules and
symlinks are explicit unsupported binding inputs. Binary blobs retain object
identity without exporting contents. Ref inputs beginning with a dash cannot
become options. The selected project must be the repository root; linked
worktrees are supported, nested project roots are qualified unavailable.

## Bundle contract

`build(root, base='HEAD~1', head='HEAD', timeout=120)` returns a new schema-1
PatchProof bundle containing the unchanged schema-1 portable report. It describes
patch identity, binding state, per-receipt applicability and qualifications, and
project-declared aggregate check availability. Child test observations cannot
replace a failed suite; timestamp ties prefer the later retained aggregate.
Result, execution and freshness remain
separate fields. Failed or incomplete commands are never turned into passes.
No active claim remains unverified even if a current receipt exists.

Binding requires complete patch collection, checkout HEAD equal to requested
head, a clean tracked/index/nonignored-untracked checkout, complete report input
coverage, and unchanged identity, ledger/configuration and fresh report inputs
across collection. Each receipt also needs current fresh nonempty observed input
coverage. Explicit-path receipts only relate to changed paths they observed;
source receipts are qualified against the existing selected-source policy.
Missing/deleted/unobserved patch paths remain visible. A receipt's association
means its recorded inputs still match this checkout, not that it executed at
the requested commit or proves compatibility of every changed feature.

The report includes absent declared commands and explicit unsupported API,
database, security and behavioral compatibility categories. Unknown applicability
is not a missing mandatory command or a green check. No percentage claims safety.
Producer/environment provenance not recorded by existing receipts stays unknown.
Ignored or excluded dependencies and external services are not certified.
These are unsigned local observations; hashes identify content, not authenticity.
Bounded before/after reads detect observed changes, not atomic filesystem snapshots
or transient changes that revert between observations.

## User interface and privacy

`python plugin/bin/ep_patchproof.py --project PATH --base BASE --head HEAD`
prints Markdown; `--format json --output bundle.json` exports the bundle.
`--force` permits replacement and `--require-bound` gates only binding, not safety
or completed work. Unsupported/incomplete collection still exports useful gaps.
Use existing credential scrubbing, root substitution, escaped Markdown and atomic
no-overwrite publication. Exclude raw diffs, file contents, prompts, transcripts,
captured output and receipt details. No host callback or completion gate changes.

## Qualification and subsequent work

Controls use disposable Git repositories with real Python and Node commands,
valid/failing/incomplete/absent receipts, committed and dirty states, ref changes,
renames/deletions/binary/symlink/submodule boundaries, unsafe refs, deadlines,
moving inputs, redaction and output refusal. Existing export consumers remain
unchanged. Use focused regressions during development, a whole-branch review and
the required full regression/host/architecture checks before integration.

The ordinary-session milestone retains two successful Claude Code installed
cells at its recorded runtime fingerprint. PatchProof changes the runtime, so
those successes are historical until requalified; eight other host/language cells
remain open. Advice consumption and causal coding benefit remain unproven. The
previous intermittent Linux descendant-cleanup CI failure is unresolved and
must not be described as repaired by PatchProof. No model sessions are needed.

Next independent contributions: compatible ImpactGraph enrichment, one real
contract adapter, explicit bounded project verification, then GitHub presentation.
Working-tree patch identity and stronger environment/attestation contracts need
separate designs. Read [the contributor brief](patchproof-contributor-brief.md).
