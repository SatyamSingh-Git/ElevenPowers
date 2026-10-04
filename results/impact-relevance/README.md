# Dynamic imports, fixtures and focused recommendation acceptance

The generalized repair and frozen evaluation are implemented.
`eval/impact_relevance_cases.json` freezes twelve
authored symbol-query scenarios against the existing ElevenPowers/Jinja source
pins: six development and six held out by relationship family. Definitions are
visible to the author, not blinded. All inputs are sealed using the original
tracked-source hashes; no upstream source is vendored.

`development-baseline.json` is produced by runtime f31f6a2, preserved before any
runtime repair. Both project attempts completed. It retains all missing known
references, candidates, explicit negative hits and semantic gaps. Extra
recommendations remain unlabelled under the partial oracle. The prior 24 cases
and process-output fault are separately reused regression evidence, not new
held-out acceptance. Final and behavioral outcomes are retained below.

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

## Known references and breadth

Runtime `4df6f30` was frozen before the first held-out queries. `all-baseline.json`
uses archived f31f6a2; `all-final.json` uses the repaired runtime, with every core
source hash attached. `heldout-baseline.json`/`heldout-final.json` retain the first
held-out runs, and `development-final.json` the final development run.
`summary.json` applies only the explicit reference withdrawal, equally to both
versions. All attempts complete their input audits; their semantic gaps remain
visible. No declared negative is selected. Extra recommendations are unlabelled.

| Valid known test references | Old | Repaired |
|---|---:|---:|
| Development | 2/6 | 6/6 |
| Held out by relationship family | 2/6 | 5/6 |
| Combined | 4/12 | 11/12 |
| Focused witnesses | unavailable | 6/12 |
| Reused prior 24-case corpus | 23/26 | 24/26 |

The prior corpus preserves 31/31 known consumers. After withdrawing the new
corpus's mistaken consumer label, it supplies no valid new consumer-reference
denominator. Do not infer consumer precision or an improvement from an empty set.
The remaining new miss and two prior misses cross subprocess CLI boundaries.

| Query | Old candidate files | Repaired focused / fallback / support |
|---|---:|---:|
| ElevenPowers run | 85 | 21 / 65 / 0 |
| ElevenPowers _read | 0 | 21 / 65 / 0 |
| ElevenPowers scrub | 73 | 5 / 77 / 0 |
| ElevenPowers analyze | 0 | 0 / 5 / 0 |
| Jinja Environment | 0 | 12 / 12 / 1 |
| Jinja DictLoader | 4 | 3 / 21 / 1 |
| ElevenPowers module_index | 0 | 0 / 5 / 0 |
| ElevenPowers safe_path | 0 | 0 / 5 / 0 |
| ElevenPowers markdown | 0 | 0 / 5 / 0 |
| Jinja ChoiceLoader | 2 | 1 / 23 / 1 |
| Jinja PrefixLoader | 2 | 1 / 23 / 1 |
| Jinja choice_loader fixture | 0 | 1 / 0 / 0 |

The six focused hits are scrub, Environment, DictLoader, ChoiceLoader,
PrefixLoader and the changed choice_loader fixture. The recovered process test
remains a fallback: the literal import reaches its module, but return-object
dispatch does not establish a continuous focused call witness. Conservative
selection is necessary. These sets are not equal-scope speedup measurements.

## Independent behavior and the classifier correction

Definitions in `eval/impact_relevance_faults.json` were pushed before execution.
The unchanged suites pass 50 process/redaction checks (two skips), 167 selected
Jinja API/filter/nodes checks and 43 Jinja loader checks. Comment controls pass
the same checks. The faulty variants respectively cause one, twenty and one
actual assertion failures. Every before/after seal and output/report hash is
retained in `behavior-first.json` and the private raw source/report directory.

The first `impact-behavior/4` classifier qualifies two of three attempts:
repaired detection 2/2, old detection 0/2. The Environment variant remains
incomplete there because real pytest emits some rewritten messages starting
`assert ` without an exception-type prefix. The original result is unchanged.
An actual numeric assertion control was observed RED and repaired; runtime
exceptions mentioning assertions remain incomplete. The initial string-valued
control passed even with the old classifier and is recorded as an insufficient
reproduction in journey 62.

`behavior-regrade.json` is a distinct historical reclassification, using
`impact-behavior/5` and `impact-behavior-regrade/1`. It checks each saved report
and normalized producer-output hash, retains the original controller and
classifications, and requires the recorded source seals. It launches no tests
and does not attest current source. All three attempts then qualify:

| Authored fault | Old recommendations | Repaired recommendations |
|---|---|---|
| Reused process-output limit | Selected redaction checks pass; process check absent | Process assertion detects the oversized-output regression |
| Environment default autoescape | No relevant checks selected; execution incomplete | 20 assertion failures |
| choice_loader wrong template | No relevant checks selected; execution incomplete | One assertion failure |

