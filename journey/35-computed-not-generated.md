# 35. The reproduction, computed instead of generated

Phase C1. The +28pp lever, and it turned out not to need a model at all.

## What the obligation used to demand

`core/obligations.py:149` has named `reproduced` — *"that test failed before the
fix"* — since M1. It was satisfied by `_demonstrated_fix`: find a test identity
with a `FAIL` record earlier in time than a `PASS` record.

Two problems, and the second is worse.

**It demanded an ordering, not a fact.** An agent that writes the test *after*
the fix can never discharge it. That is ordinary practice, not a mistake, and
the obligation was unsatisfiable for everyone who works that way. This is the
M1 shape again: a rule that blocks correct work because the proof it wants was
never produced.

**It took the ordering on trust.** An earlier `FAIL` could be a typo, a missing
import, a fixture that was not written yet. Any of those turns green when the
unrelated mistake is fixed, and the ledger reads it as a reproduction of the
bug.

## What it demands now

The same question, asked of the tree rather than of the transcript:

> **Was this test already failing on the commit the task started from?**

If it was, and it passes now, that is a reproduction — whatever order the agent
worked in, and whoever wrote the test.

## It cost one line of new work

`core/stress.py` already builds a detached worktree at the base commit and runs
the declared check inside it, to answer §5.10's *could this check have failed?*
That run was already throwing away the thing C1 needs: its **output**.

```
exit code  ->  could this check have failed at all?      (§5.10)
output     ->  which individual tests were already red?  (§5.13)
```

One run, both answers. Asking them separately would mean building the worktree
and running the suite twice for facts that arrive together.

So C1 is not a generator. It needs no model call, which matters because
`claims.py` already establishes the house rule that a model call is the
documented fallback and not the default. The field's +28pp result is about an
agent *having* the right test; this is about the runtime being able to tell when
it does.

## The case that would have made it useless

The first forward test failed, and the reason is the whole feature.

On the old tree, a test for behaviour the fix introduces cannot even import:

```
ERROR tests/test_new.py
!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!
```

**No node id.** Not `tests/test_new.py::test_mul` — just the file. The parsers
saw nothing, `failed_before` came back empty, and the obligation stayed
undischargeable.

And this is not an edge case. It is the *ordinary* shape of the change the
obligation exists to describe: the fix adds the function, so the test that
imports it cannot run before the fix exists. A version that handled only
node-level failures would have worked on every test I wrote for it and almost
nothing real.

So collection errors are captured by file and matched by prefix —
`tests/test_new.py` against `tests/test_new.py::test_mul`.

## Both directions, as ever

- **forward** — a test red on the old tree and green now discharges the
  obligation, and the file-level case is asserted explicitly rather than
  assumed.
- **adversarial** — a test green on the old tree discharges nothing, *with a
  fresh passing record sitting right there*. Without that control the feature
  would be `return True` and every suite would look like a reproduction.

557 tests.

## What this does and does not claim

It does not claim +28pp here. That figure is an *oracle* signal measured by
handing an agent a reproduction test; this is the runtime recognising one. What
it removes is a false block — an obligation that correct work could not
discharge — and what it adds is that the recognition is now a property of the
repository rather than of the order the agent typed things in.

Measuring whether it changes outcomes needs a sweep, and a sweep needs the
registry door closed first (entry 34). The instrument is ahead of the
measurement again, which is the same place entries 27 and 33 ended.
