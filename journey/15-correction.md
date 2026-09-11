# 15. A critique, and the diagnosis that did not survive it

## What had just been concluded

[14-null.md](14-null.md) reported the first fair comparison: twelve real bugs,
identical outcomes with the gate on and off, 1.4 times the cost. The explanation
offered was that the agent misunderstands what is wanted, writes a fix, then
writes a test agreeing with its fix, so every obligation is satisfied and the
work is still wrong. From that, a conclusion: a runtime watching one agent cannot
reach an oracle strong enough to matter.

An external critique challenged the evidence for that, and it was right.

## The task that was read wrongly

`click-762c97ee`, *"Fix double-bracketing of choices in synopsis"*. The account
said the agent asserted `{a|b|c}` for required choices and that this was its
misunderstanding.

Reading the answer key, which should have happened before the claim was made:

```python
def test_choice_argument_optional_metavar(runner):
    """Optional Choice arguments reuse the type's brackets instead of doubling."""
    ...  nargs=-1  and  required=False  must render [foo|bar|baz]

def test_datetime_argument_optional_metavar(runner):
    """``DateTime`` arguments behave the same way as ``Choice``."""
```

The agent's answer for the reported case was **correct**. It failed because it
fixed `Choice` and never generalised to `DateTime`, nor to the variadic path.

That is incomplete generalisation, not unknowable intent. And unlike intent, it is
sitting in the repository: `DateTime` supplies its own brackets in the same way.

**The claim was made from the agent's test without reading the answer key** — the
error this project has now catalogued five times, committed in the act of writing
about how important it is not to commit it.

## Auditing the other six

| task | why it failed | reachable? |
|---|---|---|
| `762c97ee` | fixed `Choice`, missed `DateTime` and variadic | yes, a generality probe |
| `bc32a92c` | closed a borrowed stream, no flush on exception | yes, differential against the original |
| `047adef2` | shuffled order, dedupe, conflict | yes, edge probes |
| `f316d5cb` | final position at 3, 7, 25, iterate and update | yes, edge probes |
| `9f9b149e` | a new API the commit message names outright | yes, it is in the report |
| `bec59289` | import name to distribution, ambiguity error | partly |
| `fc518e41` | exit-code policy when an interrupt races a result | a genuine decision |

**Six of seven are reachable.** The conclusion is withdrawn. What the experiment
established is narrower and still stands: *the current obligation set adds no
resolution benefit on these tasks*. It never established that the failures need
information the runtime cannot get.

`bc32a92c` is the sharpest miss. Its requirements are **preservation** properties:
a borrowed stream must still not be closed, an exception must still flush. The
original program is the oracle for those, and comparing behaviour before and
after needs no intent whatsoever. A bug fix owes two things — change the defective
behaviour, preserve the rest — and this gate only ever checked the first.

## Two citations, both trimmed the flattering way

**SWT-Bench.** The precision gain came with about 20 percent recall. It shows
useful filtering of candidate patches, not a doubling of bugs resolved. Quoting
the doubling alone overstated the case for the direction being proposed.

**All Smoke, No Alarm.** Its 86,156-patch classification is largely syntactic, and
the "assertions encode actual rather than expected behaviour" line is cited from a
separate controlled study rather than measured there. It was used here to argue
that no stronger architecture can work. It does not support that.

Both errors point the same way, which is the thing to notice.

## What the plan became

**The thesis clause is narrower and more useful.** "The oracle must not be the
agent" forbids too much. The operative rule is about promotion: an agent may
propose an expectation, and **its own passing test may not be what turns that
proposal into the standard**. Every expectation now records where it came from,
and a direct example or a mechanically checkable contract outranks an inferred
reading of prose.

**Two questions where there was one.** Contract validity — what supports this
expected behaviour — before implementation validity — what supports the claim that
this patch implements it. The runtime only ever asked the second.

**Five outcomes, not two.** Refusing the stop conflates ending computation with
certifying completion, which is why blocking bought turns and changed nothing when
the missing ingredient was information. Missing evidence, a violated grounded
expectation, an unresolved ambiguity, an environment that prevents verification,
and a satisfied protocol are five different situations that deserve five different
responses. An agent may end its turn unresolved; it may not call that verified.

**Three mechanisms, measured separately.** Issue-derived checks frozen before the
patch is visible, differential comparison against the original program, and probes
that distinguish competing interpretations. The middle one costs no model call and
the audit says it reaches `bc32a92c`.

**And the diagnostic comes before the verifier.** Freeze the twelve patches,
generate checks without sight of the candidate or the gold, then see whether they
reject the candidate and accept the maintainer's fix. Inconvenient checks get
counted, not discarded. That is cheap, needs no repair loop, and says which
mechanism carries information before any of them is built properly.

## The thing worth keeping from this

The correction did not come from a measurement. It came from someone checking the
source that the story was built on, which is the same move that has produced every
real finding here — and this time it was pointed at my own reasoning rather than
at the code.
