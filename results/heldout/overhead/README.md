# Where the held-out sweep's extra time went ($0)

The held-out sweep of 2026-10-22 found ElevenPowers cut untested fixes from
84% to 37% of resolved runs, and reported that assisted runs took "about 3.1×
the model-process time". **That figure is wall time, not model time.** This
reads the sweep's own records to find where the difference went.

## From the transcripts ([`toolprofile.py`](toolprofile.py), [output](toolprofile.txt))

Each run's `result` event gives wall time (`duration_ms`) and model time
(`duration_api_ms`). Tool calls are timed from the event that asked for them
to the event that returned them. That counts queueing when calls are asked for
together, so the per-kind split is approximate.

| mean per run | ordinary (120) | assisted (119) |
|---|---|---|
| wall | 25.3 s | 83.6 s |
| model | 23.9 s | 31.5 s |
| outside the model | 1.4 s | 52.1 s |
| of which: the agent's own test runs | 2.3 s | 11.6 s |
| of which: `ep_check` run by the agent | — | 7.1 s |
| of which: edits and reads, with their hooks | 0.3 s | 4.4 s |
| of which: outside any tool call (mostly Stop) | — | 27.9 s |

The model works about 1.3× as long. The rest is the hooks and the tests.

## What Stop spent it on ([`phaseprofile.py`](phaseprofile.py), [output](phaseprofile.txt))

Each assisted workspace keeps its `verification.json`. Summed by phase:

| phase | runs | mean |
|---|---|---|
| **test strength** (mutation analysis) | 119 | **18.3 s** |
| base-tree suite | 114 | 6.9 s |
| the agent's `ep_check` | 80 | 7.0 s |
| suite on the final tree | 54 | 5.7 s |
| confirmation | 71 | 1.0 s |

Test strength ended `incomplete` in 110 of 119 runs, `deferred` in 3 and
`complete` in 6. Its result goes to `strength.json` and the human report.
It never reaches the agent (`core/strength/runner.py`, `consider`). So the
agent waited 18 s at every Stop for a result that, in this sweep, was
almost never finished and never shown to it.

This is not the step that [multistage v3's overhead](../../multistage-v3/overhead/README.md)
withdrew. There, every Stop ran on files already dirty when the task opened,
and the step refused them in 0.6 s. Here each task opened clean, so the
analysis ran in full.

## Checked unloaded ([`strength_replay.py`](strength_replay.py), [output](strength_replay.txt))

Four final trees were copied, and `ep_strength` was run on each alone:

| task | time | result |
|---|---|---|
| cachetools | 5.7 s | gave up before any mutant (no positive pass count) |
| more-itertools | 17.2 s | gave up before any mutant (baseline timed out) |
| uvicorn | 19.1 s | gave up before any mutant (baseline timed out) |
| wrapt | 60.5 s | 7 mutants, then the time limit |

## The change, through the real hook ([`stop_atstop_replay.py`](stop_atstop_replay.py), [output](stop_atstop_replay.txt))

`strength.at_stop`, default false: Stop runs the analysis only when a project
asks. `ep_strength` and `ep_review --strength` still run it on request.

Each run was replayed from its base tree through `plugin/bin/ep_hook.py`:
SessionStart, the task's prompt, an Edit pair per changed file, then Stop.
This was done once with the default and once with `at_stop` set.

| task | default: strength phase | `at_stop`: strength phase |
|---|---|---|
| cachetools | none | 3.8 s |
| more-itertools | none | 16.4 s |
| uvicorn | none | 25.8 s |
| wrapt | none | 60.2 s |

Every Stop allowed completion in both configurations.

The replays shared the machine with an active session, so their other
phases varied widely between the two configurations. For example, uvicorn's
final-tree suite took 61 s in one and 117 s in the other. Read the strength
column, not the totals.

## What this does and does not show

- It removes about 18 s of a mean 84 s assisted run, as measured from the
  sweep's own records. That is an estimate from those records; no new sweep
  was run.
- The untested-fix benefit comes from the base-tree suite and the agent
  writing a test. Neither depends on the mutation step, which the agent
  never saw. That is an argument from the code path, not a re-measurement.
- What remains outside the model is mostly tests: the agent's own (11.6 s),
  its `ep_check` (7.1 s) and the base-tree suite (6.9 s). Those carry the
  benefit. Two earlier cuts landed after this sweep and are not reflected in
  its numbers:
  - hooks no longer start through PowerShell;
  - `ep_check` no longer hashes the runtime seven times.

  Both are in the [v3 overhead record](../../multistage-v3/overhead/README.md).
