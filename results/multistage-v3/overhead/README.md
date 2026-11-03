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

Stop is therefore a smaller part than the replay said. The next section
finds where the rest goes.

## Where the 35 s goes, from the transcripts' own clocks ([`stagewall.py`](stagewall.py))

Each stage's `result` event records the process's startup
(`time_to_request_ms`, with its hook phase), and every assistant and user
event is timestamped. Every tool call can be timed from the event that asked
for it to the event that returned it. Calls asked for together run together,
so the total counts their union. All 480 stages per arm
([output](stagewall.txt)).

| mean per stage | ElevenPowers | superpowers | difference |
|---|---|---|---|
| wall | 76.7 s | 41.8 s | **34.9 s** |
| startup (SessionStart, UserPromptSubmit) | 1.5 s | 0.2 s | 1.4 s |
| tool calls | 27.3 s | 8.9 s | **18.4 s** |
| the model, between tool calls | 30.1 s | 33.8 s | −3.7 s |
| after the last event (Stop, exit) | 17.8 s | −1.1 s | 18.9 s |

The last row's superpowers mean is pulled below zero by stages whose
background tasks reported after the result. Medians are 12.8 s against
2.9 s, a gap of about **10 s**.

Per call, median. Edits asked for in one turn run one after another, so a
call's own cost starts when the result before it arrived, not when it was
asked for. An earlier version of this table timed from the ask, which
counted the queue (Edit 3.17 s, Read 0.90 s).

| call | ElevenPowers | superpowers |
|---|---|---|
| Edit | **2.31 s** (839) | 0.03 s (497) |
| Read | **0.58 s** (764) | 0.02 s (582) |
| shell, not tests | **2.53 s** (943) | 0.45 s (1,045) |
| shell, tests | 3.63 s (690) | 1.80 s (1,103) |
| shell, `ep_check` | **7.40 s** (332) | — |

**Half the gap is the hooks on ordinary tool calls.** An Edit runs two
ElevenPowers hook processes, a shell call two and a Read one. In the run
each cost about 0.6–1.2 s. Inside the hook, the work itself had a median of
25 ms before a tool and 77 ms after it (`integrations.json`, 3,954
samples). The rest was starting the hook.

Run alone on copies of two conversations' final trees
([`edithook.py`](edithook.py), [output](edithook.txt)), the same hooks take
0.44 s for an Edit and 0.21 s for a Read. That holds with the run's own
23–70 KB ledger and with the state reset, so accumulated state is not the
cause. The run had four conversations sharing the machine. Its load is the
remaining candidate, and it is not measured.

Run alone, a Read's hook takes 0.218 s:

| part | time |
|---|---|
| bare interpreter | 0.037 s |
| imports (`core.hook`, 0.103 s, and what it pulls in) | 0.144 s |
| the work | about 0.04 s |

The work is `ledger.saw(path)`. It is not idle: the scope check before an
edit (`unrelated(here, ledger.seen, …)`) reads it, so dropping the Read hook
changes behaviour. Of the imports, most is the ledger itself (0.103 s) and
the standard library under it. Deferring the rest saves about 13%.

## Fixed: every hook started PowerShell first (`407d749`)

On Windows the installer wrote each hook as `powershell.exe -NoProfile
-NonInteractive -EncodedCommand …`. That form is correct whether a host
runs hooks through cmd, PowerShell or bash.

Claude Code 2.1.292 runs them through Git Bash: `claude.exe → bash.exe →
bash.exe → python`. That was seen at $0 by a hook that recorded its own
parents and then blocked the prompt before any model call. PowerShell in
between did nothing for that host and cost 0.17 s a start alone, 0.26 s
under load.

When every path is plain, the Claude command is now bare words. Otherwise
it keeps the encoded form, which bash also runs. The other hosts are not
shown to use bash and are unchanged.

| real Claude Code, real hooks, prompt blocked (no model call) | median of 5 |
|---|---|
| encoded hook commands | 3.95 s |
| plain hook commands | 3.69 s |

That saving is SessionStart alone. Both forms processed 5 of 5 SessionStart
and UserPromptSubmit callbacks with no errors. The tests require exit code 2,
which a Stop block uses, to survive Git Bash in both forms.

At the run's rate of about 15 hook calls per stage, the saving is roughly
3–4 s of the 35 s per stage. That is an estimate from the per-start figures;
no paid run has measured it.

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
