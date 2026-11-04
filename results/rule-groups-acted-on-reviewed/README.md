# Is a reviewed rule acted on? 15 of 50 lost with it, 31 of 50 without

[Design](../../docs/superpowers/specs/2026-11-05-rule-groups-acted-on-reviewed-design.md),
written before any run. It reruns the
[acted-on experiment](../rule-groups-acted-on/README.md) with one change:
the rules arm declares the pairs a
[blind reviewer kept](../rule-groups-reviewed/README.md) (16 of the 27
that matter), not the perfect set.

Inputs: [`accepted.json`](accepted.json), the reviewer's kept ids for the
five cases, taken verbatim from its `reviewed.json`. Scripts:
[`rehearse.py`](rehearse.py), [`analyse.py`](analyse.py), and the acted-on
[`launch.py`](../rule-groups-acted-on/launch.py).

## Gate 1: $0 rehearsal, passed 5 of 5 ([output](rehearsal.txt))

- The reviewer's pairs load as declarations in the rules arm only: 4–11
  rules per case.
- On the four stages whose pair it kept, the Edit brief and the shell note
  both name the dependent.
- On `parcelpost` 5, whose pair it dropped, no rule note names it. This
  is the gate's adversarial row.

The first rehearsal failed that row, and the fault was in the check. It
matched the dependent anywhere in the brief, and `manifest.py`'s
import-neighbourhood line names `billing.py` in both arms. It now matches
rule notes only. The acted-on gate had the same loose Edit check; a
replay shows its rule note was there
([note](../rule-groups-acted-on/README.md)).

## Run

100 one-stage runs, sealed and launched four at a time, all completed,
none at the time limit: **$16.35**, 43 minutes. Sonnet 5.5 at medium
effort, with superpowers and ElevenPowers in both arms. The arms differ
only in the declarations file.

## Result

**Primary, pre-registered:** the dependent was lost in **31 of 50 control
runs and 15 of 50 rules runs**. The exact one-sided stratified test gives
**p = 7.3 × 10⁻⁵**, in the direction fixed in advance.

| stage | rules lost | control lost | perfect run: rules | perfect run: control |
|---|---|---|---|---|
| `household_budget` 7 | 5 of 10 | 5 of 10 | 1 of 10 | 8 of 10 |
| `recipe_box` 4 | 0 of 10 | 9 of 10 | 0 of 10 | 9 of 10 |
| `library_loans` 1 | 0 of 10 | 8 of 10 | 0 of 10 | 6 of 10 |
| `payroll_lite` 2 | 0 of 10 | 0 of 10 | 0 of 10 | 2 of 10 |
| `parcelpost` 5 | 10 of 10 | 9 of 10 | 3 of 10 | 10 of 10 |

The perfect-run columns are descriptive, not tested: the two runs were
not concurrent.

**Where the gap from the perfect run comes from:**

- **`parcelpost` 5 (10 of the 15 losses).** The reviewer dropped that
  pair. None of its ten rules runs was briefed on any of its four declared
  files, so none received a rule note, and the arm behaved as control (10
  against 9).
- **`household_budget` 7 (the other 5).** All ten rules runs got the same
  note naming the dependent as in the perfect run, listed first. The only
  difference is that the perfect run's brief carried a third note, about
  `closing.py`. Rules 1 against 5 of 10 is p = 0.14 two-sided. The
  stage's control arm moved about as far between the batches (8 against
  5, p = 0.35), so this does not separate a certification effect from
  run-to-run variation.
- **On the four covered stages:** 5 of 40 lost with rules, 22 of 40
  without. The perfect run had 1 of 40 and 25 of 40 there.

## Secondary, reported whatever they show

- **Delivery:** 40 of 50 rules runs were briefed on a declared file, and
  every one of them received the dependent's note; 5 of those 40 lost it.
  The 10 runs that received no note lost it all 10 times.
- **Crowding:** the reviewer's extra pairs did not crowd the note that
  matters. The most any run received was two notes (the `household_budget`
  runs), against three in the perfect run. Thirty runs got one note.
- **Harm:** no other group was lost in either arm (0 of 50 each). The
  rules arm cost 8% more ($8.49 against $7.86), with mean time 5% longer
  (97 s against 92 s).
- **Exploratory:** the request was done in 50 of 50 rules runs and 42 of
  50 control runs.

## Between the two batches

The runtime differs from the perfect run's by one commit, `76ff758`. It
changed the milestone-advice worker's deadline. That advice is off by
default, and no rules run in either batch has an `advice.json`, so it
never ran. The harness hash differs by the runner's certification code
(`accept`), which changes the declarations and nothing the agent runs.

## Bounds

- A model reviewer stands in for a person, and saw each project's
  proposals without knowing the project.
- The same five stages, chosen for their v3 losses, with the template
  description.
- Ten runs per stage and arm, so a single stage's difference of four runs
  is within its own between-batch variation.
- Where no kept rule covers the broken pair, nothing changes: the arm is
  control.
