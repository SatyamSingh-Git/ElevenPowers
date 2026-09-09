# 8. The wiring was never measured

## Why look here at all

Two of the seven pieces the plan calls core had turned out to be dead: the
repeat runner was missing, and the scope guard's allow list was written by
nothing. Two failures with the same shape is not a coincidence, it is a class.
So instead of building the next thing, the question became: what else is
listed as working and is not?

The answer was worse than expected, and it was all in one place. Every
measurement this project had produced tested the runtime. Nothing had ever
tested the join between the runtime and the host that feeds it.

## Three defects, one layer

**The scope guard was inert one commit after it shipped.** `hooks.json`
subscribed `PostToolUse` to `Bash` alone, so no `Read` or `Edit` ever reached
the handler that records what a task has looked at. `ledger.seen` stayed empty,
and an empty seen list is the first early return in `unrelated()`. The guard
answered "not drift" to everything. Its 25 labelled cases and 20 tests all
passed, because they called the function directly.

**Failure arrives as a different event.** A tool call that fails raises
`PostToolUseFailure`, not `PostToolUse`. Nothing was subscribed to it. Every
failing command in real use was invisible.

**Failure arrives as a different shape.** This was the bad one. The reader was:

```python
response = payload.get("tool_response", {}) or {}
output = response if isinstance(response, str) else (
    response.get("stdout", "") + response.get("stderr", ""))
exit_code = 0 if isinstance(response, str) else int(response.get("exit_code", 0) or 0)
```

Three assumptions, all wrong. The field is `tool_result`. A successful command
returns an object with `stdout` and `stderr` and **no exit code at all**. A
failing command returns a bare string that starts `Error: Exit code 1`.

So the string branch, which is exactly the failure case, was scored zero, and
the object branch defaulted to zero because the key it looked for does not
exist. **Every command, passing or failing, was recorded as passing.**

Follow that through the design and the product is gone. `CONTRADICTED` can
never fire. The reproduction obligation can never be discharged, because no
record is ever red. The red-to-green transition can never be observed. A failing
suite satisfies "the related test suite passes". The system would have said
VERIFIED over a broken build, which is the precise failure it exists to prevent.

## Why 119 passing tests missed all of it

The tests invoked the hook with payloads written by the same person who wrote
the code, from the same idea of what the host sends. Both sides shared the
error, so they agreed perfectly. A test only tells you the two halves match; it
cannot tell you the pair is wrong.

There was a second, quieter reason. Each of these defects fails by doing
nothing. Nothing raises no exception, prints no warning, and looks exactly like
a run where there was nothing to record.

## Reading instead of guessing

The documentation settled one question: `PostToolUseFailure` exists and takes
the tool call that `PostToolUse` does not. It did not answer the field shapes,
so the next step was to stop reading about the host and read the host.

A session transcript records every tool result as the host produced it. Six
megabytes of this project's own first session gave the answer in one pass:

```
Bash results: {interrupted, isImage, noOutputExpected, stderr, stdout} x 98
              str x 3
'Error: Exit code 1\n..........  [100%]\r\n46 passed in 2.86s\r\n'
```

No exit code anywhere. Failure as a string. Both facts visible in ten seconds
once the right file was open.

## Measuring on 36,000 real commands

If a transcript answers that question, it can answer others, and there were
241 of them on the machine already. Replaying them costs no inference: the
whole point of the offline track in the plan.

The ground truth is the good part. Nobody had to label anything, because the
host itself records whether each command failed, by which shape it returned.
The corpus grades the code without the author's opinion entering anywhere.

```
sessions           241
turns              3557
commands           36034  (958 failed, per the host)
  object, stdout/stderr, no exit code 35057
  string (failure)                   967
readable results   36024/36034 (100%)

agreement with the host about whether a command failed
  reader            failing commands      succeeding commands
  this one          174/174 (100%)        5916/5916 (100%)
  previous          0/174 (0%)            5902/5902 (100%)
```

Reported as two rates rather than one on purpose. The corpus is 97 percent
successes, so a reader that answers "passed" to everything scores 97 percent
accuracy while being wrong about the only thing the gate needs to know. That is
the same trap as judging the gate by how often it agrees with the agent, and
the project already refuses that framing once.

## What the corpus taught the parsers

Watching what 36,000 real commands look like was worth more than the defect
hunt.

**Real commands do not start with the thing they run.** `cd api && npm run
build` was not recognised as a build, because every anchored pattern matched
from the start of the string. Worse, the evidence identity came out as the
directory. `cd <dir> &&` and `export VAR=... &&` were the two commonest
openings in the corpus. Stripping setup prefixes before matching fixed both.

**`pytest -q` prints its summary bare.** The counting pattern expected a rule of
equals signs around the totals, which quiet mode does not print, so the mode
almost every agent uses recovered no counts at all.

**`npm run typecheck` is how TypeScript projects type-check.** The detector knew
`tsc`, `mypy` and `pyright` and missed the script name that wraps them.

Evidence coverage went from 12 percent of commands to 17. The remainder is
mostly `git add`, `echo`, `cat >` and inline `python <<'PY'` scripts, which
produce no evidence because they are not evidence.

## The general fix, not three specific ones

Fixing three defects leaves the fourth one waiting, so the more useful work was
on the shape of the failure.

**Generate the subscription from what the handlers use.** The tool lists live in
`core/wiring.py`, the handlers branch on them, `hooks.json` is generated from
them, and a test asserts the checked-in file still matches. Divergence is now
impossible rather than merely unlikely.

**Make silence leave a trace.** When the runtime is handed something it cannot
read, it appends to `.elevenpowers/blindspots.jsonl`. A host that renames a
field becomes a diagnosable symptom instead of a tool that quietly stopped
working.

**Test the join, not the halves.** `ep-doctor` feeds the runtime a payload
shaped the way the host shapes one and checks that a failing command comes out
failing:

```
ok    python 3.13.2
ok    a failing command is recorded as failing
ok    a passing command is recorded as passing
ok    hooks.json subscribes to every event the runtime handles (6 tools recorded)
ok    the ledger directory is writable
ok    nothing unreadable has arrived from the host
```

The payloads in its self-check and in `tests/fixtures/` are captured from a real
session, not written by hand. That is the actual lesson: the fixtures were the
bug.

## Cost and standing

About 400 lines added across four modules, 22 tests, and two new eval tools.
169 tests green, the gate still 0 percent false blocks and 0 percent misses on
46 scenarios, the scope guard still 0 and 0 on 25 cases.

What this does not establish: the plugin has still never been installed in a
live session and watched. Replay proves the runtime reads what the host wrote
down; it does not prove the host delivers those events to a running hook. That
is the next thing, and it is the third time in a row the honest closing sentence
has been that the numbers come from replay rather than from a live agent.
