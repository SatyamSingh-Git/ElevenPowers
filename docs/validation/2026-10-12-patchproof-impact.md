# PatchProof impact validation — 2026-10-12

Scope: generalized, opt-in composition of fresh default ImpactGraph explanations
and exact patch/receipt evidence. No model calls or installed acceptance sessions.

Development controls:

- Observed the actual graph producer before writing the integration contract.
- Seven adapter controls failed against the absent module, then passed in 17.36s.
- Existing graph query/selection and patch identity checks passed 37 in 37.86s.
- Three missing bundle/CLI controls failed before implementation; combined new
  and existing PatchProof checks then passed 31 in 112.76s.
- Expanded real Python and unrelated JavaScript controls passed 18 in 58.47s.
  Explicitly ignored project configuration exposed a collection-window defect:
  a graph-time command change left the prior bundle binding qualified. The new
  end-of-graph state guard repaired the observed RED case.
- A project-declared label on an actual affected path rendered as a Markdown
  link. Literal escaping now reuses the portable exporter for both graph CLIs;
  display assertions use escaped text, with no change to JSON path identities.

Final review/full/hosted results are recorded below when completed. Historical
installed cells, correctness ties and unexplained cleanup/SQLite observations
remain dated; none are requalified or repaired by representation of graph leads.
