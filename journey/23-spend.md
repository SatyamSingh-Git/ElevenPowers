# 23. The night the instrument was allowed to cost something

Everything before this was free. B4 is the first step that spends real money on
a real model, and it came with a constraint that changed how it had to be
prepared: **one run, no second attempt.** A defect found at run eighty is not a
bug report, it is the whole night.

So the question was not "does the harness work" — 476 tests said it did. The
question was "what is true of a ninety-run unattended sweep that is not true of
a unit test", and that turned out to be a different list.

## Four things the tests could not have found

None of these were wrong code. Each was a thing the harness did not do, and a
missing thing has no test to fail.

**`--effort` never reached the process.** The flag was parsed, printed in the
banner, carried through the report — and never added to the command line. The
run would have been made at the default effort and filed under `high`, and the
only witness would have been the bill.

This is **E4 in a different costume**. E4 was an arm named for a plugin whose
directory was unset: labelled present, running absent, reported as a result. A
year of lessons about that exact shape, and it reappeared one field over, in
code written the same afternoon the lesson was reread. The fix is not the two
lines that send the flag. It is that a label is now checked against the bundle
rather than trusted, and the check **stops the sweep** instead of printing a
warning nobody is awake to read.

**Results existed only in memory.** Ninety runs, written once at the end. A
crash at run eighty-nine loses eighty-nine paid runs and reports nothing. Now
every run is appended to a journal the moment it finishes, and a restart counts
what is on disk and skips it — per replicate, not per task, because a task that
died between its second and third run is owed one more, not none.

**Nothing capped a single run.** An agent that loops on a hard task has no
natural stopping point, and the five substantial tasks in this corpus are
exactly where that would happen. `--max-budget-usd` is now wired per run.

**The corpus lived in a temp directory.** `EP_MINED` was unset, so the sweep
would have loaded zero tasks and exited in under a second — the cheapest of the
four failures and the only one that announces itself. The mined corpus and the
bundles now live outside the session scratchpad, because a sweep that outlives
the thing holding its inputs is not an overnight run.

## The grader, asked five questions on a real task

`eval.validate` grades four patches with known answers, but on fixtures. Before
spending, the same thing was done to a real corpus instance — markupsafe, with
its own maintainers' tests — by taking the agent's actual accepted patch and
damaging it five ways:

| what was done | grade | what was seen |
|---|---|---|
| the real patch | `resolved` | 36 of 36 nodes |
| nothing at all | `unfixed` | 35 nodes, the asked-for one failing |
| the module broken outright | `unfixed` | 0 nodes — collection died |
| a function the f2p test uses, broken | `unfixed` | the ask fails, and that wins |
| `soft_str`, which the ask does not use, broken | **`regressed`** | named `test_soft_str[markupsafe._native]` |

The last row is the one that mattered. Every earlier version of this project
would have called that patch a success: the requested test passes. It is the
distinction the preservation set was built for, and this is the first time it
has been demonstrated on somebody else's code rather than on a fixture written
to demonstrate it.

Five different questions, five different answers. A grader that says `resolved`
to all of them and a grader that says `unfixed` to all of them both pass a test
that only ever asks one.

## What the dry runs cost, and what that predicts badly

Two live runs, `$0.53` together. markupsafe took 59 seconds and `$0.35`; click,
with 1,847 preserved tests, took 25 seconds and `$0.18` — **the largest
repository was the cheapest task**, because cost follows how long the agent
thinks, not how much code is present.

Extrapolated, ninety runs is **$50–70 and about three hours**, against the
$20–40 this phase wrote down before it had measured anything.

That projection should be distrusted in a specific direction. Both samples were
`small`-band tasks that resolved in a handful of turns. The five substantial
tasks — 26 to 120 lines of gold patch — are unmeasured, and they are where both
the time and the money concentrate. The per-run cap is the only thing standing
between an unmeasured tail and an open-ended bill.

## Run one said `setup`, and the dry runs had proved nothing

The sweep launched. The first task, `attrs-f53fc544`, graded `setup` — the
taxonomy's word for *the harness broke, this is not the agent's fault*. The
second replicate did the same. It was stopped there, two runs and about ninety
cents in.

`git apply` had refused the patch, and its complaint printed a `?` at the end of
every context line: a carriage return that was not in the file it was matching
against. Three separate causes, stacked.

