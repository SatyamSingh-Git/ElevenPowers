# 41 — Twelve defects, and every probe reproduced

*2026-09-19. An external audit read the tree at `4e9b797`, shipped runnable
probes, and every one of them reproduced here before anything was changed.*

The useful thing about this audit is not that it found twelve implementation
defects. It is that it arrived with a **script**. Fourteen probes, each printing
one line of JSON, runnable against the repository as it stood.

So the first thing done with it was not to read the argument. It was to run the
script and compare the output to the report, line by line. **All fourteen
matched byte-for-byte.** Nothing had to be taken on trust, and nothing was.

That is the difference between a review and a finding, and it is the same
distinction this project makes about its own evidence.

---

## The shape of the worst four

| what was claimed | what was actually observed |
|---|---|
| a test passed | a test was *selected* |
| the tests ran | a TAP report was *recognised* |
| this check reproduces the bug | two different checks were each true |
| this test passed on the base tree | this test was *absent from the failures* |

Each is the same substitution: a **weaker fact standing in for the one being
claimed**, close enough to look right.

### Selection is not execution

`stress.confirm` chose node ids, ran them, subtracted the ones pytest named as
failing, and called the remainder green. The comment said why:

> *"the ids were chosen here, so what ran is known"*

Under `-x` a later selected test never executes. The audit's probe proved it
with a file the test itself writes — `executed-b` absent, and the runtime
emitted PASS anyway and accepted it as the named reproduction. A test pytest
*skipped* was emitted as passing too, with no fail-fast involved.

The fix is to read the outcomes rather than derive them: `-rA` makes pytest
state each one, and only an id it names as `PASSED` is credited. Running the
real thing to see the format paid immediately —

```
PASSED  tests/test_x.py::test_passes
SKIPPED [1] tests\test_x.py:9: probe        ← no node id at all
XFAIL   tests/test_x.py::test_xfails
FAILED  tests/test_x.py::test_fails
```

— because a rule that subtracts non-passes could never have seen that skip, and
a rule that requires a positive `PASSED` line is untouched by it.

### Recognition is not execution

`cat fixture.tap` parsed into a counted passing suite with `ran_tests` true.

This one had been *argued for*. A test in this repository asserted it, with a
rationale: a script printing `TAP version 13` is declaring itself a TAP
producer, so it is read as one — *"the one case where output alone is allowed to
decide"*. The declaration is in the **file**. The question is about the **run**.
No output can tell those apart, and `cat` is the proof.

The test is rewritten rather than deleted, and it now records the reversal and
what it costs: `bash ci.sh` emitting TAP produces no record. It produces a
blindspot instead, so the silence is diagnosable rather than quiet.

### Two true facts about different things

`DISCRIMINATES in discrimination.values()` — any check. So a discriminating
**typecheck** paired with a passing **test suite** and the ledger reported
red-then-green. Both observations were true. Neither was about the other.

---

## The rest

**A clarifying question created a proven checkpoint.** `settle` returns
`VERIFIED` for a question so a turn may end without a claim being discharged.
That is permission to stop. `on_stop` read it as proof of a tree and wrote a
snapshot noted *"the declared checks passed here"* over an UNVERIFIED claim with
zero evidence.

**The `off` profile ran test suites.** Documented as *record evidence, say
nothing, never block* — and its return sat below the verification block, so the
passive profile built a worktree, ran the declared suite in it, and took a
snapshot before going quiet.

**A cached answer outlived its inputs.** Discrimination is cached because the
base commit does not move during a task. True, and incomplete: the tests
*carried onto* that base are the other half of the question, and the task edits
them.

**The offered restore did not restore.** `git restore --source=X --worktree`
rewrites tracked paths and has nothing to say about a file the checkpoint never
had. The audit followed the printed instruction and the failing test it had just
written survived, with the tree still differing afterwards.

**An unchanged file was reported as wholly changed**, because an empty diff was
read as "untracked". **`ALL POOLED` lost attempts** to a dict keyed by task —
the same overwrite that once laundered a failing monorepo package into a passing
record.

---

## The one that was worst, and it was a delivery bug

**The architecture brief was suppressed by reading the file.**

It was gated on `ledger.seen`, which records reads as well as edits. An agent
reads a file before editing it essentially always — in this host, the edit tool
*requires* it. So the note intended for the first edit was eaten by the read
that preceded it, every time. Only a blind edit ever saw one.

That is not just a bug. It retroactively qualifies a published number. **"The
neighbourhood brief fires on 47% of files a real commit touched"** was computed
by calling `atlas.neighbourhood` over real commits — it measures what the
function *can say*. It is not a delivery rate, and the delivered rate was near
zero. PLAN §10 now says so.

> The lesson generalises past this feature: *a detector measured by calling it
> is not a feature measured by using it.* This repository has been careful about
> the difference between a claim and evidence, and sloppy about the difference
> between a capability and a delivery.

---

## Four numbers, and one of them was wrong

The audit also disputed the statistics. Each was checked by running the
arithmetic or reading the paper, not by weighing the argument.

**The pooled upper bound was wrong.** `results/b4-discriminate/findings.md` said
the 95% upper bound on 1 event in 22 was *~13%*. 13.6% is `3/22`, the **rule of
three** — an approximation for **zero** events. The exact binomial bound is
**19.81%** one-sided. The published figure made the result look tighter than it
is. The `0 of 14` figure beside it is fine: that is exactly where the rule of
three applies.

**A cited figure was wrong, from a snippet.** The plan said SWE-bench Verified
over-reports by **6.2** absolute points. The HTML says:

> *"inflates the resolution rates of the studied tools by **6.4** absolute
> percent points, on average"* — arXiv 2503.15223v2

Two of the three figures taken from that snippet — 29.6% behavioural divergence,
7.8% counted correct while failing the developer suite — appear verbatim. The
third did not. `sources.md` had graded it *(snippet)* and warned about exactly
this; it still sat in the plan for four days. **The rule was written down, and
followed, and the number was still wrong, because grading a source is not the
same as reading it.**

**A threshold was doing more work than it could bear.** *"Below about four points
of oracle gap, selectors do more harm than good"* is a result about **those
selectors** on **that benchmark**, and it was being used as a universal cutoff
that could cancel a whole phase. A selector's value is the mass it rescues minus
the mass it damages; a two-point opportunity with negligible harm is still
positive. It stays as a reference point and stops being a decision rule.

**And "no claim on a delta smaller than 6.4 points" conflates three things** —
absolute label bias, *differential* bias between arms, and sampling uncertainty.
Equal bias partly cancels in a paired design. An absolute inflation is not a
minimum detectable effect.

---

## What this cost, and what it is worth

Twelve findings, twenty new tests, and four numbers corrected in public.

Two of the new tests were **vacuous when first written**, and flipping found
both: one asserted a fingerprint changed, which it did whether or not anything
consulted it. And the forward control caught a defect inside one of the fixes
before it shipped — `git cat-file -e` answers 128 both for *"not in that tree"*
and for *"git could not do that"*, which are the two states the new-file check
exists to keep apart, so every genuinely new file came back with no changed
lines at all.

Nineteen probes were watched red with their fix removed and green with it
restored.

The uncomfortable part is the pattern. Of the twelve, **six were in code written
in the previous seventy-two hours** — including the redaction gap, where
`Ledger.saw_output` was made to scrub and `Evidence.detail`, holding a tail of
the same bytes, was missed. Yesterday's entry ended by counting five defects
found by execution and calling the tally the argument. It is still the argument.
Today it is somebody else's execution, which is better.
