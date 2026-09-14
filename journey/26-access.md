# 26. A second audit, and the answer was on the internet

A hundred paid runs were written up as *the benchmark is not hard enough*. An
external review of the saved bundles says the diagnosis is wrong, and checking
it against the archive says the review is right.

Everything below was verified here before it was accepted, because the last two
times this project explained a result it did so from a number nobody had opened.

## The agents fetched the answer

`click-bec59289` is the one clean discordant pair in the sweep — the task the
plain arm failed twice and the gated arm resolved twice, the single result the
comparison rested on. Its gated transcript contains this, as a returned
`tool_result`:

```
"sha":"f383a541...","filename":"CHANGES.md","status":"modified",
"blob_url":"https://github.com/pallets/click/blob/bec59289d8cf9b9b4010642b2fee483e5f8eeefc/CHANGES.md"
```

`bec59289d8cf9b9b4010642b2fee483e5f8eeefc` is the task's own fix commit. Not a
guess, not the agent claiming it matched upstream: the GitHub API returning the
answer's changed files, with raw URLs to the patched content.

Screening every run against its own `fix` sha, **24 of 100 runs name the commit
that is their answer**, in full. The review's broader screen for returned GitHub
diff hunks found **42 of 100**. Neither number is the interesting part. The
interesting part is that the sweep never had a closed-book condition to begin
with, so:

> **92 percent is not a measurement of independent repair. It is a measurement
> of applying a described upstream change with access to that change.**

The agents did nothing wrong. They were asked to make a change described by its
commit message, and fetching the commit is a sensible way to do that. This is an
evaluation boundary that was never drawn. `_sandboxed` stops `pip` from touching
the machine and `shared_site` notices if something moved; neither has anything to
say about the network, the local corpus clones, or the upstream repository.

And the conclusion that followed from 92 percent — *the corpus is too easy, make
it harder* — is treatment of a symptom. Rewriting commit messages into vaguer
reports does not close a channel that returns the patch on request.

## Twelve percent was the wrong denominator

The gate recorded **six block events across four runs of fifty**. Two runs were
blocked twice.

That is **8 percent of gated runs**, and 0.12 events per run. Reporting 12
percent as "the gate fires on twelve percent of runs" mixed the two, and then
D94's sizing arithmetic was built on the mixture. Events, blocked runs, blocked
tasks and blocked stopping points are four different denominators, and an
experiment sized on the wrong one is sized wrong in a direction nobody checked.

## "The hook never fired" was false

The strongest claim in the previous entry was that on the two discordant tasks
the arms differed by a hook that never fired, so the difference could not be the
mechanism.

The gated `click-bec59289` run has **zero Stop blocks and four scope questions**
in its own ledger. The package intervenes before Stop — opening obligations,
scope questions, declared commands — and `blocks_recorded` counts none of that.

So the arms were not identical on that task. Whether the intervention caused the
patch is still unknown; what is now known is that the sentence asserting it
could not have was written from a field that does not measure what it was read
as measuring.

## What else needed narrowing

- **Thirty-one discordant pairs is not a universal requirement.** It is a power
  calculation for one alternative, a 75 percent win rate among disagreements.
  Six discordant pairs all favouring one arm already give a two-sided exact
  p of 0.031.
- **The observed comparison is p = 0.5**, which is weak evidence, not the
  absence of a measurement. Saying "no measurement" overstated it in the
  direction of drama.
- **Twenty-two tasks were solved in all four attempts**, not twenty-three.
  `attrs-0f758fe5` was solved once and failed once in each arm, and calling it
  concordant hid that.
- **Concordant tasks are not worthless.** They carry prevalence and effect-size
  information even though the conditional test does not use them.

## Three gaps in the containment shipped that morning

The process-containment fix from `fd4e8ec` was reviewed too, and it had a race
and two silent-failure paths:

`Popen` started the agent running and the job was assigned afterwards, so
anything spawned in that window need not have been contained. The return values
of `SetInformationJobObject` and `AssignProcessToJobObject` were ignored, so a
job that contained nothing was indistinguishable from one that worked. And the
Win32 calls had no declared `ctypes` signatures, which passes a pointer-sized
handle as a C `int`.

All three are closed. The process is created **suspended**, assigned, checked
with `IsProcessInJob`, and only then resumed; every call is checked and a run
that cannot be contained raises instead of proceeding. The probes remove the
resume and assert nothing executes, and force the binding to fail and assert the
agent never ran.

The fix was twelve hours old and had a passing test. The test covered the case
that had already bitten.

## What this changes

The corpus work was not wasted — the mining, the lock, the chunking and the
bundles are what made this review possible without buying another sweep. But the
next purchase is not a bigger comparison, and it is not a harder corpus either.
It is an information boundary: a worker that can see the base snapshot, the task
text and its dependencies, and cannot see the fix, the hidden tests, the corpus
metadata, other attempts, or the upstream repository.

Until that exists, every number this project produces about repair performance
is a number about repair performance *with the answer available*.
