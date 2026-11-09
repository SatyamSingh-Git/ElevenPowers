# Confirmed: a rule worded as an instruction, 5 of 60 lost against 23 of 60

[Design](../../docs/superpowers/specs/2026-11-09-rule-as-mandate-confirmation-design.md),
committed (`f971d4f`) before any run. This is a fresh replication of
[the first run](../rule-mandate/README.md) (2 of 20 against 6 of 20,
p = 0.12), never pooled with it.

## Result

| `household_budget` 7, 60 runs per arm | `rules` (description) | `described` (instruction) |
|---|---|---|
| **Dependent lost** | 23 (38%) | **5 (8%)** |
| Silent losses: the final message never names `month_end` | 1 | 0 |
| Losses that offer the change or ask the user | 22 | 4 |
| `annual.py` changed (needless; the harm check) | 0 | 0 |
| Another group lost | 0 | 0 |
| Cost | $9.31 | $9.37 |
| Mean wall time | 88.3 s | 85.6 s |

**Primary:** exact one-sided test, `described` loses fewer:
**p = 8.3 × 10⁻⁵**, against the α = 0.05 fixed in advance. There was no
harm in `described`. By the design's rule the benefit is **confirmed on this
stage**:
- the README states it as a result;
- `ep_milestones --propose` now writes each entry as the tested
  instruction, "`A` (file) and `B` (file) must stay consistent: change both
  in the same task", in place of a `TODO`.

**What it means.** On a stage where the request ("make `budget status` net
refunds") and a declared rule pull apart, the agent follows a rule worded as
an instruction about four times as often as one worded as a description.
- The instruction was on all 11 rules, including one whose other file no
  correct run changes. No run edited that file because of it.
- So the wording raised compliance where the rule mattered, without
  overreaching where it did not.

## Run

- 120 slots, sealed: 119 launched after one harness-check slot
  (`rules--0`), read in full.
  - Its config was `guide` with `rule_gate` false.
  - It carried the template description.
  - The note was delivered for both files.
  - The init event listed the same plugins as the first run.
- The same runtime fingerprint, harness hash and rule texts as the first run,
  checked from the two protocols.
- Sonnet 5.5 at medium effort, Claude Code 2.1.292. **$18.68.** All 120
  completed, none retried, none read before the last finished.
- [`analysis.json`](analysis.json) and [`analysis.txt`](analysis.txt) come
  from `results/rule-mandate/analyse.py`, unchanged. Its output was moved
  here so the first run's analysis is not overwritten. The launch log is
  [`launch.log`](launch.log).

## Bounds

- **One stage,** chosen because a request and a rule conflict there.
  Confirming it here does not show it on other stages or projects.
- **One generated sentence** per rule, the same for all 11, not a person's
  words.
- **Sonnet 5.5 at medium effort only.**
- "Names `month_end`" and "offers or asks" are pattern matches on the final
  message.
