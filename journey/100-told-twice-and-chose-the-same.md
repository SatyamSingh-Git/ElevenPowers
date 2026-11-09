# 100 — Told twice, and chose the same

*2026-11-09. Test 3 of the [2026-11-05 synthesis](../docs/research/audit_2026_11_05/README.md).*

[98](98-a-reviewer-in-place-of-a-perfect-one.md) left one thing for a gate
to try. With a reviewer's rules declared, 5 of 40 covered runs got the rule
note and still lost the dependent, all on `household_budget` 7. ElevenPowers
knew each time. Its end report said the rule had changed in `budgets.py` and
not `month_end.py`, but that report goes to the person, not the agent. The
research said enforced checks beat advice. So: send the agent back once, and
see.

## What running it showed before any money

- **The finding fires on correct work.** A replay over 153 saved runs found
  it on all 9 covered losses, and on 21 of 132 correct runs. On the case
  references it fires on 45 of 95 stages.

  The rule names two files, not the two functions, so any edit to
  `budgets.py` trips every rule `budgets.py` is in. A function-level reading
  would have cut the false alarms to 6. It would also have missed every
  `parcelpost` loss, whose break goes through a function the rule does not
  name. So the gate shipped off by default.
- **`Config.save` dropped the new key.** This was found by running the
  harness path, not by reading it.

## What the run showed

The gate sent back 7 runs that had left the dependent unchanged. All 7
answered and stopped. None made another edit. Each explained, carefully and
alike, that the user had asked about `budget status`, and that changing
`report month` was a decision it would not make alone. Several corrected the
reference document to say so.

**0 of 7.** The primary's 7 against 10 is the 18 runs that had changed the
file before their first stop, not the gate. The harm side was clean. The cost
was a tenth more spend and a quarter of a minute per run.

## What it means

The losses that survive the note are not the agent missing the rule. The
agent saw the rule twice and chose the narrower reading of the request. A
reminder that offers a way out ("or say why") gets the same choice back.

That is all this shows. **A gate with no way out was not tested.** At file
level it would have had to fire on every primary run and 21 of 24 harm runs,
most of them correct. So a stricter gate first needs a finer check, and it
should demand only what a person said must hold.

Reading the replies again changed what counts as harm here. Even with no
rule, 10 of 13 losses on this stage told the user that `report month` now
differs and offered to change it. A **silent** loss is the one that hurts,
and the note nearly removes those: 16 of 50 without a rule, 0 of 50 with a
perfect one. The next question is whether a rule worded as an instruction,
"must stay consistent: change both", is followed over the request's narrow
reading
([design](../docs/superpowers/specs/2026-11-09-rule-as-mandate-design.md)).

So the declared-rule note stays as it is, and the gate stays opt-in and off.

## The same day: the rule as an instruction

The next run worded every rule as an instruction. The dependent was lost in
2 of 20 runs, against 6 of 20 with the template (p = 0.12), with no needless
edits ([results](../results/rule-mandate/README.md)).
- That leans toward the instruction, but it is a null by the rule written
  first.
- One of the two that still declined had read the instruction and said so,
  then left the file "on purpose and saying so below".

What both runs agree on is narrower and firmer: with a rule in front of
them, agents almost never leave a file behind without telling the user.
