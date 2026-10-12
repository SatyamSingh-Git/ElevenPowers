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

Before final review repairs: 33 integration and graph presentation checks passed
in 66.46s; 107 named audit probes passed in 93.35s. Standard-library imports,
11 host probes, four independent grader controls and preserved source grades
passed. Architecture 144 nodes/341 edges, all five views rendered; 463 local
documentation targets resolved. Final repaired qualification follows below.

One independent whole-branch review found one Important ignore-policy identity
gap and no Critical/Minor findings. Five actual policy controls failed before
repair; the single repair pass then passed all 24 integration checks in 111.03s.
The policy witness covers unchanged-selection local, configured/default global
and ignored nested rules and refuses excessive policy bytes. No re-review or
model session was run. Final full and hosted qualification follows below.

The separate final review regressions passed 5 in 26.03s. A real read of
ElevenPowers at `5d04ec5` selected 1,456 files and read 1,455: receipt binding
remained bound while impact stayed unavailable/incomplete because a tracked
coverage artifact exceeds the existing 4 MiB per-file limit and queries retain
semantic gaps. Sixty affected nodes and 33 fallback tests remain diagnostic.
The 31.315s wall time was observed alongside tests, not a latency benchmark.
[Saved identities and counts](../../results/patchproof-impact/observations.json)
retain the producing snapshot; later source-selected docs change current inputs.

At the repaired runtime, 107 named audit probes passed in 85.71s, all 11 host
probes passed, all four independent grader cases were correct and preserved
stage-one 6/6 and final 8/8 ties reproduced without rerunning native sessions.
A separate JavaScript export under `python -S` (optional parsers unavailable)
returned bound input association and incomplete semantic coverage with explicit
missing-grammar issues. Its 5.26s local read is descriptive, not a benchmark.

The initial hosted matrix at `5d04ec5` exposed one old display assertion in
`test_markdown_explains_focused_fallback_and_support_without_hiding_them`: it
expected raw filenames after the renderer began escaping them. Linux 3.11
reported 1 failed, 2,081 passed and 7 skipped; the same assertion failed locally.
The test now checks the same candidates using literal Markdown text. Runtime
bytes did not change. The initial local full run was stopped after that known
assertion failed; a fresh complete run uses the corrected expectation. Neither
this repair nor later green CI resolves earlier unrelated cleanup/SQLite causes.

The corrected matrix at `ce6c3a1` passed Linux 3.11, but its first Linux 3.13
job reported `test_keyboard_interrupt_cleans_tree_before_reraising` with a
surviving descendant (1 failed, 2,081 passed, 7 skipped). See the
[retained job](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38230608648/job/114748864830).
The root cause remains unknown; this is a recurrence in the earlier recorded
POSIX cleanup area, not a demonstrated integration regression or a repair.
Any identical-code rerun success below is separate qualification.
