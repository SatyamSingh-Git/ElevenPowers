# Held-out vacuity by arm — sweep of 2026-10-22

The question `PLAN.md` §10 left open after B7/B9: on tasks this project did not
pick, does an installed ElevenPowers change how often an agent's resolved patch is
VACUOUS (the repository's own tests cannot tell the patch from its absence)?

## Design (fixed before any outcome)

- **Tasks:** 40 from 12 permissive pure-Python repositories in the top-PyPI ranking,
  taken by the frozen rule in `results/heldout/corpus.json` and rehearsed 40/40 on
  their gold patches (`results/heldout/rehearsal.json`).
- **Arms:** *ordinary* Claude Code with no ElevenPowers configuration; *assisted*
  with ElevenPowers installed through `core.hosts.setup.install` and the task's own
  test command declared. Same prompt (the upstream commit message), tools and cap.
- **Runs:** 40 tasks × 2 arms × 3 replicates = 240, Sonnet 5.5 at medium effort on
  the subscription, 900 s cap, closed book, sealed (`protocol.json`, pushed in
  7911c69 before the first run) and never retried.
- **Primary analysis** (`eval/heldout_analyse.py`, committed before any run):
  per task, the VACUOUS fraction among resolved runs in each arm; two-sided
  Wilcoxon signed-rank over tasks of (ordinary − assisted). Tasks where either arm
  resolved nothing are dropped and counted; ties are counted.

## Result

| | ordinary | assisted |
|---|---|---|
| graded runs | 120 | 118 |
| resolved | 88 | 89 |
| VACUOUS among resolved | 74 (84%) | 33 (37%) |
| mean model-process seconds | 27.3 | 85.2 |
| total cost (subscription accounting) | $7.80 | $11.11 |

**Primary: p = 0.00016** (signed-rank over the 18 tasks whose arms differ).
Assisted had the lower VACUOUS fraction on 17 tasks, ordinary on 1
(uvicorn-31e3e00f); 13 tasks tied; 9 were dropped because an arm resolved nothing.

**Secondary:** resolve rates did not differ (assisted better on 3 tasks, ordinary
on 1, 36 tied; sign test p = 0.625). Assisted runs took about 3.1× the
model-process time and 1.4× the cost.

**Mechanism, descriptive:** 106 of the 107 VACUOUS patches contained no test file,
and 69 of the 70 non-VACUOUS ones did. Resolved ordinary patches added a test in
14 of 88 runs, assisted in 56 of 89: the difference is whether a test is written at all.

## What this does and does not show

- One model (Sonnet 5.5, medium), one host (Claude Code), Python only, 12
  repositories, small fixes (median 10 changed lines). Not a population estimate.
- The ordinary arm is plain Claude Code. The launcher reads project and local
  settings only, and every run's init event lists Claude Code's built-in plugins and
  nothing else, so no user plugin such as superpowers was loaded in either arm
  (checked 2026-10-23). This compares Claude Code with and without ElevenPowers,
  not superpowers with and without it.
- Both arms also carried the operator's own `~/.claude/CLAUDE.md`, which
  `--setting-sources` does not exclude (found 2026-10-28 by a one-turn probe that
  named the file). It holds general working preferences and nothing about these
  tasks, and it was the same in both arms. The launcher now excludes it.
- VACUOUS is this project's measure of whether the repository's tests pin the
  change; it is not correctness. Resolved is graded against the upstream fix's tests.
- The frame excludes projects whose packages import build-generated modules, whose
  suites read their own installed metadata, whose test dependencies fall outside
  the frozen install order, and candidates rejected only through subtest failures.
- Two of 240 runs are not graded: `wrapt-15068aae--assisted--2` was excluded as a
  closed-book breach under the frozen rule (its command included `pip install -e .`,
  a local editable install; the run resolved and was not VACUOUS, so excluding it
  works against the assisted arm), and `more-itertools-d992be0d--assisted--2` was
  cut off when the controlling session ended and, launched, was not retried. One
  ordinary resolved run's probe was unscored and counts as not VACUOUS, also
  against the hypothesis.
- The pre-registered analysis was run once early by mistake, on 232 of 240 graded
  runs, after a guard stopped the resumed driver; nothing was changed in response,
  and the result above is the analysis of the complete record.

## Selection over the same runs (added afterwards, not pre-registered)

PLAN §8's oracle gap, read from the same 238 graded runs at no cost:
coverage is the share of tasks where any of an arm's three runs succeeded,
the random pick the expected success of choosing one of them blindly.

| arm | success means | coverage | random pick | gap | tasks whose runs disagree |
|---|---|---|---|---|---|
| ordinary | resolved | 80.0% | 73.3% | +6.7 | 5 |
| assisted | resolved | 80.0% | 75.8% | +4.2 | 3 |
| ordinary | resolved and not VACUOUS | 17.5% | 11.7% | +5.8 | 4 |
| assisted | resolved and not VACUOUS | 55.0% | 47.5% | +7.5 | 6 |

The resolve gap sits near the 4-point reference line and, as in journey 31, comes
entirely from three to five tasks whose runs disagree, so it describes per-run
variation on a handful of tasks rather than a stable property of either pool. The
second pair is the sharper reading: a perfect selector over three ordinary runs
would find a resolved, tested candidate on 17.5% of tasks, well under a blind pick
from the assisted runs (47.5%). On these tasks, choosing among more ordinary
attempts does not recover what the assisted arm produced. Three runs per arm,
descriptive, no test. `oracle-gap.txt` and `oracle-gap-pinned.txt`; reproduce with
`python -m eval.pool --from-bundles results/heldout/sweep-2026-10-22/collected.json [--pinned]`.

## Every state a run passed through (added afterwards, not pre-registered)

PLAN §7's B2.3, at edit granularity for the first time. Each run's transcript
records every Edit and Write, so `eval/heldout_checkpoints.py` rebuilds the tree
after each edit from the base commit, keeps the replay only when its last state
reproduces the submitted patch (exactly, or up to the line endings a
`git stash`/`stash pop` under autocrlf rewrites), and grades every earlier distinct
state as the final one was graded.

| arm | graded | replayed | with an earlier state | better earlier state | tested runs that resolved untested first |
|---|---|---|---|---|---|
| ordinary | 120 | 79 | 36 | 1 | 4 |
| assisted | 118 | 69 (5 up to line endings) | 49 | 0 | 34 |

The one better state: `cachetools-bcf9e817--ordinary--1` resolved (VACUOUS) and then
submitted a patch that regressed. So on these tasks a ratchet back to the best
earlier state has almost nothing to recover. The last column shows how the assisted
arm reaches a tested fix: the fix lands first and resolves untested, and the test is
written after. Limits: 90 of 238 runs changed files through the shell (`sed -i`,
`cat >`, scripts) and cannot be replayed, so the replayable runs are a selected
subset; small fixes, one model, descriptive only. `checkpoints.json` (per run) and
`checkpoints.txt`; reproduce with `python -m eval.heldout_checkpoints --sweep
results/heldout/sweep-2026-10-22 --corpus results/heldout/corpus.json --out <journal>`.

## Files

`protocol.json` and `protocol-seal.json` (the frozen schedule), `collected.json`
(one record per scheduled slot), `analysis.json` (the primary and secondary
output), `runs/<slot>/` (each run's result, exported patch and host transcript),
`sweep.log`, `harness/` (the driver and the quota guard that ran it), and the
`oracle-gap*.txt` outputs above.
