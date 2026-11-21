# TestMiner, second slice: what a real run executed, and more than one extreme value

*2026-11-21. Follows [slice 1](2026-11-13-testminer-design.md), whose last
section names this slice: "try more than one extreme value per function, and
add `record`". The user asked to "start the work, next part" under the
standing "decide things yourself, just let me know at the end"; every choice
below is mine.*

## Why

Slice 1 answers the card's question only for functions a person names or a
change touched. The card's first input was always what the program does in
real use: the functions a real run executes are the ones whose silent
breakage costs something. That is `record`.

Slice 1 also empties a body to `return None` and nothing else. A test that
only crashes on `None` (a `TypeError` three calls later) counts as checking
the function, although no test looks at its value. Trying a value of the
right type is how Descartes tells those apart.

## Borrowed

- **Descartes' method classification** (LGPL-3.0, read from
  stamp-project.github.io/pitest-descartes, "how-does-it-work"): a method is
  *pseudo-tested* when "no extreme mutant created for a method are detected",
  *partially-tested* when "some extreme mutants are detected and others are
  not", *tested* when all are. Its operators include `null`, `empty` (arrays)
  and `constant` ("any method with a primitive or String return type").
  Its default constant values were not read; the values below are mine.
- **coverage.py 7** as in slice 1, run directly by the person's command.
  Checked on 7.10.7 (2026-11-21): data is saved when the program ends with
  Ctrl-C (exit 130); `[run] sigterm = true` exists; `coverage run -m pkg`
  works; an external `data_file` leaves nothing in the project folder; files
  under `source` that never ran are listed with no lines; paths come back
  with the platform's separator.
- **Slice 1's own machinery** for everything after the targets are chosen:
  copies, baseline, test selection, budgets.

What this slice adds: a sanitized record of a real run that selects the
functions to examine, and a third verdict between `checked` and `reached,
not checked`.

## Part 1: `record`

```
ep_testminer.py record [--project DIR] -- python app.py ARGS…
ep_testminer.py record -- python -m myapp serve
ep_testminer.py --observed [--base … --function … --path …]
```

- **The command** must be `python SCRIPT …` or `python -m MODULE …`, or a
  bare console script that the slice-1 `_beside` rule maps to its sibling
  interpreter as `python -m NAME` only when `NAME` is importable as a module;
  otherwise refused, naming the accepted forms. It runs as
  `PYTHON -m coverage run --rcfile RC [-m] TARGET ARGS…`.
- **Where it runs: in the person's own tree, cwd = the project root.** A
  program needs its `.env`, data and configuration, which a private copy
  lacks. This is the one place TestMiner does not use a copy. It is safe on
  the same terms as running the command by hand, because it *is* the
  person's command: TestMiner adds nothing to the tree except its state file.
  The rcfile and the coverage data file live in a temporary folder.
- **Stopping.** The command runs in the foreground, inheriting the terminal.
  It ends when it exits, or when the person presses Ctrl-C; coverage.py saves
  on both. `sigterm = true` is set so a POSIX `kill` also saves. There is no
  timer: on Windows a timed stop could only terminate the process, which
  loses the data.
