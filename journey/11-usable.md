# 11. Two wrong fixes and a right one

## What M1 was for

Live measurement had left the product failing its own headline product metric.
The gate blocked three quarters of runs, and on nearly all of them the work was
already correct. A tool that interrupts almost every turn gets switched off, and
once it is off nothing else about it matters.

The plan gave M1 an exit criterion rather than an intention: **blocks on
already-correct work below 25 percent of runs, with resolution no worse.** Four
passes over the same sixteen tasks and model were needed to reach it, and the
first two were wrong.

## The first wrong fix: say it earlier

The obvious theory was that the gate fires at the end, by which point the
obligations named in the opening banner are long gone. So the runtime gained a
guidance channel: once, at the edit that opens a claim, say what will be needed.

```
this task will need, before it can be called done:
  a test covering the change passes
    run the test that exercises this change, by name or by file
  the related test suite passes
    run the suite covering the files you changed, not just the one test
```

Blocking went from 12 of 16 runs to 14. Within the noise floor, and if anything
worse.

Before concluding the idea had failed, the obvious question was whether the text
had arrived at all, because three components in this project have shipped doing
nothing. It had: the guidance appears verbatim in the run transcripts. The
channel works and the hypothesis was simply wrong. **Telling an agent what will
be needed does not make it go and get it.**

## What the decision records said

M1 also made a block record *which* obligation was unmet, which every block in
ten phases had failed to do. That, plus the transcripts, gave the answer the
theory could not:

```
blocked runs examined: 15
    25  the related test suite passes
     8  a test covering the change passes

blocked runs where the agent edited a test file: 15/15
```

**In every blocked run the agent had written a test and run it.** What it never
did was run the whole suite, because that is a second invocation of the same
tool. The gate demanded a scoped run and a broad one, and nothing does both
voluntarily.

## A defect found on the way

The commonest unmet obligation before that was stability: twenty clean runs of a
repeat harness. It was triggered by any of a list of words appearing anywhere in
the request, so `truncate(text, limit) sometimes returns a string longer than
limit` was treated as nondeterministic. It is entirely deterministic, described
conditionally. A bare "race" also triggered it, so pasting a job advert into a
bug report demanded a repeat harness.

Measured on 566 real bug reports, the old rule asked for twenty clean runs on
**26 percent** of them. A term that can only mean nondeterminism now stands
alone; an ambiguous adverb needs the same thing failing and not failing, in the
same sentence as the failure. That is 4 percent, and the residue is pasted
documentation containing the word flaky.

This is the same defect as the unanchored "read" in the no-claim rule: one word
matched anywhere in text the user pasted rather than wrote. Twice makes it a
pattern.

## The right fix: stop demanding, start computing

Blocking to make an agent run a command costs another agent turn, which is 2.5
times the tokens. Running the command costs seconds and no tokens.

So when a project declares how its tests run, the runtime runs them at the stop
and computes the evidence itself. Only declared commands ever execute; guessing
one would mean running something nobody asked for, which is not a trade worth
making for a shorter obligation list.

The thesis was always that completion is computed rather than asserted. It had
simply never been applied to the runtime's own gaps.

One more step was needed. A whole-suite run produces no per-test record, so a
task that writes a test and runs everything still cannot discharge a scoped
obligation. Watching the task write a test and the suite go green is the same
proof by another route, which is the argument that already admits a red-to-green
transition.

## The held-out set caught that cheating immediately

"A test file was touched and the suite is green" also describes an agent that
**emptied** a failing test. Miss rate went from 0 to 6 percent the moment the
rule was written, on `failing_test_deleted_instead_of_fixed`.

The fix is that the file must still declare a test. Third time a held-out case
has caught something the tuned set waved through, and the strongest argument in
this project for keeping one.

## Result

| pass | blocked | on already-correct | resolved | turns | cost |
|---|---|---|---|---|---|
| no guidance, old rule | 75% | 69% | 88% | 12.8 | $2.63 |
| guidance, old rule | 88% | 81% | 88% | 14.4 | $2.74 |
| guidance, narrowed rule | 81% | 75% | 81% | 13.7 | $2.58 |
| **self-discharge** | **12%** | **12%** | 75% | 9.8 | $2.23 |

Resolution reads as a drop against that 94 percent plain pass, so the question
is whether anything that reliably works broke:

```
tasks a plain agent always resolves : 11
  of those, self-discharge failed   : 0   (none)
unstable tasks                      : 4   3 failed
never-resolved tasks                : 1   1 failed
```

Every failure was a task that fails anyway. The plain arm itself scored 69 and
94 percent on two identical passes, so 75 sits inside its own range, and the
task-level breakdown says that far more convincingly than a p-value at sixteen
runs would.

**M1 exits.** Blocks on already-correct work fell from 69 percent to 12, turns
fell by a quarter, cost by 15 percent, and nothing stable regressed.

## What it cost, and what that says about method

Four live passes, 64 runs, about $10. Two of the four tested ideas that turned
out to be wrong, and both were wrong in the same way: they were theories about
why the agent behaves as it does. The one that worked came from an instrument
that recorded which obligation was unmet, and from reading fifteen transcripts.

The plan says the next unmet exit criterion is what gets worked on. That rule is
what kept three failed attempts pointed at the same target instead of drifting
to something more interesting after the first one did not work.
