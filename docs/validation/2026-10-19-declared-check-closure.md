# Declared-check completion closure — validation

Exact declared-check rows now appear beside the unchanged task verdict, and
declared-check feedback leaves separate intent, emission and follow-up
observations. Everything here is no-model: actual local checks through the real
launchers. See [results](../../results/declared-check-closure/README.md),
[design](../design/declared-check-closure.md) and the
[plan](../superpowers/plans/2026-10-18-declared-check-closure.md).

## Witnessed controls

- The delivery observer existed uncommitted with one forward test. Its new
  controls were run with the implementation stashed (20 failed on the missing
  module), then restored. Two then failed on a real defect: a non-object intent
  note crashed `end_report`. Eighteen guard mutations were applied one at a
  time; all were killed after two more controls were added (reinstalled
  integration; a privacy assertion that had been vacuous).
- Running the real Claude launcher showed owned-runner follow-ups always
  `unobserved`: `parse()` returns no records for an owned envelope, so no link
  was ever made. The forward owned control failed before the attempt-link repair
  and passed after; five of six mutations were killed, the sixth is equivalent.
- `INCOMPLETEtests` in the annex failed a new separation assertion before the
  column was widened.

## Fresh review and fix pass

A fresh-context review of `24ad2ce..77e56e0` reproduced two Critical and two
Important findings. Each was witnessed failing before its fix:

| Finding | Witness | After |
|---|---|---|
| `ep_check.py` exit 1 and traceback on refused checks | existing `test_cli_refuses_invalid_request[args0]` failed | exit 2, no attempt line |
| intent skipped on adapter callbacks with `tool_use_id` | four adapter producer cases failed once the payload carried one | all pass |
| credential-bearing commands never exact | two new controls failed | `CURRENT`; feedback quiet |
| owned links in native receipt history (health, acceptance) | new control failed | separate `owned_links` |

Eight of nine fix mutations were killed; the survivor was a weak mutation of the
CLI fix whose real defect the existing CLI test had already witnessed. The plan's
missing configuration-mismatch control was added. Two minors are deferred and
listed in the results.

The first selection of affected tests omitted `tests/test_check_cli.py`, which is
why the CLI regression reached `main` at `77e56e0`.

## Runs

- Affected groups, first push: 549 passed in 667.69 seconds. An earlier run of
  the same group reported 3 failed / 520 passed while runtime files were being
  edited under its subprocesses; the three passed when rerun on the settled tree.
  It is not counted.
- Affected groups after the fix pass (adds CLI, batch, checks and advice
  exercise): 610 passed in 579.54 seconds.
- No-model exercise at `3f3e2e7`: 20/20 qualified, 202.75 seconds of case time.
  The `77e56e0` run is retained as superseded.
- A full local suite started at `77e56e0` was stopped at about 24% when the
  review invalidated that runtime; it is not a result.
- Full local suite at `3f3e2e7` runtime: **1 failed, 2629 passed, 3 skipped in
  4318.34 seconds**. The failure,
  `test_impact_query.py::test_non_git_requested_history_is_incomplete`, is caused
  by this run's `--basetemp` inside the repository: its "non-Git" project had
  this Git work tree as a parent. It passes with the default temporary
  directory. This is not a clean full pass, and is recorded as such.
- Hosted `tests.yml`: `77e56e0` and `4638e66` fail one test in every finished
  cell, `test_cli_refuses_invalid_request[args0]` (`assert 1 == 2`), the CLI
  regression fixed in `3f3e2e7`. At `3f3e2e7`, `361c44f` and `4cf14bb` all four
  cells pass.
- Architecture: `python architecture/check.py --render` passes with 173 nodes,
  430 edges and all five tabs.

## Installed observation (2026-10-20)

Prelaunch: hosted `tests.yml` passed all four cells at `3f3e2e7`, `361c44f` and
`4cf14bb`. Returning from a stray checkout had rewritten working files with CRLF
endings, so the raw runtime fingerprint moved from `c0f9f81a…` to `8ceec45c…`
with identical Git content; the no-model exercise was rerun at the new bytes
(20/20, [record](../../results/declared-check-closure/no-model-checkout-bytes.json))
before any launch. A new per-turn readout of declared rows and delivery stages
was witnessed failing before it existed; a fake host driving the real launcher
shows owned (`CURRENT`/`current`) and generic-only (`STALE`/`unobserved`) turns.

Attempt 1 stopped `model_unqualified` on a host auxiliary Haiku call and is
retained uncounted. A real probe reproduced the call and its removal by
`ANTHROPIC_DEFAULT_HAIKU_MODEL`; the launch control failed before the repair and
34 harness tests passed after. Attempt 2 was frozen and pushed before launch:
feedback emitted in turn 2, owned runner used next with a `current` follow-up,
turn 3 timed out at its time share and turn 4 never ran. See the
[results](../../results/declared-check-closure/README.md#installed-observation-2026-10-20).

## unittest summary and attempt 3 (2026-10-20)

The `unittest` summary shapes were captured from real Python 3.13.2 runs before
any pattern was written. Nineteen controls on actual runs failed before the
reader existed (one adversarial control passed throughout); ten mutations were
killed after a multi-summary control and a declared-wrapper control were added.
The enforced both-ways table refused the change until `unittest` was added.
Before the two-case launch, the full local suite passed 2655 with 3 skipped and
no failure at runtime `f4f0956e`, all four hosted cells passed at `24ace0a` and
`34ea800`, and the no-model exercise was 20/20.

Attempt 3: both cases emitted feedback in turn 1 and used the owned runner in
all four turns; JavaScript completed, and Python's turn 4 is recorded
`scope_violation` from a milestone readout error on a host scratchpad path. That
was reproduced on a copy of the candidate, witnessed failing, fixed in `addf985`
(4/4 mutations killed) and the harness label repaired in `dd8e4c2` (both
directions witnessed). See the
[results](../../results/declared-check-closure/README.md#attempt-3-both-cases-2026-10-20).
