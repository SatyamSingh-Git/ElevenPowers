# The instruction wording on Sonnet 5: nothing to improve, 0 of 40 lost in both arms

[Design](../../docs/superpowers/specs/2026-11-10-rule-as-mandate-sonnet-5-design.md),
committed (`81c72b8`) before any run. It was amended before launch
(`ebdcebf`, `0654c28`) to 40 per arm after the harness-check slot cost $0.58.
The analysis is `../rule-mandate/analyse.py`, unchanged
([output](analysis.json), [text](analysis.txt)). The launcher is
[`launch.py`](launch.py) ([log](launch.log)).

## Result

| `household_budget` 7, `claude-sonnet-5`, 40 per arm | `rules` (description) | `described` (instruction) |
|---|---|---|
| **Dependent lost** | **0** | **0** |
| Changed both `budgets.py` and `month_end.py` | 40 of 40 | 40 of 40 |
| `annual.py` changed (needless) | 0 | 0 |
| Another group lost | 0 | 0 |
| Cost | $15.83 | $15.90 |
| Mean wall time | 185.9 s | 192.0 s |

**Primary:** p = 1.0. By the design's rule, the README states the instruction
benefit for Sonnet 5.5 only.

**What it means.** The rule did not fail to replicate. On Sonnet 5 there was
nothing to replicate. Every run, with either wording, made the matching
change to the month report. That was checked from the trees, not only from
the oracle: all 80 runs changed both files. On this stage it is Sonnet 5.5
that reads "make `budget status` net refunds" narrowly, and only Sonnet 5.5
needs the instruction to change both. Sonnet 5 was 3.5 times the cost per run
of Sonnet 5.5 here.

So the wording effect depends on the model:
- it matters where a model takes the narrow reading;
- it does no harm where a model does not.

That fits the harm check: the instruction made no needless edits across 45
stages.

## Run

- 120 slots sealed, 80 launched: replicates 0–39 of each arm, including the
  harness-check slot. Replicates 40–59 were never launched, as amended.
  - All 80 completed, none retried.
  - Every run's `observation.models` was exactly `claude-sonnet-5`.
- Claude Code 2.1.319.
- **$31.73.**

## Bounds

- One stage, two models of one family.
- With 0 losses in both arms, this says nothing about how Sonnet 5 would treat
  a case where it does take the narrow reading.
