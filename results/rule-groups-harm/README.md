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
