# Reverted-tree discrimination — 2026-10-10

Would the agents' own passing checks have passed without their change? P22,
asked of every saved ledger with [`eval/reverted.py`](../../eval/reverted.py).
No agent and no model call: only local pytest runs.

**Method.** Each bundle's base commit is built twice, the way the harness built
it. Forward: the saved patch applied; the recorded check must pass there today.
Adversarial: the old source carrying the patch's test files — `core/stress.py`'s
method and its states. Passing there is `VACUOUS`; failing tests there is
`DISCRIMINATES`; anything else is `UNCHECKABLE` with its reason. Only
`python -m pytest` lines are re-run, with the workspace prefix and output
shaping removed; anything that could write, chain, substitute or name the old
workspace is refused.

**Corrected the same day.** The first publication measured 54 of the 106 saved
ledgers: its discovery globbed `bundles/` and missed the chunked sweeps'
`bundles-chunk1/` and `bundles-chunk2/`. The figures below are the full corpus;
the shape of the result did not change.

## Funnel

| Step | Records |
|---|---:|
| Evidence records in 106 saved ledgers (all gate arm) | 2,954 |
| Passing | 676 |
| Passing test records that ran at least one test | 342 |
| Re-executable `python -m pytest` lines | 125 |
| Distinct checks (bundle × command) | **101**, from 68 bundles and 29 tasks |

Excluded on the way, by reason: 2,278 not passing; 334 not a test record that
ran tests (lint, typecheck, zero counts); 210 not a pytest run; 7 could write,
chain or substitute. Vanilla-arm bundles carry no ledger and are not in scope.

## Result

| Verdict | Checks |
|---|---:|
| `DISCRIMINATES` — failing test on the old tree | 40 |
| `VACUOUS` — passes on the old tree | 8 |
| `UNCHECKABLE` — does not reproduce on the patched tree today | 53 |

**The vacuous checks are the patches with no test.** Seven of eight come from
patches that touched no test file, where a suite run on the old code passes by
construction (7/7; exact 95% interval 59.0–100%). Where the patch added or
edited tests, 1 of 41 checks was vacuous (2.4%; 0.1–12.9%) — a single
parametrised case, `opt_params6`, whose sibling `opt_params7` discriminates.
Pooled, 8 of 48 classified checks are vacuous (16.7%; 7.5–30.2%). None
discriminated by import alone.

That is consistent with [B9](../b9-gate-tests/), where all fourteen vacuous
patches had no test, and with stress's declared-command verdicts, 1 vacuous in
26 ledgers that recorded one. Those measure different checks — stress runs the
project's declared command, this the agent's own — and do not contradict each
other.

**Every uncheckable check has a named cause, and none is the agent's.**

| Cause | Checks |
|---|---:|
| attrs: `No module named 'hypothesis'` | 32 |
| click: pytest 9.1.1 raises `PytestRemovedIn10Warning` at collection | 14 |
| itsdangerous: `No module named 'freezegun'` | 6 |
| click: the recorded `-k` selection matches no test today | 1 |

Without the forward control all fifty-three would have failed on the old tree
and been counted as discriminating.

## What this does not establish

- **Every run predates toolchain recording** (`fafe61a`), so every result is the
  *unrecorded* stratum. Its only qualification is that the check reproduced
  forward under pytest 9.1.1 today.
- **Checks are not independent.** The 48 classified checks come from 35 bundles
  and only 14 tasks, which recur across sweeps; the intervals above treat checks
  as independent and are narrower than the truth.
- **Coverage is partial, and attrs is absent.** Its suite needs `hypothesis`,
  which this interpreter does not have; installing it would change the
  environment future runs inherit, so it was not done here.
- It describes the evidence agents recorded, not whether any gate decision or
  outcome would have changed.

## Reproduce

```sh
python -m eval.reverted --bundles results --out NEW_DIRECTORY
```

`rows.jsonl` holds one line per ledger, keyed by its path, with every check's
command, record count, toolchain stratum, verdict and reason; `summary.json` the
funnel and counts. An interrupted sweep resumes from `rows.jsonl`.
