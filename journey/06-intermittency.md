# 6. The flaky-bug problem

## The defect that started it

The plan listed seven core pieces. Six were built. The seventh, a repeat runner,
was not, and its absence left a hole that was worse than a missing feature.

A request describing intermittency adds a `stable` obligation: repeated runs must
show the failure is gone. But that obligation was declared as runtime evidence,
and any runtime evidence satisfied it. So:

```
obligations: ['test_added', 'suite_green', 'stable']
  test_added   met=True  from: pytest tests/test_race.py -q
  suite_green  met=True  from: pytest tests/ -q
  stable       met=True  from: python repro.py
STATUS: VERIFIED
```

One execution of a reproduction script that happened not to fail satisfied
"repeated runs are stable". On a one-in-six bug, that verdict is wrong five
times out of six.

This was the worst kind of bug for this project: a false verification, on the
exact task class named as the differentiator, produced by the verification layer
itself.

## Why nothing else has this

Across the fourteen systems read from source, none ships a repeat runner, a
stress harness, or any instrumentation for nondeterministic bugs. Every hard-task
trace in the research notes ends the same way, with the analysis left to the
model.

One system is actively worse than neutral. OpenHands halts a run after three or
four identical action and observation pairs, which is precisely what
deliberately re-running a flaky test looks like.

## The interesting part is not the runner

Running a command fifty times is fifteen lines. The question worth answering is
how many times is enough, and "a few more" is not a standard.

It has an arithmetic answer. If a fault still occurs with probability p, the
chance of n clean runs in a row is (1-p)^n. Requiring that to fall below one
minus the confidence gives:

```
n >= log(1 - confidence) / log(1 - p)
```

The failure rate is not a guess either, because the agent measures it while
reproducing the bug. Observing 3 failures in 30 runs gives 10 percent, and 95
percent confidence then needs 29 clean runs.

So the runtime computes the bar and names the exact command:

```
missing  repeated runs show the failure is gone
         ep-repeat 29 -- python -m pytest tests/test_worker.py -q
         so far: still failed 3 of 30
```

The agent does not have to reason about statistics, and cannot pick a
convenient number. This is the principle from the plan applied literally:
deterministic software should remove reasoning burden from the model, but only
where the answer really is deterministic.

## Verified end to end, with real randomness

A repository was built with a genuine one-in-six failure, and the whole loop run
against it. Measured: 3 failures in 30 runs. The gate demanded 29 clean runs,
named the command, and refused completion. After 29 clean runs it passed:

```
VERIFIED
  bug_fixed (verified)
    ok      a test covering the change passes  <- tests/test_worker.py
    ok      the related test suite passes  <- tests/
    ok      repeated runs show the failure is gone  <- 29 runs, 0 failed
```

## Three defects the demo found that the tests did not

Every one appeared only when the whole loop ran against a real repository.

**The hint named the wrong command.** It suggested repeating the whole suite
rather than the test that had actually been measured flaky. The fix is obvious in
hindsight: whatever was already measured for flakiness is by definition the
command that shows the bug.

**The reproduction was reported as somebody else's breakage.** The end report
lists failures that predate the task so the agent is not blamed for them. A
repeat run that found the bug looked exactly like one, so the bug being fixed was
listed as pre-existing. Stability measurements are now excluded from that check.

**The coverage warning fired on a correct pairing.** `tests/test_race.py`
exercising `src/worker.py` shares no name, so the advisory note complained. That
describes most real projects. The note now speaks only when a better-matching
test file exists in the repository and was not the one run, which is the only
case where the reader can act on it.

## What it cost

About 200 lines: the runner, the arithmetic, the command-line tool, an evidence
kind, and the obligation check. Plus 20 tests and 4 scenarios.

Standing result across the whole scenario set: 46 scenarios, 0 percent false
blocks, 0 percent misses, 70 unit tests green.

The runner is also useful on its own. `ep-repeat 50 -- pytest tests/test_x.py`
answers "is this test flaky, and how flaky" without any of the rest of this
project being involved.
