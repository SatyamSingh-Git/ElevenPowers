# Multi-stage comparison v2: do earlier work and docs survive later steps?

**Status: pilot run 2026-10-28; no real headroom.** Neither arm lost any earlier
behaviour, and every stale fact was an oracle defect. The stage rules are to be
redesigned before the full run ([journey 92](../../../journey/92-the-pilot-found-nothing-to-prevent.md)).
The runner allows the Skill tool in both arms and keeps the operator's own
CLAUDE.md out; both were fixed at qualification. Twelve cases were written instead of eight, because the
power simulation showed eight cannot reach significance unless seven differ. The
cases are published at
<https://github.com/SatyamSingh-Git/elevenpowers-multistage-cases>; the build
record is [results/multistage](../../../results/multistage/README.md).

## Intent

Three developers using ElevenPowers on a real project report two effects a
single-fix sweep cannot see ([field report](../../field/2026-10-real-project.md)):

1. **Docs kept current.** About 95% of the time with superpowers plus
   ElevenPowers, against "often forgotten" with superpowers alone, under a
   `CLAUDE.md` rule that said to update the docs whenever work is done.
2. **No fix that breaks a dependent part.** With superpowers alone, once or twice
   a fix changed something other code depended on, the dependent code was not
   updated and a new bug followed. With ElevenPowers they have not met it. They
   attribute this to its blast-radius check.

They also report that it was slightly slower and used slightly more tokens.

This experiment tests those two claims as they were made: on a project that
evolves through several requests in one conversation, comparing **superpowers**
with **superpowers plus ElevenPowers**.

## Why the last multi-stage comparison could not answer this

The 2026-10-17 [matched comparison](../../../results/matched-workflow/README.md)
ran two authored four-stage cases, one conversation per arm. Both arms passed
every group at every stage. Its own verdict: *"There was no observed ordinary
regression for the assisted workflow to prevent."* Three things made that a
non-answer, and each one is changed here:

| 2026-10-17 | This design |
|---|---|
| No stage required changing code that earlier stages depended on, so there was nothing to break | Most stages change a shared function, format or default that earlier code relies on, and the request does not name the dependents |
| Two cases, one run per arm | 8 cases, replicated; size fixed by a power simulation before anything is frozen |
| Correctness only | Docs freshness and project-rule adherence are measured mechanically |
| Plain Claude Code against ElevenPowers | Superpowers in both arms, as in the field report |

The held-out sweep (2026-10-22) also compared plain Claude Code with
ElevenPowers. Its launcher reads project and local settings only, so no user
plugin loaded in either arm. That is a different comparison from the one the
field report describes.

## Goals

- **Co-primary outcome 1 — earlier behaviour lost.** Per conversation, the number
  of oracle groups that passed at the previous graded stage and fail now, summed
  over stages. This is the field report's "a fix that breaks a dependent part",
  counted mechanically.
- **Co-primary outcome 2 — stale docs.** Per conversation, the number of documented
  facts that are wrong or missing at the end of each stage, summed over stages.
  A documented fact is something the case's reference document states, such as an
  option and its default, an error message, or a record format.
- **Secondary outcomes:**
  - project-rule violations (listed under cases);
  - final cumulative correctness;
  - new-feature correctness per stage;
  - the vacuity of each stage's diff, using the held-out sweep's revert probe;
  - model-process time and cost per stage.

## Non-goals

- Not a population estimate. The cases are authored so that dependents and docs
  matter, which is what the claims are about. The result says whether the effect
  appears where it should, not how often such stages occur in real work.
- Not a test of plain Claude Code against ElevenPowers; the held-out sweep covers
  that.
- Python only. JavaScript owned-runner adoption was 0/4 in the last comparison,
  which would mix a delivery gap into the outcome.
- No runtime feature is added or tuned for this experiment. ElevenPowers runs as
  shipped, at the default `guide` profile.

## Anti-goals

These would make it a failure even if it ran cleanly:

- Cases or oracles adjusted after any arm's outcome is seen.
- Dropping or replacing a case because of how either arm did on it.
- A timeout, a missing stage or an ungraded stage counted as a pass, or dropped
  from the denominator.
- Requests that mention docs, tests or dependents. The field claim is that the
  rule in `CLAUDE.md` is followed without being repeated in each request.

## Arms

| | A — superpowers | B — superpowers + ElevenPowers |
|---|---|---|
| superpowers | enabled in the project's `.claude/settings.json` | same |
| ElevenPowers | absent | installed with `core.hosts.setup.install`, `Config(profile='guide')`, declaring the case's test command |
| `CLAUDE.md` | the case's project rules | identical |
| Model | Sonnet 5.5, medium effort | same |
| Time | 900 s per stage turn | same |

