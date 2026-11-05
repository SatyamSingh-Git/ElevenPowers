# Rule groups on real history

*Plan written 2026-11-05, before the benchmark or any measurement exists.
$0, no model.*

Every rule-group figure so far comes from the twelve v3 cases. The
[scopes spike](../rule-groups-scopes/README.md) ends on the problem: any
further variant would be shaped by those 51 dependents, so it needs other
cases to judge it. Real projects have no declared dependents, but their
history records what changed together.

## Cases from history

Four real Python projects with public histories, the four of the
[real-project check](../rule-groups-real-projects/README.md) that have
one. Each was cloned on 2026-11-05 and is pinned at this commit:

| project | repository | pinned | non-merge commits |
|---|---|---|---|
| `click` | pallets/click | `2247b35` | 2,172 |
| `attrs` | python-attrs/attrs | `9d9f94a` | 1,835 |
| `rich` | Textualize/rich | `9d8f9a3` | 3,387 |
| `pytest` | pytest-dev/pytest | `08017d9` | 13,272 |

ElevenPowers' own history is left out, because its author wrote the
method.

- **Commits:** non-merge commits reachable from the pinned commit, newest
  first, each against its only parent, renames off.
- **A commit qualifies** if it modifies 2 to 5 non-test Python files, by
  the product's own test-file rule (`core.surface.TEST_NAME`). Larger
  commits are left out, as the ones most likely to bundle unrelated
  changes.
- **A quiet dependent** is a modified non-test Python file of a
  qualifying commit that passes the v3 check of a quiet dependent
  (`eval/multistage_quiet.py`): its parent version mentions, as a whole
  word, none of the names the rest of the commit changes. Those names are
  the changed definitions, the reassigned module names and the removed
  identifiers and literals.
- **The edit** is the commit's other modified non-test Python files.
- **Sample:** per project, the newest qualifying commits until 40 quiet
  dependents are collected or 3,000 commits are examined. Dependents of
  one commit share its proposals, so they are not independent; the number
  of commits is reported beside the number of dependents.

**What a case is not:** the v3 dependents were shown to break earlier
behaviour when left behind. Nothing here shows that. A file that changed
quietly beside another may carry the same rule, or receive the same
mechanical edit, or be an unrelated change in the same commit.

## Reading a sample, before any coverage

Thirty quiet dependents are drawn with `random.Random(0)`. Each is read
with its commit's diff and sorted, before any coverage is computed:

- **rule:** the two sides apply one rule, format, order, key or
  contract. One left behind would break or diverge.
- **sweep:** the same kind of edit in both, with no rule between them,
  such as annotations, lint or one third-party API changing.
- **unrelated:** changes bundled into one commit.

The reader is the author of the plan, which bounds the sort.

## Measures

For each quiet dependent, from the parent commit's tree:

1. **Product:** `propose(tree, limit=100, seconds=120)` on the parent tree
   made a Git repository, as [`product.py`](../multistage-v3/discover/product.py)
   does. A dependent is covered within K if a top-K pair joins it to a
   file of the edit.
2. **Product control:** the same dependent and proposals, with the edit
   replaced by the next older qualifying commit's modified files, leaving
   out the dependent.
3. **Co-change:** from the 1,000 most recent non-merge ancestors of the
   parent, those modifying 2 to 20 non-test Python files. Each pair of
   files present in the parent tree is scored by the number of those
   commits that modified both. Pairs are ranked by that count, then by
   name. Covered within K as in 1.
4. **Co-change control:** the co-change list with the control's edit.
5. **Combined:** covered within K if the product covers it within K/2 or
   co-change does within K/2, so a reader still reads K pairs.

All at K = 10, 20, 50 and 100, per project and in total, and on the
read sample by its sort.

## Decided in advance

- **The product's coverage carries over to real history** only if, in
  total at K = 50, it covers more than its control, with p < 0.05 on the
  one-sided exact sign test of the discordant dependents. Otherwise PLAN
  §13 B records that the v3 coverage was not seen on real history. On v3
  it was 20 of 51 against 11.
- **Co-change becomes a candidate source** only if, in total at K = 50:
  - the combined list covers at least 5 more dependents than the
    product's top 50, with p < 0.05 on the same test; and
  - co-change alone covers more than its own control, with p < 0.05.

  Even then it is a candidate for a plan of its own, not built from this:
  the v3 cases cannot judge it, with eight stages of history each.
- **The read sample bounds every figure.** If fewer than a third of the
  sample sort as **rule**, the totals say mostly how well each signal
  finds files changed together, not rules, and the write-up says so.
- Every figure is reported whatever it shows.
