# 19. The host contract, read rather than assumed

## Four findings the audit never ran

H1 to H4 were source findings: the audit read the documented contract against
the code and reported the mismatch, but its script never executed them. So
unlike the sixteen, these had no probes. They were written here, from the
documentation, before any fix.

That ordering matters more than usual, because the last time this project
believed something about its host it was wrong in three ways at once
([08-wiring.md](08-wiring.md)), and the correction came from reading 36,000 real
commands rather than from reasoning.

## Reading the documentation changed two of the four answers

**H2 was not a host limit.** The plan recorded it as "20-second hook timeout
against 300-second verification" and proposed running long verification outside
the callback, with snapshot-bound job state and a resume path. That is a
substantial piece of machinery.

The host's documented default for a command hook is **600 seconds**. The twenty
was this project's own constant, chosen in `core/wiring.py` and never revisited,
and it was shorter than the work the hook does. Stop now gets 600 and every
other event keeps 20, because a hook that hangs is worse than one that gives up
and only Stop runs the project's suite.

An afternoon of design, avoided by reading the page.

**H4 was live on this machine.** `PowerShell` is a distinct tool name, used on
Windows where Git Bash is not installed. `COMMAND_TOOLS` was `("Bash",)`. On
those machines the runtime subscribed to a shell that never ran and captured no
commands at all — the whole product, silently inert, on the operating system it
is being developed on.

## H1: a shape with no result object

The documented failure hook does not nest its result:

```python
{
    "hook_event_name": "PostToolUseFailure",
    "tool_name": "Bash",
    "tool_input": {"command": "python -m pytest -q"},
    "error": "Exit code 1\n1 failed in 0.1s",
    "is_interrupt": False,
}
```

`read_result` looked under `tool_result`, `tool_response` and `toolUseResult`,
found none of them, and returned `readable=False`. No evidence, one blind-spot
entry, and a failing test suite unrecorded.

Two smaller things came with it. The interrupt flag is top-level too, where the
code checked for `interrupted` *inside* the result object. And the message is
`Exit code 1`, not `Error: Exit code 1` — only the transcript form writes the
prefix, and the pattern matched only the prefixed one, so even a payload that
did reach the reader would have had its exit code read as output.

**That narrows the headline again.** 174 of 174 failures read correctly is a
replay result, and replay replays what was recorded. It cannot contain a shape
the recorder never produced. Replay fidelity is not delivery fidelity, and this
project has now confused the two twice.

## H3: reporting into a field that discards it

`additionalContext` is honoured on `SessionStart`, `UserPromptSubmit` and
`PostToolUse`. It is **not** honoured on `Stop`.

All three of the Stop handler's report-only branches used it — the verified
report, the non-blocking report, and the one that fires after the gate gives up.
Every one of those is a path where the runtime has decided *not* to interrupt
and instead to say something. All three said it into a field the contract drops.

Two existing tests asserted that behaviour and passed, which is the ordinary way
a defect becomes load-bearing.

## Both directions, as a standing requirement

Partway through this work the instruction arrived to test everything forward and
adversarially, conclude from the four states, and build the same discipline into
the product.

The first part was half-true already. Since **E1** every narrowing fix has
shipped a control asserting the rule still fires, and that is not decoration:
fixing **R6** without one would have looked exactly like reverting the M1 work
that cut live blocking from 75 percent of runs to 12. But H1 to H4 had been
written with one direction each, and the other direction found nothing wrong —
which is the point. *A check that refuses everything passes every adversarial
test. A check that accepts everything passes every forward test.* Running only
one is indistinguishable from the feature being deleted.

The second part is a genuine gap and is now [PLAN.md](../PLAN.md) §5.0, ahead of
the rest of the architecture:

> The runtime watches commands the agent chose to run and reads their output.
> That is passive, and passive observation cannot tell a test that discriminates
> from one that agrees with whatever it is handed.

So the system must do the breaking itself: revert the candidate's change and
confirm the new test goes red, weaken a test and confirm the check stops being
satisfied, run the preserved set against the pre-patch tree to establish which
failures are the agent's. **Recorded, not built.** Writing it down is not the
same as having it, and the difference is exactly what this journey exists to
keep honest.

And conclusions come from the four states rather than a pass/fail bit.
`VERIFIED`, `UNVERIFIED`, `STALE` and `CONTRADICTED` already separate *no
evidence* from *evidence that expired* from *evidence pointing the other way*.
Collapsing that to a boolean is what the grader did before E1, and it is why a
regression and a patch that never worked came out as the same zero.

## Where Phase A stands

Fifteen of the sixteen audit defects closed, R2 narrowed rather than closed, and
H1 to H4 closed with probes of their own. **418 tests, no xfails.**

Four remain, all evaluator infrastructure: workspaces are deleted so nothing is
re-gradable (**E3**), an arm can be labelled present and be absent (**E4**),
grading happens inside the candidate's own mutable workspace (**E5**), and task
selection is keyed to the gate's own detection mechanism (**E6**).

Three exit criteria are still unmet, and one of them was lying. `ep_doctor.py
--host` printed six green lines and exit 0 — because the script parses `--cwd`
and nothing else, so the flag was discarded and what ran was the ordinary check
against no host at all. The four host defects are fixed; the `--host` mode that
criterion actually asks for does not exist yet.
