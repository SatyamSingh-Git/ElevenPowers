# ImpactGraph foundation validation — 2026-10-04

This delivery adds a generalized fresh graph inside ElevenPowers. CLI/library
queries explain conservative Python calls, JS/TS imports, declared contracts,
current local observations and candidate tests. It does not establish an AI
coding-quality gain, a complete call graph or calibrated breakage probabilities.

Runtime repair head: `4095c46`, on `codex/impact-graph`. The design and delivery
plan were committed before implementation. Each working part and review repair
was pushed as completed. No paid engine/host/model session was launched.

## Producers and focused checks

Windows, repository `.venv`, Python's actual AST and optional
`tree-sitter-language-pack==1.20.0` / `tree-sitter==0.26.0` supplied the source
producers. Optional dependencies are acceptance pins, not mandatory installation
requirements. Standard-library-only import and Python CLI controls pass.

```powershell
.venv/Scripts/python.exe -m pytest tests/test_impact_source.py tests/test_impact_typescript.py tests/test_impact_ingest.py tests/test_impact_query.py tests/test_impact_cli.py tests/test_impact_acceptance.py tests/test_repository_scan.py tests/test_polyglot.py -q --tb=short
```

Result on `4095c46`: **131 passed in 26.30 seconds**. Ninety are new ImpactGraph
controls; fourteen exercise shared repository scanning and twenty-seven exercise
the real optional polyglot producer. Before implementation, source, import,
ingestion and query controls failed at their missing interfaces. Review repairs
also had reproduced failing controls before the code changed.

The independent reviewer rechecked **122 controls** on the preceding repair,
including the audit probe. On `4095c46`, the reviewer then ran **25 TS controls**
and **14 separate binding probes**; all passed and the runtime review was cleared.
These counts describe separate executions, not additional unique tests.

## Independent component behavior

`tests/test_impact_acceptance.py` uses an expiration function consumed by an API
and a worker, plus unrelated same-name code and declared route/storage nodes.
The graph selects the two relevant test files through actual relationship paths.
Fresh Python unittest subprocesses independently check their behavior:

| Input | Independent outcome |
|---|---|
| Valid expiration `now >= deadline + grace` | Four checks pass |
| Seeded expiration `now > deadline + grace` | Two checks fail at the API and worker boundary |
| Equivalent expiration `not now < deadline + grace` | Four checks pass |

This demonstrates useful test selection for this fixture and discrimination of a
real boundary regression from equivalent code. It is not a comparison of agents,
a large-repository precision/recall estimate or evidence of reduced development
time. Recommendations remain candidate tests until a separate runner executes
them and records its own outcome.

## Repository query sample

A fresh local query of this ElevenPowers working tree for `core/evidence.py`,
with a 1,000-result limit, selected **1,277 files**, built **3,116 nodes / 2,913
edges**, and returned **66 affected nodes / 82 candidate tests** in **4.348
seconds**. The run reported **67 coverage issues** and remained incomplete.
Shadowed test bindings, unresolved project imports and dynamic imports were
visible qualifications. Input fingerprint:
`c7269f69052d4c4017ad7340d45d2f7adc4389b9265c5177f9a6f5c05eaed96d`.

This is one development-tree sample, taken while the full suite was running;
it is not a benchmark or a precision/recall score. Candidate count does not show
that all suggested tests are useful. The incomplete outcome is why larger-project
acceptance and automatic integration remain open.

## Reproduced review corrections

- Git source selection disables project fsmonitor execution.
- ImpactGraph reads only a safe capped scan configuration, bypassing eager
  command discovery. Oversized source/manifests remain explicit omissions.
- Indexed Python alias lookup and inner traversal deadlines replace quadratic
  scans. The independent 6,000-alias/6,000-call probe returned in 0.307 seconds
  for a 0.3-second cooperative budget with an explicit deadline issue.
- Python match captures, module mutation and rebound exports suppress false
  callable witnesses. Package initializer precedence, longest imported aliases
  and invalid beyond-root imports have independent controls.
- Arbitrary suffixes are not guessed as Python source roots; root and
  conventional `src/` roots are supported.
- CommonJS local bindings, aliases, destructuring, arrow/catch parameters and
  function-expression names suppress false imports. Property keys, default
  expressions and imports renamed away from `require` retain genuine imports.
