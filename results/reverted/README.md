# Reverted-tree discrimination — 2026-10-10

Would the agents' own passing checks have passed without their change? P22,
asked of every saved bundle with [`eval/reverted.py`](../../eval/reverted.py).
No agent and no model call: only local pytest runs.

**Method.** Each bundle's base commit is built twice, the way the harness built
it. Forward: the saved patch applied; the recorded check must pass there today.
Adversarial: the old source carrying the patch's test files — `core/stress.py`'s
method and its states. Passing there is `VACUOUS`; failing tests there is
`DISCRIMINATES`; anything else is `UNCHECKABLE` with its reason. Only
`python -m pytest` lines are re-run, with the workspace prefix and output
shaping removed; anything that could write, chain, substitute or name the old
workspace is refused.

## Funnel

| Step | Records |
|---|---:|
| Evidence records in 54 saved ledgers | 2,017 |
| Passing | 432 |
| Passing test records that ran at least one test | 200 |
| Re-executable `python -m pytest` lines | 62 |
| Distinct checks (bundle × command) | **44**, from 28 bundles |

Excluded on the way, by reason: 1,585 not passing; 232 not a test record that
ran tests (lint, typecheck, zero counts); 134 not a pytest run; 4 could write,
chain or substitute.

## Result

| Verdict | Checks |
|---|---:|
| `DISCRIMINATES` — failing test on the old tree | 16 |
| `VACUOUS` — passes on the old tree | 7 |
| `UNCHECKABLE` — does not reproduce on the patched tree today | 21 |

**The vacuous checks are almost all patches with no test.** Six of seven come
from patches that touched no test file, where a suite run on the old code
passes by construction (6/6; exact 95% interval 54.1–100%). Where the patch
added or edited tests, 1 of 17 checks was vacuous (5.9%; 0.1–28.7%) — a single
parametrised case, `opt_params6`, whose sibling `opt_params7` discriminates.
Pooled, 7 of 23 classified checks are vacuous (30.4%; 13.2–52.9%). None
discriminated by import alone.

That is consistent with [B9](../b9-gate-tests/), where all fourteen vacuous
patches had no test, and with stress's declared-command verdicts on the same
ledgers, 1 vacuous in 26 (3.8%; 0.1–19.6%). Those measure different checks —
stress runs the project's declared command, this the agent's own — and do not
contradict each other.

**Every uncheckable check has a named cause, and none is the agent's.**

| Cause | Checks |
|---|---:|
| attrs: `No module named 'hypothesis'` | 10 |
| click: pytest 9.1.1 raises `PytestRemovedIn10Warning` at collection | 8 |
| itsdangerous: `No module named 'freezegun'` | 2 |
| click: the recorded `-k` selection matches no test today | 1 |

Without the forward control all twenty-one would have failed on the old tree and
been counted as discriminating.

## What this does not establish

- **Every run predates toolchain recording** (`fafe61a`), so every result is the
  *unrecorded* stratum. Its only qualification is that the check reproduced
  forward under pytest 9.1.1 today.
- **Checks are not independent.** Tasks repeat across sweeps and bundles hold
  several checks; the intervals above treat them as independent and are
  therefore narrower than the truth.
- **Coverage is partial.** 44 of 432 passing records, and none of attrs: its
  suite needs `hypothesis`, which this interpreter does not have. Installing it
  would change the environment future runs inherit, so it was not done here.
- It describes the evidence agents recorded, not whether any gate decision or
  outcome would have changed.

## Reproduce

```sh
python -m eval.reverted --bundles results --out NEW_DIRECTORY
```

`rows.jsonl` holds one line per bundle with every check's command, record
count, toolchain stratum, verdict and reason; `summary.json` the funnel and
counts. An interrupted sweep resumes from `rows.jsonl`.