Both arms run in one persistent conversation per case and replicate, resumed
between stages, as in the 2026-10-17 controller. Arm order alternates by case and
replicate.

**Qualification for one cent, before anything else is paid:**
- one-turn runs show superpowers in the init event's plugin list in both arms;
- ElevenPowers' hooks appear only in arm B;
- the exact model is used, read from the stream as the held-out runner does.

If superpowers cannot be enabled at project scope through the subscription
launcher, stop and report it. Do not fall back to user settings, which would also
load every other user plugin.

## Cases

**Count and language.** Eight authored Python projects, each with six stages.

**Starting state.** Each case starts as a small working project of roughly 600
to 1,500 lines. It ships with:

- **source and its own public test suite**, green at the start;
- **a reference document** (`docs/reference.md`). It states the project's
  facts in a fixed shape: an options table with name, default and meaning, plus
  lists of error messages and record formats;
- **a `CHANGELOG.md`** with an `Unreleased` section;
- **one protected path** that the rules say must not be edited, such as
  `src/<pkg>/_generated.py`;
- **a `CLAUDE.md` with four project rules:**
  1. Keep `docs/reference.md` current whenever behaviour changes.
  2. Add a `CHANGELOG.md` entry for every change.
  3. Every bug fix carries a test.
  4. Never edit the protected path.

**Stages.** Each stage is one request, written the way a user writes one: a
feature or a bug fix.
- **Cross-cutting stages (at least four of the six):** the request changes a
  shared helper, a data format, a default or a signature that existing code and
  earlier stages depend on. The request does not name the dependents.
- **Self-contained stages (at least one of the six):** nothing else depends on
  the change. These are a control: there is nothing for a blast-radius check to
  find.
- **Docs:** every stage changes, adds or removes at least one documented fact,
  and no request mentions the docs.

**Independent authoring.** A fresh agent writes the cases, the reference
solutions and the oracles. It is given this section and the oracle rules below,
and nothing about how ElevenPowers works. A second fresh agent then reviews each
case for two things: that requests do not leak the dependents, and that the
oracles check behaviour rather than spelling. This mirrors the held-out rule that
whoever chooses the material should not know which arm it favours.

**Oracles.** All oracles stay outside the model's project directory.
- **Behaviour groups:** hidden tests, two base groups plus two per stage,
  cumulative. They check observable behaviour, never source spelling or a
  preferred implementation. This is the 2026-10-16 contract rule, unchanged.
- **Docs facts:**
  - For each stage, the reference solution lists the facts it changed, added and
    removed.
  - The oracle parses `docs/reference.md`, matching table rows by name and list
    items by key.
  - An added fact counts as current when it is present with the right value.
  - A changed fact counts as current when the new value is present and the old
    one is gone.
  - A removed fact counts as current when it is absent.
  - Restructuring the document so a fact cannot be found counts as stale. This is
    disclosed as a limit, and it is the reason rule 1 names the file.
- **Rules:**
  - The changelog rule counts entries added per stage.
  - The test-with-fix rule asks the revert probe whether each bug-fix stage's
    diff is non-VACUOUS.
  - The protected-path rule compares the protected file's hash.

**Rehearsal, no model.** Each case passes four checks:
- The reference solution passes every applicable group at every stage, and its
  docs and rules oracles report zero.
- A *dependent-missed* variant fails the earlier groups it should fail. In this
  variant the stage's change is made correctly but one dependent caller is not
  updated.
- A *docs-forgotten* variant fails exactly the facts its stage changed.
- A *no-op* variant fails the stage's new groups.

## Headroom gate

The 2026-10-17 tie came from a suite where nothing could go wrong. Before the
full run, a small paid pilot checks that something can.

**Pilot.** 2 of the 8 cases × both arms × 1 replicate: four conversations,
24 stage turns. The pilot cases are chosen by seeded hash before any run.

**Go or no-go for the whole suite.** Go if the pilot's arm-A conversations show
at least one lost earlier group **or** at least one stale fact. If neither appears,
the stages are too easy for this model. Redesign the stage rules for every case
and repeat the no-model rehearsal before any further spending.

**No case is filtered on its pilot result.** Keeping only the cases where
arm A failed would select A's unlucky draws, and A would regress toward its mean
in the real run, which would look like an ElevenPowers effect.

**Pilot runs are excluded from the analysis.** They measure cost, time and
headroom only.