- `.mts` and `.cts` are selected; deeply nested package JSON becomes a parse gap.
- Invalid API/CLI budgets are rejected and Windows human output uses UTF-8.

The first full-suite attempt at an earlier head reported **1,449 passed,
2 skipped and one failure**. The descendant audit's child created a PID marker
before writing its contents, so its parent could observe an empty file and stop
the child too early. Atomic pending-file publication fixes the producer race;
the original containment assertion is preserved. The focused probe passed both
locally and independently. Final full-suite and hosted results are recorded
below.

## Final regression gates

```powershell
.venv/Scripts/python.exe -m pytest -q --tb=short
.venv/Scripts/python.exe -S -c "import core.impact"
.venv/Scripts/python.exe -m eval.validate
.venv/Scripts/python.exe plugin/bin/ep_doctor.py --host
```

The final local full suite on runtime head `4095c46` passed **1,476 tests with
two skips in 829.99 seconds**. This includes the final CommonJS binding repair.
The standard-library import passed, all four grader controls classified correctly,
and every host diagnostic check passed. The preceding repaired run at `0e100a3`
passed 1,466 tests with two skips; its ten fewer cases preceded the final binding
controls. Timings describe these executions, not a performance comparison.

The later documentation/architecture delivery `7d19734` changes no runtime,
plugin, test, dependency or test-workflow files from `4095c46`. Its recursive
architecture inventory check and generated views passed the separate render gate.

Hosted [test matrix run 37189606163](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/37189606163)
passed on runtime head `4095c46`: Ubuntu and Windows, Python 3.11 and 3.13,
all four cells successful. Each cell installs the optional real grammar pins,
runs the full suite, separately runs descendant audit probes, grades the grader
and checks the host seam. This establishes those CI controls on these environments;
it does not establish installed native sessions or compatibility with all projects.

Integration uses a fast-forward of the published `codex/impact-graph` history to
`main`; no runtime changes follow the reviewed and matrix-tested head. The final
validation record and completed plan checklist are documentation changes.

## Documentation and architecture

The README feature section, command and ImpactGraph guides, status, master plan,
readable roadmap/features, journey and validation indexes describe the shipped
foundation and its remaining limits. The README opening stays focused on what
ElevenPowers is. **320 local Markdown links** resolved.

`architecture/check.py --render` passed: **112 nodes / 258 edges / seven planes**;
all five tabs draw. Cards, filters, keyboard controls, shared links and narrow
layout were exercised. The ImpactGraph card is now an open acceptance milestone;
the shared runtime and explicit query workflow appear in the other views. The
41 cards contain four open milestones, seventeen research items, fourteen
conditional extensions and six proposals. Nested runtime packages are included
in module coverage checks, and the previously omitted strength baseline is mapped.
The new card and architecture view were also visually inspected.

After integration, GitHub Pages
[deployment 37190421048](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/37190421048)
succeeded. The served architecture HTML matched the committed `a40d5f7` Git blob
byte for byte (261,035 bytes; SHA-256
`3ec2c503ce9e0068f021de0aac4339fa9eda0990ffc3691cb42cb2175a06952a`).
An actual HTTPS browser check opened `#planned/impact-graph`, confirmed that its
card expands and identifies the shipped foundation as an open acceptance
milestone. Windows checkout CRLF conversion was accounted for by comparing
against the Git blob rather than raw working-tree bytes.

## Remaining acceptance

Large-project relevant-consumer/test recall, false-lead rate and hook overhead
remain unmeasured. TS calls/types, export maps/tsconfig aliases, framework route
and storage extraction, native coverage/OpenTelemetry converters and automatic
hook integration remain open. Explicit schema-1 observations are unsigned local
reports; they require complete capture, producer/run identity, current source
fingerprint and existing endpoints before entering the active graph.

History is opt-in, bounded file co-change with no author/prose collection, and
never a causal edge. Accepted history output is capped at 2 MiB; contained
capture has a separate 8 MiB ceiling. Filesystem/native parser operations retain
cooperative timing limits; reads do not produce an atomic filesystem snapshot.

See the [guide](../../the-guide/impactgraph.md),
[design](../design/impact-graph.md),
[delivery plan](../superpowers/plans/2026-10-04-impact-graph.md), and
[journey 60](../../journey/60-an-impact-path-needs-a-reason.md).
