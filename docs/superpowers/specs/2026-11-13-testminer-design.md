# TestMiner, first slice: behaviour that runs but no test checks

*2026-11-13. The roadmap card `test-miner` (architecture/index.html, Planned
tab), first slice. The user asked for it on 2026-11-13: "start the work on
TestMiner". A builder check was run; see "Decided after the builder check",
which overrides the sections above where they differ.*

## Why

A function can be reached by tests without any test checking what it does.
Line coverage counts it as covered. The card says so: "Reaching a line does
not establish that an assertion checks its behavior."

ElevenPowers already asks a narrower question for the agent's own change:
would the tests notice it undone? That is the vacuity check, and changed-code
test strength. TestMiner asks it of code a person points at: the functions a
real run of the program executed, or the functions a change touched.

## Borrowed

- **Pseudo-tested methods, by extreme mutation.** Niedermayr et al. (2016)
  introduced it; Descartes implements it for Java's PIT. A method is
  pseudo-tested when tests execute it, yet replacing its whole body with a
  trivial one fails none of them. A 2018 replication found pseudo-tested
  methods "in all our subjects", over 28K+ methods (Vera-Pérez et al.,
  *Empirical Software Engineering*; abstract only,
  [arXiv:1807.05030](https://arxiv.org/abs/1807.05030)).
- **coverage.py dynamic contexts.** With `dynamic_context = test_function`,
  each executed line records which test ran it. ImpactGraph already reads
  coverage.py 7.10.7 JSON with contexts (`core/impact/coverage.py`).
- **This repository's isolation and budgets.** `core/strength` provides the
  private copies (`isolation.snapshot`, `trial`), the timed execution
  (`execution.execute`, `Budget`) and the function spans
  (`regions.python_targets`).

What TestMiner adds: it joins *what ran*, *which tests reached it* and
*whether emptying it fails any of those tests* into one explained verdict per
function. It also keeps "cannot tell" separate from "untested".

## Scope of this slice

- Python only. The test command must be a pytest or unittest invocation, as
  discovery now reduces declared commands to.
- Function granularity: top-level functions and methods.
- Detection only. No test skeletons. The card allows those only once expected
  behaviour is established independently, and the independent-oracles work
  is not built.
- Report only. A person runs it; the agent is not told, and no verdict changes.

## Inputs: which functions to examine

1. **Observed at runtime (optional).** `ep_testminer.py record -- COMMAND`
   runs the person's own command under coverage.py. It saves the line data
   plus a sha256 of every measured project file. Line numbers carry no
   values, so the observation is sanitized by construction.
2. **Changed.** With `--base COMMIT`, the functions whose lines changed since
   that commit.
3. **Named.** `--function path.py::name`, repeatable.

## Verdict per function

| verdict | meaning |
|---|---|
| `not reached` | no test executed any line of its body |
| `reached, not checked` | tests executed it (named), and with its body replaced none of them failed |
| `checked` | at least one of those tests failed with the body replaced; not listed by default |
| `unknown` | with the reason, as below |

`unknown`, never `not reached`, when:
- coverage.py is not importable in the test interpreter;
- the tests fail on the unmodified tree;
- a test context cannot be mapped back to a runnable test;
- the observation's file hashes do not match the current tree (an unmatched
  build);
- the budget runs out;
- the body cannot be emptied safely: generators, `async` functions,
  `__init__`, abstract methods, or a body that is only a docstring or `...`.

**Replacement body:** `return None`. A function that already returns `None`
on every path is one a test can only check through its side effects. It is
still the right probe: if nothing fails, nothing checks it.

## Behaviour

- **Every run uses a private copy.** The person's tree is never modified,
  the same rule as test strength.
- **The baseline run** is the project's test command under
  `coverage run --context` settings passed by rcfile in the copy. If it is
  not green, every function is `unknown`.
- **Each mutant runs only the tests that reached that function,** selected by
  context, with the same per-command timeout as strength.
- **Bounded.** Defaults: 60 s overall, 20 functions, 15 s per command. A
  budget that ends early leaves the rest `unknown`.
- **Output:** text by default, `--json` for structure, and a saved
  `.elevenpowers/testminer.json`.

## Acceptance (from the card)

1. A known unreached function gives an explained candidate. An asserted,
   covered function gives none.
2. Missing coverage.py, an unmatched observation, a red baseline and an
   exhausted budget give `unknown`, never certainty.

The card's third check, suggested tests, is out of this slice.

## Decided after the builder check

These are my calls, under the user's standing "decide things yourself".

1. **Reached outside any test.** coverage.py 7.10.7 records lines run from a
   pytest fixture, a unittest `setUp` or test-module import under the empty
   context `""`. A function whose body ran only there is `unknown` ("reached
   outside any test"), never `not reached`. If the baseline recorded no test
   context at all, everything is `unknown`.
2. **coverage.py version.** No pin. Any coverage.py 7.x importable in the
   project's own test interpreter is used. Missing or older gives `unknown`
   with the install line. Function spans come from TestMiner's own AST pass,
   not the JSON `functions` section, which varies by version.
3. **`record` moves to slice 2.** A private copy lacks `.env` and data, the
   person's tree must not be written, and servers need a defined stop. Those
   are design questions of their own. So slice 1 has no runtime observation,
   and the unmatched-build `unknown` arrives with it.
4. **What is examined.** One of `--base`, `--function path.py::Qual.name` or
   `--path FILE` is required. Nothing is selected by default. Over the cap,
   functions are taken in file and line order, and the rest are counted as
   `unknown (budget)`.
5. **Test command.** The configured `tests` command, or `--command`, runs as
   written, options kept, wrapped as `python -m coverage run --rcfile=… -m
   RUNNER …`. That applies only when it is a direct `pytest`,
   `python -m pytest` or `python -m unittest` call. Anything else, and `-n` or
   `-p xdist`, is refused with a message naming `--command`.
6. **Editable installs.** As in test strength, the guard stops a run that
   imports the person's own folder through an editable install. Every
   function is then `unknown`, with that reason.
7. **Mutant outcomes**, following PIT's convention. A failure, an error or a
   timeout of the reaching tests means `checked`. Only all passing means
   `reached, not checked`.

From reading the code:

- **Function spans:** TestMiner's own AST pass. `regions.python_targets`
  includes nested functions, starts at decorators and returns bare names.
- **Test selection for a mutant.** Dotted context names (`tests.test_a.T.test_m`)
  run directly under unittest. Under pytest they are mapped to
  `FILE::Class::name` when the module resolves to exactly one file.
  Otherwise the mutant runs the whole command: slower, still a valid probe.
  Node ids are passed as an argument list, not through a shell.
- **Not reused:** `core/impact/coverage.convert`. It needs a receipt and
  reduces everything to file edges.
- **`--base`** is resolved to a full SHA, then given to `scope.select`.
  Python files only.
- **No config block.** Limits are CLI flags with the defaults above.

## What the real runs showed (2026-11-13)

See [results/testminer](../../../results/testminer/README.md). Neither
held-out environment had coverage.py, so the out-of-the-box answer is
`unknown` with the install line.

With coverage.py available, there were three findings:
- the main parser read pytest 9's subtests summary as 0 passed (fixed);
- one false candidate came from an equivalent mutant (`__getstate__`);
- doctest contexts cannot be mapped to a runnable test.

The next slice should try more than one extreme value per function, and add
`record`.

## Checks planned

- **Fixture service** (the card's "first contribution"):
  - one function reached only by a test with no assertion on it;
  - one covered and asserted;
  - one never reached;
  - one observation recorded on an older version of a file.
- **Real projects, $0:** a held-out project or two at a clean commit, checked
  by hand against the verdicts for a handful of functions.
- **Both directions:** each verdict is watched flipping. Add an assertion and
  `reached, not checked` becomes `checked`; delete the test and it becomes
  `not reached`.
