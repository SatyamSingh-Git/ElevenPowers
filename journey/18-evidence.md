# 18. Repairing the foundation, and the defect underneath the one that was reported

## The part that was supposed to be solid

The evaluator defects in [17-preservation.md](17-preservation.md) were
embarrassing but peripheral: they made measurements wrong, not the tool wrong.
The evidence layer is different. It is what this project claims to have built —
completion computed from dependency-tracked evidence rather than asserted — and
the audit reproduced **nine soundness defects in it**.

Six are now closed, one partly. What follows is what each actually was,
because in every case the one-line description understates it.

## R1: a status names files, not contents

`tree_hash` is size and modification time, which is fast and cannot tell a
rewrite from a no-op. So `vcs_state` was the tie-breaker: ask git, which
compares content, whether anything really changed.

Except it asked with `git status --porcelain`, which answers *which files
differ from HEAD*, not *how*. Two different edits to one already-modified file
produce the same line. So:

```
edit a file once   ->  " M src/app.py"
edit it again      ->  " M src/app.py"
```

Identical fingerprint, mtime moved, verdict **fresh**. Evidence recorded
against the first content survived the second. That is not a corner case — an
agent edits the same file repeatedly, all day, and after the first edit every
later one was free.

It now folds in `git diff HEAD` for tracked content and reads untracked files
directly. Untracked matters more than it sounds: a test file the agent wrote a
minute ago is untracked, and it is exactly what changes next.

## R1, again: the audit named the symptom

The tie-breaker fix above is real and it did not close R1.

A test I wrote for R2 — edit a lock file, expect the suite result to go stale —
passed on its own and failed in the full suite. Chasing that flake rather than
re-running it:

```
same size:            300/300
size AND mtime equal: 220/300   <- the edit is invisible to stat
```

Both versions of the lock file are the same length, and on this filesystem a
rewrite lands inside the timestamp's resolution about three times in four. So
`tree_hash` — size and modification time — **could not see the edit at all.**

Worse, `freshness` returns fresh on a `tree_hash` match *before* it ever
consults `vcs_state`:

```python
if tree_hash(root, current) == self.tree:
    return Freshness.FRESH
```

The tie-breaker is never reached. Fixing it, which is what the audit's R1
described, could not have closed the case it described.

The original docstring argued the trade openly and got the direction wrong:

> The trade is that a file rewritten with identical bytes changes its
> modification time and so reads as stale. That costs one redundant re-run and
> is self-correcting.

It reasoned about the harmless error — falsely stale — and never about the
harmful one. A rewrite that keeps the length is falsely **fresh**, and that is
not self-correcting. It is the failure the whole project exists to prevent,
sitting in the function the whole project rests on, with a comment explaining
why it was acceptable.

`tree_hash` now hashes content, with stat as a cache key rather than as the
answer, and re-reads any file touched in the last two seconds whatever the
cache says — the window where stat cannot resolve an edit is exactly where an
agent's edits land. Git calls that racily-clean and does it for the same reason.

Measured before choosing: 6ms to hash 59 files against 1ms to stat them. The
cache matters because a status check hashes the tree once per evidence record,
and an uncached pass on a large repository would run into the host's
twenty-second hook timeout rather than merely being slow.

**And the tie-breaker is now dead code, so it is gone.** It existed only to
compensate for a fingerprint that could not tell identical bytes from a
rewrite. Hash the bytes and there is nothing left for it to do.

## R2: a list cannot contain what did not exist

`observed` is a stored list of paths, captured when the command ran. Freshness
hashed that list. A file created afterwards is not in it, and a stat signature
over a fixed list cannot notice an addition.

**Adding a new failing test staled nothing at all.** The suite result recorded
before it still read fresh.

Records produced by scanning the tree now record that they were a scan, and
freshness re-derives the set. And dependency manifests and lock files joined
the observed set, because a dependency upgrade changes behaviour exactly as an
edit does, and `.lock`, `.txt` and `.mod` say nothing by suffix.

**This one is marked `part`, not `fixed.`** Its row also says environment and
dependency changes are not fingerprinted at all, and a package installed
without touching a manifest is still invisible. Nothing fingerprints the
interpreter the command actually ran in. Marking the row closed would have
claimed more than the change delivers.

## R3: gone is not stale, and only stale was rejected

Freshness has three values. The verdict logic checked for one:

```python
elif any(c.freshness is Freshness.STALE for c in checks):
```

Delete a file the evidence observed and it returns `GONE`, which is not
`STALE`, so the claim stayed **verified** — on a test result whose files no
longer existed. The strongest possible form of out of date read as no problem
at all, because it was too far out of date to match the one case being checked.

## R4: which record speaks for an identity

Two defects wearing one number.

`satisfied_by` filtered to the passing records and took the last of those. With
a fail → pass → fail history it returned the middle one. The newest failure was
separately written off by `_contradictions`, which excuses an identity whose
first observation failed as pre-existing breakage. Between them, **a currently
red suite verified.**

