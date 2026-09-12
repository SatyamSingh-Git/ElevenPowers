# 13. Building the ruler, and finding it already existed

## Why this phase happened

M2 compared the composition baseline against its parts on a suite where the
plain agent failed one task of sixteen, and that task was the one nothing ever
resolves. No arm had headroom, so no arm could have shown a benefit. The
comparison could not have worked.

A suite that can measure blocks M2's exit and M5's both, so it became the
critical path.

## Four rounds of being wrong

**Round one: harder tasks.** Six tasks in what looked like the right shape.
Calibration, run before comparing anything on them, said three of the six were
resolved by a plain agent every time. All three turned out to be single-function
bugs with extra files around them: one function, one stated contract. That is
the shape that had already failed twice.

**Round two: genuinely multi-file.** An export whose cause is in a batching
helper, an index and a search that disagree about spacing, a tax helper applied
at the wrong level. All three scored 100 percent. In a three-file repository
nothing is hidden; the agent reads all of it in one turn.

**Round three: add traps.** Give each a second consumer the obvious fix breaks.
Now four of six scored zero. Nothing could show an improvement from the other
direction.

**Round four: change the model.** The weak model failed four and resolved two.
The strong model resolved four and failed two. **Neither ever landed in
between.** These outcomes are not coin flips: for a given model a trap is either
seen or it is not, consistently, so chasing a 30-to-70-percent band was chasing
something that does not exist for this kind of task.

## The rule the fourth round exposed

Sorting the tasks by which model resolved them made it obvious.

| task | does the naive fix turn the **visible** suite red? | weak | strong |
|---|---|---|---|
| `credit_sign` | yes, the receipt test | 0% | 100% |
| `percent_display` | yes, the export test | 0% | 100% |
| `stale_admin` | no, nothing visible counts fetches | 0% | 0% |
| `dropped_rows` | no, the page test passes either way | 0% | 0% |

> **A task measures verification only if running the existing suite would catch
> the fix an agent reaches for first.**

Where it would not, no amount of evidence-gathering helps, and the task measures
raw capability instead. That is why both models failed those two identically:
the gate's entire mechanism is to make the agent run the suite, and for those
tasks running the suite would have told it nothing.

Obvious in hindsight, and derivable before writing a single task by asking what
the gate could possibly do here. It cost four rounds and about eight dollars
instead.

## Then the search for how to do this properly found something else

Looking up how benchmark builders construct discriminating suites turned up
**SWE-bench's structure, which is this rule under other names**: `FAIL_TO_PASS`
is the hidden test, `PASS_TO_PASS` is the visible suite that a wrong fix must
break, and each instance is validated repeatedly to exclude flaky ones, which is
the calibration built here. Three things re-derived the slow way.

And in the same search, **prior art on the thesis**.

