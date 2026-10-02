# Native validation and subscription pilot, 2026-10-02

This delivery adds generalized runtime/version qualification, explicit native
captures and a ten-cell matrix, bounded read-only latency sampling, and a frozen
subscription coding-outcome pilot. It does **not establish improved coding**.
Task size was not the criterion; any observed coding or verification improvement
would have counted. Native activation and execution failures prevented that comparison.

## Runtime and installed host observations

New preparation and real SessionStart must bind to the shipped runtime content
identity. Old unbound preparations and changed runtime cannot qualify. Version
probes execute only `--version` with contained processes and bounded output/time.
They do not launch a model, authenticate a host, or retain raw output.

Installed probes observed Codex **0.159.2** and Claude Code **2.1.286**.
New Python and JavaScript exercises were prepared for both. All four remain
waiting for complete native histories; six unsupplied host/language cells remain
waiting. The [saved matrix](2026-10-02-native-validation/matrix.json) is **0/10**.
Gemini CLI, Cursor Agent and Copilot CLI were unavailable on PATH.

A subsequent Codex disposable exercise changed its source after the shell launch
correction, but timed out after 180 seconds and delivered no observed callbacks.
Native hook trust/enablement remains necessary. It is not passed acceptance.
The later performance correction changed the runtime, so that earlier preparation
also became incomplete; it was retained, and a new preparation was made.

## Read-only performance

Three reads each, no warmup, every attempted read retained, 90-second cooperative
budget; Python 3.13.2, Windows 11. No model, checks or engine ran. The small
project is a new disposable Python exercise; the large project is an external
acceptance repository. Neither receives a special runtime rule.

| Project | Selected files | Selected bytes | Median read ms | Sample p95 ms | Sampling |
|---|---:|---:|---:|---:|---|
| Small | 3 | 4,008 | 139.088 | 139.099 | complete |
| Large | 5,209 | 78,409,173 | 2,511.143 | 2,736.005 | complete |

The [small](2026-10-02-native-validation/small-performance.json) and
[large](2026-10-02-native-validation/large-performance.json) reports retain each
read's coverage, source identity, scan/report/read durations and health state.
These are descriptive samples, not speedup or universal latency guarantees.
Pipeline health remains waiting and task verification UNVERIFIED. Retained
callbacks and command times are separate; Stop can include verification work.

The real producer exposed a validation error: project fingerprints contain 16
hex characters, whereas software identities contain 64. Positive actual-project
sampling controls were observed failing, corrected, and passing. The first
incomplete samples were retained locally rather than discarded as slow reads.

## Frozen subscription comparison

[All eight original results](2026-10-02-native-validation/subscription-pilot.json)
are retained. The atomic/idempotent batch task, prompt, visible contracts and
independent 16-check grader were frozen before models ran. Gold passed 16/16;
broken atomicity and modified visible tests failed their controls. Each arm had
240 seconds, two replicates, balanced reversed order and equal permitted tools.
The grader stayed outside candidates; this is not an OS closed-book boundary.

| Host / requested model | Effort | Baseline | ElevenPowers | Native delivery |
|---|---|---|---|---|
| Codex / gpt-6.1-sol | medium | 2 unresolved, 7/16 unchanged behavior | 2 unresolved, 7/16 unchanged behavior | no callbacks |
| Claude / claude-sonnet-5-5 | medium | 2 host failures | 2 host failures | no callbacks |

Both subscription auth checks and initial exact-model smoke calls succeeded.
Later diagnosis found Codex shell commands rejected as **blocked by policy** and
Claude returning **429 / weekly limit reached**, with zero generated usage in
the failed pilot calls. Codex's supported `--approve-for-me` enabled a subsequent
read-only smoke command; it selects workspace-write and conflicts with an
explicit `--sandbox`. Claude must load `project,local` settings to include owned
local hooks. These producer-driven corrections ship with regression controls.

The original pilot was not replaced with a favorable rerun. Its complete
protocol means eight records exist, not eight valid coding comparisons. It
establishes no positive or negative treatment effect. Patch behavior, native
engagement, completion wording and usage stay separate. Completion wording is
a heuristic and none of these records establishes false completion or improved
verification. CLI usage estimates are not evidence of API billing; API key and
provider overrides are refused, and there is no paid API fallback.

## Reproduction and remaining work

Use `ep_validate.py capture HOST --project EXERCISE --observe-version --json`
and supply one chosen current capture per host/language to `matrix`. Use
`performance HOST --project PATH --repeats 3 --seconds 90 --json` for a new sample.
Reports are explicit, atomic and refuse overwrite without `--force`.

Run native acceptance in a trusted installed session following its `EXERCISE.md`.
Do not bypass hook trust. After Claude subscription capacity is available and
Codex native hooks are trusted/enabled, start a **new** explicitly identified
comparison with `python -m eval.paired --directory NEW_DIR --codex CODEX_EXE
--claude CLAUDE_EXE`. Exact models/medium effort, task/grader identities and equal
budgets are recorded before execution. A new protocol must preserve these eight
inconclusive results and report neutral or worse outcomes as well as improvements.

Final whole-branch verification and review are recorded in the delivery check.


## Recorded-protocol reproduction

The [original protocol](2026-10-02-native-validation/protocol.json) remains pinned
to the original grader identity. [Reproduced aggregates](2026-10-02-native-validation/reproduced-pilot.json)
match all four original arms and label `current_evaluator: false`. This performs
no candidate execution, regrading, project checks or model calls. It does not
repair the original evaluator, authenticate its records or establish a coding effect.

```bash
python -m eval.paired --inspect docs/validation/2026-10-02-native-validation/subscription-pilot.json --protocol docs/validation/2026-10-02-native-validation/protocol.json
```

Only structurally qualified recorded observations are counted. Protocol/runtime/
budget conflicts, unsupported resolved states and private/unknown fields are
rejected. Optional output is explicit and atomically refuses overwrite unless
`--force` is supplied. Archive and model-launch modes cannot be combined.

Independent review identified three Important grader/summary defects. All three
were reproduced failing before correction. The current grader's controller
never imports candidate code: a contained worker preserves normal package
imports and returns behavior, while final assertions stay in the controller.
Grader and worker content now define a new protocol identity. The sixteen
behavioral checks remain the same; the original eight records are preserved.
Two Minor findings remain qualified: deleted sealed metadata is classified as
setup instead of invalidation, and the sixteen checks do not exercise invalid
source/target identifiers already present as balance keys. Passing all checks
is not complete coverage or correctness. Expanded cases require a new protocol.
