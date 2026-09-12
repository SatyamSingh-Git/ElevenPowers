# 17. Two evaluator defects closed, and a test that could never have passed

## The one that changes what past numbers mean

Of the sixteen defects, **E1** goes first because it is the only one that
reaches backwards. The others make future measurements untrustworthy. This one
made a published null mean something narrower than it was reported to mean.

`_verify_real` overlaid the fix commit's test files and ran exactly the
fail-to-pass node ids. If they passed, the task was resolved. Nothing asked
whether the rest of the suite still worked.

So `resolved` meant *the requested behaviour works*. It did not mean *and
nothing else broke*. A bug fix owes two things, and the grader checked one —
on a project whose gate exists almost entirely to catch the other.

## The fix, in two halves

**The miner had nowhere to put a preservation set.** `Instance` recorded `f2p`
and no counterpart, so even a correct grader would have had nothing to enforce.
`eval/mine.py` now runs the whole suite at both ends, with the fix commit's
tests in place, and keeps what is green in both:

```python
p2p = sorted((passing_nodes(before) & passing_nodes(after)) - set(f2p))
if not p2p:
    return None
```

A commit yielding none is discarded. A task that cannot show a regression
cannot grade a fix, and keeping it would reintroduce E1 for that task alone
while the schema claimed otherwise.

**The grader ran node ids and read an exit code.** Both parts were wrong. A
preservation set on a real repository is hundreds or thousands of nodes, and
no argv holds that — Windows gives up around 32k characters, which a suite of
1,900 tests exceeds by a factor of three. So grading now runs the suite once
and asks a different question: **is each required node in the set that passed?**

```python
passed = passing_nodes(done.stdout + done.stderr)
unfixed = [n for n in source["f2p"] if n not in passed]
```

Membership rather than exit code, and that is not a stylistic preference. An
exit code says the run was green. It does not say the tests anyone cared about
were collected at all, and the audit asked for exactly that distinction. It
also means tests the agent wrote for itself cannot fail the grade, which is
right: they are its own working notes, not the standard it is held to.

## The hole the fix opened, and closing it

Adding a preservation set creates an incentive that did not previously exist.
If the grader checks `tests/test_keep.py::test_label`, then an agent that edits
`test_keep.py` until it agrees with its patch is recorded as having preserved
it.

That is this project's oldest failure in a new place: **the agent marking its
own work, with the grader as the second marker.** So the test tree is restored
from the upstream repository before grading — not from the run's own git, which
the agent can rewrite, but from the copy the run cannot reach. SWE-bench does
the same thing for the same reason.

It would have been easy to ship the preservation set without this and report
E1 as closed. The check would have looked identical and meant nothing.

## Replacing the probe that found it

The audit's own probe for E1 mocked `subprocess.run` and asserted on the argv.
That was enough to demonstrate the defect and it is the wrong test to keep: it
would pass against a grader that invokes the right tests and then ignores their
result. **What it invokes is not the claim. The claim is what it says about a
patch.**

So the probe is now five tests against a real two-commit repository, real git,
real pytest, no mocks:

| | |
|---|---|
| a correct patch | resolves — the control, because a check that rejects everything proves nothing |
| a patch that fixes the bug and breaks `label()` | `regressed` |
| the same patch, with the existing test edited to agree | still `regressed` |
| a required node that was never written | `unfixed`, not a green exit code |
| the miner, on the same repository | records a preservation set disjoint from `f2p` |

`Graded` replaced the boolean, reporting `resolved`, `unfixed`, `regressed`,
`timeout` and `setup` separately. A bare bool cannot distinguish a patch that
never worked from one that worked and broke something else, and reporting them
as the same number is how the measurement lost sight of its own subject.

## The probe that could never have passed

**E2** — `eval/analyse.py` kept one row per task and arm, so a second `--runs`
replicate overwrote the first — came with a probe I had written the day before:

```python
assert sum(len(v) for v in load(data).values()) == len(rows)
```

Those values are per-arm dictionaries. `len(v)` counts **arms**, not runs. It
sums to one against the defect, which looks like a correct failure, and it sums
to one against the fix as well.

So the test failed for a plausible reason and **would have gone on failing
after the defect was gone**. A strict xfail that can never xpass is a defect
recorded as permanently unfixed — the file's whole mechanism is that a fix
forces its marker off, and this one would never have fired. It would have sat
there looking like diligence.

I found it by reading the probe before implementing the fix, which is only
luck. The reliable check is the one the mechanism already provides: **fix the
defect and confirm the test flips.** It did, once the assertion counted runs:

```
[XPASS(strict)] E2: analyse keeps one row per task and arm
```

That is now the rule for the remaining fourteen. A probe is not evidence that a
defect is captured until it has been seen to xpass against a real fix.

## What replicates cost the statistics

Retaining them raised a question the old code had never had to answer. Rates
are now over runs; **the paired test stays over tasks.** Pairing replicate
against replicate would have multiplied the apparent sample size by the number
of passes while the runs within a task stayed correlated — significance bought
by claiming independence that was never there. At one replicate each the test
reduces to exactly McNemar, which is the check that it is the right
generalisation rather than a different test wearing the same name.

`eval/noise.py::outcomes` now refuses a file holding replicates rather than
reading its last run. Its question is what two separate passes did; a file of
replicates is not a pass, and answering anyway with a quarter of the data is
the same failure as E2 in a second place.

## What it costs, and a number that was nearly invented

This section first said the suite had gone from about forty seconds to 164, and
that the slowdown was the price of tests that exercise the thing rather than its
call signature. The forty seconds was written from memory. Measured, against a
worktree at the previous commit:

```
before   379 passed, 16 xfailed in 167.79s
after    387 passed, 14 xfailed in 163.89s
```

**It did not get slower.** It was already this slow, and the reasoning built on
top of the invented number — a trade-off accepted, a cost justified — was
reasoning about something that never happened.

Then, writing that correction, I typed the "after" line before running it. The
counts were right by luck; the time was four seconds out. **Twice in one
afternoon, in the section about not asserting numbers.**

The new E1 tests are the slowest in the suite at about six seconds, and grading
a seeded task now runs the whole visible suite instead of one file. Neither
shows above the run-to-run variation.

This repository's rule is that every figure in it comes from a command. The
figure was in a document about the importance of not asserting things, in a
section explaining what a measurement cost.

## What this does not fix

The twelve-bug null is still not re-runnable. Those candidate patches were
deleted with their `TemporaryDirectory` (**E3**), so the corrected grader has
nothing to re-grade. Whether any of those five successes was a regression is
now unanswerable rather than merely unasked — the fix arrived after the
evidence was thrown away.

That is the argument for E3 being next among the evaluator defects, and for the
rule the audit stated plainly: preserve the artifacts before trusting the
number.

## A process mistake, since they get recorded here

While a full suite run was in flight I ran `git stash` in the same working tree
to time the old code for comparison. The run finished and reported a number
that was measured against a tree changing underneath it. It happened to be the
right number; that was luck, and a corrupted one would have looked exactly the
same. Two operations on one working tree is the same class of error as the
concurrent-writer defect sitting unfixed in **R7**.
