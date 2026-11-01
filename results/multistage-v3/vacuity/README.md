# VACUOUS by arm on the v3 snapshots ($0)

[`PLAN.md` §13](../../../PLAN.md#13-two-directions-reviewer-evidence-and-coding-helper)
A, step 2. The held-out sweep measured VACUOUS falling from 84% to 37% with
ElevenPowers, but superpowers was in neither arm. In v3, superpowers was in
both. The question is whether the ElevenPowers arm leaves fewer changes that
no test pins.

## Pre-registration (written 2026-11-01, before any feature stage was computed)

**Method.** This uses the held-out sweep's own check, `eval.heldout_vacuity.vacuity`,
on each stage's kept trees: snapshot *n−1* is the base and the patch is snapshot
*n*. The v3 grader already runs this on bugfix stages as `test_with_fix`
(`eval/multistage_oracles.rules`); here it runs on every stage.
- A stage is **VACUOUS** when two things hold: its changed non-test Python
  files are put back to the pre-stage version, and the post-stage tree's own
  tests stay green.
- Tests already red with the change are deselected.
- A no-op control must stay green, or the stage is not scored.

**Denominator.** The resolved stages: every group the case introduces at that
stage passes on the post-stage tree. A stage that cannot be scored (no source
change, patch did not apply, suite timed out, survive control failed) is
counted by reason, never as either value.

**Primary.** For each case, take the VACUOUS fraction among the scored
resolved stages. Pool across that arm's 5 conversations. The case's difference
is superpowers − ElevenPowers, so a positive value means fewer VACUOUS stages
with ElevenPowers. The test is an exact two-sided signed-rank over the 12 cases
(`eval.multistage_power.exact_signed_rank`). A case where either arm has no
scored resolved stage is dropped and counted.

**Reported beside it, never in its place:**
- bugfix and feature stages separately;
- pooled counts per arm;
- the unscored stages by reason.

**Known before computing.** The bugfix stages were graded at run time:
- superpowers: 65 of 65 resolved bugfixes carried a test that fails without the fix;
- ElevenPowers: 61 of 61 resolved, and 65 of 65 counting the unresolved ones.

So any difference has to come from the feature stages: 411 resolved in the
superpowers arm and 412 in the ElevenPowers arm.

**Checks on the method.**
- *Forward:* recomputed bugfix values must equal the recorded `test_with_fix`.
- *Adversarial:* on real trees, the check must be able to flag a stage. For
  each case and arm, take the first resolved stage that scores not VACUOUS,
  remove that stage's test changes, and run the check again. It should now
  come out VACUOUS. If it cannot, the check is refusing to flag anything here,
  and a low VACUOUS figure means nothing.

**Decision (PLAN §13 A.2).** If the ElevenPowers arm does not leave fewer
VACUOUS stages, then for superpowers users the reviewer value is the report
itself, not a change in what the agent does.

**Its bound.** The method keeps any file the agent added, because it puts back
only files that existed before. A feature written entirely in a new module
counts as pinned if a test imports that module. This matches the held-out
sweep, which shared the same bound.
