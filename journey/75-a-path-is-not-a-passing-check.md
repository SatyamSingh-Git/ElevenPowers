# 75 — a path is not a passing check

2026-10-12

PatchProof could say which exact patch a receipt described. ImpactGraph could
explain who might depend on a changed file. Connecting them adds something useful
for a reviewer, provided the connection does not turn a recommendation into a
passing test or a claim that omitted relationships are safe.

The first producer exercise used a Python session function, an actual consumer,
a specifically calling test and a broader import-only test. The graph recovered
the consumer and focused/fallback distinction. An unrelated JavaScript project
declared a checkout route and its test; those witnesses stayed labelled as project
assertions. Both use the same integration without any named-project behavior.

Two fresh graph scans compare complete input/declaration selection, graph content,
policy, runtime identity and comparable verification fingerprints. Final patch
qualification remains mandatory. Semantic gaps can coexist with matching input
association: deleted paths, unknown dispatch and bounded queries stay incomplete.
The ordinary report avoids these scans; `--impact` selects them explicitly.

Two controls caught mistakes during implementation. An ignored command
configuration could change after the original report guard while graph collection
ran. The binding stayed green until the guard was extended through the scans.
And a declared graph label could become an active Markdown link. The renderer now
uses the existing exporter's literal escaping; JSON values retain their identity.
The first label test accidentally queried only the changed declaration, so it
did not exercise the affected label. Correcting the requested range exposed the
actual link before the fix. A test expectation is not evidence until the relevant
path and failure are observed.

No tests or models run during export, no recommendation becomes a receipt, and
broader declared checks remain intact. The next milestone is explicit bounded
verification planning/execution, with unsigned evidence and limits preserved.
This work explains existing evidence; it does not establish improved coding
correctness or speed. See [validation](../docs/validation/2026-10-12-patchproof-impact.md)
and [guide](../the-guide/patchproof-impact.md).

The fresh reviewer then found a third identity gap: changing `info/exclude`
without changing selected files escaped both graph hashes. Five controls for
local, configured/default global, ignored nested rules and excessive bytes
failed before repair. Selection policy now has its own bounded identity across
verification and graph collection. Effective Git config and applicable rule
bytes are hashed locally; exported evidence contains neither their bodies nor
external paths. Equal observed source bytes do not imply equal selection policy.

Full-suite qualification caught one remaining old Markdown assertion that the
focused renderer checks had not included. It expected raw underscores/dots,
although the candidates were present as escaped literal text. The same failure
reproduced locally and in both Linux jobs. The assertion now checks literal
content, retaining the focused/fallback requirement; no runtime bytes changed.
The initial full run was replaced with a fresh run of all checks.
