# ImpactGraph inside PatchProof

The [verification planner](patchproof-verification.md) can include this advisory
view through `--plan --impact`. Explicit execution preserves all declared checks;
candidate paths never generate shell commands or justify safe exclusions.
Graph scans share the selected operation's budget and may leave it incomplete.

Export possible effects and relevant test candidates alongside exact patch
evidence, for any repository using the shared runtime:

```sh
python plugin/bin/ep_patchproof.py --project PATH --base BASE --head HEAD --impact
python plugin/bin/ep_patchproof.py --project PATH --impact --format json --output bundle.json
```

`--impact` is explicit. Without it, no graph scan runs and the additive `impact`
section says `not_requested`. Neither mode runs tests, project code, a compiler,
installation or a model. Export writes only the requested output file, under the
existing overwrite policy. This does not add a host-specific completion gate.

## Reading the recommendations

The section contains the exact patch identity and full tree-pair digest, current
runtime fingerprint, graph input and snapshot digests and the bounded query
configuration and repository-policy fingerprint. Two fresh scans of the chosen root are compared against each
other and both verification reads; final patch and ignored state guards qualify
the association. Effective Git configuration, local `info/exclude`, configured
or default global excludes and nested rules in active directories are inspected
across the whole collection window, even when selected bytes stay unchanged.
No saved or foreign graph is accepted.

`association: bound` means these graph recommendations qualify for the inspected
patch/current inputs. It does not mean exhaustive impact coverage, that a test
passed, or that the patch is safe. `state: incomplete` may coexist with bound
inputs when semantic adapters or query scope have gaps. Unavailable association
can retain diagnostic recommendations, explicitly labelled unqualified in
Markdown. Existing receipts and declared checks remain separate.

| Query field | How to use it |
|---|---|
| `affected` | Possible consumers/components, with dependent-to-dependency witnesses and static/declared origins. |
| `test_selection.focused` | Tests with more specific relationship paths; recommendations to consider. |
| `test_selection.fallback` | Broader candidate tests retained when a focused witness is absent. |
| `test_selection.support` | Supporting files such as fixture helpers; not standalone runnable tests. |
| `coverage` | Selection, input, adapter and query completeness, plus unresolved or bounded-out relationships. |

All explanation edges, candidate groups and qualifications are available in
JSON and Markdown. Candidate tests never become execution receipts. Missing
paths never justify removing fallback candidates or skipping project-declared
checks. Semantic functionality names appear only when existing adapters or
project-owned [declarations](impactgraph.md) supply them; the integration does
not invent endpoint or database behavior.

## Limits

The total existing bundle deadline defaults to 120 seconds (`--timeout 0–600`).
Each graph scan uses up to 30 remaining seconds. Up to 256 unique changed and
previous rename paths are queried, depth 6 and 100 results; omissions and query
limits stay explicit. An empty patch has no query. The graph describes current
head inputs, so removed and old rename paths are gaps, not reconstructed base
dependencies. No path is silently dropped from patch identity or receipt scope.

Default Python and optional installed tree-sitter adapters plus project-owned
`impactgraph.json` apply. Missing JS grammars and other language adapters remain
gaps. This first integration does not select a TypeScript compiler, external
observation artifact or Git history. Use the standalone ImpactGraph CLI for those
options. The project's existing scan policy and repository boundaries apply. The runtime
fingerprint covers ElevenPowers source; installed parser packages and the
execution environment are not independently certified.

Policy inspection refuses linked/unreadable inputs, warnings, 1 MiB per rule
file, 8 MiB total rule bytes, 20,000 visited directories or the shared deadline.
Wholly ignored directories are identified by Git and pruned; their nested rules
cannot re-include children while the parent remains ignored. Raw rule/config
bodies and external paths are hashed locally and excluded from exports.

Two snapshots and state guards are bounded reads, not an atomic transaction;
transient reverted changes cannot be detected. Local declarations and evidence
are unsigned. Runtime changes require new qualification; historical installed
sessions are not requalified by this model-free integration.

See [design](../docs/design/patchproof-impact.md), [PatchProof](patchproof.md),
[ImpactGraph](impactgraph.md) and [dated validation](../docs/validation/2026-10-12-patchproof-impact.md).
