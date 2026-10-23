# Held-out vacuity by arm — design

> **Executed 2026-10-23.** 240 sealed runs on 40 held-out tasks: VACUOUS among resolved 84% ordinary vs 37% assisted, per-task p = 0.00016, resolve rate unchanged. See [results](../../../results/heldout/sweep-2026-10-22/README.md) and [validation](../../validation/2026-10-23-heldout-vacuity.md).

## Intent

The one benefit signal this project has seen came from a secondary metric of a
sweep that was not designed for it: in the `chunks` sweep, resolved patches with
no test that could fail without the change were 10 of 46 under the ordinary arm
and 4 of 49 under the gate (per task 5 fewer, 0 more, 19 tied, p = 0.062;
`results/b9-gate-tests/`). Its pre-registered primary metric was a null. PLAN
§10 says what would settle it: vacuity by arm, in one sweep, by one method. That
is the question here, asked of the current runtime on tasks this project neither
wrote nor tuned on, with the analysis fixed before any run.

## Estimand and analysis (fixed now)

- **Population:** single-commit bug-fix/feature tasks mined from the history of
  independently selected open-source Python libraries (rule below).
- **Unit:** the task. Replicates are aggregated per task, never treated as tasks.
- **Primary outcome:** per task and arm, the fraction of *resolved* runs whose
  patch is VACUOUS (reverting the patch's source change leaves every test in the
  candidate tree passing; the B7/B9 probe in `core/stress.py`'s sense).
- **Primary test:** two-sided Wilcoxon signed-rank over tasks of
  (ordinary − assisted), α = 0.05, tasks where either arm has no resolved run or
  the fractions tie are dropped and counted. `eval/vacuity_power.py` implements
  the same statistic for planning.
- **Secondary, reported beside it, never substituted:** resolve rate per task
  (exact sign test over discordant tasks), regressions, model-process seconds,
  cost, owned-runner adoption and declared-check delivery stages per run.
- **Claim limit:** the measured tasks, this model and this runtime. A null is a
  null; a difference is not a coding-quality claim beyond vacuity.

## Size (from simulation, before spending)

At B9's observed rates (22% vs 8%, odds ratio 0.31), task heterogeneity σ = 1,
resolve 0.92: signed-rank power ≈ 0.82 at 40 tasks × 3 replicates (240 runs) and
0.82 at 60 × 2; a repeat of B9's 100 runs has 0.39. At odds ratio 0.5 (a likely
smaller true effect after selection) 240 runs give ≈ 0.44. **Design: 40 tasks ×
3 replicates × 2 arms = 240 runs**, Sonnet 5.5 medium (standing authorization),
subscription only. The full sweep starts only after the pilot measures cost and
resolve rate and the estimate is restated.

## Independent sourcing rule (frozen before mining)

1. **Repositories:** from a public ranking this project does not control (the
   most-downloaded PyPI packages list), in rank order, keep a package whose
   GitHub source is pure Python, tested with pytest, permissively licensed, and
   not one of the libraries used for tuning (click, attrs, jinja2, markupsafe,
   itsdangerous, or anything else in `eval/corpus*.lock`).
2. **Commits:** non-merge commits dated after a fixed cutoff that touch source and
   test files and pass `eval.mine.validate` (fail-to-pass at the parent, pass at
   the fix, green suite at the parent).
3. **Order:** by sha256(seed ‖ commit sha), with a per-repository cap so no
   library supplies more than a fixed share; the first 40 that validate are the
   corpus. Every rejected candidate is retained with its reason.

## Closed book

The workspace has no Git history; network-reaching tools stay denied; the
answer must not be importable from site-packages (the task's package is not
installed in the environment, or is installed at the base version). A canary
check confirms the fix is unreachable before any paid run.

## Arms

- **ordinary:** Claude Code with no ElevenPowers configuration.
- **assisted:** ElevenPowers installed through `core.hosts.setup.install` with the
  project's own test command declared, exactly as a user would get it.
Same prompt (the commit's message, wrapped as `eval.mine` already does), same
time cap, same tools. Arms interleave per task; replicates alternate order.

## Phases

1. **Sourcing (no model):** apply the rule, clone, mine, validate, lock. Rehearse:
   gold passes, base fails, the vacuity probe is calibrated on gold patches.
2. **Harness (no model):** a sealed, never-retry runner on the subscription path
   (`eval.subscription`) for mined tasks, reusing `eval.live` materialise/grade
   and `eval.preservation`'s sealing; fake-host controls.
3. **Pilot (paid, small):** 4 tasks × 2 arms × 1 replicate — cost per run,
   resolve rate, engagement, harness health. Not analysed for the estimand.
4. **Sweep (paid):** 240 runs, frozen schedule pushed before launch, every
   attempt retained, analysis exactly as above.

## Not in scope

Selection between candidates, other models, effort levels, or any claim about
correctness beyond the secondary report.
