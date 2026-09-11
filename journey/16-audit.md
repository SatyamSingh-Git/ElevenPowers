# 16. An audit, sixteen reproduced defects, and a different objective

## What arrived

An external audit of revision `9a21de1`, with a reproduction script, an evidence
appendix, and a report that does two things at once: it reproduces sixteen
defects in the runtime and the evaluator, and it argues the project has been
optimising the wrong objective.

Both halves are accepted. The second is the larger change.

## The defect that undoes a published result

**E1: the grader never ran a preservation set.** `_verify_real` overlays the fix
commit's test files and invokes only the fail-to-pass node ids. Nothing checks
that the rest of the suite still passes.

The audit's own probe mocked `subprocess.run` and therefore only established the
argv. That was worth confirming for real, so: take a mined instance, apply the
maintainer's own source fix so the hidden tests pass, then break an unrelated
existing test.

```
hidden tests pass after the maintainer fix: True
broke test_arguments.py, existing suite: RED | 1 failed, 1914 passed
grader still says resolved: True
```

So "resolved" meant *the new tests pass*, not *and nothing broke*.

The twelve-bug comparison is not invalidated as a comparison — both arms were
graded the same way. It is worse than that in a specific direction: **the gate's
primary mechanism is catching regressions, and the grader was blind to
regressions.** If the gate had prevented one, the measurement could not have
seen it. A null was published from an experiment structurally incapable of
detecting the intervention's main benefit.

## Fifteen more, all reproduced

Running `docs/research/audit_2026_09_11/reproduce.py` reproduces every one.

The evidence layer, which is the part this project claims as its foundation:

- **R3** deleting an observed file yields `GONE`, and the ledger rejects only
  `STALE`, so the verdict is `VERIFIED`.
- **R4** fail → pass → fail returns `VERIFIED`: an older pass satisfies the
  obligation while the latest failure is excused as pre-existing.
- **R5** `echo pytest` produces a passing suite record with zero tests.
- **R6** `_test_written_and_suite_green` searches `touched ∪ seen`, and `seen`
  includes files merely **read**. Reading an existing test plus a green suite
  satisfies "a test covering the change passes", with a caveat that says a test
  was written. **That rule was added in M1 to cut false blocks, and it cut them
  partly by being wrong.**
- **R7** a new request inherits the previous task's id, evidence, read set and
  `guided` flag.
- **R9** clean repeats of `python -c pass` certify a flaky test.

And the host contract: **H1**, documented failure hooks put the error at the top
level, while `read_result` looks only under nested keys. A documented failure
shape yields no evidence at all. That narrows the headline "174 of 174 failures
read correctly" to what it always was — **a replay result. Replay fidelity is
not delivery fidelity**, and this project has confused the two before.

## The argument that changes the plan

Beneath the defects, a harder point. The project has been organised around a
stop gate and a census of gaps in competing frameworks. That is a reasonable
scope for a verification plugin and too narrow for the brief, which was to make
coding agents dramatically more capable.

> Better stopping cannot explore a diagnosis or implementation the worker never
> considered.

The residual-gap census ranks work by novelty. A mature, widely implemented
capability — localisation, for instance, explicitly excluded from the old plan
because the field is crowded — can be the largest missing contributor to
performance. Excluding it optimises novelty rather than task success.

And the decomposition that makes this concrete: for a pool of candidate patches,
**pool coverage** is how often at least one is correct, **selected success** is
how often the chosen one is, and the gap between them is selection regret. If
every candidate is wrong, no better examiner helps. That is far more actionable
than another gate-on/gate-off number, and it was never measured here because
candidates were never preserved — `TemporaryDirectory` deletes them, and the run
record keeps no diff.

## What v0.7 became

The system now owns an **outer loop**: generate candidates, select among them,
decide what to try next. Verification is one component rather than the purpose.
The completion state is an output, not the organising principle.

Phase A is blocking and unglamorous: fix all sixteen defects with regression
tests, add run bundles that make a run reconstructible, grade in an
evaluator-owned workspace from an exported patch, and provision an isolated
Linux worker — because letting the absence of Docker on one laptop define the
scientific scope was a mistake nobody should have to point out.

Then baseline, then separate generation from selection, then spend compute where
it creates new solutions.

## Eight claims withdrawn or qualified

Including some this journey has repeated: evidence is *not* bound to exact file
contents; "the instrument is honest" conflates five separate things; equal
failure counts do not mean no new failures; real commits improve authenticity
without removing sampling bias or grader defects; and the rule that a useful task
requires the naive fix to break the visible suite defines a diagnostic subset for
one mechanism rather than coding correctness — **selecting the benchmark that way
favours the intervention being measured**, which is the thing this project has
been most careful about elsewhere.

## What it cost, and what it is worth

Nothing except the reading. Sixteen defects, a withdrawn interpretation of the
headline result, and a change of objective, for the price of someone else looking
carefully.

The uncomfortable part is the pattern. The audit found what it found by opening
the source and running it. That is the same move that produced every real finding
in this journey, and it keeps having to come from outside.
