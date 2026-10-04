# ImpactGraph relevance repair implementation plan

Spec: `docs/design/impact-relevance.md`. User authorized implementation inline,
incremental pushes and verified integration to main. Branch
`codex/impact-relevance`, baseline `f31f6a2`. Private evidence belongs to
`.venv/impact-relevance/`. Preserve the prior acceptance history.

## Task 1: Freeze cases and measure the old runtime

- [ ] Extend corpus validation to accept safe existing symbol query IDs. Add
  a RED control for `symbol:pkg/api.py#expire` and reject unsafe paths/names.
- [ ] Freeze twelve independently read Python scenarios (six development,
  six held out) with unchanged source seals and explicit positive/negative sets.
- [ ] Run the old runtime through the current evaluator; save all baseline
  attempts and producer fixture-resolution output before runtime repairs.
- [ ] Run evaluator controls and push the completed corpus/baseline part.

## Task 2: Literal imports and scoped call witnesses

- [ ] Write RED controls for absolute/relative literal imports, proven aliases,
  and no invented targets after shadowing, mutation or dynamic names.
- [ ] Extend selected AST resolution; emit typed location-bound dependencies
  and enclosing-function call witnesses. Preserve existing conservative paths.
- [ ] Run source/query/ingestion controls and development cases; push the repair.

## Task 3: Qualified pytest fixture relationships

- [ ] Observe actual pytest fixture precedence, dependencies, autouse,
  usefixtures and parametrize behavior in a disposable control project.
- [ ] Write RED controls for ancestor/local fixture resolution, dependency
  chains, class test requests and unrelated same-name/shadowed declarations.
- [ ] Add a source-only fixture helper with the shared deadline and graph cap;
  unsupported/dynamic requests remain gaps. Run development/fixture controls.
- [ ] Push the generalized fixture adapter and actual producer controls.

## Task 4: Focused recommendations and independent qualification

- [ ] Write RED controls for a stronger longer witness, retained broad
  fallbacks, duplicate files, provenance, cycles and query caps.
- [ ] Add `test_selection` to JSON and both groups to Markdown; the existing
  conservative `tests` list stays available and no tests execute on queries.
- [ ] Freeze final runtime, run held-out and prior regression cases. Execute
  independent unchanged/equivalent/fault checks and repeated read samples,
  retaining every outcome. Publish actual denominators and breadth limits.
- [ ] Push the report behavior and evaluation results as completed parts.

## Task 5: Review and delivery

- [ ] One independent whole-branch review; reproduce Important findings before
  repair. Run focused controls, full regression, stdlib imports, host diagnostic
  and independent grader after the final code repairs.
- [ ] Update all affected docs and architecture views; run rendered checks and
  local file-link validation. Push completed docs with descriptive messages.

Final external gate: exact-head four-cell hosted matrix, then authorized main
fast-forward. GitHub checks/history record that state. Do not mark a failed
advisory exit complete or turn authored cases into population quality evidence.

Review focus: Python binding mutations and comprehensions; fixture override
visibility; parametrize arguments falsely inferred as fixtures; shortest broad
paths hiding specific witnesses; partial/capped data masquerading as safe test
exclusion. Each owning task includes positive and adversarial controls.
