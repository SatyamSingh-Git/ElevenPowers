# A rule worded as an instruction: 2 of 20 lost against 6 of 20, not significant

[Design](../../docs/superpowers/specs/2026-11-09-rule-as-mandate-design.md),
committed (`0cbd317`) before any run. Inputs:
- [`describe.py`](describe.py) ([descriptions](descriptions.json));
- [`rehearse.py`](rehearse.py) ([output](rehearsal.json), 5 of 5);
- [`analyse.py`](analyse.py) ([output](analysis.json)), written before the
  batch finished;
- the acted-on [`launch.py`](../rule-groups-acted-on/launch.py)
  ([log](launch.log)).

## Result

| `household_budget` 7, 20 runs per arm | `rules` (template) | `described` (instruction) |
|---|---|---|
| **Dependent lost** | 6 | **2** |
| Silent losses: the final message never names `month_end` | 1 | 0 |
| Losses that offer the change or ask the user | 5 | 2 |
| `annual.py` changed (needless; the harm check) | 0 | 0 |
| Another group lost | 0 | 0 |
| Cost | $3.42 | $3.34 |
| Mean wall time | 136.4 s | 92.8 s |

**Primary:** exact one-sided test, `described` loses fewer, **p = 0.12**. That
does not clear the 0.05 fixed in advance, so by the design's rule this is a
**null**:
- the rule stays a note;
- nothing changes by default;
- the instruction-following angle is not built on from this result.

**What it does and does not show:**
- **The direction favours the instruction**, with no harm. The instruction
  was on all 11 rules, including `year_report`/`_carried_into`, and no run
  edited `annual.py` because of it.
- **It is underpowered for an effect this size.** The template arm lost 30%
  here, below the 40% the power estimate assumed, and 20 runs per arm cannot
  reliably separate 30% from 10%.
- **Only a fresh, larger, pre-registered run can settle it.** Pooling more
  runs into this one after seeing it would be retrying for a favourable
  result, which this project does not do.

## What the agents said

Both instruction-arm losses told the user and gave a reason.
- One said it was "checking the two consistency notes from the hook". It
  found that `_carried_into` was untouched, then decided: "The month-end
  `summarise` is a different matter, so I'm leaving it unchanged on purpose
  and saying so below."
- The harness check's run, which kept the dependent, explained its edit as
  following the project: "your project has a rule that these two functions
  change together".

So an explicit "must" is followed more often, and when it is overridden the
override is told to the user, never silent. ElevenPowers' own note still ends
"or say why one should differ" in both arms. That exit was not varied here.

## Run

- 40 slots: 39 launched after one harness-check slot (`described--0`), read
  in full.
  - Its config was `guide` with `rule_gate` false.
  - The rule file carried the instruction.
  - The ledger's `briefed` shows the note was delivered for both files.
  - The init event listed the same plugins as the earlier batches.
- Sonnet 5.5 at medium effort, Claude Code 2.1.292. **$6.76**, all 40
  completed, none retried.
- **One run did not do the request.** `rules--11` changed no source file in
  782 s, only tests, and counts as kept by the protocol. Without it the
  template arm is 6 of 19, and the conclusion does not change.

## Bounds

- One stage, chosen because the request and a rule conflict there.
- The instruction is one generated sentence, not a person's explanation of
  why the two must agree.
- "Names `month_end`" and "offers or asks" are pattern matches on the final
  message.
