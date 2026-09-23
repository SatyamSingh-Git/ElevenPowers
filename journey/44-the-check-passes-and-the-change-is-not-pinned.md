# 44 — The check passes, and the change is not pinned

*2026-09-24. Twenty-two minutes, no money, and the question behind the whole
project gets its first measured answer.*

The question, as it was asked: *the agent runs pytest, and this system watches
pytest. If the agent can always make pytest green, what is the system for? Was
it not meant to improve the logic, the edge cases, the bugs?*

Entry 43 ended with the plan answering half of it. `core/stress.py` does not ask
whether pytest passed; it asks whether the test would have passed **before** the
change. A test green on both trees is `VACUOUS`, so an agent cannot clear the bar
with any passing test — only with one that was red on the old code.

The other half was the important half, and it was still an argument: **one**
such test clears the bar. PLAN §5.16 proposed mutants confined to the changed
lines as the answer, and — because this project has been wrong every time it
argued instead of measuring — gated it on a free run with the outcomes decided in
advance. Near-zero survival would withdraw the section outright.

---

## The probe that measured its own blind spot first

The first task came back with **zero mutation sites**. Not zero survivors — zero
places to put a mutant.

Its whole fix was one line:

```python
annot = getattr(annot, "__forward_arg__", annot)
```

An assignment of a call. The operator set had comparisons, booleans, arithmetic,
constants and returns, and not one of them applies. One-line fixes are the common
case. An operator set that cannot touch them measures the operator set.

So statement deletion went in — the finest-grained form of `stress.py`'s own
reversion — and string mutation beside it. Both mutants on that line were then
**killed**: the maintainer's test pins that fix completely.

## Three traps, built in before the first real run

Every one of them learned in the previous five days:

- **The declared environment is applied.** Without `PYTHONPATH=src` the suite
  imports the installed release, nothing runs against the mutant, and every
  mutant survives — the exact failure that corrupted two published figures two
  days earlier.
- **Node ids go in an argument list, never through a shell.** `[<lambda>0]`
  killed a shell command outright on 2026-09-22.
- **A baseline comes first.** A test already failing on the patched tree would
  make every mutant look killed, so those are deselected and only a *new*
  failure counts.

## And the probe was made to flip, on every task

Two controls per task, before any mutant:

- **Revert the gold patch.** That is `stress.py`'s own mutant. The tests the fix
  made pass must now fail — if they do not, the suite is not reading this
  source, and every "survived" below would be an artifact.
- **Add a harmless no-op.** It must survive. If it is killed, the suite is flaky
  or the harness over-reports.

**Both controls passed on all sixteen tasks.**

---

## What came back

```
attrs      1 survived of 35
click     19 survived of 47
itsdangerous 2 of 8
jinja2     5 of 8
```

**27 of 98 mutants survived, on 9 of 16 tasks.** Outcome one — near zero —
does not apply. §5.16 is not withdrawn.

But the number is the less interesting half. Read the first control again:
reverting the gold patch was **killed on all sixteen tasks.** That is precisely
the mutant the discrimination check runs. So `stress.py` would report
`DISCRIMINATES` on every one of these sixteen — every one of them would look
properly evidenced — while **nine of the sixteen carry changed lines their own
tests do not notice**.

That is the question that started this, answered with data rather than with an
argument:

> **The check passing and the change being pinned are different facts, and on
> this corpus they disagree more often than they agree.**

## Were the survivors real?

Every one of the 27 was read. Three were clearly equivalent — nothing they
changed could alter behaviour:

```
sys.version_info[:2] >= (3, 11)   ->   sys.version_info[:3] >= (3, 11)
```

— the same answer on every real Python. Three were uncertain. One was real but
trivial. **Twenty were real, unpinned behaviour** — in the maintainers' own
code, under the maintainers' own tests:

```
ctx.exit()                              ->  pass
```

after printing `--version`, so the command carries on running.

```
len(lines) + 1 < self.max_lines         ->  len(lines) + 2 < self.max_lines
```

A boundary moved by one. That is the literal form of *"is it tested on the edge
case"*, and the answer is no.

And `jinja2-065334d1`, where **five of seven** mutants survived: the new
branch's condition negated, deleted, its return replaced, its return deleted.
The maintainer's test exercises the fix without ever entering the branch the fix
adds.

## Why "provisionally", and not "earned"

The gate said *survivors a reviewer agrees are real gaps*. The reviewer here is
the one who designed the probe, and the bias runs in exactly one direction — the
mechanism looking useful. That is not a reviewer the gate meant.

So §5.16 **provisionally passes**, and the next thing in the queue is not more
mutants. It is somebody who did not build this, shown each of the 27 diffs
without the verdicts, saying which are real.

## The finding that was not being looked for

**attrs: 1 of 35. click: 19 of 47.**

Whatever this measures, it is at least as much a property of a project's testing
culture as of any single change. A reviewer-facing report that says *"these
three lines are unpinned"* means something different in a repository where that
is unusual than in one where it is normal — and the report would have to say
which kind it is looking at.

## What it does not say

It says nothing about agents. The **gold patch** was applied, so these are gaps
the maintainer left; an agent's own tests are the untested case, and the
expectation that they pin *less* is an expectation. It is not a rate — eight
mutants per task, sampled. And a surviving mutant is not a bug: it is a line the
tests would not notice changing. Whether the line is *right* is a question
nothing here answers, and §1.6 says so.

---

Twenty-two minutes. It turned the most important open question in the plan from
an argument into a measurement, and the measurement came back on the side of the
person who asked it.

`results/b7-mutants/` — findings, raw per-mutant diffs, and the probe, labelled
as a spike rather than product code, so the number can be reproduced.
