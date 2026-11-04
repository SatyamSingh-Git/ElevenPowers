# Do certified rules do harm where no one needs them? (PLAN §13 B)

**Status: design, 2026-11-04, written before any run of it.**

## Question

The acted-on experiment
([design](2026-11-04-rule-groups-acted-on-design.md),
[results](../../../results/rule-groups-acted-on/README.md)) found the
certified rule note cut lost dependents from 35 of 50 to 4 of 50. It ran
only the five stages chosen for their v3 losses. Two of its pre-registered
secondaries were therefore unmeasured:

- the outcome on the other covered stages;
- edits to declared files where nothing needed them.

A note that says "change them together" could make agents edit files a
stage never needed, or break something while doing so. **On the stages
where the rule is not the point, does the note do harm?**

## Stages ([scan](../../../results/rule-groups-harm/stage_scan.py), [output](../../../results/rule-groups-harm/stage-scan.json), $0)

Certification is the acted-on experiment's simulated perfect reviewer,
unchanged. Of v3's 96 stages:

- **20 other covered stages.** A certified rule covers the stage's broken
  pair, and the stage is not one of the five already run. v3 lost the
  dependent on none of them (0 of 5 each).
- **33 self-contained stages.** No dependent is declared. In 28 of them
  the reference changes no declared file. The other 5 are run but excluded
  from the unneeded-edit measure.

The 38 uncovered stages are not run. No certified rule names their broken
pair, so the note cannot speak there.

## Design

The harness, model (Sonnet 5.5, medium), arms, certification, time limit
and sealing are the acted-on experiment's, unchanged:
`eval/rule_groups_run.py` at its current hash. Each of the 53 stages runs
once per arm, which is 106 runs. Breadth was chosen over replicates.

**Primary (harm):** a run regresses when any oracle group that passed
before the stage fails after it, the stage's declared dependent group
excepted. The dependent is the acted-on outcome, already measured.

- **Comparison:** rules against control, stratified by stage.
- **Test:** the runner's exact one-sided stratified test, with the arms
  swapped so it asks whether the rules arm regresses more. α = 0.05.
- **Reading:** a significant result is harm. A null result rules out only
  a large harm, by the size below.

**Secondary, each reported whatever it shows:**

- **Edits beyond the reference.** On the 28 self-contained stages whose
  reference changes no declared file, a run changed a declared input. This
  is an upper bound on unneeded edits, since another implementation may
  touch the file for good reason. Same test, for more.
- **Dependent lost** on the 20 covered stages, per arm. Descriptive, plus
  the acted-on test for fewer. v3's base rate was 0, so little effect is
  expected.
- **Request done:** the stage's own new groups pass, per arm.
- **Cost and model time,** per arm.
- **Delivery:** rules-arm runs briefed on a declared file.

**Size** ([`power.py`](../../../results/rule-groups-harm/power.py),
[output](../../../results/rule-groups-harm/power.txt)). 106 runs, about $17
at the acted-on rate of $0.164 per run, and about an hour at four at a
time.

| control regression rate | rules rate | power |
|---|---|---|
| 5% | 5% (no harm) | 1% (false positive) |
| 5% | 15% | 39% |
| 5% | 25% | 88% |
| 10% | 30% | 79% |

It detects a harm of about 20 points. Two runs per arm would detect about
10 points, at about $34. That was declined for now: if this run shows a
hint of harm, the hinted stages get their own follow-up.

## Gates

1. **$0 rehearsal on all 53 stages.**
   - The declarations load, and only the rules arm has them.
   - The reference is graded as regressing nothing, with the request done.
   - The untouched tree is graded as request not done. Where it is graded
     done, that stage's request-done result is reported as uninformative,
     never dropped.
2. **No pilot.** The harness, model, runner and arms are the ones the
   acted-on run qualified on 100 of 100 runs this same day. The first
   slots are watched for infrastructure.
3. **Seal and run** the 106, never retrying. Every attempt is kept.

## Bounds known in advance

- One run per arm per stage: small harms (under about 15 points) can be
  missed.
- Certification is perfect by construction, so a wrongly certified pair,
  the likeliest source of harm, is not tested here.
- One stage from the reference tree is not a conversation.
