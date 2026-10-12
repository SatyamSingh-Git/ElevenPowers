# PatchProof impact enrichment

The approved milestone connects existing ImpactGraph explanations to an exact
PatchProof patch. It must work for any repository and host, keep recommendations
separate from execution evidence, and never infer safety from missing paths.

## Design

Add opt-in `ep_patchproof.py --impact`, and `build(..., impact=False)` to the
existing API. The default report remains unchanged in cost. An additive `impact`
section identifies the exact commit pair, full tree-pair digest, graph input
fingerprint, query policy and current runtime fingerprint. No saved foreign graph
is accepted: two fresh scans of the chosen root avoid cross-project cache reuse.
Use existing `core.impact.build`, `analyze` and test selection without inventing
another graph or claiming predicted failures.

Each scan uses the project's existing scan policy and declarations, default
Python/tree-sitter adapters and no compiler, external observation or history
option in this first integration. Compare full graph snapshots (including
relationships and policy-bound source fingerprint), comparable evidence source
fingerprints against both verification reads, complete input/declaration
selection and final patch/checkout qualification. Global receipt binding stays
separate: incomplete semantic impact coverage does not invalidate other receipts.
If any association check fails, impact association is unavailable; diagnostic
recommendations can still be displayed but must be labelled unqualified.

## Bounds and outputs

Use the existing bundle deadline, at most 30 seconds per graph scan, 256 unique
changed/previous rename paths, depth 6 and 100 query results. Deleted, unsupported
or excluded paths stay query gaps; omitted paths stay explicit. Empty patches
produce no query and no affected-behavior claim. Preserve explained affected
nodes, focused/fallback/support candidates, coverage issues and existing graph
limits in JSON and Markdown. Candidates are recommendations, never added as
execution receipts, never remove project-declared checks and never certify
assertion coverage. No checks, project source, compiler or model calls run; no
state is written except explicitly requested exported files.

## Validation and limits

Independently author Python consumers/tests and unrelated JavaScript declared
relationships, then assert expected witness paths in the actual bundle. Exercise
dirty/wrong-head/changed source and declaration, truncated query, unsupported
adapter, empty/deleted/rename paths, expired budget and disabled mode. Substitution
controls instrument the producer boundary only to introduce observable races or
incompatible fingerprints. Fresh graph snapshots are bounded before/after reads,
not atomic snapshots; unsigned declarations and local evidence remain unsigned.
No improvement in coding correctness or speed is claimed by this integration.

Borrow existing ElevenPowers graph, selection, Git identity and portable export
components under the repository license; add patch-qualified composition only.

## Review repair: selection policy

`core/patchproof/policy.py` reuses bounded Git metadata reads and SHA-256.
The source enumerator inherits effective global/system Git configuration, so
the witness reads that same environment, hashes effective configuration and
local/configured/default global excludes, and walks active directories for
`.gitignore` files even when the filename itself is ignored. Git identifies
wholly ignored directories to prune; nested repositories/runtime state remain
separate. Limits: 1 MiB per rule, 8 MiB total, 20,000 directories, shared deadline.
Warnings, links, unreadable inputs and limits leave qualification unavailable.
Policy identity is compared before verification, around both graph reads and
after their final state guard. Only hashes are exported. This is conservative
selection-policy qualification, not authenticity or an atomic snapshot.

Configured global exclude filenames use actual NUL-delimited Git path output;
leading spaces in relative filenames remain significant. Trimming path text
would inspect a different policy file and cannot qualify association.
