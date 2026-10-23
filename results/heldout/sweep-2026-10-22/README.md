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

## What this does and does not show

- One model (Sonnet 5.5, medium), one host (Claude Code), Python only, 12
  repositories, small fixes (median 10 changed lines). Not a population estimate.
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

## Files

`protocol.json` and `protocol-seal.json` (the frozen schedule), `collected.json`
(one record per scheduled slot), `analysis.json` (the primary and secondary
output), `runs/<slot>/` (each run's result, exported patch and host transcript),
`sweep.log`, and `harness/` (the driver and the quota guard that ran it).