[Proof-or-Stop](https://arxiv.org/html/2607.14890v1) publishes the same spine
this project has: claim, evidence, gate, lifecycle transition. It binds evidence
to a `materialHash` over the tracked source tree and rejects it "the instant the
source tree changes". That is the invalidation mechanism this project treated as
its distinguishing feature. It names the failure this project was built around,
an unattended agent retrying until a visible check turns green. Its endpoint,
visible-pass/hidden-fail amplification, is the structure of these task suites,
arrived at independently.

So the bounded novelty claim was withdrawn. What survives is narrower and is now
stated that way: evidence captured by parsing tool output the agent already
produced, needing no cooperation from the agent and no process from the user;
claims inferred rather than declared; and invalidation at test-impact
granularity rather than whole-tree, which is planned and therefore a claim about
the future.

Finding it while researching something else is the ordinary way prior art turns
up, and the standing rule in this project has always been that a novelty claim
names the search that failed to find it. This search succeeded.

## What it gives back

Their ablation is powered where everything here has been a pilot: 9,240 cells
over 24 tasks, amplification of 1.72 percent for naive retry against 0.11
percent gated, interval excluding zero, at 1.2 times the tokens and 1.5 times
the wall clock.

Three things follow. The effect being hunted is **small**, so the 252-runs
estimate was not pessimistic. The base rate has to be **raised by design**, which
is exactly what a suite of catchable traps does. And the cost figures here, 1.4
to 2.5 times, sit just above theirs, which is a sanity check on both.

## What changed as a result

**The design rule is a test.** Each task records the fix an agent reaches for
first, as data, and `test_the_naive_fix_turns_the_visible_suite_red` asserts the
suite catches it. A task that cannot fail that test cannot measure anything.

**The calibration tool was wrong and is fixed.** It treated a task the baseline
never resolves as useless and lumped it with the ceiling. Only the ceiling is
useless: a task at zero is prime headroom provided some arm can overturn it, and
one run says whether it can.

**Two instruments, not one.** The hand-written suite for cheap per-run metrics
such as block rate and cost, and real bugs for anything else. The second exists
because the population problem has now bitten five times: hook payloads, gate
scenarios, claim prompts, and two rounds of seeded bugs, each written by the
person whose code they graded and each agreeing with it.

## The trapped suite did not test what it was built to test

Before moving on, the trapped tasks got their proper trial: the gate against a
plain agent, on a suite designed so that running the tests would catch the wrong
fix.

**The gate blocked 1 of 12 gated runs.** Self-discharge ran the suite almost
every time and found it green.

Which means the traps were never sprung. The design assumed the agent would
reach for the obvious wrong fix, break the suite, and be sent back. It does not
do that. It makes a change that leaves the suite green and still fails the
hidden test — an ineffective fix rather than a harmful one. The trap was built
for a failure mode that was imagined rather than observed.

That is the fifth time a suite written here encoded an assumption instead of
testing one, and it is the argument for the rest of this entry.

## Real bugs without Docker

The SWE-bench harness needs Docker, which this machine does not have. But the
harness is not the valuable part. **The construction is**, and it needs only a
git repository, a commit that changes source and tests together, and a test
runner.

`click` turned out to be an ideal subject: 3,362 commits of real history, no
dependencies at all, and a suite of 1,982 tests that runs in 6.9 seconds with
nothing installed beyond `PYTHONPATH=src`.

`eval/mine.py` implements SWE-bench's validation directly:

1. check out the parent, which is the code the agent will be given
2. write in only the test files as the fix commit left them
3. run those tests; the ones that fail are the fail-to-pass set, and a commit
   with none is discarded because nothing about it can be verified
4. check out the fix and run the same tests; they must now pass
5. run the existing suite at the parent; it must be green, or the agent starts
   from a broken repository and a green run proves nothing

Of the last 25 commits, 10 changed source and tests together and **3 survived
all five checks**:

```
click-fc518e41  Fix race condition on KeyboardInterrupt arriving in Command.main()
click-f58ca3e8  Fix copy, deepcopy and pickle of Sentinel members
click-bc32a92c  Refactor pager stream handling; drop text/binary branching
```

The bug report is the commit message as its author wrote it. The hidden tests
are the ones that commit added. Nothing in the task was written by this project.

End to end on the first of them: the repository materialises at the base commit,
the agent gets the real report, then the fix commit's tests are written in and
its three node ids run. Resolved, 164 seconds, $0.24 — slower and dearer than a
toy task, and worth it.

## Where that leaves the plan

The instrument no longer depends on an install this machine cannot do, and no
longer depends on my imagination about how agents fail. Mining more instances is
now a matter of CPU time rather than of invention, and a second repository can be
added by pointing the miner at it.

> **The 252 figure was withdrawn on 2026-09-12** as audit finding E6: it divided discordant pairs by the within-arm flip rate, which does not bound them. Left here as written, because this is what was believed at the time. See [20-reconstructible.md](20-reconstructible.md).
