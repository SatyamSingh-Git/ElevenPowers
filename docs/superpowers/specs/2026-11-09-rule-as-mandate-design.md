# A rule worded as an instruction: does the agent follow it over a narrow request?

*Written 2026-11-09, before any run. It follows
[the rule gate](2026-11-09-declared-rule-gate-design.md), whose
[result](../../../results/rule-gate/README.md) left this open.*

## Question

On `household_budget` 7 the request ("make `budget status` net refunds")
and a declared rule (`summarise` and `_spent_by_category` keep the same
spending rule) pull in opposite directions. Agents that leave `month_end.py`
unchanged say why: you asked for `budget status` only.

The rule they were shown is the generic text the proposer generates:
"These files keep the same rule (they share is_spending, get, catalog)."
That describes; it does not instruct. **If the rule is worded as an
instruction, do agents follow it rather than the request's narrow reading?**

- **If yes:** ElevenPowers' value is carrying a person's instructions to the
  moment they apply, which is an instruction-following product.
- **If no:** the agent's scope judgement wins over a written rule, and no
  wording fixes it.

## What was measured before this design ($0, exploratory, not pre-registered)

- **On this stage, losses are scope choices the agent tells the user about.**
  Even with no rule, 10 of 13 losses across two batches said that `report
  month` now differs and offered to change it. The agents found the coupling
  through `docs/reference.md` ("same as budget status").
- **Silent losses,** where the final message never names the dependent file,
  fall with the note:
  - perfect rules: 16 of 50 runs without a rule, 0 of 50 with one;
  - a reviewer's rules: 19 of 50 without, 8 of 50 with. Seven of the 8 were
    on `parcelpost` 5, where no rule was declared.

  The figures come from a file-name pattern match on the final message.

## Arms

Both arms: superpowers plus ElevenPowers, the `guide` profile (note only, no
gate), and the reviewer's 11 kept rules for `household_budget`. They differ
in each rule's description only.

| arm | description |
|---|---|
| `rules` | the proposer's template: "These files keep the same rule (they share …)" |
| `described` | one fixed sentence per rule, built from its two functions by [`describe.py`](../../../results/rule-mandate/describe.py): "`A` (file A) and `B` (file B) must stay consistent: change both in the same task." |

The mandate is generated, not written, so no sentence carries knowledge of
any stage. Every rule gets it, including `year_report`/`_carried_into`, whose
file no correct run changes. The longest sentence is 174 characters, inside
the rule note's 200-character cut.

## Runs

- `household_budget` 7, 20 replicates per arm: 40 runs.
- Sonnet 5.5 at medium effort, under the standing authorization.
- About $7.50 and 25 minutes. Every slot runs once and none is retried.
- Harness: `eval/rule_groups_run.py`, arms `rules` and `described`,
  `--accepted results/rule-gate/accepted.json`,
  `--descriptions results/rule-mandate/descriptions.json`.

## Outcomes, fixed now

**Primary.** Dependent lost, `described` against `rules`.
- Exact one-sided test, `described` loses fewer, α = 0.05.
- With the template note this stage lost 10 of 25 today, 5 of 10 and 1 of 10
  earlier. Power with 20 per arm is about 0.75 if 40% falls to 5%, and lower
  for smaller effects.

**Secondary, reported whatever they show.**
1. **Silent losses:** dependent lost and the final message never names
   `month_end`.
2. **Harm:**
   - runs that changed `src/budgetbook/reports/annual.py`, which no correct
     run needs;
   - any other group lost.
3. **Asked the user:** among losses, how many end by offering the change or
   asking whether to make it. Descriptive.
4. Cost and wall time per arm.

## Decision rule, fixed now

- **Primary favours `described`, and no more `annual.py` changes than
  `rules`:**
  - the proposer's entries change from "TODO: name the rule…" to the
    instruction form;
  - the guide tells people to write rules as instructions;
  - a no-exit gate for rules a person marks `must` becomes the next design.
- **Primary favours `described`, and `annual.py` is changed more:** wording
  works but overreaches. The guide says to write instructions only for rules
  that are strict, and nothing changes by default.
- **Null:** a written instruction does not move a scope choice. The rule
  stays a note, and the instruction-following angle is dropped for this kind
  of rule.

## Gates before any money

1. **$0 rehearsal.** The `described` arm's rule note, on an edit of
   `budgets.py`, carries the full mandate sentence for
   `rule-summarise-_spent_by_category`. The `rules` arm carries the template.
2. **One-slot harness check,** read in full.

## Bounds, known now

- **One stage,** chosen because the request and the rule conflict there.
- **The note keeps its own exit in both arms.** The rehearsal showed that
  ElevenPowers' rule note ends "Change them together, or say why one should
  differ", whatever the description says. This experiment varies only the
  description inside that note. A note without the exit is a product change
  and is not tested here.
- **The mandate is one generated sentence,** not a person's explanation of
  why the files must agree.

## Designed, not built: never force a change silently

From the measurement above. Without a gate, the note already gets agents to
either make the change or tell the user. A gate would be justified only for:
- **Silent divergence:** a rule was left behind and the final message does
  not name the file. The gate would ask the agent to tell the user and ask,
  never to edit. On covered stages this happened in 1 run of 40, so it is
  not built.
- **Rules a person marks `must`:** the change is demanded with no exit. If
  the agent judges that the request conflicts with the rule, it must ask the
  user rather than decide alone. This waits on this experiment.
