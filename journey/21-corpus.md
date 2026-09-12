# 21. A corpus from five repositories, and the silence that nearly hid it

## Why several repositories

Phase B asks for a baseline "over several repositories and difficulty
categories". The reason is narrow and this project has paid for it twice:
hand-written suites agreed with the assumptions of the code they graded, and the
mined suite came from **one** repository, so one project's testing habits decided
what a task looked like.

Five is not many. It is the difference between a property of the corpus and a
property of one codebase.

## Two of five contributed, and nothing said why

The first run mined `click` and `markupsafe` and reported nothing at all about
`attrs`, `jinja2` and `itsdangerous`. They appeared in the output as a count of
candidate commits, and then silence.

Diagnosing by hand: `attrs` needs `hypothesis`, `jinja2` needs `trio`,
`itsdangerous` needs `freezegun`. All three were **environment problems wearing
the shape of an empty result** — indistinguishable, from the output, from a
repository whose recent history simply held no suitable bug fixes.

`validate` returned a bare `None` for six different reasons: no parent commit,
the commit's test files are not in its tree, the suite is already red at the
parent, the new tests already pass before the fix, the fix does not satisfy its
own tests, and nothing to preserve.

It now returns the reason with the result, the caller tallies them, and a
repository that contributes nothing says so and names the most common cause.
That is Phase B's exit criterion — *separate setup problems from coding
failures* — showing up one layer earlier than expected, at corpus level rather
than at run level.

## The reason was right by luck

`_why_red` reported `itsdangerous` as a setup problem "fixable by installing
it", and could not say what to install.

`run_tests` passes `--tb=no`, because the callers that parse node ids do not want
tracebacks. With tracebacks suppressed, a collection failure prints

```
2 errors during collection
```

and discards the only actionable line in it: `No module named 'freezegun'`. The
guess was correct and unsupported, which is the same shape as a docstring
claiming to record the resolved model while the code recorded an alias.

`run_tests` now takes a `traceback` argument. The one caller that wants a
*reason* asks for `--tb=line`; the ones parsing node ids still get none. And the
note says "which is installable" only when a dependency was actually named,
rather than for anything beginning with `setup:`.

With the three packages installed, all five repositories contribute: **15
instances, about 16,600 preserved tests.**

## Difficulty as a label, never a filter

Audit finding **E6** was that this project selected its benchmark around the
mechanism it was measuring: keep a task only if the naive fix breaks the visible
suite. A corpus containing only tasks the gate can win is not evidence about the
gate.

So each instance records `gold_lines` — how many lines of **source** the
maintainer changed, tests excluded, because the test files are the answer key
and counting them would make a task look large when its author simply wrote
thorough tests. Three bands:

| band | tasks | |
|---|---|---|
| one-liner | 2 | one to three lines |
| small | 8 | four to twenty |
| substantial | 5 | more than twenty |

Nothing is dropped for being easy or hard. The bands exist so that a gain
concentrated in one of them cannot hide inside an average.

## Pinning, which turned out to be the real work

A built corpus is 1.78 MB of test bodies and preservation sets — too large for
git, and rebuilding it is not the obvious fallback. Scanning "the last 150
commits" of five repositories gives a different answer every week as those
repositories gain commits. **A rerun would score a different benchmark and call
it the same one**, which is exactly what Phase B's exit forbids.

`corpus.lock` is 3.8 KB: origin, base commit, fix commit and test files per
instance. `--rebuild` reconstructs from those and nothing else.

It **refuses** when a pin is unreachable. That is the whole point — a rebuild
that quietly mined a nearby commit would produce a corpus that looks like the
original and scores differently, which is worse than not rebuilding at all. The
test for it is the adversarial one: an unreachable sha must come back missing,
and the output file must be empty rather than plausible.

Verified rather than asserted:

```
same names: True
base, fix, f2p, p2p, hidden_files, gold_lines, gold_files, prompt: identical
```

Fifteen of fifteen, including click's 1,871-node preservation set.

## What B1 leaves

A corpus that is somebody else's code, somebody else's bugs, somebody else's
tests and somebody else's words, from five projects rather than one, labelled by
a measured property rather than filtered by the mechanism under test, and pinned
so that the next run and the Linux worker grade the same thing.

What it does not have is a baseline. Nothing has been run against it yet, and
the number that matters — how often a strong host configuration resolves these —
belongs to B4, after the harness and the taxonomy exist to record it properly.
