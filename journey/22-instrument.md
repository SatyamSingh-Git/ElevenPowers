# 22. A score that can be disbelieved, and a taxonomy that can be opened

Phase B's exit is two commands: a baseline that reports a score with an interval
a rerun reproduces, and a failure taxonomy where every category cites saved
trajectories. B2 and B3 build both. Neither spends anything, which is the point
of doing them before the run rather than during it.

## Pinned means refused, not warned

Every number this project published before Phase A came from a run nobody could
repeat. The corpus was whatever had been mined that week, the model was an alias
that could point somewhere else tomorrow, and the score was a bare percentage
with no statement of how much of it was luck.

`--pinned` refuses on any of the three:

- **a model alias.** The host resolves it at request time, so two sweeps a month
  apart can run different models and report one number. This is not
  hypothetical — the bundle manifest was doing exactly that until a live run
  exposed it.
- **no corpus lock**, because a score is a claim about a benchmark and an
  unidentified benchmark makes it a claim about nothing.
- **a dirty working tree**, because the harness that produced the score would not
  be recoverable from the commit.

A refusal is tested in each direction. A harness that refuses everything is not
pinned, it is broken, and only the forward case tells those apart.

## The interval resamples tasks, not runs

Fifteen tasks at three replicates is forty-five numbers and nowhere near
forty-five independent ones. A task the agent always solves contributes three
identical successes; a task it never solves contributes three identical
failures. Treating those as independent observations narrows the interval by
roughly the square root of the replicate count.

The consequence is specific and bad: **a rerun that agrees would look like a
contradiction.** The interval would be too tight to contain honest variation, and
the natural reading of that is "something changed" rather than "the interval was
wrong".

So the interval is a percentile bootstrap that resamples tasks, carrying each
task's replicates with it. The test asserts that tripling the replicates changes
the interval *not at all*, which is the property that matters and the one an
implementation is most likely to get backwards.

This is the third time the same correction has been needed. E2 forced it on the
paired comparison, E6 forced the withdrawal of a run count derived from a
within-arm quantity, and here it decides the interval. The unit of evidence is
the task; runs of one task are one observation seen repeatedly.

## Reproduces means overlapping, not equal

Agent runs are stochastic. A rerun producing the identical score would be
suspicious rather than reassuring, so `--compare` asks whether each score falls
inside the other's interval.

And it **refuses outright when the corpora differ**, however close the numbers.
Two scores from two benchmarks are not a reproduction, and that is the comparison
somebody makes by accident a week after re-mining. The fingerprint is order
independent, because the same instances mined in a different sequence are the
same benchmark — a check I first wrote as `fingerprint(lock) == fingerprint(lock)`,
which compares a file with itself and cannot fail.

## Measuring what reached the model

The plan's sentence for this phase is *measure what actually reaches the model
rather than what is installed*, and it is there because of **E4**: an arm named
for a plugin whose directory was unset ran as plain vanilla, was recorded under
the plugin's name, and would have been reported as a composition result. Nothing
measured the difference, so nothing noticed.

From a real answer:

```
cacheReadInputTokens      584,272
cacheCreationInputTokens   14,935
inputTokens                   123
```

Cache **creation** is the stable prefix — system prompt, tool definitions,
whatever a plugin injected — written once. Cache **reads** grow with the number
of turns and say nothing about configuration; using the larger number would
report a talkative run as a heavily configured one. So context is measured from
creation, and an arm that declares a plugin while sending vanilla's context now
says so in the report.

It is a proxy, not an inventory. It cannot say *what* arrived, only how much,
and that is worth stating rather than implying otherwise.

## A taxonomy decided by evidence

This project has twice explained a failure from a story rather than from the
run: a null diagnosed from the agent's own test without reading the answer key,
and a conclusion that failures needed information the runtime could not reach
when six of seven were reachable. A taxonomy is the obvious next place for that
to happen.

So every category is decided by something in the bundle, and every category
prints the bundles it came from. **A category you cannot open is a category you
are about to tell a story about.**

| category | decided by |
|---|---|
| setup, timeout | the grade outcome — harness breakage, never the agent |
| host-error | `is_error`, `api_error_status`, or an unfinished turn |
| abstained | the agent said it could not |
| no-patch | the patch is empty |
| regressed | the ask passes, something else broke |
| **localised** | wrong fix, but it edited the maintainer's files |
| **misplaced** | wrong fix, and it edited none of them |
| resolved | the ask passes and nothing else broke |

The order is part of the taxonomy and is tested. A run that timed out *and*
changed nothing is a timeout; without a fixed order the same run lands wherever
the implementation happens to look first, and the counts describe the code
rather than the runs.

The last two are the split that matters. A candidate touching the right files
found the code and wrote the wrong change; one touching none of them never found
it. Different problems, different fixes, and nothing here has distinguished them
before. It needed bundles to record the maintainer's file list — **a bundle that
needs the corpus to be interpretable is not the self-contained thing E3 bought.**

Where that list is missing the answer is `unattributed`, not a guess. Both
categories would be a coin flip.

## Refusing to look more certain than it is

Two things the report says about itself:

Under thirty runs it prints *a listing, not a distribution — read the bundles, do
not quote the proportions*. And it names any task whose replicates landed in more
than one category, because reading one failure of a flaky task as a finding is
how a noise floor becomes a diagnosis. This project published a null once on a
suite where two identical passes scored 69 and 94 percent.

The baseline does the same: when the interval spans more than forty points it
says plainly that it is a pilot and that the point estimate alone would be a
claim it cannot support.

## What is still not known

Nothing has been run. B2 and B3 are an instrument, and an instrument that has
measured nothing has proved nothing about itself beyond its unit tests.

The one real check available — the four bundles from Phase A's live sweep —
classifies all four as `resolved`, which exercises the happy path and nothing
else. Every failure category is unit-tested and none has been seen in the wild.
That is exactly the state Phase A was in before its first live sweep found a
defect in twenty minutes, and it is the reason B4 is a separate step rather than
a formality.
