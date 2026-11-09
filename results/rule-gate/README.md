# A rule left behind: gate against note. The gate converted 0 of 7

[Design](../../docs/superpowers/specs/2026-11-09-declared-rule-gate-design.md),
written before any run. Inputs:
- [`accepted.json`](accepted.json): the blind reviewer's kept pairs for all
  12 cases.
- [`rehearse.py`](rehearse.py) ([output](rehearsal.json)).
- [`analyse.py`](analyse.py) ([output](analysis.json)).
- The acted-on [`launch.py`](../rule-groups-acted-on/launch.py)
  ([primary log](launch-primary.log), [harm log](launch-harm.log)).

## Result

**Sending the agent back did not change what it did.** The gate sent back 7
runs with the dependent left behind. All 7 ended the turn with no further
tool call and an explanation of why the file should stay as it was. By the
rule fixed in advance (conversion below half), the gate stays **off by
default**. It remains an opt-in setting.

| | `note` | `gate` |
|---|---|---|
| **Primary:** dependent lost, `household_budget` 7 | 10 of 25 | 7 of 25 |
| One-sided exact test, gate loses fewer | | p = 0.28 |
| **Conversion:** sent back for the dependent's rule, then kept it | | **0 of 7** |
| Gate runs that kept the dependent: another group lost / `annual.py` changed | | 0 of 18 / 0 of 18 |
| **Harm stages:** any group lost (8 stages × 3) | 0 of 24 | 1 of 24 |
| One-sided exact test, gate loses more | | p = 0.5 |
| Sent back at least once (primary / harm) | 0 / 0 | 25 of 25 / 21 of 24 |
| Cost (primary / harm) | $4.38 / $4.35 | $4.90 / $4.73 |
| Mean wall time (primary / harm) | 92.7 s / 84.3 s | 107.6 s / 98.6 s |

**The primary gap of 3 runs is not the gate's.** The 18 gate runs that kept
the dependent had already changed `month_end.py` before their first stop.
The 7 that had not were all sent back, and none changed it.

**The harm-stage loss is not the gate's either.** `gradebook` 2, gate run 1
lost `base_reports`. That run made no tool call after the block. Its reply
said neither named file needed to change, and gave the reason.

## What the agents said

Every one of the 7 gave the same kind of answer: a scope decision, not a
missed file.
- *"You asked for `budget status` only, and netting refunds there would also
  change the headline Spending and Net figures… I'm not making that call on
  my own."* (gate 0)
- *"Netting refunds there would change those totals, which you didn't ask
  for. I recorded the difference in `docs/reference.md` and `CHANGELOG.md`.
  If you want the month report to match, I can change it in a follow-up."*
  (gate 23)

Several also corrected the reference document to say the two reports now
differ. **The losses the note leaves are disagreements, not oversights.** The
agent had seen the rule, before the edit and again at Stop. It weighed the
rule against the request's scope and chose the request. Whether that choice
is wrong depends on the user. The case's check says it is wrong; a user who
meant `budget status` only would say it is right. A reminder cannot change a
judgement already made, and the gate's "or say why" exit gave the agent an
honest place to record it.

## Silent and told losses (exploratory, after the fact)

Read after the result, so not pre-registered. "Told" means the agent's final
message names the dependent file, by a file-name pattern match.

- **Here:** all 10 note losses and all 7 gate losses told the user, mostly
  with an offer to make the change.
- **Even with no rule:** 10 of 13 losses on this stage in the two earlier
  batches told the user. Agents found the coupling through the reference
  doc.
- **Across every stage of those batches, silent losses:**
  - perfect rules: 16 of 50 without a rule, 0 of 50 with one;
  - a reviewer's rules: 19 of 50 without, 8 of 50 with. Seven of the 8 were
    on `parcelpost` 5, which no declared rule covered.

So the note's measured benefit is larger than the lost-dependent count
shows. What remains is mostly decisions told to the user, not silent
breakage.

## Run

98 slots in two sealed batches, every slot completed, none retried:
- primary: 50 slots, one of them the harness check;
- harm: 48 slots.

Sonnet 5.5 at medium effort, Claude Code 2.1.292, under the standing
authorization. **$18.36**, 45 minutes after the harness check (14:32 to 15:17).
The estimate was about $17.

- **The harness check:** `household_budget--7--gate--0`, read in full before
  launching the rest.
  - The config was `strict` with `rule_gate: true`.
  - The block reached the agent as Stop hook feedback.
  - The init event listed the same plugins as the reviewed batch:
    superpowers plus three marked `builtin`.
- **Gate 1** ($0, [output](rehearsal.json)) passed 4 of 4 through the real
  plugin hook:
  - `gate` sends the left-behind variant back naming `month_end.py`;
  - `note` never sends a rule back;
  - `gate` sends the correct reference back, but only for `annual.py`;
  - harm stages exist.
- **The harm stages** are the 8 v3 stages whose correct reference leaves the
  most reviewed rules behind:
  - `gradebook` 2, 7 and 8;
  - `fleet_service` 2, 3, 5 and 6;
  - `greenhouse_monitor` 4.

  The reference leaves a reviewed rule behind on **45 of the 95** v3 stages
  other than the primary, so a file-level gate would send a correct agent
  back on about half of them.

## Bounds

- One primary stage, chosen because the note left room there, with 25 runs
  per arm.
- The conversion figure rests on 7 runs. All 7 point the same way, and every
  reply gave a reason.
- The gate's message offered a way out ("or say why"). A gate without one
  would be a different design, and was not tested. At file level it would
  also have fired on the 21 of 24 harm runs it sent back here, nearly all of
  them correct.
- The reviewer is a model, and its 11 kept rules on this case include one
  (`year_report`/`_carried_into`) that no correct run touches. So every gate
  run was sent back at least once.