## Size, power and cost

**Power simulation (no model).** It follows the method of
`eval/vacuity_power.py`:
- regressions and stale facts are counted per stage;
- each case has its own rate, with heterogeneity across cases;
- the arm effect is a rate ratio;
- the analysis is the one below.

It reports power across arm-A rates of 0.1 to 1.0 lost groups per conversation,
for rate ratios of 1.0, 0.5 and 0.3, for these layouts: 8 cases × 2 replicates,
8 × 3, and 12 × 2. The largest affordable layout with at least 0.8 power at
ratio 0.5 is chosen, and the rates come from the pilot. If none reaches that, say
so and run the cheapest layout as a descriptive study, labelled as such before
it runs.

**Cost and time, estimated before the pilot.** The basis is the held-out
calibration of $0.079 and 85 s per run, with assisted runs taking about 1.4× the
cost and 3.1× the model time. A stage turn in a growing project with
superpowers loaded is assumed to cost two to three times a single fix.

| | conversations | stage turns | estimated cost | estimated wall time |
|---|---|---|---|---|
| no-model rehearsal, power simulation | 0 | 0 | $0 | under an hour |
| one-cent qualification | 2–4 single turns | 2–4 | about $0.05 | minutes |
| pilot | 4 | 24 | about $4–7 | about 1–2 h |
| full, 8 × 3 | 48 | 288 | about $50–70 | about 19 h one at a time, about 5 h four at a time |
| full, 8 × 2 | 32 | 192 | about $35–50 | about 13 h one at a time, about 3.5 h four at a time |

These are floors and guesses until the pilot measures them. The pilot's measured
costs replace them before the full run is proposed.

## Analysis, fixed before any outcome

- **Unit:** the case. For each outcome, take the per-case mean over replicates of
  (arm A − arm B).
- **Test:** a two-sided Wilcoxon signed-rank test across cases, for each
  co-primary outcome. Holm correction across the two. Cases tied at zero are
  dropped from the signed-rank test and counted in plain sight. With 8 cases the
  smallest attainable two-sided p is 2/256 = 0.0078.
- **Comparable pairs:** a conversation counts for the primary outcomes only if
  every stage was attempted and graded. All others stay in the scheduled
  denominator with their state, as in the held-out sweep, and an incomplete
  conversation's outcome is reported as missing, never as zero.
- **Secondary outcomes** are reported descriptively per arm, with no tests.
- **Self-contained stages** are reported separately. An effect that appears only
  on cross-cutting stages is the pattern the blast-radius explanation predicts.
  An effect that also appears on self-contained stages points elsewhere.

## Built on

- the 2026-10-16/17 staged preservation controller and its resume-per-stage
  conversation (`eval/preservation.py`, `eval/input_scope_pilot.py`);
- the held-out runner's sealing, never-retry and stream-based
  model/breach/plugin reading (`eval/heldout_run.py`), and its revert probe
  (`eval/heldout_vacuity.py`);
- the signed-rank analysis (`eval/heldout_analyse.py`) and the power method
  (`eval/vacuity_power.py`);
- superpowers itself (MIT), enabled per project, as the baseline the field
  report used.

What this adds is cases with dependents and documented facts, plus oracles that
count lost earlier behaviour and stale docs.

## Integrity

- The protocol, cases, requests, oracles, analysis script and power choice are
  hashed and pushed before the first paid run.
- No launched conversation is retried.
- Every conversation, stage, timeout and failure is retained.
- Prompts and host output stay private.
- Authored cases, requests and grades may be published.
- Reference solutions and oracles stay outside the model's project directory.
  That is withholding, not an OS-level guarantee, and it is disclosed as such.

## Left to the builder

- Case topics, as long as they meet the case rules above and are varied:
  different domains, and at least two cases with a persisted data format.
- The exact docs table shape, as long as the docs oracle can parse it by name.
- Whether the power simulation lives in `eval/vacuity_power.py` or beside it.
- How the pilot cases are hashed, given a fixed seed.

## Exit

**Delivered** when every scheduled conversation and stage is accounted for and
regraded from exported snapshots. The record covers ties, incomplete runs and
results that go against ElevenPowers. The results README, `PLAN.md`, the status
page, a journey entry, the field report's "how it sits beside the measurements"
and the architecture graph are updated.

**What it can support:** whether, on authored projects built to have dependents
and documented facts, superpowers plus ElevenPowers loses less earlier behaviour
and leaves fewer stale facts than superpowers alone, with one model on one host.
A tie is published as a tie.
