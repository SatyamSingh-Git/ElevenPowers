# Frozen real-project ImpactGraph acceptance

This is an unfinished acceptance milestone, not evidence of improved agent
coding. `eval/impact_cases.json` freezes 24 independently inspected path-reference
cases across three pinned repositories: 16 development and eight held out by
family. The author sees the held-out definitions; this is not a blinded study.
The held-out cases have not been run at this stage.

`development-baseline.json` was produced by the frozen runtime at `995d2d7`.
All 16 attempts completed with unchanged pinned inputs. Every known consumer
was found, but the builder case missed `tests/test_impact_cli.py` and Jinja's
nodes case missed `tests/test_nodes.py`. The first invokes a subprocess; the
second reaches nodes through a pytest fixture. These are genuine omissions in
static relationships. No declared negative was selected. Extra candidates are
unlabelled, not automatically false positives: the partial reference set cannot
establish precision. Jinja returned 23 candidate files per development query and
Zod 56, so noise and cost still need assessment.

Attempt completion does not mean complete graph semantics. All three graphs
report gaps. Known-reference recall is not independent regression detection;
the behavioral denominator is still pending.

The actual unchanged baselines were 131 focused ElevenPowers checks, 909 Jinja
tests, and 462 Zod tests in 55 suites. The ElevenPowers count is not its full
suite. Zod used Jest 29.7.0, ts-jest 29.1.5 and TypeScript 5.7.3, with ts-jest
diagnostics disabled; it establishes runtime behavior, not type checking.
Jinja's initial collection failed because trio was absent. Both that setup
failure and the subsequent passing run are retained. Its pinned requirements
declare trio 0.27.0. Python was 3.13.2 and Node was 22.17.1.

Source provenance and SHA-256 hashes of tracked files are in the corpus. Jinja
3.1.6 is BSD-3-Clause; Zod 3.22.4 is MIT. ElevenPowers declares Apache-2.0 in
its README and has no dedicated LICENSE file at this pin. Upstream source is
not vendored in these results. An initial private baseline used incorrect
ElevenPowers license metadata; this published result corrects that metadata
without changing source pins or reference cases.

To reproduce, check out each corpus pin with Git line-ending conversion
disabled. Extract the ElevenPowers pin using `git archive`. Install the Python
evaluation requirements and the exact Node tools above into an isolated tools
directory; use the source checkout on PYTHONPATH for Jinja. Write an external
JSON object mapping `elevenpowers`, `jinja`, and `zod` to those roots. Then run:

```text
python -m eval.impact_benchmark --roots ROOTS.json --runtime-root FROZEN_EP_ROOT --split development --output NEW_RESULT.json
```

The controller refuses source changes and new source files, records its runtime
identity, preserves failed cases, and refuses to overwrite the output. Private
absolute paths in the supplied roots are not part of the portable corpus.

The final adapter revision must be frozen before the first held-out execution.
No automatic session integration is qualified by this baseline.
