# Do the agents' tests pin behaviour or their own implementation? Test transfer

2026-11-28. Written before anything was computed. Follows the four-arm sweep
([results](../../../results/heldout/sweep-2026-11-26-four/README.md)), where one line
of instruction took VACUOUS to 0 of 90. VACUOUS says a test fails when the agent's
change is undone; it does not say the test checks the behaviour the request asked
for rather than the way this agent happened to write it. A reviewer will ask that
first, and the project has seen the failure: handed raw mutants, agents wrote
white-box tests aimed at them (B8, `PLAN.md` §10).

## The measure, borrowed

SWT-bench (Mündler et al., NeurIPS 2024) scores a generated test by running it
against the repository's own fix: a good test fails before the fix and passes after
it. Here the "fix" is the upstream maintainers' commit, which the agent never saw,
so a test that passes on it describes behaviour both fixes share, not the agent's
implementation. Added: the agent's own patch as the third tree, so only tests that
actually pin the agent's change are judged.

For each graded, resolved run whose patch changes a test file:

- split the patch into its test files (`core.surface.TEST_NAME`) and the rest;
- **A** = base + the agent's test files; **B** = base + the whole agent patch;
  **G** = base + the upstream fix's source change (no upstream tests) + the agent's
  test files;
- run pytest on the agent's changed test files in each tree, `-rA`, reading the test
  ids reported PASSED;
- **pinning tests** = PASSED in B and not PASSED in A (failing, erroring, or not even
  collected without the change);
- **transferring** = pinning and PASSED in G.

A run's outcome: `transfers` (every pinning test passes on G), `partial`, `none`
(no pinning test passes on G), or `no pinning test`.

## Analysis (fixed now)

- **Primary:** `instructed` against `assisted`, the two arms that write tests. Per
  task, the fraction of runs with a pinning test whose pinning tests all transfer;
  two-sided signed-rank over tasks where both arms have such a run.
- **Secondary, descriptive:** the same outcome for `ordinary` and `superpowers`
  (few runs write tests), for October's two arms, and the test-level share of pinning
  tests that transfer, per arm.
- **Read, not counted:** for up to 10 runs per arm that do not fully transfer, the
  failing test and the upstream diff are read and the reason written down (a
  different public API, behaviour upstream chose differently, an implementation
  detail). One reader, the author, not blind; reported as such.

## Bounds

A test that fails on G is not necessarily a bad test: the request may leave an API
name or an edge case open, and upstream chose differently. Transfer is evidence about
specification, not a grade of test quality. Python, small fixes, one model.
