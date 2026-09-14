# 25. The first paired comparison, and a treatment that barely applied

Fifty-two runs, $51.60, two hours and fifty minutes. Thirteen tasks, both arms,
two replicates each, `claude-sonnet-5` at `--effort high` against a pinned
corpus and a pinned model. Nothing broke: no setup failure, no timeout, no model
mismatch, and the shared site was the same afterwards as before.

| arm | resolved |
|---|---|
| vanilla | 23 of 26 |
| gate | 25 of 26 |

That table is the least interesting thing here, and publishing it alone would
repeat every mistake this project has already made.

## Eleven of thirteen tasks agreed

| | tasks |
|---|---|
| both arms solved it, twice each | **11** |
| discordant | 1 |
| split within an arm | 1 |

A paired comparison is decided entirely by the discordant pairs. Eleven tasks
where both arms score two out of two contribute nothing at all — they are not
evidence of equivalence, they are the absence of evidence either way, and they
cost forty-four of the fifty-two runs.

The one discordant pair is `click-bec59289`: vanilla nothing in two attempts,
gate resolved in both.

## The gate blocked twice in twenty-six runs

And then the part that decides what this chunk actually measured.

The gate works by refusing to let an agent stop while its claims are unsupported.
Across the gated arm it **blocked in two runs of twenty-six** — eight percent,
consistent with the twelve percent measured in Phase A, so the mechanism is
behaving as designed rather than broken.

Both runs where it blocked were tasks **both arms already resolved**.

And on `click-bec59289`, the one pair where the arms disagreed, the gate
recorded **zero blocks**. The two arms differed by a hook that never fired. So
the difference on the only task that could carry a result is run-to-run
variance, and:

> **No discordant pair in this chunk is attributable to the gate doing anything.**

That sentence is worth more than the score. An arm can be labelled present and
be absent — E4 — and this is the same shape one level in: the arm was present,
the mechanism was installed and running, and it simply did not engage. Measuring
a treatment that applies to eight percent of runs needs vastly more pairs than
measuring one that applies to all of them, and nothing before this had measured
how often it applies *while a comparison was running*.

## The prompt fix made the corpus easier

The corpus was selected on band because the B4 sweep found `substantial` tasks
resolving at 27 to 40 percent while `small` ones resolved at 92. Pick the hard
band, get a benchmark that can move.

With the prompts framed as requests, a plain agent resolves **88 percent** of
that same hard band.

So a large part of what looked like difficulty was tasks that never asked for
anything, and the selection was aimed at a target that partly did not exist. The
selection is not wrong — it was made on the best measurement available, and it
is declared in the lock — but what it bought is smaller than it looked.

## What this costs to finish

One discordant pair in thirteen tasks. Thirty-one are needed. Taken literally
that is about four hundred tasks and sixteen hundred dollars, and taken honestly
it is one event, whose interval runs from eighty-six tasks to several thousand.

The useful thing the next chunk buys is not an answer to P1. It is a discordance
rate with an interval narrow enough to say whether P1 is answerable at this
budget at all.

## Chunk two, and the thing both chunks agree on

Another forty-eight runs, $50.17, twenty-five tasks in total across the two.
Again nothing broke.

| | vanilla | gate |
|---|---|---|
| resolved | 46 of 50 (92%) | 49 of 50 (98%) |
| gate blocks | — | **6 of 50 (12%)** |

Twelve percent is the figure Phase A measured for live blocking, arrived at
again by a different route, so the treatment rate is a property of the gate and
not an accident of one chunk.

Of twenty-five tasks: **twenty-three concordant**, one clean discordant, one
partial. And then the row that decides it.

| the gate fired on | outcome |
|---|---|
| attrs-577c782c | both arms resolved, 2/2 |
| click-4f9086bf | both arms resolved, 2/2 |
| attrs-1e07f468 | both arms resolved, 2/2 |
| attrs-e21793e9 | both arms resolved, 2/2 |

| the arms differed on | gate blocks |
|---|---|
| click-bec59289 | **0** |
| attrs-6fda0a4e | **0** |

**The gate fired on four tasks and changed the outcome on none of them. On the
two tasks where the arms disagreed, it never fired at all.**

So the six-point gap in the headline table is two tasks' worth of run-to-run
variance between two configurations that were, on those tasks, doing the same
thing. Both differences happen to favour the gated arm, which is what a
six-point gap is made of, and neither is attributable to the mechanism.

This is not "the gate does not work". It is narrower and more useful: **on this
corpus the gate fires only where it was not needed.** Four tasks is far too few
to bound the effect — it is consistent with no effect and with an effect too
small to see — but it is the first time this project has been able to say where
the treatment applied rather than only what the scores were.

## Why the baseline is at ninety-two percent

The prompts hand the agent the answer.

They are the maintainer's commit messages, and a commit message describes the
change that was made:

- *Expose converter as a decorator*
- *Make `kw_only=True` behavior consistent with dataclasses*
- *Allow field(on_setattr=NO_OP) on frozen classes*

Each names the thing to build. The agent is not diagnosing a bug, it is
implementing a described specification, and then it is graded on tests written
for exactly that behaviour. SWE-bench uses the **issue** text — somebody
reporting that something is broken — for precisely this reason: the commit
message leaks the solution.

That is the most likely cause of a ceiling, and a ceiling is fatal to a
comparison in a way a hard benchmark is not. With the baseline at ninety-two
percent there are four failures in fifty runs for any treatment to improve on,
so an effect has almost nowhere to appear even if it exists.

It is a likely cause, not a proven one. The corpus might simply be easy for this
model. Distinguishing those costs about ten dollars — a handful of tasks with
problem-shaped prompts, one arm — and is worth doing before anything is rebuilt
on the assumption.

**One shortcut to refuse.** The tempting fix is to keep only tasks the plain arm
fails. That selects on the control arm's own outcome, and regression to the mean
then manufactures an effect out of nothing. It is E6 again in a new costume, and
it would produce a positive result that means nothing at all.

## What finishing would cost

One clean discordant pair in twenty-five tasks, two counting the partial. Thirty
one are needed.

| | tasks | cost |
|---|---|---|
| at 2 in 25 | ~390 | ~$1,600 |
| at 1 in 25 | ~780 | ~$3,200 |

And that arithmetic is optimistic, because it counts discordant pairs the gate
had nothing to do with. Pairs it *caused* are running at zero in twenty-five.

The sentence that has been true since Phase A is still true, with a number
attached now: a plain agent resolves ninety-two percent of this corpus, so
there are four failures in fifty runs for any treatment to improve on. The
benchmark is not hard enough to answer the question, and more of it is not the
fix.

## What is still not known

P1, again, and now with a reason rather than an absence.

What is known that was not before: the treatment applies to twelve percent of
runs, it applied to four tasks in twenty-five, and it changed the outcome on
none of them. The next experiment is not a bigger version of this one. It needs
a corpus a plain agent does not already solve nine times in ten, and it needs to
be sized on how often the gate fires rather than on how many tasks there are.

Two chunks, one hundred runs, $101.76. The instrument is sound and the benchmark
is not hard enough to use it on.
