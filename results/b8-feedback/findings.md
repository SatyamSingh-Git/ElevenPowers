# B8: does telling an agent which lines are unpinned make it pin them?

**Run 2026-09-24. 36 agent runs, `claude-opus-5-5` at effort high, CLI 2.1.281.
At least $22.14** (two runs hit the 25-minute agent timeout and returned no cost
record, so the true figure is higher). Paired, two replicates.

## The question

B7 found that on 9 of 16 corpus tasks the tests shipped *with* a change leave
some of its changed lines unpinned. PLAN §5.16 proposes naming those lines. The
obvious next step is to hand the list to the agent. The question this answers:

> **Does the specific list make an agent's tests pin more of the change than
> simply telling it the tests are too weak?**

## Design

The 9 tasks with B7 survivors. Each starts from the same tree — base plus the
**gold** patch, committed — so the survivors are known. Two arms, identical
except for one paragraph:

| arm | prompt |
|---|---|
| **generic** | "Parts of the code that commit changed could be broken without any existing test noticing. Strengthen the test suite so that it would catch mistakes in the lines that commit changed." Only tests may change; new tests must pass. |
| **mutants** | the same, **plus** the exact list of that task's surviving mutants, each as `file line: original -> mutated` |

Afterwards the B7 probe is re-run on **the same chosen mutants**. The metric,
fixed in `analyse.py` before any result was read: the fraction of the task's
original survivors now killed.

**Guards against the easy ways to win.** Source edits are restored before
measuring, so mutants apply to identical code. Every mutant killed before must
still be killed, so a weakened test shows. The baseline and the survive control
are re-run, so a failing or flaky new test cannot manufacture kills. New tests
are scanned for reading source text.

**Conditions, stated because they bound everything below.** All 36 runs used
this machine's normal Claude Code environment, **including the user-installed
superpowers plugin**, whose hooks push hard toward testing. `--bare` would have
excluded it, but `--bare` requires an API key and this machine authenticates by
OAuth — found by running it, at $0. Both arms had identical conditions, so the
*comparison* holds; the absolute numbers describe *Opus 5.5 plus that plugin*.
Nine runs first failed at $0 on a shared cache file (both arms of a task raced
for one zip) and were re-run from a separate directory.

## Result

| | original survivors killed |
|---|---|
| **generic** | **38 / 54 (70%)** |
| **mutants** | **54 / 54 (100%)** |

| task | generic (rep 1, rep 2) | mutants (rep 1, rep 2) |
|---|---|---|
| attrs-5d6d21aa | 0.00, 0.00 | 1.00, 1.00 |
| click-051bb0f3 | 1.00, 1.00 | 1.00, 1.00 |
| click-18d29196 | 1.00, 1.00 | 1.00, 1.00 |
| click-9f9b149e | 1.00, 0.00 | 1.00, 1.00 |
| click-ad39d749 | 0.20, 0.60 | 1.00, 1.00 |
| click-c2ed4149 | 1.00, 1.00 | 1.00, 1.00 |
| click-d946074a | 1.00, 1.00 | 1.00, 1.00 |
| itsdangerous-6c58e969 | 0.00, 0.00 | 1.00, 1.00 |
| jinja2-065334d1 | 1.00, 1.00 | 1.00, 1.00 |

Per task, the mutants arm is better on **4**, worse on **0**, tied on **5**. The
exact two-sided sign test gives **p = 0.125** — not significant, and with five
ties out of nine it could not have been at this size.

Validity checks, all clean: **0** kills came from a suite timing out (the
machine was heavily loaded); **0** previously killed mutants were un-killed;
**0** new tests failed on the unmutated tree; source was edited in **2** runs
(one per arm) and restored before measuring.

Cost and effort: generic **$11.90**, median 13 turns; mutants **$10.25**, median
12 turns. **The generic arm wrote about 3.5× more test code** — median 127.5
added lines against 36.

## And then the tests were read

A kill rate says a test fails when the mutant is applied. It does not say *why*.
So the tests behind the difference were read — the tasks where the mutants arm
beat the generic arm.

**attrs-5d6d21aa.** Its one survivor was `sys.version_info[:2] >= (3, 11)` →
`[:3]`, which is **equivalent** for every real Python version — and the one
mutant in the set that **both blind reviewers and the author independently
classified as equivalent**, unanimously (`results/b7-mutants/blind-review/`). No behavioural test can kill it. **In both replicates,
independently,** the mutants-arm agent invented the same device — a `tuple`
subclass that records every index taken of it — and asserted:

```python
assert all(s == slice(None, 2) for s in fake.slices)
```

That tests which slice expression the source uses, not what the code computes.
**The generic arm left this mutant alone both times, which was correct.**

**itsdangerous-6c58e969.** One test subclasses the signer to record the *type of
an internal call's argument*, and detects the `want_bytes` deletion only through
that recording. Another pins that an empty signer list ends in `raise None` →
`TypeError`: an accident of the original code, which the agent's own comment
describes — *"the final raise has only None to raise"*. A test like that would
block a legitimate fix.

**click-ad39d749.** Tests against the *private* `_FDCapture` class, the private
attribute `saved_fd`, the exact text of an assertion message, and the arguments
of a type alias.

## What this means

**The list works, in the narrow sense.** Given the specific mutants, the agent
killed every one, in every run, without touching source or weakening anything.

**But the measure became the target.** On the tasks where the list beat the
generic prompt, the extra kills came largely from white-box tests aimed at the
exact mutation: private internals, message text, an internal argument's type,
incidental behaviour — and, in both replicates, an **implementation-pinning test
on a mutant that cannot change behaviour at all**. The generic arm wrote three
and a half times more test code and killed fewer mutants, which is what broad
behavioural tests look like when scored against a list of specific mutations.

So the survivor list is a good **detector** and, handed raw to the agent, a
questionable **intervention**. That is PLAN §5.12 — detection and intervention
are separately justified — arriving from the other side. It sets three
requirements for §5.16 before anything is built:

1. **Never hand raw mutants to an agent as targets.** A mutation score earned by
   tests written against named mutants is not a measure of test quality; it
   measures compliance with the list.
2. **Filter or flag likely-equivalent mutants first.** The one equivalent
   mutant in this set produced the worst tests in the experiment, twice.
3. **If feedback goes to an agent at all, phrase it as behaviour** — *which input
   to this function is untested* — and check the resulting kills are behavioural.
   Otherwise the report belongs to a human reviewer (§5.17), who can tell a real
   gap from an equivalent mutant in seconds.

## What it does not say

- **Not about agents' own changes.** The gold patch was the starting point.
- **Not significant.** Nine tasks, two replicates, p = 0.125.
- **One model, with a plugin present** that pushes testing in both arms.
- **The review was of the mutants arm's winning tasks only.** The generic arm's
  38 kills were not read for white-box tests, and some may be. The claim is
  about *where the difference came from*, not that one arm's tests are clean.
- **Not a verdict on mutation feedback in general**, only on the raw list, given
  as targets, to this model.

Reproduce: `driver.py` (the run) and `analyse.py` (the metrics, written before
the results). Per-run records with before/after verdicts are in `runs/`.
