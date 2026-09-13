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

**Every saved patch was damaged on the way to disk.** `write_text` translates a newline
to the platform separator, so every `patch.diff` in every bundle held CRLF
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

## The run

Ninety runs, two passes of fifteen tasks at three replicates, `claude-sonnet-5`
at `--effort high`, from 03:05 to 06:56. **$67.42**, three hours thirty-seven of
agent time, against the $20-40 this phase had written down before it had
measured anything.

**Nothing broke.** Zero setup failures, zero timeouts, zero host errors, no
model mismatch, in ninety paid runs.

```
pass A   68.9%   [46.7%, 88.9%]
pass B   53.3%   [33.3%, 73.3%]

Each score falls inside the other's interval: the rerun reproduces.
```

Phase B's exit is met on its own terms. What follows is why those terms are
weaker than they look.

### An agent uninstalled a package from under the next task

Four hours after the sweep finished, a committed bundle was re-graded from a
fresh clone as a check that the archive works at all. It came back with a
different answer, and that was the thread.

An agent working an attrs task in pass B ran `pip install -e .` inside its temp
workspace. The system site-packages is not writable, so pip wrote into the
**shared user site** instead: a `.pth` pointing `attrs` at
`.../Temp/tmpiwikiyyk/src`, and an `attrs-0.1.dev1.dist-info` on top of the
real distribution's metadata. The file is timestamped 05:22:59, which is
twenty-six minutes into pass B.

The workspace was deleted when that run ended. From then on `import attrs`
failed machine-wide, and jinja2's `tests/test_async.py` imports `trio`, which
imports `attrs`. **Every jinja2 run for the rest of the night collected zero
nodes**, and every one of them was recorded as the agent having failed to fix
the bug.

The same metadata corruption broke
`tests/test_packaging.py::TestLegacyMetadataHack::test_version_info`, which
reads attrs' own installed version — so two runs were recorded as `regressed`
for a version string another agent had overwritten.

**A run's grade depended on what a different run had done to the machine.** That
is D55 for the third time in one night, in a way no amount of care inside the
grader would have caught, because nothing inside the grader was wrong.

It had been happening for days. A second dangling pointer, `click.pth`, is dated
three days earlier and had left `import click` broken machine-wide that whole
time. It never showed up because click's own tasks put `src` on `PYTHONPATH`
ahead of site-packages, so the one repository that could have noticed was the
one immune to it. Both were repaired; neither was ever reported by anything.

### What the bundles were for

Every candidate is preserved as a patch against a recorded base precisely so
that a grade can be taken again when the grader, or the machine, turns out to
have been wrong. This is the first time that has been needed, and it was needed
within four hours.

`attrs` was reinstalled and all ninety bundles re-graded from disk, free:

| | grades changed |
|---|---|
| pass A | **0 of 45** |
| pass B | 9 of 45 |

Pass A not moving at all is the control. It says the re-grade is deterministic,
that the bundles round-trip, and that the contamination is confined to what came
after 05:22.

### The corpus was mined on the same contaminated machine

Repairing `click` broke four tasks, and that is the useful part.

`tests/test_deprecations.py::test_attr_deprecated` parametrises on
`importlib.metadata.version("click")`, so the version string ends up **inside
the node id**. The corpus pinned it as
`test_attr_deprecated[click-__version__-8.4.2.dev0]`, in the preservation set of
all four click tasks.

