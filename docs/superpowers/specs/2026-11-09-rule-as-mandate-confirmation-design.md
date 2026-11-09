# Confirming the rule as an instruction

*Written 2026-11-09, before any run. A fresh replication of
[the first run](2026-11-09-rule-as-mandate-design.md)
([result](../../../results/rule-mandate/README.md): 2 of 20 lost against
6 of 20, one-sided p = 0.12).*

## Why a new run, not more runs

The first run leaned toward the instruction but missed α = 0.05. Adding runs
to it after seeing that would be retrying for a favourable result. This is a
new batch, analysed on its own. The first run is never pooled with it.

## Unchanged from the first run

- The stage: `household_budget` 7.
- The arms: `rules` (the template) against `described` (the instruction).
- The inputs:
  - `results/rule-gate/accepted.json`;
  - `results/rule-mandate/descriptions.json`, byte-identical.
- The profile: `guide`.
- The model: Sonnet 5.5 at medium effort.
- The harness (`eval/rule_groups_run.py`) and the runtime are unchanged since
  the first run.

## Changed

- **60 runs per arm: 120 runs.** About $20 and 45 minutes, under the
  standing authorization. Every slot runs once and none is retried.
- **Power** (exact one-sided test, α = 0.05):

  | template loss → instruction loss | power |
  |---|---|
  | 30% → 10% | 0.83 |
  | 35% → 10% | 0.94 |
  | 25% → 10% | 0.63 |
  | 30% → 15% | 0.55 |

  The template has lost 30% to 40% on this stage across batches. A smaller
  effect than 30% to 10% may be missed.

## Outcomes, fixed now

**Primary:** dependent lost, `described` against `rules`. Exact one-sided
test, `described` loses fewer, α = 0.05. Computed by
`results/rule-mandate/analyse.py`, unchanged.

**Secondary, reported whatever they show:**
- silent losses;
- losses that offer the change or ask;
- `annual.py` changed;
- another group lost;
- cost and wall time.

## Decision rule, fixed now

- **Primary at α = 0.05, and no more `annual.py` changes or other losses in
  `described`:** the benefit is confirmed on this stage.
  - The README's "did even better in an early test" becomes a confirmed
    result.
  - The proposer's entry template changes from "TODO: name the rule…" to the
    instruction form.
- **Primary not at α = 0.05:** the early lean did not replicate. The README
  line is withdrawn, and `PLAN.md` §10 records the withdrawal.
- **More harm in `described`:** whatever the primary shows, nothing changes
  by default, and the guide warns that instructions overreach.

## Gates before any money

1. **The $0 rehearsal** ([`rehearse.py`](../../../results/rule-mandate/rehearse.py))
   passes again on the tree as committed.
2. **One-slot harness check,** read in full.

## Bounds, known now

- **One stage,** chosen because the request and a rule conflict there.
  Confirming it here does not show it on other stages.
- **A generated sentence,** not a person's words.
