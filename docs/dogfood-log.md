# Dogfood log

Every friction event and defect found by using the thing, dated. This log is the
product track's raw data. Bugs found by using it count for more than bugs found
by testing it.

## 2026-09-09, first end-to-end run on this repository

**Defect: risk tier inherited from a parent repository.**
`git status --porcelain` walks up the directory tree, so a project that is not
itself a repository reported an unrelated parent's changed files and was scored
medium risk instead of low. Fixed by confirming `rev-parse --show-toplevel`
matches the working root before trusting the output. Found by a test that ran in
a temp directory; would have shipped as mysterious over-strictness for anyone
running inside a monorepo subdirectory.

**Friction: `pytest -q` made an obligation impossible to satisfy.**
The `test_added` obligation wanted a per-test record, but `-q` prints no
per-test lines, so an agent that ran exactly the right test could never
discharge it. Rather than instructing the model to pass `-v`, a scoped suite run
(one that names a test file or node) now counts. The rule: when the runtime can
infer something deterministically, it should, instead of pushing work onto the
model.

**Defect: reproduction evidence read as contradiction.**
The reproduce-then-fix cycle produced a failing record followed by a passing one
for the same test. The gate treated any fresh failure as CONTRADICTED, so doing
exactly what a high-risk `bug_fixed` claim demands produced a permanent block.
Fixed by counting only the most recent record per identity. This was the most
important find of the day and no unit test would have suggested it; it only
appears when the whole cycle runs in order.

**Friction: wrong closing line on a stale-only verdict.**
The gate said "discharge the missing obligations" when nothing was missing and
everything was merely stale. Now it says to re-run the stale checks.

Ledger for a full cycle: 3 evidence records, all fresh, about 4 KB on disk.
Hook latency: under 200 ms per event on this repository, dominated by hashing
the source set.
