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

### Pilot result: the harness qualifies, and delivery has a gap

All 12 runs completed, with nothing lost to infrastructure: $1.63, 43–136
s each ([batch](E:/ep-runs/rule-groups-acted-on-pilot-2026-11-04)).

| stage | control: dependent lost | rules: dependent lost |
|---|---|---|
| `household_budget` 7 | 3 of 3 | 1 of 3 |
| `recipe_box` 4 | 3 of 3 | 0 of 3 |

As pre-registered, this is not read for an effect. Reading the transcripts
shows why it must not be. The note reached the agent in only 3 of 6 rules
runs:

- **Note received:** in both `household_budget` runs that kept the
  dependent, and in `recipe_box` 2, the agent edited a declared file with
  the Edit tool, and the brief named the other file.
- **Note never received:** in `recipe_box` 0 and 1, the agent wrote every
  file by running Python in Bash. No Edit was made, so no brief fired.
  Neither run read `elevenpowers.milestones.json`, and the session-start
  context is the same in both arms. Those agents found the dependent on
  their own, so the arms' difference there is not the note's.
- **Note never received, dependent lost:** `household_budget` rules 1 also
  edited through Bash.

**Decision:** the full run waits for a repair. A rule note has to reach an
agent that edits through the shell as well. It is repaired, rehearsed again
at $0 on the shell path, and only then sealed and run. The pilot batch is
kept as it is.
