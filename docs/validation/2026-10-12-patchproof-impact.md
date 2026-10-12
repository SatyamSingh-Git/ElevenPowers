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
Later successful qualification below is separate from a cleanup repair; the
process runner was unchanged.

The complete local run after the display repair passed **2,087 tests, 2 skipped
in 1398.67s (23:18)**. Its producing runtime predates the final path-format
repair: a relative global ignore filename beginning with a space was trimmed
by text-line parsing, so its changed rules escaped association checks. The
actual regression failed before repair. Git NUL-delimited config path output
was observed and now preserves that significant space. Final-code qualification
is recorded separately below; the earlier full count is not substituted.

Final exact-path integration, selection and CLI controls passed **39 in 117.57s**.
Runtime source fingerprint: `ca68e4c5643e30adb95c68881b8df44f944e46d6ce845307df0abba418e68222`.
The prior saved larger-repository observation retains its original runtime
identity rather than being relabelled. Final full/hosted results follow below.

At the final `ca68e4c...` runtime, **107 named audit probes passed in 82.68s**;
standard-library imports, all 11 host probes, all four independent grader
controls and preserved source grades passed. No new installed session or
coding-benefit evaluation was run.

The final-code matrix at `cd19ed5` passed both Linux jobs and Windows 3.13.
The initial Windows 3.11 job timed out after 20 seconds in the existing
`test_codex_setup_launches_quoted_paths` control (1 failed, 2,085 passed,
4 skipped). See the [retained failure](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38233475183/job/114758348251).
The same control passed locally in 1.20s without changing its timeout or host
code. Its cause remains unknown; only that failed job was retried at identical
code. Rerun qualification below does not constitute a launcher repair.

## Final local qualification

The final runtime passed **2,088 tests, 2 skipped in 1483.94s (24:43)**, plus
**107 named audit probes in 82.68s**, 39 focused integration/presentation
controls, all 11 host probes, four independent grader cases and preserved
source-grade reproduction. No new installed/model session was run. The
remaining hosted Windows 3.11 retry is recorded separately when it completes.

## Final hosted qualification

[All four hosted jobs passed](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38233475183)
at `cd19ed59d1750892861ef2a53f63f88a6b10a609`: Ubuntu/Windows, Python
3.11/3.13. Windows 3.11 passed on its identical-code retry; the original
20-second launcher timeout remains unexplained. The previous Linux interrupt
cleanup failure and older SQLite-reference observations also remain unresolved.
No launcher/process runtime repair is inferred from these passes.

The final architecture has **144 nodes / 345 edges / 7 planes**; all five tabs,
contributor cards/filters, keyboard controls, shared links and narrow layout
rendered. Current changed-document links resolved. Exact runtime and tests
remain unchanged after this code commit; final delivery changes only docs and
the already rendered architecture. Earlier installed cells and correctness
ties remain historical. No deferred Minor review findings.
