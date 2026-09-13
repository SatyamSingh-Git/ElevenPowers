# 24. A benchmark that can move, and a second agent that broke the machine

Phase B ended with an instrument that worked and a benchmark that could not
answer anything with it. Ninety paid runs established a baseline, a taxonomy and
a reproduction, and then the per-task table said the quiet part: **nine of
fifteen tasks were solved on every one of six replicates, and one was never
solved at all.** Five tasks carried the entire ability of the corpus to detect a
difference between two arms.

A paired comparison needs about thirty-one tasks where the arms disagree. Five
candidates is not a small sample, it is an impossible one, and no amount of
money spent on that corpus would have changed it. So the next thing was not the
comparison. It was a corpus that could move.

## The size of the benchmark was set by three accidents

The corpus was mined from "the last 200 commits", which reads like a judgement
about diminishing returns. It was not a judgement at all.

`candidates()` spent two subprocesses per commit, one for the subject and one
for the file list. Scanning deep history meant tens of thousands of process
spawns, which on Windows is most of an hour spent on nothing. One `git log
--name-only` returns both: the same four hundred commits went from eighteen
seconds to three hundredths of one, with byte-identical output.

`git()` decoded with the machine's codepage. A commit subject in click's history
carries a byte cp1252 has no character for, and the default decode raised inside
subprocess's reader thread — the call returned `None` and mining died on
`.strip()` several frames away, naming neither the commit nor the encoding.
Only scanning deeper than usual ever reached it. Fifteen other pipes in this
project had the same exposure, including the one that reads the grader's own
test output.

And `validate()` ran a full test suite on every candidate before asking anything
answerable from the commit's own test files. On markupsafe, eight of nine
candidates are rejected without it.

Together those three made a corpus of fifteen look like the yield of five
repositories. **451 candidate commits were reachable; about 130 had ever been
looked at.** The deep mine returned **94 instances**, and every one of the
original fifteen was among them.

## Difficulty as a filter, once, declared

D62 has said since Phase B that difficulty is a label and never a filter,
because **E6** was a suite selected on whether the naive fix broke the visible
tests — the benchmark chosen around the mechanism being measured.

Gold-patch size is not that. It is fixed by the upstream commit before any arm
exists and cannot favour one. What it can do is waste money, and the B4 data
says how much:

| band | always solved | never | split |
|---|---|---|---|
| one-liner | 1 | 0 | 1 |
| small | **7** | 0 | 1 |
| substantial | 1 | 1 | **3** |

Seven of eight `small` tasks were solved on every replicate. Forty-five of the
ninety-four mined instances are `small`. Half the corpus would have been budget
spent on tasks no arm can lose.

So the selection was allowed and **written into the lock it produces**, so a
rebuild reproduces the selected corpus exactly; and `show` names the missing
band every time it prints, because the line it used to print — *nothing was
dropped for being easy or hard* — would otherwise have gone on asserting itself
over a corpus with forty-five tasks removed. Forty-nine tasks: 36 substantial,
13 one-liner.

Two asymmetries are recorded rather than fixed. `--want 40` bound click, which
contributed forty instances from the newest seventy-six of its 255 candidates
while attrs was mined to the bottom of all sixty of its. And markupsafe's four
instances are all `small`, so it leaves the corpus entirely.

## Both arms of a task, back to back

The sweep now runs `--arm vanilla,gate` and finishes both arms of a task before
moving to the next.

This is not a convenience. In the B4 sweep the arms were separate sittings, and
when an agent broke the machine partway through the second one, **every affected
run was in the same arm** — because only one arm was in flight. Drift that lands
on one side of a comparison is indistinguishable from an effect. Running both
arms of a task together makes anything that drifts hit both equally.

`arm_order` had shuffled a list of arms since Phase A, for exactly this reason.
Nothing had ever passed it more than one element.

Resume had the matching hole: it counted replicates per task, so a restart would
have seen three vanilla runs, skipped the gate arm entirely, and reported a
paired comparison with one side missing.

## The second agent to break the machine

Five dollars were spent confirming the isolation fix survived a real agent,
because it had been wrong twice already that morning.

It was wrong a third time. Four runs in, an agent working an attrs task
**uninstalled attrs from the machine**. `PIP_PREFIX` steers where a package is
written and says nothing about where one is removed from. The detector added
that morning compared the shared site for *new* entries, so a deletion was
invisible to it.

The consequences were immediate and would have been silent:

- the forty-nine-task corpus rebuilt **eleven of forty-nine**, thirty-two of the
  failures reading "the fix does not satisfy its own tests"
- the gated arm's one `regressed` was `TestLegacyMetadataHack::test_version`,
  the same metadata test that faked a regression the night before

**The corpus is the problem.** Every repository in it — attrs, click, jinja2,
markupsafe, itsdangerous — is also installed in the environment that grades it.
An agent working on attrs is one `pip uninstall` from the grader's own
dependency. That is not an exotic failure mode; it is the default one, and it
has now fired twice in a day.

`PIP_REQUIRE_VIRTUALENV` makes pip refuse both directions outside a virtualenv,
verified against real pip rather than argued. The site comparison is symmetric.
A run whose shared site moved during it is graded `setup` — harness breakage,
never counted against the agent, which is the right side to err on given what
the other side did to pass B.

The real answer is a grading environment the agent cannot reach at all, and that
is not built.

## What the four runs did show

| task | arm | outcome | turns | cost |
|---|---|---|---|---|
| attrs-0f758fe5 | vanilla | unfixed | **2** | $0.32 |
| attrs-0f758fe5 | gate | *contaminated* | **41** | $1.05 |
| click-fc518e41 | vanilla | resolved | 39 | $1.30 |

The plain agent stopped after two turns on a task it had not fixed. The gated
arm worked forty-one. That is the mechanism this whole project exists to test,
visibly doing the thing it claims to do, on somebody else's bug — and it is one
run, on a contaminated machine, and it is not evidence of anything yet.

It also cost 3.3x the plain arm rather than the 1.4x the budget assumed, which
if it holds changes what a paired sweep costs.

## The corpus is pinned, on the second attempt

The first rebuild of the forty-nine returned **eleven**, because the machine had
been changed underneath it by the agent above. The second was killed partway
when the session holding it exited. The third, on a repaired machine and with
pip locked, returned **49 of 49, identical on every field that decides a score**.

That is what pinned has to mean: a twelve-kilobyte lock, and the same benchmark
on the other side of it. The first attempt is worth keeping in mind though —
the lock was fine both times. What moved was the room it was measured in.

## What is still not known

P1. Nothing here measures it. This chapter built the thing that could.
