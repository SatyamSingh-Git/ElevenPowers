# Is a reviewed rule acted on? The acted-on design, with a reviewer's certification (PLAN §13 B)

**Status: design, 2026-11-05, written before any run. It follows from a
decision fixed in advance**
([reviewer design](2026-11-05-rule-groups-reviewed-design.md)). The blind
reviewer kept 16 of 27 pairs, past half, so the acted-on design reruns with
its certification in place of the perfect one.

## Question

With a perfect certification, the dependent was lost in 35 of 50 control
runs and 4 of 50 rules runs
([results](../../../results/rule-groups-acted-on/README.md)). **With the
pairs a reviewer actually keeps, how much of that holds?**

## Design

Everything is the [acted-on design](2026-11-04-rule-groups-acted-on-design.md),
as amended before its sealing:

- the harness, model (Sonnet 5.5, medium), arms, time limit and sealing;
- the five primary stages, ten replicates per arm, 100 runs, about $16;
- the primary outcome and its exact one-sided stratified test, α = 0.05,
  pre-registered direction "rules lose fewer".

One thing changes. **Certification:** the rules arm declares the
proposals the reviewer kept for that case
([`reviewed.json`](../../../results/rule-groups-reviewed/reviewed.json)),
all of them, frozen into the sealed protocol. Each entry is built exactly
as the perfect certification builds it: the neutral template description
and the case's test command.

That means:

- on 4 of the 5 stages a kept rule covers the broken pair;
- on `parcelpost` 5 none does;
- every case also declares the reviewer's other kept pairs, 4–11 per case
  here, which bring notes on files no stage needs.

**Secondary, each reported whatever it shows:**

- per stage, against the perfect-certification run (descriptive, not
  tested: the two runs are not concurrent);
- **harm:** other groups lost; cost and model time;
- **delivery:** briefed runs, and how many distinct rule notes a run
  received, to see whether the extra declared pairs crowd the note that
  matters.

## Gates

1. **$0 rehearsal.**
   - The reviewed declarations load, and only the rules arm has them.
   - On the four covered stages, the replayed Edit and shell write bring
     the note naming the dependent.
   - On `parcelpost` 5 they do not, which is the gate's adversarial check.
2. **No pilot.** The harness is the acted-on one, qualified on 206 runs.
   Only the certification differs, and that is tested before sealing.
3. **Seal and run** the 100, never retrying.

## Bounds known in advance

- A model reviewer, not a person. It saw the proposals as a person would,
  but did not know the project.
- The template description, as before.
- The same five stages, chosen for their v3 losses.