Detection is **0/3 old versus 3/3 repaired**, conditioned on full relevant-suite
qualification. A missing selection is not a passing test. Selected commands
intersect graph suggestions with the explicitly named relevant suites;
unrelated suggestions are retained but not executed. The process fault is
reused evidence; two faults are newly authored. These results support useful
selection recovery, not population precision, agent patch quality or universal
safety. Equivalent controls are comments, not general semantic equivalence.

One early controller invocation occurred before all-final.json had finished
writing. It failed its prediction-file preflight and launched no experiment;
the later execution used the complete file. No setup outcome was scored as a
fault or hidden by overwriting an attempted producer run.

## Descriptive read samples

Three complete sealed reads have identical runtime hashes. Graph-build samples
are 3.763, 5.649 and 4.724 seconds on ElevenPowers; 0.828, 1.071 and 2.193 seconds
on Jinja. `summary.json` retains every value, fingerprint, input/after seal and
raw result hash. Sample one is all-final.json; samples two/three remain in the
private ignored workspace. These are one-machine Windows observations under
concurrent load. Build duration excludes query time. The separate
worker-plus-after-seal metric includes subprocess startup, queries and after
source audit, with pre-audit excluded; it is not native-session latency.

## Reproduction

Use the same source pins and line-ending-free checkouts as the earlier
acceptance record, Python 3.13.2 and the evaluation requirements. The real
fixture producer here used pytest 9.1.1. Reconstruct baseline core with
`git archive f31f6a2 core` into a separate runtime root. ROOTS.json maps
`elevenpowers` and `jinja` to those pinned inputs, not the edited current repo.
The previous regression also needs `zod` and trusted TypeScript 5.7.3.

```text
python -m eval.impact_benchmark --cases eval/impact_relevance_cases.json --roots ROOTS.json --runtime-root BASELINE_RUNTIME --split all --output NEW_OLD.json
python -m eval.impact_benchmark --cases eval/impact_relevance_cases.json --roots ROOTS.json --runtime-root REPAIRED_RUNTIME --split all --output NEW_FINAL.json
python -m eval.impact_behavior --cases eval/impact_relevance_cases.json --definitions eval/impact_relevance_faults.json --roots ROOTS.json --old NEW_OLD.json --final NEW_FINAL.json --tools TOOLS --private NEW_PRIVATE_DIR --output NEW_BEHAVIOR.json
python -m eval.impact_behavior_regrade --result SAVED_BEHAVIOR.json --private SAVED_PRIVATE_DIR --output NEW_REGRADE.json
```

Fresh replay with the current controller has a new identity; do not call it the
original producer run. Old archived behavior classifiers can be reconstructed
from their recorded controller commit/hash if comparing historical grades.
The reports do not include upstream source or raw output; those copies remain
privately for local reproduction, with published SHA-256 identities.

Supported collection/source relationships are bounded; plugins, custom pytest
collection, dynamic fixture registration and return-object dispatch stay gaps.
Automatic hook integration remains unqualified pending relevance/noise and
native cost. See [delivery validation](../../docs/validation/2026-10-04-impact-relevance.md).

## Independent review and post-review qualification

The fresh whole-branch review reproduced four Important findings: class-body
mark omission, imported wildcard/re-export fallback, active override-chain
lookup and definition-time/container mutation qualification. Nine controls were
observed RED; repairs passed all 149 integrated controls. Six disposable real
pytest counterparts passed and agree with the graph (`review-producers.json`).
Imported registrations remain explicit uncertainty instead of guessed ancestor
relationships. The review also replayed the historical behavior regrade and
independently obtained the published 3/3 versus 0/3 totals.

`post-review-all.json` and `post-review-prior.json` identify runtime 61553e3
separately. These are reused frozen cases, preserving earlier reports. They
retain 11/12 valid new tests (six focused), 31/31 prior consumers and 24/26 prior
tests, with no declared negative hit. The behavioral source copies and raw
producer reports are unchanged; their recorded reclassification is historical.
No new behavioral execution is claimed for the post-review graph.

One Minor finding is deferred: comprehension targets can shadow a local call
for the entire function, moving a valid focused witness into the retained
fallback. A later scope repair needs real Python controls; current reports do
not establish safe exclusion. Final documentation/render, hosted checks,
arbitrary plugin/runtime fidelity and population benefit were expressly outside
the review's certification and remain separately checked or qualified.

Final local regression passed 1,624 tests, two skipped, in 752.56 seconds;
stdlib imports, actual host diagnostic, independent grader, five-tab rendered
architecture and 332 local documentation links passed. Exact-head hosted checks
are the remaining integration gate, recorded by GitHub; they do not enlarge the
measurement's precision, execution fidelity or coding-benefit claims.