- **What is kept**, in `.elevenpowers/testminer-observed.json`: schema,
  the command's form and target without its arguments (decision 1 below),
  a UTC timestamp, and for each measured file that the project
  tracks or would track (the slice-1 copy plan's `git ls-files --cached
  --others --exclude-standard` set), its sha256 and executed line numbers.
  Files with no executed lines are dropped. Line numbers and hashes carry no
  values: the observation is sanitized by construction. A new `record`
  replaces the old observation.
- **Exit status** of `record` is the command's own; a run that produced no
  data (the command was not Python, crashed before start) is reported as
  such and writes nothing.

`--observed` adds, to whatever else is selected, every function whose body
has an executed line in the observation:

- file hash matches the current file: selected normally;
- hash differs: each function whose span holds an observed line is
  `unknown`, reason "changed since it was recorded; record again". Its lines
  may have moved, so this can name the wrong functions, but it never claims
  anything about them;
- file gone: one issue line naming it;
- no observation file: refused, naming `record`.

Observed functions over the cap are counted `unknown (budget)` in file and
line order, as in slice 1.

## Part 2: extreme values

Each examined function gets one or more replacement bodies, `return VALUE`:

| the function's return | values tried, in order |
|---|---|
| no annotation and no inferable type, `-> None`, or no `return` with a value | `None` |
| `bool` | `None`, `True`, `False` |
| `int` | `None`, `0`, `1` |
| `float` | `None`, `0.0`, `1.0` |
| `str` | `None`, `''`, `'A'` |
| `bytes` | `None`, `b''`, `b'A'` |
| `list`, `dict`, `set`, `tuple`, also subscripted (`list[int]`, `typing.List[int]`) | `None`, the empty one, a one-item one (`[None]`, `{None: None}`, `{None}`, `(None,)`) |
| `Optional[X]`, `X \| None` | as for `X` |
| anything else | `None` |

The type comes from the return annotation as written (a name, an attribute
such as `typing.List`, a subscript, a `|` union, a string annotation parsed
once). Without one, from the function's own `return` expressions when every
one of them is of a single kind: a literal of one of the types above, a
display (`[…]`, `{…}`, `(…)`), an f-string (`str`), or a comparison or `not`
(`bool`). Otherwise `None` only. This is my call; it keeps the extra runs to
functions whose type is evident.

`None` is always tried first, so a function slice 1 examined gets at least
the slice-1 probe.

### Verdicts

| verdict | meaning |
|---|---|
| `not reached` | as slice 1 |
| `reached, not checked` | every value tried passed the reaching tests (Descartes: pseudo-tested) |
| `partly checked` | at least one value failed them and at least one passed; the passing values are listed (partially-tested) |
| `checked` | every value failed them (tested) |
| `unknown` | as slice 1, plus the observation reason above |

A value's outcome follows slice 1's rule: failure, error or timeout of the
reaching tests is detected; all passing is not. If the budget ends before
every value of a function has run, the function is `unknown (budget)`: a
partial set cannot tell `partly checked` from either neighbour.

The JSON entry gains `values`: `[{"value": "0", "detected": true}, …]`. The
text output prints a `partly checked` function with the values that passed,
e.g. `svc.py:12 total: partly checked (returning 0 failed no test)`.
`checked` stays hidden without `--all`.

Defaults stay 60 s, 20 functions, 15 s per command. More values per function
use more of the budget; raise `--seconds`.

## Decided after the builder check

My calls, under the same standing instruction.

1. **The command is not stored as typed.** Arguments can carry tokens, and
   the state file may be committed. The observation keeps the form and the
   target only (`python -m myapp`, `python app.py`) and the number of
   arguments. A test passes a secret as an argument and asserts it is
   absent from the file.
2. **The `__getstate__` false candidate is not fixed by this slice.** Slice
   1 named more values as its remedy, but that function has no annotation,
   so it gets `None` only and stays `reached, not checked`. The rehearsal
   expects it and says so. Containers and bytes gain a one-item value
   (table above), so a function whose real return is the empty value can
   still leave `reached, not checked` when it is annotated.
3. **Explicit selection wins over a stale observation.** A function named
   by `--base`, `--function` or `--path` is examined normally even when its
   file changed since recording; the stale `unknown` applies only to
   functions the observation alone selected.
4. **Hashes are taken before and after the run.** A file that changed
   during it (a reloader, a generated module) is stored with no hash, so it
   is treated as changed.
5. **No attempt cap to scale.** The builder check proposed scaling
   `Budget(deadline, limit + 3)`. A mutation check showed the change made no
   difference: `execute` never calls `Budget.attempt()`, only test
   strength's mutation loop does, so TestMiner is bounded by its deadline
   alone. The line is unchanged.
6. **The parent ignores SIGINT while the command runs**, restored after.
   Otherwise Ctrl-C ends TestMiner first and its wait kills the child
   before coverage.py has saved.
7. **A console script maps to `python -m NAME` only when that runs:** the
   module `NAME`, or for a package `NAME.__main__`, is importable by the
   sibling interpreter. Checked with `importlib.util.find_spec` in that
   interpreter; otherwise refused.
8. **Any value `unknown` for a reason other than the budget makes the
   function `unknown` with that reason.**

## Non-goals

- Doctest contexts (slice 1's third finding) stay unmapped.
- No suggested tests; no agent-facing output; report only, as slice 1.
- No subprocess measurement: a program that forks workers records only the
  main process.
- No values for arguments (Descartes' `argument`, `this`, `new` operators).

## Anti-goals

- `record` writing anything into the tree but its state file.
- A `partly checked` or `checked` drawn from a partial set of values.
- An observation from a changed file selecting functions as if it were
  current.

## Checks

Both directions for each, as in slice 1, each test seen failing first:

- an `-> int` function whose only test asserts `result is not None` (or
  crashes on `None`): slice 1 says `checked`, slice 2 `partly checked`
  (`0` and `1` pass); add `assert f() == 5` and it becomes `checked`;
- the value table, per row, including the inference from `return`
  expressions, a mixed-kind function getting `None` only, and a string
  annotation;
- budget ending between two values: `unknown (budget)`, never a verdict;
- `record` on a fixture script: the observation holds only tracked files,
  hashes match, nothing else appears in the tree (compared with `git status
  --porcelain` before and after); a Ctrl-C ending (simulated by the script
  raising `KeyboardInterrupt`) still records;
- `--observed` after editing a recorded file: `unknown` with the reason,
  never `not reached` or a verdict;
- a refused command form, with the message naming the accepted ones;
- a held-out project at $0: `record` one real entry point, then
  `--observed`, read by hand against a handful of functions, as slice 1's
  rehearsal.
