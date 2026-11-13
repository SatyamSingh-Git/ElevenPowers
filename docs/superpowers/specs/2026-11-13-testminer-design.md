# TestMiner, first slice: behaviour that runs but no test checks

*2026-11-13. The roadmap card `test-miner` (architecture/index.html, Planned
tab), first slice. The user asked for it on 2026-11-13: "start the work on
TestMiner".*

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
