# Rules kept outside functions

*Plan written 2026-11-05, before the candidate exists. $0, no model.*

PLAN §13 B leaves open the 31 of 51 never-read dependents that no proposal
covers at K = 50 ([discover](../multistage-v3/discover/README.md)).
`ep_milestones --propose` compares functions only. A rule a project keeps
in a module-level table, such as `parcelpost`'s `STATUS_COLUMNS`, is in no
function, so it can never be proposed, whatever words it shares.

## Diagnosis ([`where.py`](where.py), [rows](where.json), [summary](where.txt))

For each dependent, the lines its fix changes and the lines the stage's
other edits change are placed by the AST of the file before and after the
stage: inside a function, or outside any (module or class body), with
imports apart.

- **All 20 covered dependents** have changed lines inside a function on
  both sides.
- **14 of the 31 missed** have a side with no changed line in any function:
  the dependent in 12 (10 of them `key`), the edit in 6.
- **The other 17 missed** have both sides in functions. That is a different
  failure, not addressed here.

The diagnosis was made on these 51, so anything it suggests is in-sample.

## Candidate

Each module's and each class's own statements become a unit beside its
functions: everything in that body except functions, classes, imports and
a leading docstring. A module's unit is named `<module>`, a class's by the
class. Scoring is unchanged. Imports stay out because they are the import
graph, which briefs already name and which covered 4 of 31 v3 losses.

## Measures

1. **The 51 never-read dependents:** the place of each, with the current
   code and with the candidate, from the tree before each stage, as
   [`product.py`](../multistage-v3/discover/product.py) does (limit 100).
2. **The control,** as in the discover spike: the same dependent joined to
   another stage's changed files, with the same proposals.
3. **The 17 read stages,** for completeness only.
4. **The six real projects** of the
   [real-project check](../rule-groups-real-projects/README.md): exit, wall
   time, and how many of the top 50 have a module or class unit on either
   side, with the first five such pairs quoted.
5. **The reviewed run's accepted pairs:** whether each is still among its
   case's top 50 at stage 0. If not, that run cannot be prepared again with
   the new code.

## Decided in advance

- **Adopted only if,** at K = 50, it covers **at least 23 of the 51**
  (now 20), and its margin over the control is **no smaller** than the
  current code's, recomputed by the same script.
- **Every dependent that leaves the top 50 is named,** whatever the total.
- **Every real project must still exit 0 within its 30 s budget.**
  Measure 4 has no labels, so it is reported, not judged.
- Otherwise the candidate is recorded as tried and not built.
