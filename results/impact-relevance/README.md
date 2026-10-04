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
