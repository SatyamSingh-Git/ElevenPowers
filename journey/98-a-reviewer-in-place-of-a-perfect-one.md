# 98 — A reviewer in place of a perfect one

*2026-11-05. PLAN §13 B, open problem 2.*

[97](97-the-first-note-acted-on.md) measured a certified rule acted on,
with one large simplification: certification was perfect. Of each
project's 50 proposals, exactly the pairs some stage breaks were declared.
No person does that, because no person knows the future changes.

So the next two steps put a reviewer in that seat and changed nothing
else.

## Would a reviewer keep the pairs that matter?

One tool-free Sonnet turn per project, blind to every stage, read the 50
proposals with both functions' source and replied with the numbers it
would certify ([results](../results/rule-groups-reviewed/README.md),
$1.44). It kept 16 of the 27 pairs that matter, past the half fixed in
advance, while keeping 3–11 proposals per project.

It was better where the proposal was right. It kept 12 of the 16 pairs
whose proposed functions really are the tie the stage breaks, and 3 of
the 9 whose are not. One of those it dropped was `parcelpost` 5's
filename pair. 97 and the stopped description experiment had already
shown that this stage breaks a different tie between the same files.

## Would its rules still be acted on?

The acted-on design was rerun with exactly the reviewer's kept pairs
declared ([results](../results/rule-groups-acted-on-reviewed/README.md),
$16.35). The dependent was lost in 31 of 50 runs without rules and 15 of
50 with them, p = 7.3 × 10⁻⁵.

Fifteen is not four, and the gap has two parts:

- **Ten losses are the dropped pair.** On `parcelpost` 5 no rules run was
  briefed on a declared file, so none received a note. Ten of ten lost,
  as control did. A rule nobody certified does nothing, as it should.
- **Five are `household_budget` 7, with the same note.** Every rules run
  there got the note naming the dependent, first in its brief, exactly
  as in the perfect run. Five of ten still left it behind, against one
  of ten before. The stage's control arm moved about as far between the
  two batches, eight then five, so ten runs a side cannot say whether the
  perfect run's extra third note mattered.

The reviewer's extra pairs were the feared cost: 4–11 declared rules a
project, most of them pairs no stage breaks. They did not crowd the note.
No run received more than two notes, and no other group was lost in
either arm.

## What the adversarial row caught

The $0 rehearsal checked `parcelpost` 5 the other way round: with its
pair dropped, no note should name the dependent. It failed. The brief did
name `billing.py`, in the import-neighbourhood line, which says what
imports the file being edited and which both arms get.

The check had matched the dependent anywhere in the brief. 97's gate used
the same check, and every row there was expected to name the dependent,
so the loose match could not show. A replay showed 97's rule note was
there, but the gate as written had not established it. This is the
rule's own argument: a check run only in the direction it is expected to
pass cannot tell a rule note from a neighbourhood line.

## Between the batches

The runtime changed between the two runs: the advice worker's deadline
fix landed after 97 was sealed. Advice is off by default, and no rules run
in either batch has an `advice.json`, so it never ran. That was checked
rather than assumed, because the cross-batch comparison is otherwise the
first thing it would undermine.

## Bounds

A model stood in for a person who knows the project, on the same five
stages chosen for their losses. The per-stage comparison with 97 is
descriptive: the runs were not concurrent.
