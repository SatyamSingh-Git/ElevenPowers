# 70 — Verified is not tested

The reverted-tree sweep left one question: seven of its eight vacuous checks
came from patches that touched no test, and every one of them resolved in the
gated arm. Was that history, or would the gate still allow it?

It still allows it. Two of those runs were rebuilt at their base commits, given
their saved patches, and driven through today's hooks with the agents' own
pytest commands. Both reached plain VERIFIED. `test_added` reads as "a test
covering the change passes", and an existing test that imports the changed file
satisfies it. `feature_added` at low or medium risk asks only for a green suite,
which an untested change passes on the old code as readily as on the new.

Blocking was not the answer. §5.12 asks a refusal to earn its cost separately,
and the evidence for that is one p = 0.06 comparison. So the verdict now says
it: on a bug fix or a feature where no test was written, every met check carries
"this shows existing tests still pass, not that the new behaviour is tested".
The status does not move. A refactor is exempt, because existing tests still
passing is exactly what a refactor claims.

The replay found something else on the way. Today's pytest cannot collect
click's base trees without silencing one deprecation, and passing that as
`-W ignore::pytest.PytestRemovedIn10Warning` made the full suite read as a
scoped run: the parser took the option's value for a test node id because it
contains `::`. A broad run with a warning filter can therefore never meet
`suite_green`. It is recorded here, not fixed in this change.
