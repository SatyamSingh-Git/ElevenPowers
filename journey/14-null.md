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

## What it does not say

It does not say gating is useless. It says **this obligation set is inert on
these bugs**, because everything it asks for is something the agent already does.
Whether a reproduction-first obligation changes that is the next measurement, on
the same twelve tasks, where a real effect can now show itself.
