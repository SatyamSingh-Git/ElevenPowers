# 87 — a scratch file is not a scope violation

Journey 86 ended with one JavaScript conversation that followed the feedback and
then ran out of time, and with a Python case that could not be asked at all: a
filtered `python -m unittest` run produced no evidence, so no feedback ever fired.

## Read the summary the standard library prints

The parser knew pytest, Jest, Vitest, Go, Cargo, RSpec and more, but not the
runner every Python install ships. Its summary was captured from real runs first:
`Ran N tests in Xs`, a blank line, and one status line that can say `OK`,
`OK (skipped=1)`, `FAILED (failures=1, errors=1)`, `FAILED (unexpected
successes=1)` or `NO TESTS RAN`. Errors and unexpected successes are failures;
skips and expected failures are neither; zero tests is not proof. Only a command
that names `unittest` is read, so `cat old.log` stays nothing.

The first version read only the last summary, and a run of two suites could hide
an earlier failure behind a later pass; a control caught it before it shipped.
The project's own rule then refused the change outright: a test counts parser
dispatch sites, and a new runner cannot land without its forward and adversarial
pair in the both-ways table.

## Two cases, both followed

With the summary read, one frozen batch ran both cases. Each emitted the feedback
in turn 1, and each used the owned runner in every turn after it. JavaScript
completed all four turns at 4/6/8/10. Python graded 4/6/8/10 too, but its last
turn is recorded as a scope violation.

It was not one. The agent had written a scratch file into the host's own
scratchpad, outside the project. The edit reached the task's touched paths as an
absolute path, and milestone impact advice, which validates paths with the same
strict rule it applies to a project's own declarations, raised on it. The
harness caught every error after its scope check under one label. Observed edits
outside the project are now excluded and reported; an explicitly requested path
still fails; and a readout error is now called a readout error. The recorded
turn keeps the label it was given.
