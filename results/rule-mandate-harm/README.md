# "Change both" where only one side should change: no harm found

[Design](../../docs/superpowers/specs/2026-11-10-rule-as-mandate-harm-design.md),
committed (`1fe5f48`) before any run. Inputs:
- [`descriptions.json`](descriptions.json): the instruction for every
  reviewed rule in all 12 cases, by `../rule-mandate/describe.py`;
- [`analyse.py`](analyse.py) ([output](analysis.json)), written before the
  run;
- the acted-on [`launch.py`](../rule-groups-acted-on/launch.py)
  ([log](launch.log)).

## Result

On all 45 v3 stages where the correct reference changes one side of a
reviewed rule and not the other, so that "change both" is the wrong
instruction:

| 45 stages, 1 run per arm | `rules` (description) | `described` (instruction) |
|---|---|---|
| **Any group lost** | 3 | 3 |
| Runs with a needless edit | 2 | 2 |
| Dependent lost | 3 | 3 |
| Cost | $6.42 | $6.79 |
| Mean wall time | 80.0 s | 80.4 s |

A needless edit is an edit to a file a left-behind rule names, which the
reference does not change.

**Primary:** exact one-sided stratified test, `described` loses more:
**p = 0.75**. By the design's rule, the proposer's instruction default stays.
The no-harm finding now covers these 45 stages as well as the confirmed one.

**The instruction did not make agents edit the other file.**
- The needless edits came in identical pairs: the same file on the same stage
  in both arms (`fleet_service` 3, `household_budget` 1). So the request
  invites them, not the wording.
- The losses show no pattern:
  - two stages lost in both arms (`gradebook` 4, `parcelpost` 5);
  - one in `described` only (`hotel_desk` 7);
  - one in `rules` only (`survey_tally` 5).
- **The measure is not vacuous.** All 90 runs edited source files, a median
  of 4 files, and the measure fired 4 times.

**Read with the confirmation run,** the instruction is followed where the
rule matters (5 of 60 lost against 23 of 60). Here, on 45 stages where it
does not, agents did not act on it wrongly. They appear to tell "change how
one works" from a change that leaves the shared behaviour alone.

## Run

- 90 slots, sealed: 89 launched after one harness-check slot
  (`gradebook--2--described--0`), read in full.
  - Its config was `guide` with `rule_gate` false.
  - It carried 8 instruction-worded rules.
  - Notes were delivered for 3 files.
  - There was no breach.
- Sonnet 5.5 at medium effort. **$13.21**, all 90 completed, none retried.
- **The host changed overnight.** All 90 runs used Claude Code **2.1.319**,
  where the earlier batches used 2.1.292. The init event lists one more
  built-in plugin, `cc-plugin-privacy`. Both arms share the version, so the
  comparison here holds. Comparing with earlier batches crosses a host
  change.
- The harness hash equals the confirmation run's. The runtime differs only by
  the proposer change, which these runs do not use: their rule texts come
  from the sealed protocol.

## Bounds

- **One run per arm per stage,** so only the pooled test is read. A harm
  rarer than about one stage in five can be missed.
- **The cases are built,** not real projects.
- **Needless edits are counted by file,** not by whether the edit changed
  behaviour.
