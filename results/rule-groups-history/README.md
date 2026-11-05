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

## Result: neither bar met ([`build.py`](build.py), [`measure.py`](measure.py), [cases](benchmark.json), [sample](sample.json), [rows](measure.json), [summary](summary.txt))

Run 2026-11-05 on the code at `d5397d3`. There are 160 quiet dependents
in 108 commits, 40 per project. They come from the newest 882 commits of
`click`, 794 of `attrs`, 500 of `rich` and 221 of `pytest`. No run hit a
time budget or an unreadable file.

| 160 quiet dependents, covered within K | 10 | 20 | **50** | 100 |
|---|---|---|---|---|
| product | 26 | 40 | **60** | 69 |
| product control | 28 | 40 | **60** | 73 |
| co-change | 41 | 53 | **93** | 105 |
| co-change control | 47 | 64 | **90** | 105 |
| combined | 39 | 57 | **85** | 105 |

- **The product's v3 coverage was not seen on real history.** At K = 50
  it covered 60, the same as its control. There were 11 discordant
  dependents each way, p = 0.58. On v3 it was 20 of 51 against 11.
- **Co-change is not a candidate.** The combined list did cover 25 more
  than the product's top 50 (32 against 7 discordant, p = 3.5 × 10⁻⁵).
  But co-change alone covered 93 against its control's 90 (p = 0.36), so
  the second condition fails.
- **By project,** the product at K = 50 covered:
  - `click`: 30, control 26;
  - `attrs`: 28, control 31;
  - `rich`: 2, control 2;
  - `pytest`: 0, control 1.

  In the two small projects a few central files pair with nearly anything.
  In the two larger ones the top 100 rarely joins the edit's files at all.
- **The read sample:**
  - it sorted as 16 **rule**, 10 **sweep** and 4 **unrelated**, so rules
    are more than a third;
  - on the 16 rules the product covered 3 at K = 50, as did its control;
  - co-change covered 8, as did its control.

**Checked by hand, both ways** (`attrs` `45b6b6b`):
- A recount of co-change with a different Git command matched: 67
  commits, 160 pairs, places 5 and 3.
- The product's place 1 is a `__call__` pair between `_make.py` and
  `validators.py`, and `_make.py` is in 8 of the top 10 proposals. A hit
  there says the file is central, not that the edit was found.
- An edit naming a file that does not exist gets no place.
- No edit or control of the 160 contains its own dependent.

### Exploratory, chosen after seeing the above

- **Controls that share a file with the edit:** 61 of 160 do, because
  small projects keep changing the same files. On the 99 that share none,
  the product covered 31 against 33, and co-change 51 against 47
  (p = 0.29). The verdict stands.
- **Linked by an import at the parent,** by the product's own import graph
  (`core.atlas.source_model`): 90 of 160.
  - On those 90, both signals beat their controls. The product won 10
    discordant and lost 2 (p = 0.019); co-change won 9 and lost 2
    (p = 0.033).
  - On the 70 not linked, neither did. The product won 1 and lost 9;
    co-change won 7 and lost 11.
  - Of the 16 read as rules, 6 are linked at the parent. The other links
    the reading saw were made by the commit itself.

  So on real history, what the proposals find is already joined by an
  import, which the existing brief names. The dependents an import does
  not join are the problem rule groups exist for, and there they found
  nothing a control did not.

**What this does and does not say:**
- The labels are quiet co-changes, not breakages shown as on v3.
- There are four projects, and the reader of the sample is the plan's
  author.
- Coverage is by file pair, as on v3.
- It does not touch the finding that agents act on a declared rule
  ([acted on](../rule-groups-acted-on/README.md)). It says that
  proposals, as built, are not shown to find undeclared rules in real
  code. A person still has to name them.
