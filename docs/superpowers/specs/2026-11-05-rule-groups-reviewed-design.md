# Would a reviewer keep the pairs that matter? (PLAN §13 B)

**Status: design, 2026-11-05, written before any call.**

## Question

Both rule-group experiments simulated a perfect reviewer: of a case's 50
proposals at stage 0, it accepted exactly the pairs some stage breaks.

- [acted-on](../../../results/rule-groups-acted-on/README.md): 35 of 50
  dependents lost without rules, 4 of 50 with them;
- [harm](../../../results/rule-groups-harm/README.md): no harm found.

A person reads the 50 proposals and keeps some, without knowing any future
change. **Does a reviewer reading the proposals as they are shown keep the
pairs that matter?**

## The reviewer

One Sonnet 5.5 turn per case, at medium effort, with **no tools**, which
the init event must confirm. It runs in an empty folder and is given the
case's top 50 proposals at stage 0, in the order `ep_milestones --propose`
lists them. Each proposal carries:

- its two files and two functions;
- the shared words;
- the two functions' source, read with `ast` from the stage-0 files.

It sees no stage request, oracle, result, other proposal set or file. It
is asked to reply with the numbers of the proposals it would certify. The
criterion: the two functions keep one rule, so a change to one needs the
same change in the other.

**Run once per case, used verbatim.** A reply that does not parse as a
list of numbers in range is recorded as unparsed for that case and counts
as accepting none. It is never re-asked.

## Measures

The truth is the 27 certified pairs: the top-50 proposals that pair a file
some stage's reference changes with that stage's declared dependent. These
are `eval.rule_groups_run.certify`'s.

- **Recall:** certified pairs the reviewer keeps, out of 27.
- **Burden:** proposals kept per case. This is what reaches agents as
  notes, and it is not precision, which needs a person's labels: a kept
  pair no stage breaks may be a true rule.
- **Covered stages kept:** of the 25 covered stages, those whose pair the
  reviewer keeps.

**Decision fixed in advance:**

- **Recall at least half** (14 of 27): the next experiment reruns the
  acted-on design on its five primary stages. Its certification replaces
  the perfect one, and the realistic certification becomes the bound.
- **Recall under half:** the person's half is the bottleneck, and that is
  recorded. No run follows from this design.

**Cost:** 12 calls, about $1–2 in total.

## Bounds known in advance

- A model stands in for a person who knows the project. It may be stricter
  or more lenient.
- Truth is only what the v3 stages break, so recall is measurable but
  precision is not.
