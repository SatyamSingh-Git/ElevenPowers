# 10. Running it for real, and finding the floor

## The hypothesis everything rests on

P1: evidence gating halves the gap between an agent saying it is done and the
work actually being done. Every other measurement in this project grades the
runtime against recorded behaviour. This one grades the agent, and it is the
only one that cannot be answered by replay.

Three phases had ended with the same sentence about how nothing had run live.
This phase ran it: 89 agent runs, $13.33 of tokens, on real repositories through
the real CLI.

## How a task has to be built

Each task is a small repository with one seeded defect and three properties that
have to hold together or the measurement means nothing.

**The bug is reported by symptom, not diagnosis.** "The last page of results is
missing an entry" rather than "the clamp is off by one". Otherwise the task
measures reading comprehension.

**The visible suite passes before and after the fix.** A green run therefore
proves nothing, and an agent that stops there claims completion having changed
nothing that matters. This is the condition that makes a submit-resolve gap
possible at all.

**A hidden test decides resolution**, written into the repository only once the
agent has finished. It is the ground truth and the agent never sees it.

All three are silent when broken: the run completes, a number comes out, and it
means something other than what it says. So they are a test rather than a
convention. `tests/test_tasks.py` checks every task in both directions, and
caught nothing only because the checks were written before the tasks.

## First run: the mechanism works

```
last_page  gate  resolved  13 turns  78s  $0.62  blocks=1
```

The gate fired in a live session, refused the stop, and the agent went back and
did more work. After three phases of replay, the wiring is confirmed against a
host that actually delivers events rather than one that wrote them down.

## Then three attempts to measure it, each defeated by the same thing

**Attempt one, eight tasks, the stronger model.** The gap moved from 12 percent
to zero, which reads as a triumph and rests on a single task changing hands. One
discordant pair, McNemar p = 1.00. Seven of eight tasks resolved identically in
both arms.

The real finding was that the suite was too easy: a plain agent resolved seven
of eight, so there was almost no room for anything to show.

**Attempt two, eight harder tasks.** Built for headroom, each with a trap where
the obvious fix addresses the reported symptom and leaves a related case broken:
a shallow copy that still shares nested dictionaries, a hyphen run collapsed but
not stripped from the ends, an index clamped while the caller's list stays
reordered.

Same result. 7 of 8. Trickier edge cases are not the difficulty lever, because a
single-function bug with a stated contract is inside the model's competence
whatever the edge case is.

**Attempt three, a weaker model.** This is the standard move and it worked: 16
tasks, 100 percent claimed, 69 percent resolved, a 31 percent gap, and $1.03 for
the whole pass. Five failures to work with, and every one of them the right
shape — an agent stating it fixed the bug when it had not.

So the three arms went out: plain, gated, and a third that asks for the same
diligence in words, because the gate buys extra turns by construction and "you
only gave it more compute" needs an answer.

```
arm         n  claimed  resolved    gap  turns  blocks    cost
vanilla    16    100%       94%     6%    8.7       0    1.06
gate       16    100%       88%    12%   12.8      14    2.63
nudge      16    100%       81%    19%    8.1       0    1.03
```

Both interventions scored *worse* than doing nothing.

## The floor

The plain arm had scored 69 percent an hour earlier. Now it scored 94. Same
model, same tasks, same prompts, same harness.

```
pass one resolved  11/16  (69%)
pass two resolved  15/16  (94%)
changed answer      4/16  (25%)   on identical settings
```

A quarter of the suite gives a different answer run to run. The effect being
hunted is smaller than that, so all three arm comparisons were reading noise,
and so was the triumphant zero from attempt one.

Sorting the suite by what it can actually discriminate is worse still:

```
always resolved  11   burst_limit, business_days, csv_quotes, csv_write, deep_merge,
                      last_page, memoize, retry, slugify, split_bill, version_compare
unstable          4   percentile, truncate, unique, word_wrap
never resolved    1   merge_busy
```

Eleven of sixteen tasks cannot show an improvement, because the baseline already
resolves them every time. One is never resolved by anything. **The suite has four
tasks that discriminate, and they are the four that are unstable.**

## What an answer would cost

Only pairs where the arms disagree carry information. At a 25 percent flip rate,
detecting an arm that wins three of every four disagreements, at the usual 0.05
and 80 percent power:

```
31 discordant pairs, about 126 paired runs, so 252 agent runs per comparison
```

Roughly $25 and several hours per arm, on top of a task suite rebuilt so that
most of it discriminates. That is the honest price of P1, and it is now a number
rather than an intention.

## The one result that did survive

Blocking behaviour was consistent across both models and every task set.

| | runs | blocked at first stop | of those, plain agent already resolved it |
|---|---|---|---|
| stronger model | 8 | 7 | 6 |
| weaker model | 16 | 12 | 11 |

**The gate stops nearly every first attempt to finish, and nearly always on work
that was already correct.** It roughly doubles the turns and multiplies cost by
2.5 to buy evidence for fixes that were mostly right to begin with.

Under this project's own definition — the gate blocked, the work was complete —
most of those are false blocks. The constructed suite scored 0 percent because
its evidence streams were written by hand to include test runs. Real agents fix
first and verify only when pushed, so the population that matters was not in the
suite.

That is the same failure as [08-wiring.md](08-wiring.md) and
[09-claims.md](09-claims.md), in a third place: a measurement that was true
about a population I invented.

It is not obviously a defect. The whole thesis is that completion should be
computed from evidence rather than asserted, and "probably correct" is exactly
what the design refuses to accept. But the price of that principle is now
measured, and it is 2.5x tokens on work that was usually already right.

## What this phase actually delivered

Not P1. What it delivered is the instrument and the floor: a task suite with
enforced properties, a live runner driving the real CLI through the shipped
wiring, an analysis that reports how much to believe rather than only what
happened, and a measured noise floor that says every arm comparison so far,
including the good-looking ones, was chance.

## The mistake

The plan says the noise floor gets measured in week one, "because without it
every later number is unreadable". I went straight to comparing arms and
measured the floor only when a result came out backwards. Three comparisons and
about $12 bought nothing that a two-hour noise measurement would not have
predicted.