The newest record for an identity now speaks for it, and a single target that
is red right now withholds the obligation rather than being outvoted by an
older pass somewhere else.

The second half was `_no_new_failures`, the concession for repositories that
are red on their main branch. It compared failure *counts*. One test stops
failing, a different one starts, the count holds at one, and the suite is
declared no worse — having regressed. It now compares which tests failed, using
the per-test records that share the timestamp of the run that produced them.

Where the runner reported no per-test detail there is nothing to compare, and
**the concession is now refused rather than granted on a number that cannot
support it.** That is a deliberate loss of leniency. A stable count is not
evidence of preserved behaviour, and pretending otherwise is the same move as
grading a patch on the tests it chose to run.

## R5: four facts that had become one

`echo pytest` produced a passing suite record. So did `pytest --version`.

The chain was: the command text contains a runner's name, so parse it as a test
run; the process exited zero, so the run passed. Nothing in between asked
whether a test had executed. Four separate facts — **the command was
recognised, the process finished, tests ran, the required ones passed** — had
collapsed into one.

A suite record now reports whether it counted any test at all, and one that
counted none cannot satisfy an obligation that a suite passes.

## R6 and R8 are one fix

R6: `_test_written_and_suite_green` searched `touched ∪ seen`, and `seen`
includes files the agent merely **read**. Reading an existing test and running
a green suite satisfied *a test covering the change passes* — with a caveat
that said a test had been written.

That rule was added in M1 to cut false blocking from 75 percent of runs to 12.
It worked partly by being wrong.

The fix is to drop `seen`. Which is useless on its own, because of **R8**:
`observe_edit` returned early whenever a claim was already open, so `touched`
was only ever populated by the edit that opened the claim. Every later edit was
invisible — including risk, which is why a task that began on a README and then
reached into `src/auth/` kept the risk the README earned it.

Fixing R6 without R8 would have deleted the concession rather than narrowing
it. They had to land together.

## The controls, which are the actual work

Every one of these fixes can be faked by making the rule never fire. A gate
that refuses everything passes every test that asserts something is not
verified.

So each came with a control asserting the opposite:

| | |
|---|---|
| R4 | a fail → pass history still verifies |
| R5 | a suite that really ran still satisfies; zero tests is the disqualifier, not the runner's name |
| R6 | an agent that **did** write the test still gets the concession, caveat and all |

The R6 control is the one that matters. Without it, "R6 fixed" and "M1 reverted"
look identical from the outside, and the difference is the 63 percentage points
of live blocking that M1 bought.

## Three probes could not see their own fix

This is the finding worth keeping.

**R1's probe pinned `vcs_state` to a constant** — I had written that pin myself,
to work around a platform flake. It stubbed out the exact function the fix
changed, and in doing so quietly changed what the test demanded: not *correct
the tie-breaker* but *remove it*. The fix landed and the test could not see it.

**R2's probe built its evidence record by hand**, so it proved nothing about
what a real suite run records. The production path could have gone on storing a
list that never grows.

**R4's second probe asserted against a `detail` string**, a three-line tail of
output, rather than against the per-test records that actually name failures.

All three now run through the parser against real git, and all three were
checked against a worktree at the previous commit: **they fail there and pass
here.** That check is the only thing that distinguishes a test that captured a
defect from a test that merely looks like it did.

Added to [17-preservation.md](17-preservation.md)'s rule about E2 — a strict
xfail that can never xpass is a defect recorded as permanently unfixed — that
makes two ways a probe can be worthless while looking diligent, found in one
afternoon, in a file built specifically to prevent defects being forgotten.

**The file was the right idea and it was not self-validating.** Sixteen probes
written in an afternoon, four of which could not do their job. The reproduction
script they came from had the same weakness and nobody noticed, because a probe
that fails against a defect looks correct, and there is no way to tell it from
one that fails for its own reasons until you fix the defect and watch.

## What the audit could not have told me

The largest defect found today was not in the audit.

R1 as reported is a bad tie-breaker, and it is a real bug, and fixing it changes
nothing about the case that made it famous — because the tie-breaker sits behind
a check that returns first. The actual defect is that the fingerprint underneath
everything could not see a same-length edit, three times in four.

An external audit is authoritative about what it examined. This journey already
wrote that sentence once, in [16-audit.md](16-audit.md), about the audit being
silent on discipline it had no reason to discuss. Here it holds in a sharper
form: **the audit reported the symptom it could reproduce, and the disease was
one layer down.** Fixing exactly what was reported, marking the row closed, and
moving on is a completely defensible way to have left the headline promise of
this project broken.

It surfaced because a test I had written half an hour earlier flaked, and
because chasing a flake beats re-running it. That is the whole method, and it is
the fourth time in this journey it has been the thing that worked.
