# Frozen real-project ImpactGraph acceptance

The approved implementation and evaluation are delivered. The proposed detection
exit failed, so automatic advisories remain unqualified. This is not evidence
of improved agent coding. `eval/impact_cases.json` freezes 24 independently inspected path-reference
cases across three pinned repositories: 16 development and eight held out by
family. The author sees the held-out definitions; this is not a blinded study.
The held-out split was first run after freezing adapter head `7e980eb`. After
review repairs, `21c7c88` was revalidated against all cases; those are reused
cases, not a new held-out experiment.

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
the behavioral denominator is reported separately below.

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

## Final reference and behavior results

The old runtime at `995d2d7`, first optional compiler at `7e980eb`, and reviewed
adapter at `21c7c88` retain separate code hashes. `heldout-baseline.json` and
`heldout-final.json` preserve the initial eight held-out cases;
`post-review-revalidation.json` records all 24 reused cases after repairs.
All 31 known consumer references and 23 of 26 known test references were found.
The three misses are two query references to the ElevenPowers CLI test and one
Jinja fixture-dependent test. No declared negative was selected. These partial
reference sets do not establish precision, safety or representative recall.

`behavior-original.json` retains every attempt. Eight authored fault definitions
are frozen in `eval/impact_faults.json`. They were authored after development
adapter work, before behavioral execution; they are not blinded agent patches.
Six meet the strict qualification: unchanged and comment controls pass, faulty
inputs fail through assertions, and no mixed runtime/setup failure occurs.
Both old and final selected checks detect **5/6 (83.3%)**, below the proposed
90% exit. The actual process-output-limit fault fails its full relevant suite
while selected checks pass. Its test uses `importlib.import_module`, a missing
dynamic relationship. The string-minimum fault has mixed matcher/runtime
failures and the default-export fault passes existing tests; neither is removed
from the record or silently promoted into the qualified denominator.

ElevenPowers' behavioral relevant suite is explicitly `test_process.py` plus
`test_redact.py`: 50 passing tests and two Windows skips before faults. Jinja
uses its 909-test suite. Zod uses the same configured Jest runtime scope of 55
suites/462 tests, retaining the language-server exclusion and disabled type
diagnostics. Selected execution intersects graph candidate files with each
named full relevant suite; outside-scope candidates are listed separately.
This is not whole-project correctness or an unequal-scope speedup claim.

The initial classifier identity was not recorded. That limitation is preserved,
rather than backdating provenance. `behavior-regrade-before-review.json` records
the first source-hashed regrade. `behavior-regrade.json` separately records
version 3 classification against all 40 original raw report hashes, plus eight
new post-review selected runs with before/after seals. The reviewer independently
checked all original hashes. Regrading and fresh selection still yield 5/6.
Raw outputs remain in the disposable operator directory; their hashes, all
outcomes and failed test identifiers are published. Credential-shaped negative
fixtures in the redaction suite are not copied into public diagnostics.

## Actual coverage recovery

The saved coverage.py 7.10.7 report, receipt, one-test pass, converted artifact
and `jinja-nodes-observed-query.json` show `tests/test_nodes.py -> nodes.py` as a
current `observed_test` relationship. Whole static coverage remains incomplete.
This recovers a genuine missing relationship, separately from the unchanged
static corpus score. Receipt/context attribution is unsigned and executed lines
do not prove assertions. The Node 22.17.1 report and receipt qualify an isolated
native CommonJS fixture; they are not Zod source-map acceptance.

## Cost and remaining exit

Both sets of 18 local read samples are retained. The post-review median fresh
builds under concurrent delivery checks ranged from 1.3 to 6.5 seconds; graph
query medians ranged from 4 to 31 ms. These are three samples per project/mode,
not native ordinary-session measurements or universal latency guarantees.
Jinja still recommends 23 files. Zod's final file queries recommend 52–55 versus
56 in the original cases. The owner-project compiler payload hits its explicit
32 MiB limit; that failed adapter result remains visible.

Automatic advisories fail both the detection target and the need for useful
recommendation breadth/native-session cost qualification. No hook or completion
blocker was added. Next use new frozen dynamic-import, fixture and symbol-query
cases; source maps, framework/live traces, multi-config compiler programs and
additional languages remain open.

## Reproducing behavior and read samples

After the unchanged baselines and source seal pass, execute the explicit fault
controller with pinned tools, a new private directory and a new output:

```text
python -m eval.impact_behavior --roots ROOTS.json --definitions eval/impact_faults.json --old OLD_HELDOUT.json --final FINAL_QUERY_RESULT.json --tools TOOLS --private NEW_PRIVATE_DIR --output NEW_BEHAVIOR.json
```

The current controller records its code identity and frozen input hashes before
launch. It preserves raw machine/output files in the private directory, seals
each source variant and qualifies actual pytest/Jest assertions. It executes
trusted project tests; this explicit evaluator is separate from ordinary plugin
queries. The original retained attempt predates the identity and per-selected
seal fixes; its limitations are reported above.

For read samples, build each pinned project three times in both default and
explicit compiler modes. Time `build(root)` with `time.monotonic()` and then
`analyze(graph, [QUERY], max_depth=20, max_results=1000)` separately. Queries used
were `core/impact/model.py`, `src/jinja2/utils.py`, and `src/types.ts`. Preserve
every result, source fingerprint, input/semantic coverage and runtime/engine
hash. Do not compare samples collected under different concurrent load as a
speedup. See [delivery validation](../../docs/validation/2026-10-04-impact-acceptance.md)
for review repairs and implementation checks.
