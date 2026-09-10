# 14. The first fair test, and the gate walked past the failure

## What was finally possible

Twelve bugs from `click`'s own history, each one a real commit that changed
source and tests together, validated the way SWE-bench validates: the fix
commit's tests must fail at the parent and pass at the fix, and the existing
suite must be green at the parent. The bug report is the commit message as its
author wrote it. Nothing in the task came from this project.

That mattered arithmetically as well as morally. With seven of twelve failing
for a plain agent, seven tasks carried headroom, so a clean sweep for the gate
would have produced p = 0.016. **Every previous suite in this project had a
ceiling of p = 1.000 before a single run**: incapable of producing evidence
whatever happened.

## The result

```
arm         n  claimed  resolved    gap  turns  blocks    cost
vanilla    12    100%       42%    58%   32.6       0    4.39
gate       12    100%       42%    58%   35.2       2    6.01

  gate     fixed 0, broke 0   p = 1.000
           cost x1.4, turns x1.1
```

**Identical on all twelve.** The same five resolved in both arms, the same seven
failed in both, zero discordant pairs. The gate changed nothing and cost 40
percent more.

## Why, which is the part worth keeping

The gate stopped 1 of 12 runs. In the other eleven every obligation was already
met, so the runtime looked at the work, found its conditions satisfied, and said
nothing.

Reading back what those obligations are:

- `test_added` — a test covering the change passes
- `suite_green` — the related suite passes

The agent does both unprompted. It edits a test file, its own test passes, and
self-discharge finds the suite green. There is nothing left for the gate to
object to.

But **the agent writes that test after deciding its fix is correct**, so the test
asserts whatever the fix happens to do. A wrong fix gets a test that is wrong in
the same direction, and it passes. The existing suite stays green because the
buggy behaviour was never covered — that is why the bug existed.

**It is marking its own homework, and the gate was accepting the marks.**

This is weakness class L in this project's own complementarity matrix,
self-confirming review, catalogued in other systems and then built here. Twelve
real bugs walked past it, twelve times out of twelve.

## The obligation that would bite

`reproduced` — the test must be seen failing **before** the fix. An agent cannot
satisfy that by writing something agreeable afterwards, because the evidence is
a transition from red to green, and the red half has to exist first.

It is already in the table. It is attached only to high risk, and none of these
twelve scored high risk, so it never applied.

## What this phase cost and bought

$10.40 for the comparison, on top of roughly $14 building an instrument that
could carry it.

What it bought is the first honest answer to the question the project exists to
ask, and a specific defect to fix rather than a number to feel good about. The
null is only trustworthy because the bugs came from somebody else, which is the
whole argument for the instrument.

## The obvious fix, and why it is wrong

Demand a test that fails first. An agent cannot satisfy that by writing something
agreeable afterwards, because the evidence is a transition and the red half has
to exist first. It seemed obvious enough to start implementing.

Researching it first turned up three things.

**The null is already published.** *Rethinking the Value of Agent-Generated
Tests* (arXiv 2602.07900): "prompt-induced changes in the volume of agent-written
tests do not significantly change final outcomes" and they "reshape process and
cost more than final task outcomes". That is this result, at larger scale, by
someone else.

**The mechanism has a name and no cure.** *All Smoke, No Alarm* (arXiv
2606.18168), over 86,156 test patches: LLM assertions "frequently encode actual
program behavior rather than expected behavior, turning bugs into passing tests".
Their remedy is syntactic, and they say what it cannot do: confirming an equality
check exists is not confirming it checks the right property.

**The obvious fix was run and it is theatre.** Fowler's team compared TDD inside
the agent loop against no TDD: "there was no clearly discernable difference", and
"more than once Opus ranked the non-TDD workflow solutions slightly higher". The
agent "implements ahead of the test" so it "passed immediately" and never went
red; tests "checked the implementation's output against itself"; an active bug
was "enshrined by a test". Her conclusion: "I have stopped telling my coding
agents to write tests first."

One difference this project can claim: she tested *instructing* TDD, and this
runtime would *verify* that a red-to-green transition actually happened. That
catches implement-ahead instead of trusting it.

It does not catch the failure that matters. A reproduction test encoding a
misunderstanding fails against current code and passes against a fix that
implements the same misunderstanding. Red to green, bug still there — which is
the shape of all seven tasks that failed here.

## The conclusion, which is structural

**No obligation over agent-authored evidence escapes the oracle problem.** The
agent is author and examiner. Reproduction improves the process evidence and
leaves the oracle untouched.

Grading the obligation table by whose word it takes should have been done before
any of this was built:

| Obligation | Oracle | Independent? |
|---|---|---|
| `suite_green` | the project's tests | yes, but blind to the bug by definition |
| `build_ok`, `typecheck_ok` | the compiler | yes, and narrow |
| `stable` | this runtime's repeat runner | yes, and only for nondeterminism |
| `test_added` | a test the agent wrote after deciding it was done | **no** |
| `reproduced` | a test the agent wrote, in verified order | **no** |
| `runtime_ok` | the agent reading its own output | **no** |

Two of the four in the default set are the agent's own word, and the two that are
not are blind to the bug. **The whole null is visible in that table**, and the
table could have been written in week one.

## What it does not say

It does not say gating is useless. It says this obligation set is inert on these
bugs, for a reason that is now understood rather than guessed at.

The next measurement is an oracle that is not the agent. Mutation score over the
changed lines is the cheapest one a runtime watching a single agent can reach:
mutate what changed, run the tests the agent wrote, and see whether they notice.
It is also what Fowler recommends in place of agent-side TDD. That is P17, on the
same twelve bugs, where an effect can now show itself.

And if that fails too, the honest finding is that a layer watching one agent
cannot verify that agent's work, and this becomes a reporting tool rather than a
gate. The plan says so now, before the measurement.
