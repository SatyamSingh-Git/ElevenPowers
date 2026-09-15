# 32. The tool now runs its own checks the other way round

`core/stress.py`. Sixty lines of product, and the first time this runtime asks
the question it exists to ask.

## The instruction

> adversarial and forward stress tests must always run. both you should do and
> its should be a feature in our tool too. i want it must, its the best thing
> that i have learned from exp. many defects are found when these both ways of
> stress tests run.

It arrived in the middle of R10, which had just proved the point twice in an
hour. §5.0 had said this since 2026-09-12 and had been honoured in the test
suite and nowhere else. The instruction closed that gap in both directions at
once: **enforce it in code, and ship it.**

## Enforce it

R10 was fixed in `_pytest` and declared done. It was not: every counting parser
calls `_record`, which decides the result from the exit code, and *then* fills
in `record.failed` without revisiting the verdict. Seven parsers, twelve
dispatch paths, one defect — and one direction of one runner going green made
the fix look complete.

That is R5's lesson wearing a new coat. R5 put the counts within reach of the
decision and stopped one line short of using them; this stopped one parser short
of fixing them. Twice now the shape has been *almost closed*.

So the rule stopped being a rule:

| | |
|---|---|
| `test_every_runner_is_read_both_ways` | both directions for all twelve paths, **paired in one test** so neither can ship alone |
| `test_the_both_ways_table_covers_every_runner_parse_dispatches_to` | counts dispatch sites in the source and **fails if a runner is added without both** |

The second guard was watched firing — remove the `dotnet` pair, it fails — and
clearing when restored. A guard nobody has seen fail is a guard nobody has
tested.

## Ship it

A passing check is two facts short of being evidence. It has to be **fresh**,
which `evidence.py` has answered since R1. And it has to be able to **fail**,
which nothing answered at all.

```
forward       the declared check passes on the tree as it stands
adversarial   the same check, against the tree as it was before this task
              began, must NOT pass
```

`core/stress.py` runs the second one. A detached `git worktree` built from the
commit the task started at, the declared command run inside it, and the answer
cached — the base does not move while a task runs, so each command is asked once
rather than once per stop.

End to end, on a repository where the agent added a function and ran the suite
that was already green:

```
UNVERIFIED
  bug_fixed (unverified)
    missing a test covering the change passes
    ok      the related test suite passes  <- python pytest 1 passed, 0 failed
  evidence: 1 record(s), 1 fresh
  could not fail: tests: this check passes without your change, so it is not
                  evidence the change works
```

The check is still `ok`. The record is still fresh. And the tool says the thing
that matters anyway.

## Four decisions, and the reasons they went that way

**It reports; it never refuses.** §5.12: detection and intervention are
separately justified, and this project has already paid for the other choice —
the gate blocked 75 percent of runs on work that was already correct before M1
brought it to 12. Naming a weak check costs nothing and cannot destroy correct
work. Blocking on one has to earn its cost with evidence that does not exist
yet, and if it ever does, that is a separate experiment with its own false-block
rate.

**Only declared commands are run.** The same rule as `core/verify.py`, for the
same reason and one more: a recorded command is a shell line from somebody
else's workspace. The preserved corpus is full of
`cd "C:\...\tmp6wszojx2" && python -m pytest`, and re-running that somewhere new
is at best meaningless.

**The base is captured at task open, not read on demand.** An agent that commits
mid-task would otherwise move the thing its own work is compared against, and
the check would be asking whether the change discriminates from itself.

**Unknown is a third answer.** No git, no such commit, a worktree that will not
build — all report `n/a` rather than guessing in either direction. A missing
answer that reads as "fine" is the failure mode this whole layer exists to
prevent.

## Tested the way it tests

Eight tests against a real `git init`, not a mock — the entire mechanism *is*
`git worktree add --detach`, and a mocked worktree would test the mock.

- **adversarial** — a suite green at HEAD is caught as one that could not fail
- **forward** — a suite that is red at the base and green now is **not** reported
  as weak, and that control is the whole difference between a feature and
  `return VACUOUS`
- the working tree is byte-identical afterwards, HEAD has not moved, and no
  worktree is left behind
- no repository returns unknown, not a guess
- nothing runs for a need with no passing evidence, or for an undeclared command

A module that marked everything vacuous would pass the adversarial test alone.
One that marked nothing vacuous would pass the forward test alone. Either on its
own is indistinguishable from the feature being deleted, which is the sentence
§5.0 has been making since the beginning and is now making about itself.

548 tests.

## What it does not do yet

It checks **declared** commands. Most evidence in a real session comes from
commands the agent chose, and those are not covered — the ones in the corpus are
pinned to workspaces that no longer exist, so this is a real limit rather than an
oversight, and closing it means deciding when re-running an agent's own command
somewhere new is safe.

And it has never been pointed at a paid sweep. The number that would matter —
*what fraction of our own evidence could not have failed* — still needs a run
where `stress` is on. The instrument exists now, which is the part that did not
before.
