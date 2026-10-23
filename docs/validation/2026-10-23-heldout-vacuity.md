# Held-out vacuity by arm — validation

The held-out comparison asked whether an installed ElevenPowers changes how often
a resolved patch is VACUOUS on tasks this project did not pick. This record lists
what was checked before and during the paid runs. See
[results](../../results/heldout/sweep-2026-10-22/README.md),
[design](../superpowers/specs/2026-10-20-heldout-vacuity-design.md) and the plans
([sourcing and harness](../superpowers/plans/2026-10-20-heldout-vacuity.md),
[robustness and runs](../superpowers/plans/2026-10-21-heldout-sourcing-robustness.md)).

## Witnessed controls (no model)

- Every new or changed reader, sampler and runner rule was written test-first and
  mutation-checked; each fix for a defect found by running the real producer has
  a test that failed before it and passed after.
- Defects found only by running the producer, each fixed before any spend: patches
  piped to `git apply` as text (no patch would apply on Windows); a one-way
  environment check (urllib3's generated `_version.py`); `github.com/sponsors/`
  links taken as repositories (nine accepted packages); a journal truncated by a
  full disk; and pytest 9 printing `PASSED` for a test whose subtests failed, in
  three `SUBFAILED` forms, which grading, mining, the vacuity probe and the
  runtime's own `core/parsers.py` and `core/stress.py` all misread.
- The sampler was stopped and resumed on the real run, and resumed after two real
  Windows file-handle crashes, without losing a finished repository.
- All 40 kept tasks were re-validated with the corrected readers (three moved
  subtest-only tests from preservation to fail-to-pass; one intermittent uvicorn
  preservation node was dropped) and rehearsed 40/40 on their gold patches: base
  fails, gold resolves, canary holds, probe killed with the fix's tests and
  surviving without them.
- An independent review of the round found four serious issues; all were fixed
  test-first before the pilot. Full local suite afterwards: 2759 passed, 3 skipped.

## Paid runs

- **Pilot:** 8 runs, 4 tasks from 4 repositories × 2 arms, 8/8 graded on the exact
  model, hooks and a ledger in every assisted run and in no ordinary run, $0.46.
  The schedule's runtime and harness hashes matched the sweep's.
- **Sweep:** 240 slots sealed and pushed (7911c69) before the first launch;
  238 graded, one excluded as a closed-book breach by the frozen rule, one cut off
  when the controlling session ended and not retried. A quota guard ran beside the
  driver; it once stopped a resume before any launch by reading stale log lines,
  and was corrected to read only lines after the latest resume.
- **Analysis:** the committed `eval/heldout_analyse.py` on all 240 records. It had
  been run once early, on 232, while that stop was investigated; nothing changed.

## Result and limits

VACUOUS among resolved: 74/88 ordinary (84%) vs 33/89 assisted (37%); per task
lower under ElevenPowers on 17, higher on 1, 13 tied, 9 dropped; signed-rank
p = 0.00016. Resolve rates unchanged (p = 0.625). 106 of 107 VACUOUS patches had
no test file. Sonnet 5.5 medium, Claude Code, Python, 12 repositories, small
fixes, stated frame exclusions: not a population estimate, and VACUOUS measures
test pinning, not correctness.
