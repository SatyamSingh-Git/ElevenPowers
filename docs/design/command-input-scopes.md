# Command-scoped inputs and shared collection

Projects may opt into schema 2 of `elevenpowers.inputs.json`. Its optional
`commands` list contains exact declared `command` strings, a nonempty list of
`witnesses` IDs, and an explicit Boolean `complete`. At most 64 mappings are
allowed. Identities that redact are refused, since distinct secret-bearing
commands can collapse to the same public identity. A complete mapping selects its witnesses; an incomplete or unmatched
mapping retains every witness. Only the existing parser's declared command
identity licenses narrowing. No dependency graph or missing edge licenses it.

New receipts carry the selected command digest, witness IDs and per-witness digests alongside paired
fingerprints. Scoped fingerprints include selected witness definitions, approved
root identities and effective budgets. Unrelated declaration edits do not expire
a scoped association, but selected edits, rebinding, command/scope changes and
missing observations do. Schema 1 receipts remain broad and are never narrowed
retrospectively. Source, configuration, producer and task guards remain separate.

Collection observes a bounded union with one aggregate budget. Available witness
rows can qualify an explicit scope even when a different row is unavailable;
structural declaration/approval failures and closing collection races remain
conservative. Public outputs contain labels and digests, never approved paths.

An operation-local context shares external opening and closing observations
across nested PatchProof, ordinary and milestone reports. It never shares source
snapshots, execution observations, project roots, or results across operations.
The closing phase reads bytes again. Unchanged bundles should read each selected
file twice, rather than the eight reads observed in the previous milestone.
After nested consumers, a bounded stamp/declaration/approval guard checks for
persistent late movement without a third byte read. This is sampling, not an
atomic snapshot; undetectable reverted or deliberately hidden changes remain out
of scope. An opaque final-state failure conservatively invalidates associations.

Acceptance uses real Python and JavaScript consumers with two independently
selected inputs, command counters, broad fallback, source controls, relevant and
irrelevant drift, missing inputs and closing races. Installed sessions require
a new explicit allowance. Neither a project assertion nor these exercises proves
complete environment coverage, atomic execution, safety, or population benefit.
