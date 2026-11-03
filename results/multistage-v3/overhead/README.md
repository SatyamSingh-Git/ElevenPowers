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

~~Stop, 1–3 s of tool hooks and the agent's own `ep_check` add up to about
29 s, most of the 33 s gap; the largest single cost is the mutation step at
Stop.~~ **Withdrawn the same day.** The replay is not how the run's stages
began; see the next section.

## The Stop runs the conversations actually made ([`stopphases.py`](stopphases.py))

The replay committed each stage's starting snapshot, so the stage's edits
were the only change and the mutation step examined them. The run never
committed between stages. From stage 2 on, every earlier stage's edit was
already uncommitted when the task opened, and the mutation step refuses
those files: whose change they are cannot be told.

Each conversation's `verification.json` keeps its recent Stop runs: 125
from the 60 ElevenPowers conversations, all from later stages
([output](stopphases.txt)).

| per Stop run | median | mean |
|---|---|---|
| **whole run** | **5.3 s** | **6.1 s** |
| base-tree suite | 2.0 s | 2.1 s |
| confirmation | 1.0 s | 1.2 s |
| test strength | 0.6 s | 0.8 s |
| worktree and Git inspection | 0.4 s | 0.5 s |

All 125 ended test strength with "changed source was already dirty when
the task opened" and examined no mutant. A first stage starts clean and
would run the whole analysis, as the replays did; none of those runs was
kept.

So Stop, the tool hooks and the agent's own `ep_check` account for about
10–12 s of the 33 s per stage. **About 20 s per stage is not attributed.**
Four conversations shared the machine during the run, and this file does not
measure what that cost.

## What the mutation step tells the agent: nothing, here

Its result goes to `strength.json`, the exported report and the doctor's
health view. Neither the Stop message nor the gate message carries it. In
the 60 conversations no agent ran the export or the doctor, and no
assistant message mentions mutants or test strength.

## Found on the way: a test id cut at its first space

In 2 of the 9 replays the confirmation command named a test id cut at a
space inside its parameters (`test_bad_settings_are_refused[raw4-setting`,
`test_damaged_ledger[something`). pytest cannot find it, so confirmation
ends "incomplete".

## Bounds

- **The replay is a floor, but not of the run.** It is unloaded, on one
  machine, one stage per case, with the stage's whole change written at
  once, and it starts each stage clean, which the run did not.
- **The real Stop runs are later stages only.** `verification.json` keeps
  recent runs, so no first-stage Stop is measured.
- **"Tells the agent nothing" is this harness's flow.** A person who runs
  the export or the doctor does see the analysis.