**The machine's git config decided the base tree.** `core.autocrlf` is `true`
here, and `git archive` honours it. markupsafe ships no `.gitattributes`, so it
was extracted with CRLF line endings; attrs ships `* text=auto eol=lf`, so it
was not. **The grade was a function of the grader's git configuration** — which
is D55 not merely bent but inverted, in the one module written to enforce it.

**Every saved patch was damaged on the way to disk.** `write_text` translates
`
` to the platform separator, so every `patch.diff` in every bundle held CRLF
that git never emitted — including inside the `--binary` blocks.

**Every patch was damaged again on the way into git.** `subprocess.run(...,
input=patch, text=True)` translates in *that* direction too. A carriage return
was added to every line of every patch the grader ever handed to `git apply`.

### Why two green live runs were worth nothing

`git apply` tolerates the extra carriage returns for some hunks and not others.
markupsafe's tolerated them. click's tolerated them. attrs' did not.

So the pre-flight — two real agent runs on two real repositories, both scoring
correctly, plus a five-way adversarial matrix that gave five different answers —
**passed while the grader was corrupting every patch it was handed.** That is
the strongest evidence this project knows how to produce, and it was evidence of
nothing, because both samples landed on the lucky side of a coin flip nobody
knew was being tossed.

The existing probe was no better. It asserts `read(bundle)["patch"] == patch`
and passed throughout, because `read_text` translates the damage back out again.
**A file written and read by the same library agrees with itself no matter what
it put on disk.**

### What the two runs actually said

Re-graded after the fix, both attrs runs are `resolved`, on 1,405 observed
nodes. The agent had solved the task twice. The grader threw both answers away
and filed them under harness breakage — a category the report excludes from the
agent's score, so the night would have ended with a clean number that silently
omitted every task in every repository without a `.gitattributes`.

### The fix, and the probe that would have caught it

Every git call in the evaluation pipeline now pins `core.autocrlf=false` and
`core.eol=lf`, so a base tree is the repository's own bytes on any machine. A
patch moves as bytes from `git diff` to disk to `git apply`, never through a
text pipe.

The probe asserts **bytes**, not outcome, because an "it applied" test passed
before the fix. Watched failing first, both of them.

With that in place the five-way matrix was rerun against the *maintainer's own
fix* rather than an agent's patch — an answer known before the grader is asked:

| patch | grade | seen |
|---|---|---|
| the maintainer's fix | `resolved` | 36 of 36 |
| nothing at all | `unfixed` | 35 |
| the module broken outright | `unfixed` | 0, collection died |
| `escape()` broken, which the ask uses | `unfixed` | 10 |
| `soft_str()` broken, which it does not | **`regressed`** | names `test_soft_str[markupsafe._native]` |

And on attrs, the repository that exposed all of this: the maintainer's fix
`resolved` at 1,405 nodes, an empty patch `unfixed`, a broken module `unfixed`.

### The check that was missing

A sample of outcomes is not a test of a pipeline, so `eval.validate --corpus`
asks every mined task two questions whose answers are known before it starts:
the maintainer's own fix must come out `resolved`, and an empty patch must come
out `unfixed`. A task failing the first is mined wrong or missing its
environment; a task failing the second has a required test that already passes
at the base commit and is measuring nothing at all. Neither is visible in a
score, and neither was visible in a sample of two.

All fifteen pass, across all five repositories, on observed node counts from 36
to 1,876. It costs nothing but CPU and it was available during the entire six
hours spent preparing to spend money.

`python -m eval.validate` itself had to be fixed to survive this. Its fixture
wrote files with `write_text` and then built patches from the same constants in
LF, so with conversion pinned off the tree and the patch disagreed and three of
its four cases came out `setup`. It had been passing only because the machine's
`autocrlf` was quietly normalising both sides — which means the grader's own
grader would have failed on any machine configured differently.

## What this step still cannot answer

Every failure category remains unit-tested and unseen. The single real check
available before tonight — Phase A's four bundles — classifies all four as
`resolved`, which exercises the happy path and nothing else.

That is the same position Phase A was in before its first live sweep found a
defect in twenty minutes. The difference is only that this time the harness was
made to fail five ways on purpose first.

## The run

<!-- filled in once the sweep completes -->