`8.4.2.dev0` is not click's version at any of those commits — `git describe`
there says `8.5.0`. It is what setuptools-scm falls back to when it is run
inside a tree with no git history, which is exactly what an agent's `pip install
-e .` saw in a workspace built by `git archive`. **The number was invented by
the contamination and then pinned into the benchmark.**

So with click correctly installed, that node is never collected, a preserved
test appears to have vanished, and the gold patch itself grades `regressed`.
`eval.validate --corpus` reports 4 of 15 WRONG, which is the honest answer: this
machine can no longer grade those four tasks.

Nothing was invented to make it pass again. Recreating `8.4.2.dev0` would mean
reproducing a stray install on purpose so a benchmark keeps agreeing with it.

Two ways out, and the choice is not the harness's to make quietly:

- **drop the node** from those four preservation sets. Correct, cheap, and it
  changes the corpus fingerprint, so tonight's numbers stop being comparable to
  anything measured after it.
- **leave it and re-mine later**, with mining taught to reject any node whose id
  is not stable across two collections in different environments — which is the
  general form of the defect and would have caught it at B1.

Either way the lesson is fixed: **a pinned identifier that contains a value from
the machine is not pinned.** It is the corpus version of the same sentence this
night has now written three times.

### What the night actually measured

| | as recorded | corrected |
|---|---|---|
| pass A | 68.9% [46.7, 88.9] | **68.9%** [46.7, 88.9] |
| pass B | 53.3% [33.3, 73.3] | **73.3%** [55.6, 88.9] |
| gap | 15.6 points | **4.4 points** |
| `regressed` runs | 2 | **0** |

Over six replicates: **nine tasks solved every time, one never, five split.**

That is a better reproduction than the contaminated numbers showed and a worse
benchmark. Nine of fifteen tasks cannot demonstrate an improvement, because a
plain agent already solves them every time, and one is never solved at all.
**Five tasks carry the entire ability of this corpus to detect an effect.**

### Everything this entry claimed four hours ago and got wrong

Written up at 07:00 from the numbers as recorded, committed, and reported:

- *"`regressed` caught a real agent breaking something else — the first time the
  preservation set has done that on somebody else's code."* **Withdrawn.** Both
  cases were the corrupted attrs metadata. That category has still never been
  seen in the wild.
- *"`jinja2-66587ce9` and `jinja2-ee832194` were solved 3/3 in pass A and 0/3 in
  pass B — the agent failed to fix a bug it had solved an hour earlier."*
  **Withdrawn.** Both are 3/3 and 3/3. Nothing ran.
- *"Replicates inside one sitting are more correlated with each other than two
  sittings are."* **Withdrawn as stated.** It was inferred entirely from the
  reversal that did not happen. Five tasks split rather than seven, and the two
  passes agree to within 4.4 points.

The pattern is the one this project keeps writing down: **a story told from a
number without opening the evidence underneath it.** A null was once diagnosed
from an agent's own test without reading the answer key. Here a failure
taxonomy, an interval and a reproduction were all computed correctly from grades
that were wrong, and the reasoning on top of them was careful, specific, and
about nothing.

What found it was not more care. It was running the archive against itself.

## Four states, not a pass mark

| claim | state |
|---|---|
| the harness survives ninety unattended paid runs | **verified** — nothing broke, nothing needed a human |
| the grade is a function of the base and the patch | **contradicted twice in one night** — first by the grader's git config, then by what another agent installed on the machine |
| a rerun reproduces | **verified, weakly** — 68.9 and 73.3, and the criterion is met mostly because a 42-point interval is hard to miss |
| a grade survives being taken again from the bundle | **verified** — pass A moved on none of its 45; pass B on 9, every one of them the contamination |
| the taxonomy describes real runs | **verified for three of ten categories**; `regressed` is not one of them, and seven have still never been seen |
| P1, the hypothesis | **unverified**, and not addressed by this run at all — one arm was measured, not two |

The last line is the one to keep. This phase built an instrument and pointed it
at a baseline. It did not test the idea the project exists to test.

## What the night actually cost, and what it bought

$67.42 and about four hours, against a $20-40 envelope written before anything
had been measured. Roughly a dollar of that went on the two runs that found the
line-ending defect, which is the cheapest thing that happened.

The defect is what makes the rest of it worth the money. Ninety runs of clean
data are worth having; ninety runs that silently filed every solved attrs task
under "harness breakage" would have been worth less than nothing, because they
would have carried a pinned corpus, a pinned model, an interval and a
reproduction, and been wrong.

**The verification that was supposed to prevent that looked exactly like
success.** That is the part to remember the next time something is declared
ready.
