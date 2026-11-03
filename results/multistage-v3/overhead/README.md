# Where the ElevenPowers arm's extra minutes go (open problem 4, $0)

v3 reported that ElevenPowers took 10.8 minutes per conversation against
6.5, and called it model time. **It is wall time.** The figure is the
harness's clock around each `claude` process (`eval/multistage_run.py`).
The model's own time hardly differs.

## Per stage, from the transcripts ([`overhead.py`](overhead.py))

All 960 stage transcripts, 480 per arm. Model time and cost are cumulative
in a resumed session, so each stage's figure is its difference from the
stage before.

| mean per stage | ElevenPowers | superpowers alone |
|---|---|---|
| wall time | **76.7 s** | **41.8 s** |
| model time (`duration_api_ms`) | 36.2 s | 34.3 s |
| wall time outside the model | about 40 s | about 7.5 s |
| turns | 9.4 | 8.5 |
| output tokens | 3,496 | 3,264 |
| cost | $0.15 | $0.14 |
| `ep_check --all` run by the agent | 0.68 | 0 |
| Edit / Read calls | 1.75 / 1.59 | 1.04 / 1.21 |

The model works about 6% longer. The other 33 s per stage is spent outside
it.

## Per hook, replayed ([`stopreplay.py`](stopreplay.py))

Nine stages from nine cases were replayed through the real hook on this
machine, unloaded. The pre-stage snapshot is committed, the stage's request
is submitted, the post-stage files are written with Edit events, and Stop
runs.

| hook | time |
|---|---|
| SessionStart | 0.5 s |
| UserPromptSubmit | 0.4–0.5 s |
| each Edit's PreToolUse plus PostToolUse | about 0.5 s |
| **Stop** | **9–28 s, median 21 s** |
| of which test strength (mutation) | **3–21 s, median 16 s** |
| of which the suite, the base-tree suite and confirmation | about 4 s |
| `ep_check --all`, when the agent runs it | about 3 s |

Stop, 1–3 s of tool hooks and the agent's own `ep_check` add up to about
29 s. That is most of the 33 s gap. The run had four conversations at once
and this replay had one, so the replay is a floor.

**The largest single cost is the mutation step at Stop.** It takes about
half the gap, and it ended "incomplete" at its mutation limit in all nine
replays.

## Found on the way: a test id cut at its first space

In 2 of the 9 replays the confirmation command named a test id cut at a
space inside its parameters (`test_bad_settings_are_refused[raw4-setting`,
`test_damaged_ledger[something`). pytest cannot find it, so confirmation
ends "incomplete".

## Bounds

- **Floor, not a measurement of the run.** The replay is unloaded, on one
  machine, one stage per case, with the stage's whole change written at
  once.
- **What the mutation step tells the agent was not measured here.** Cutting
  it saves time; whether it costs information is a separate question.
