# Dynamic imports, fixtures and focused recommendation acceptance

Implementation in progress. `eval/impact_relevance_cases.json` freezes twelve
authored symbol-query scenarios against the existing ElevenPowers/Jinja source
pins: six development and six held out by relationship family. Definitions are
visible to the author, not blinded. All inputs are sealed using the original
tracked-source hashes; no upstream source is vendored.

`development-baseline.json` is produced by runtime f31f6a2, preserved before any
runtime repair. Both project attempts completed. It retains all missing known
references, candidates, explicit negative hits and semantic gaps. Extra
recommendations remain unlabelled under the partial oracle. The prior 24 cases
and process-output fault are separately reused regression evidence, not new
held-out acceptance. Final/behavioral results will be appended after execution.

`development-fixtures.json` retains the first fixture adapter outcomes.
`development-export-repair.json` separately records the class-export repair.
Jinja assigns `Environment.template_class`; that attribute mutation had been
mistaken for a rebinding of `Environment`. The class name now retains its
qualified symbol while rebinding and function-implementation mutations still
reject qualification. Context-bound fixture relationships do not execute pytest.

One frozen reference was wrong: `ep-scrub-call` labelled core/process.py as a
redaction consumer and tests/test_process.py as a redaction test. Inspection of
the pinned source shows neither relationship. The original corpus and every raw
result remain unchanged. `eval/impact_relevance_qualifications.json` binds an
explicit withdrawal to the corpus and inspected source hashes. Qualified
analysis excludes those two mistaken labels equally for both versions; it does
not call their absence a graph failure or silently rewrite the expectations.

Reproduction uses the existing pinned disposable roots documented in
[the earlier acceptance record](../impact-acceptance/README.md):

```text
python -m eval.impact_benchmark --cases eval/impact_relevance_cases.json --roots ROOTS.json --runtime-root FROZEN_RUNTIME --split development --output NEW_RESULT.json
```

The runtime never imports project source or runs tests on a query. Actual pytest
9.1.1 `--fixtures-per-test` resolved Jinja's test_template_hash to `env` at
tests/conftest.py:10 before implementing fixture semantics. Relative Python
import_module resolved `.model` with package `core.impact` as documented.

New evaluations do not certify safe test exclusion, runtime dispatch, agent
quality, representative precision, speedup or automatic advisory readiness.
See the [approved repair scope](../../docs/design/impact-relevance.md) and
[implementation plan](../../docs/superpowers/plans/2026-10-04-impact-relevance.md).
