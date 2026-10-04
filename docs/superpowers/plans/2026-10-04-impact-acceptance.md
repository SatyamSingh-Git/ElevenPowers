# ImpactGraph real-project acceptance implementation plan

Spec: `docs/design/impact-acceptance.md`. Execute inline on
`codex/impact-acceptance`, based on `995d2d7`. The user approved the plan and
implementation; standing authorization covers incremental pushes and verified
integration to main. Scratch artifacts belong to `.venv/impact-acceptance/`.

Global constraints: generalized behavior; no project source imports in queries;
bounded inputs and subprocesses; no model calls; pin and preserve all outcomes;
do not grade with ImpactGraph's own predictions; no automatic queries before
the measured relevance/noise/overhead exit. Run actual producers before assuming
their output shapes. Preserve current stdlib-only behavior.

## Task 1: Freeze a portable corpus and initial graph results

Files: `eval/impact_cases.json`, `eval/impact_benchmark.py`,
`tests/test_impact_benchmark.py`, `requirements-impact-eval.txt`.
Interfaces: `load_cases(path) -> dict`, `evaluate(manifest, roots, *, split,
runtime_root, output) -> dict`. Results include schema, corpus hash, runtime
identity, project/source qualification and all attempted case outcomes.

- [x] Write schema/path/split/source-seal and precision-denominator controls;
  expected RED before the evaluator exists.
- [x] Freeze three pinned repositories and 24 independently inspected cases;
  eight held out by family. Run real passing baselines in disposable roots.
- [x] Build each graph once per attempt through the actual selected runtime;
  grade known positives/negatives separately from unlabelled leads and gaps.
- [x] Run development baseline on the frozen old runtime, retain its identity
  and output. Expected: a qualified result, not necessarily a passing exit.
- [x] Run evaluator controls; commit/push the corpus, controller and baseline.

## Task 2: Improve optional compiler-backed TypeScript relationships

Files: `core/impact/compiler.py`, `core/impact/compiler.cjs`, builder/CLI flags,
`tests/test_impact_compiler.py`. Interface: explicit compiler path option;
worker consumes only selected virtual source/config bytes, produces schema-1
nodes/edges and qualifications; parent validates endpoints, paths and limits.

- [x] Observe TypeScript 5.7.3 producer output; write real aliases/exports,
  symbols/calls, shadows/external/ambiguous/deadline/malformed engine controls.
  Expected RED for the new optional interface.
- [x] Add version-qualified contained producer with no project config/source
  execution or implicit engine installation. Unsupported dispatch remains gaps.
- [x] Re-run development cases, retain both old and new outcomes. Use generic
  resolution rules only; current tree-sitter and stdlib controls still pass.
- [x] Commit/push the supported compiler adapter and its negative controls.

## Task 3: Convert actual coverage with explicit provenance

Files: `core/impact/coverage.py`, `plugin/bin/ep_impact_capture.py`, input coverage
qualification in build/ingest, `tests/test_impact_coverage.py`.
Interfaces: offline converters consume producer files and an execution receipt;
emit schema-1 observed-test edges or a qualified incomplete artifact.

- [x] Execute actual coverage.py contexts and Node V8 output; write current,
  stale, incomplete, no-context, source-map and unsafe-path controls. Expected RED.
- [x] Distinguish incomplete input/declaration coverage from static omissions;
  accept current complete observations only inside known readable endpoints.
- [x] Add offline conversion, bounded reads and explicit no-overwrite export.
  Ordinary queries still execute no tests, compiler unless selected, or host.
- [x] Run producer and ingestion/CLI controls; commit/push useful observations.

## Task 4: Independent behavior and held-out results

Files: evaluator fault/control definitions and result artifacts under
`results/impact-acceptance/`; behavioral controller tests.
Interfaces: producer journals distinguish pass/fail/incomplete/setup; selected
and full relevant suites share the same immutable inputs and independent checks.

- [ ] Validate faults and equivalent controls using actual independent tests;
  test controller rejection of setup failures, forged summaries and missing runs.
- [ ] Freeze final adapter head, execute all held-out cases with both the old
  and final runtimes, and publish every outcome and exact denominators.
- [ ] Record repeated graph/read timings and candidate breadth; explicitly
  qualify any selected/full execution comparison and failed acceptance exit.
- [ ] Commit/push reproducible results and producer identities.

## Task 5: Advisory qualification and delivery

Files: automatic shared hook adapter only if its measured exit is met; guide,
README, status/PLAN, journey 61, validation, architecture and generated mirror.

- [ ] Assess detection, noise and ordinary-session cost. Record the integration
  ruling; implement shared bounded advisories only if evidence qualifies them.
- [ ] Run focused controls, stdlib import, full regression, host diagnostic and
  grader. Request one independent whole-branch review; repair reproduced defects.
- [ ] Update all relevant docs and every new architecture module/workflow;
  `architecture/check.py --render` must pass. Validate local links.
- [ ] Push each completed part, pass hosted checks, integrate verified code to
  main and publish actual limits. Do not claim the entire ImpactGraph is finished.
