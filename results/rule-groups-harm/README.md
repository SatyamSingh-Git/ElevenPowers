# Do certified rules do harm where no one needs them?

PLAN §13 B, following [the acted-on result](../rule-groups-acted-on/README.md).
[Design](../../docs/superpowers/specs/2026-11-04-rule-groups-harm-design.md),
written before any run. Harness: [`eval/rule_groups_run.py`](../../eval/rule_groups_run.py),
unchanged from the acted-on run.

The acted-on run measured the note only on the five stages chosen for their
v3 losses. This run takes every stage it left out where a certified rule
could matter:

- the 20 other covered stages;
- the 33 self-contained stages.

Each runs once per arm, which is 106 runs.

## Inputs, $0

- [`stage_scan.py`](stage_scan.py) ([output](stage-scan.json)) classifies
  v3's 96 stages: 25 covered, 38 uncovered, 33 self-contained.
- [`power.py`](power.py) ([output](power.txt)): one run per arm detects a
  harm of about 20 points, with 79–88% power, and can miss smaller ones.
- **Gate 1** ([`rehearse.py`](rehearse.py), [output](rehearsal.txt))
  passes on 53 of 53 stages:
  - the declarations load in the rules arm only;
  - every reference regresses nothing and does its request;
  - no untouched tree does the request.
- [`analyse.py`](analyse.py) was checked before the run on the acted-on
  batch. It reproduces that run's p = 8.6 × 10⁻¹³ and gives p = 1.0 for
  harm. A synthetic rules-only regression gives p = 0.00098, and the
  reverse gives 1.0.

## Run: sealed and launched 2026-11-04

`E:/ep-runs/rule-groups-harm-2026-11-04` holds 106 one-stage runs at Sonnet
5.5, medium effort, about $17. The acted-on [`launch.py`](../rule-groups-acted-on/launch.py)
runs four at a time, in a seeded order fixed before the first launch. No
run is retried.

## Result: no harm found

All 106 runs completed, and none was retried. Cost was $15.52
([analysis](analysis-rule-groups-harm-2026-11-04.json), from
[`analyse.py`](analyse.py)).

| pre-registered measure | control | rules | one-sided p |
|---|---|---|---|
| **Primary:** a group other than the dependent lost | 0 of 53 | 0 of 53 | 1.0 (harm) |
| A declared file changed where the reference changes none | 0 of 28 | 0 of 28 | 1.0 (more) |
| Dependent lost, 20 other covered stages | 2 of 20 | 2 of 20 | 0.75 (fewer) |
| Stage's own request done | 53 of 53 | 53 of 53 | |
| Cost | $7.65 | $7.87 (+3%) | |
| Mean model time per run | 81.4 s | 101.8 s | |

- **Harm.** No run in either arm lost anything except a declared
  dependent, and no agent edited a declared file the stage did not need.
  One run per arm rules out a harm of about 20 points, not a small one.
- **Covered stages.** These are not the stages chosen for their losses.
  Each arm lost 2 of 20, so there was nothing to gain where v3 never lost.
  One rules-arm loss (`library_loans` 6) was never briefed, because the
  agent did not touch a declared file. The other (`hotel_desk` 7) was
  briefed, and that stage's control lost too.
- **Time, read with care.** The +25% mean is one run: `household_budget` 4
  in the rules arm took 792 s at an ordinary $0.21. Its own `python -`
  heredoc command hit the Bash tool's 120 s limit and was moved to the
  background, and the session waited for it. That happens inside the tool,
  before any hook runs. The median paired difference is +3.8 s.
- **The shell-path note's own cost, measured at $0.** The real PostToolUse
  Bash hook takes 0.331 s with declarations against 0.265 s without, the
  medians of 30 calls each. That is +66 ms a command. Rules-arm runs made
  4.6 shell calls on average, so about 0.3 s a run.

Together with [the acted-on result](../rule-groups-acted-on/README.md):
where a certified rule covers the broken pair and a loss is likely, the
note cut lost dependents from 35 of 50 to 4 of 50. Everywhere else it was
run, it changed nothing measurable. Certification was simulated as perfect
in both. A wrongly certified pair, the likeliest source of harm, is
untested.
