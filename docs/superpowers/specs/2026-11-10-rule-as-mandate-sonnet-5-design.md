# Does the instruction wording hold on another model?

*Written 2026-11-10, before any run. It replicates
[the confirmation](2026-11-09-rule-as-mandate-confirmation-design.md)
([result](../../../results/rule-mandate-confirm/README.md): 5 of 60 lost
against 23 of 60 on Sonnet 5.5) on a second model.*

## Why

The confirmed benefit and its harm check rest on one model, Sonnet 5.5. A
wording effect can be model-specific. The other model this harness supports,
and the one the standing authorization names for these sessions, is
`claude-sonnet-5`.

## Unchanged from the confirmation

- The stage: `household_budget` 7.
- The arms: `rules` (description) against `described` (instruction).
- The inputs: `results/rule-gate/accepted.json` and
  `results/rule-mandate/descriptions.json`.
- The profile: `guide`.
- The effort: medium, which the runner fixes.
- The analysis: `results/rule-mandate/analyse.py`, unchanged.

## Changed

- **Model:** `claude-sonnet-5`. `eval/rule_groups_run.py prepare` gains a
  `--model` option, limited to the supported models.
- **Host:** Claude Code 2.1.319. The confirmation ran on 2.1.292, which
  updated itself overnight.
- **Runs:** 60 per arm, 120 runs. About $20 and 45 minutes if Sonnet 5 costs
  what Sonnet 5.5 does. That is not known yet, and the harness-check slot
  will show it.

## Outcomes, fixed now

**Primary:** dependent lost, `described` against `rules`. Exact one-sided
test, α = 0.05.

**Secondary:**
- silent losses;
- `annual.py` changed;
- another group lost;
- cost and wall time.

## Decision rule, fixed now

- **Primary at α = 0.05:** the README states the benefit on two models.
- **Not at α = 0.05:** the README states it on Sonnet 5.5 only, and says
  that it did not replicate on Sonnet 5.
  - The proposer default stays either way. The harm check found no cost
    to it, and on Sonnet 5.5 it helps.
- **More harm in `described`** (an `annual.py` edit or another group lost
  more often): reported, and the guide warns for that model.

## Gates before any money

1. **The harness-check slot** shows three things:
   - the host accepts `claude-sonnet-5`;
   - `observation.models` is exactly `claude-sonnet-5`;
   - the cost per run, so the estimate can be corrected before launch.

   If one run costs more than $0.50, the batch is cut to 40 per arm before
   launch, and that is recorded here.

## Bounds, known now

- **One stage,** chosen because the request and a rule conflict there.
- **Two models of one family,** both Sonnet, so this is not a test across
  vendors.
