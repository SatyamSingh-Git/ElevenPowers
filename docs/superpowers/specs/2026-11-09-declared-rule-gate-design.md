# A declared rule left behind: gate against note

*Written 2026-11-09, before any run. Test 3 of the
[2026-11-05 synthesis](../../research/audit_2026_11_05/README.md#cheapest-tests-first):
"the declared-rule note stays until a gate beats it".*

## Question

When an agent ends a task with a declared rule changed in some of its files
and not the others, does sending it back once, naming the rule and the
unchanged file, lose fewer dependents than the rule note alone? And does it
do harm where the agent was already right?

## Why now

- The rule note works: dependents lost fell from 31 of 50 to 15 of 50 with
  a reviewer's rules ([results](../../../results/rule-groups-acted-on-reviewed/README.md)).
- What it leaves is narrow. On the four stages the reviewer covered, 5 of
  40 runs got the note and still lost the dependent, all on
  `household_budget` 7. All five ended with the rule changed in
  `budgets.py` and not `month_end.py`. ElevenPowers named that in the end
  report, which goes to the person, not the agent.
- The research found enforced checks beat advice (ECLoop, ContextCov), and
  Chromium's IfThisThenThat already gates this exact shape.

## What was measured before this design ($0)

A replay over every saved run that carried declarations: 153 runs in the
acted-on, reviewed and harm batches.

| | runs | file-level finding fires | function-level would fire |
|---|---|---|---|
| dependent lost, a declared rule covers the break | 9 | 9 | 6 |
| nothing lost | 132 | 21 (16%) | 6 (4.5%) |

- **File-level** is the shipped finding (`partly_changed`). It catches every
  covered loss. It also fires on one correct run in six.
- **Function-level** would ask whether the diff touched the rule's two
  proposed functions. It misses all three `parcelpost` 5 losses, whose break
  goes through a function the rule does not name.
- **On `household_budget` 7, file-level fires on every run.** The reviewer
  also kept `year_report`/`_carried_into`, and no correct run changes
  `annual.py`. A gate there sends back every run, so the stage measures
  benefit and harm at once.

## The gate (built before the run)

- Under `strict`, with `"rule_gate": true` in `.elevenpowers/config.json`.
  **Off by default** until this comparison says otherwise.
- At Stop, each finding `partly_changed` reports (declared rules and
  `LINT.IfChange` blocks) that the agent has not yet been sent back for
  blocks the stop once. The message names the rule and the files, and says:
  change the other files, or say why they should differ.
- Each finding is asked once per request. A repeat is let through and logged
  as `rule gate released`. It shares the existing cap of two blocks.
- It joins an existing block on unmet obligations rather than adding a
  second one.

## Arms

Both arms are identical except for one config key:
- superpowers plus ElevenPowers;
- the `strict` profile;
- the reviewer's kept rules (`results/rule-groups-reviewed/reviewed.json`,
  `kept`) as declarations.

| arm | `rule_gate` |
|---|---|
| `note` | false |
| `gate` | true |

`strict` in both arms, not `guide`, so the arms differ only in the rule
gate. This also means neither arm is the earlier batches' rules arm, which
ran `guide`. Only concurrent arms are compared.

## Stages and runs

- **Primary:** `household_budget` 7, 25 runs per arm (50 runs).
- **Harm:** the v3 stages, other than `household_budget` 7, where the file-level
  finding fires on the stage's reference solution under this certification.
  These are stages where a correct agent is sent back. They are computed at
  $0 before sealing, and the list is frozen into the protocol. Each stage
  gets 3 runs per arm. If more than 8 stages qualify, the 8 with the most
  findings are used, ties broken by name.

Model: Sonnet 5.5 at medium effort, under the standing authorization.

The two parts run as two sealed batches, primary first, because the runner
gives one replicate count per batch. The harness is `eval/rule_groups_run.py`
with arms `note` and `gate`, and `--accepted results/rule-gate/accepted.json`.
That file is the reviewer's `kept` ids, written by the rehearsal.

**Estimate:** about 98 runs at about $0.17 each, so about $17. At four at a
time and about 100 s each, about 45 minutes. Every slot runs once and none is
retried.

## Outcomes, fixed now

**Primary.** Dependent lost on `household_budget` 7, `gate` against `note`.
- Exact one-sided Fisher test, gate fewer, α = 0.05.
- Power is 0.91 if the note arm loses half and the gate a tenth; 0.69 at 30%
  against 5%.
- The two earlier batches' runs that got the note lost 6 of 20 on this
  stage, so a null here is weak evidence.

**Secondary, reported whatever they show.**
1. **Conversion (mechanism).** In the `gate` arm, of the runs blocked with
   `rule-summarise-_spent_by_category` left behind, how many ended with
   `month_end.py` changed and the dependent kept. This compares the same run
   before and after the block.
2. **Harm on the primary stage.**
   - Among `gate` runs that kept the dependent: any other group lost, and
     whether `annual.py` was changed.
   - Cost and wall time per arm.
3. **Harm on the harm stages.**
   - Any group lost per arm, pooled, by the stratified exact test used in
     the harm batch.
   - Cost and time per arm.
   - How often the gate fired.
4. **Released.** How often a finding was let through on the second stop, and
   what the agent's reply said about it.

## Decision rule, fixed now

- **Turn `rule_gate` on by default in `strict`** only if both hold:
  - the primary favours the gate at α = 0.05;
  - harm stages show no more groups lost in `gate` than in `note`.
- **Primary null, conversion at least half:** keep the gate opt-in, and say
  the arm comparison was underpowered.
- **More harm in `gate`:** keep it off, and record why.
- **Conversion below half:** sending the agent back does not do what a note
  does not. Keep it off.

## Gates before any money

1. **$0 rehearsal through the real hooks.** On `household_budget` 7, the
   reference edit with the dependent left behind is blocked in `gate` and not
   in `note`. The reference with both files changed is blocked in `gate`
   only for `year_report`, and the block message names `annual.py`.
2. **One-slot harness check.** One run of the `gate` arm, read in full
   before the rest are launched. It must show:
   - the profile is `strict`;
   - `rule_gate` is set;
   - the init event lists no user plugins beyond superpowers.

## Bounds, known now

- One primary stage, chosen because the note left room there.
- A model reviewer's rules stand in for a person's.
- The gate is file-level. Function-level was weighed and set aside for
  missing breaks that go through a function the rule does not name.
