# 104 — Reached is not checked

*2026-11-13. TestMiner's first slice ([spec](../docs/superpowers/specs/2026-11-13-testminer-design.md),
[results](../results/testminer/README.md)).*

TestMiner had been a roadmap card since [59](59-a-roadmap-contributors-can-open.md):
find behaviour that runs, but that no test checks. The first slice asks it
of functions a person names. Do the project's own tests reach the function,
and if the body is replaced by `return None`, does any of them fail?

The idea is borrowed. Niedermayr called such methods pseudo-tested;
Descartes finds them for Java's PIT by extreme mutation. A 2018 replication
found them in every project it studied. What is added here is the join with
per-test coverage, and an `unknown` that stays separate from "untested".

## What a builder asked before anything was built

The builder check read the design against the code and came back with seven
questions. The first one changed the verdict rules. coverage.py records lines
run from a pytest fixture or a unittest `setUp` under an empty context, not
under any test. Without a rule for that, those functions would be reported
as certainly `not reached`. They are `unknown` now.

## What running it showed

- **A unittest name that does not exist exits as `FAILED (errors=1)`.** The
  outcome rule would have read that as "a test failed with the body
  emptied", that is, `checked`. So mapped test names are now run once on the
  unmodified copy before any mutant trusts them.
- **Both held-out environments lacked coverage.py.** Out of the box,
  TestMiner says `unknown` and prints the install line. That is the usual
  case, not an edge.
- **The parser bug.** With coverage.py available, cachetools' baseline came
  back red. It was green when run by hand: `366 passed, 8 subtests passed`.
  ElevenPowers' main output parser read that pytest 9 summary as 0 passed,
  in every hook, not only here. Fixed, with each pattern change watched
  flipping.
- **One false candidate.** cachetools' `__getstate__` returns `{}`, and
  `test_pickle` checks what that achieves. But `return None` achieves the
  same, so nothing failed. An equivalent mutant: `reached, not checked` is a
  candidate to look at, not proof. Descartes tries several extreme values
  for this reason; that is the next slice.
- **One real detection that looked wrong.** more-itertools' `take` was
  `checked` by a timeout. `chunked` iterates `iter(partial(take, …), [])`,
  and `None` never equals that `[]` sentinel, so the loop never ends.

## Also caught

The map edge from the hook to test strength still said "silent optional
completion", two days after [101](101-the-agent-waited-for-a-report-it-never-read.md)
made it opt-in. A stale node is worse than a missing one.
