# 43 — The free run that corrected two published numbers

*2026-09-22. Four minutes, no money, and a figure in this repository turns out
to have been measuring the harness in both directions at once.*

The last entry ended with a recommendation: before spending anything on the
paid pilot, run the rehearsal — the harness that seeds a real task at its real
base commit, applies the gold patch, and asks the runtime the question a sweep
would ask, without paying for an agent.

It cost **253 seconds and $0.00**. It found two defects and corrected a
published number.

---

## What it reported first

```
attrs-97f8d175   verdict=yes  red_before=7  reproduced=suite
click-d340b0c1   verdict=yes  red_before=48 reproduced=suite
...
targeted: 3 of 16
```

The published figure was **6 of 16** (journey 37). So the week's work appeared
to have *halved* it.

That is the moment the run earns its cost. Either the fix was a regression, or
the 6 was never real — and no amount of reading decides which.

---

## Defect one: a node id is full of shell metacharacters

Watching `confirm` actually run:

```
command  python -m pytest -q -rA tests/test_make.py::TestCountingAttr::test_converter_decorator[<lambda>0] ...
exit 1
The system cannot find the file specified.
```

`test_converter_decorator[<lambda>0]` is an ordinary parametrised id. `<` is
cmd.exe's **input redirect**, so the shell tried to read from a file named
`lambda` and the command died before pytest started. Zero tests executed.

And exit 1 means *"some test failed"*, which the code allows through. So the
old code found no named failures in that error message and credited **every
selected id as a passing reproduction** — seven fabricated named reproductions
from a command that ran nothing.

That is the audit's F1 defect, caught in the wild rather than in a fixture, and
it is where a good part of the published 6 came from. The `-rA` change had
already stopped the fabrication, which is why the number *fell*: **3 was more
honest than 6.**

Fixed by quoting the ids. Measured, not assumed:

```
unquoted  exit=1  PASSED lines=0
quoted    exit=0  PASSED lines=1
```

---

## Defect two: the rehearsal was not rehearsing

Three was still wrong, and this one is worse, because it had nothing to do with
the mechanism at all.

Every corpus task declares `env: {"PYTHONPATH": "src"}`. `eval/rehearse.py`
set `EP_MINED` and nothing else. So every check it ran imported the **installed
release** of the package instead of the patched source sitting in the
workspace, and the tests failed against code that did not contain the fix:

```
FAILED tests/test_annotations.py::test_is_class_var[annot4] - AssertionError
FAILED tests/test_make.py::TestConverter::test_converter_decorated - TypeError
... 7 of 7
```

A rehearsal whose environment differs from the run it rehearses is measuring
itself. This file's own docstring says the point is to be genuine in everything
but the agent; the environment was the one thing nobody checked.

---

## With both fixed

```
attrs-97f8d175   red_before= 1   reproduced=targeted
click-d340b0c1   red_before= 1   reproduced=targeted
click-18d29196   red_before= 4   reproduced=targeted
...
targeted: 16 of 16
```

**16 of 16**, and the `red_before` counts collapse: `click-d340b0c1` from **48
to 1**, `click-18d29196` from 47 to 4, `click-051bb0f3` from 31 to 2. Those
were never bugs on the base tree. They were import failures, counted as
evidence.

---

## What 16 of 16 does *not* mean

The rehearsal applies the **gold patch**. Of course the targeted tests pass —
the correct fix is in the tree by construction. This measures that the targeted
path is **no longer starved**, which it demonstrably was: it needed a passing
record carrying a node id, `pytest -q` prints passes as dots, and now the
runtime asks directly and can read the answer.

It says nothing about what a real agent will produce. The file's own line says
it best: *a rehearsal where every task discriminates is a rehearsal, not a
result.*

---

## The point of the entry

Two numbers in this repository were wrong in opposite directions at the same
time — one inflated by a shell bug crediting dead runs, one deflated by a
missing environment variable — and both were published, and neither was caught
by reading, by testing, or by an external audit that reproduced fourteen other
probes.

They were caught by running the thing for four minutes.

The last entry's argument was that the free measurement should happen before
the paid one. This is the case for it, made by the measurement itself.
