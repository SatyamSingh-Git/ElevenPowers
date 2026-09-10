# The oracle problem in agent-authored evidence

Read 2026-09-10, after twelve real bugs showed the gate changing nothing. The
question was whether "demand a test that fails first" is the right fix. It is
not, and the reason matters more than the fix.

## What the measurement here found

Twelve mined bugs, gate against plain agent, identical outcomes on all twelve at
1.4x the cost. The gate's obligations — a passing test covering the change, a
green suite — are things the agent already does. It writes the test after
deciding its fix is right, so the test asserts whatever the fix does.

## The field has measured the same thing

**Rethinking the Value of Agent-Generated Tests** (arXiv 2602.07900): *"prompt-induced changes in the volume of agent-written tests do not significantly change final outcomes"* and *"current agent-written testing practices reshape process and cost more than final task outcomes."*

That is this project's null result, independently and at larger scale. More
agent-written tests do not improve resolution. They change process and cost.

**All Smoke, No Alarm** (arXiv 2606.18168), over 86,156 test patches: LLM-generated assertions *"frequently encode actual program behavior rather than expected behavior, turning bugs into passing tests."* Their remedy is syntactic — flag test files with no assertion patterns — and they state its limit plainly: *"a patch classified as S1 confirms that an equality check exists, not that it checks the right property."*

**Nobody has a semantic solution.** This is an open problem, not something this
project failed to look up.

## Why the obvious fix does not work

Requiring the test to fail before the fix sounds like it breaks self-confirmation.
Martin Fowler's team ran that experiment inside the agent loop:

> "there was no clearly discernable difference based on TDD workflow versus no
> TDD workflow"

and *"more than once Opus ranked the non-TDD workflow solutions slightly higher"*.
The observed failure modes are specific:

- *"the agent implements ahead of the test"*, so it *"passed immediately"* and never went red
- *"tests checked the implementation's output against itself"*
- an *"active TOTAL-row bug ... enshrined by a test"*

Her conclusion: *"I have stopped telling my coding agents to write tests first."*
The reasoning is that a human writing a test first experiences friction from
specifying behaviour before implementing it, and *"an agent doesn't experience
that and can write a test the same instant it plans an implementation."*

**One difference this project can claim.** Fowler tested *instructing* TDD.
This runtime would *verify* a red-to-green transition actually occurred in the
evidence stream, so "implemented ahead, passed immediately" is caught rather
than trusted. That closes one failure mode.

**It does not close the important one.** If the agent misunderstands the
expected behaviour, its reproduction test encodes the misunderstanding, fails
against current code, and passes after a fix that implements the
misunderstanding. Red to green, bug still there. Which is exactly the shape of
the seven tasks that failed here.

## The actual conclusion

**No obligation over agent-authored evidence escapes the oracle problem.** The
agent is author and examiner. Reproduction improves the *process* evidence — did
you verify anything at all — and leaves the *oracle* untouched.

What escapes it is evidence whose oracle is not the agent:

| Source of truth | Available here? |
|---|---|
| The project's pre-existing tests | yes, already `suite_green`; they do not cover the bug, which is why it existed |
| **Mutation score over the changed lines** | computable, independent of the agent's opinion, and what Fowler recommends: *"monitor and improve regression quality with the help of mutation testing"* |
| Properties or metamorphic relations | needs domain input |
| A human-written test | outside the runtime's reach |
| A second model as independent oracle | costs another call, and shares the first one's priors |

**SWT-Bench** (NeurIPS 2024) is the positive result and shows the shape that
works: tests generated *from the issue*, used to *filter candidate patches*,
*"doubling the precision of SWE-Agent"*. The generation is decoupled from the
patch it judges. A gate watching one agent write one patch does not have that
separation, and cannot manufacture it by reordering the agent's own steps.

## What this should change

1. **Stop counting a passing agent-written test as evidence of correctness.** It
   is evidence that a test exists. `test_added` currently treats the two as the
   same thing.
2. **Add an obligation whose oracle is not the agent.** Mutation score over the
   changed lines is the cheapest one available: mutate what the agent changed,
   run the agent's own tests, and see whether they notice. A test that survives
   every mutant asserts nothing about the change.
3. **Keep reproduction, but demote the claim made for it.** Verified red-to-green
   is real process evidence and catches implement-ahead. It is not a correctness
   oracle and should not be described as one.
