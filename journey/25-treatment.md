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

## What is still not known

P1, again. What is now known is something that was never measured before: the
treatment applies to roughly one run in twelve, and on the single pair where the
arms disagreed it had not applied at all.
