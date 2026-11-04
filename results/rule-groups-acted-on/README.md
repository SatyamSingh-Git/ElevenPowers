# Does an agent act on a certified rule?

PLAN §13 B, open problem 2.
[Design](../../docs/superpowers/specs/2026-11-04-rule-groups-acted-on-design.md),
written before any run. Harness: [`eval/rule_groups_run.py`](../../eval/rule_groups_run.py).

Each run is one v3 stage from its reference tree. The arms are superpowers
plus ElevenPowers as shipped, identical except that `rules` carries the
case's certified rules in `elevenpowers.milestones.json`. Certification is a
simulated perfect reviewer of the stage-0 proposals, fixed in advance and
frozen into the sealed protocol.

## Gate 1: $0 rehearsal, passed 5 of 5 ([`rehearse.py`](rehearse.py), [output](rehearsal.txt))

On each primary stage:

- the stage's pair is certified (2–3 declared rules per case);
- the declarations load, and only the rules arm carries them;
- the reference edit, replayed through the real hooks, brings a brief naming
  the dependent before the rule's other file is edited;
- the grader scores the reference as kept and the left-behind variant as
  lost.

## Gate 2: pilot, launched 2026-11-04

Two stages chosen for their v3 baseline:

- `household_budget` stage 7, lost 5 of 5 in v3;
- `recipe_box` stage 4, lost 4 of 5.

Three runs per arm on each: 12 runs, about $2, Sonnet 5.5 at medium effort,
sealed in `E:/ep-runs/rule-groups-acted-on-pilot-2026-11-04`.

The first slot was the harness check: completed, $0.14, 103 s, and the
control arm lost the dependent. The pilot must show four things:

- the harness runs;
- the brief is received in the rules arm;
- the control arm loses the dependent at least once;
- no run is lost to infrastructure.

It is too small to show an effect and is not read for one.
