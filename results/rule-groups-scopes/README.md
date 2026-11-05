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

## Result: not adopted ([`measure.py`](measure.py), [`summary.py`](summary.py), [summary](summary.txt))

Run 2026-11-05: [`candidate.diff`](candidate.diff) applied to `7592cde`,
against `7592cde` itself. The code was then reverted. Its tests and
mutants are in the diff: ten mutants, all killed.

| 51 never-read dependents, covered within K | K = 10 | 20 | **50** | 100 |
|---|---|---|---|---|
| functions only (current) | 8 | 11 | **20** | 32 |
| with module and class bodies | 13 | 16 | **20** | 35 |
| control, current | 3 | 5 | 11 | 18 |
| control, with bodies | 3 | 7 | 12 | 18 |

- **The bar was not met:** 20 of 51 at K = 50 against 23, and the margin
  over the control fell from 9 to 8.
- **It reaches the rules it was meant for, but displaces others.** Of the
  14 dependents with a side outside any function, 4 entered the top 50:
  `clinic_booking` 1 and 3, `gradebook` 1 and `recipe_box` 3. Of the 37
  with both sides in functions, 3 entered and 7 left, so those covered fell
  from 20 to 16. Eight entered and eight left in all.
- **Nearer the top it helps:** 13 of 51 in the top 10, against 8. A person
  who reads only the first ten would see more, but the plan's question was
  50, decided in advance, and the answer stands.
- **The read stages,** for completeness: 8 of 17 at K = 50 fell to 7.
- **The reviewed run would change:** of the 34 pairs its reviewer kept, 3
  leave the top 50 at stage 0 (`household_budget` 2, `library_loans` 1),
  and 3 more stay under another id.

**Real projects: all six exit 0 within the propose deadline**, with
`sqlalchemy` taking 17.0 s against 13.8 s. What the bodies bring is mostly
boilerplate:

| project | bodies | top 50 with a body |
|---|---|---|
| `attr` | 35 | 16 |
| `click` | 82 | 10 |
| `_pytest` | 190 | 23 |
| `rich` | 170 | **46** |
| `sqlalchemy` | 1,461 | 11 |
| ElevenPowers | 1,303 | 32 |

- **`rich`:** 37 of its 46 are generated Unicode width tables, each paired
  with the next version's. Six more share only `TYPE_CHECKING`, and three
  only `T = TypeVar("T")`.
- **`_pytest`:** 15 of its 23 share only `TYPE_CHECKING`.
- **`sqlalchemy`:** some are real copies, such as two dialects'
  `RESERVED_WORDS` tables. Five share only `inherit_cache`.
- **ElevenPowers:** all 32 pair files under `eval/`, its bundled cases'
  fixture data.

**Left open:** the 14 rules outside functions are still not proposed,
and the 17 missed with both sides in functions are a separate failure.
Any further variant, such as dropping `TYPE_CHECKING` blocks, would be
shaped by these 51 after seeing them, so it needs other cases to judge it.

## The other 17: both sides in functions ([`infunction.py`](infunction.py), [rows](infunction.json))

*Diagnosis only, 2026-11-05, $0, in-sample.* For each, the changed
functions on both sides are scored as proposals score them: rare words
shared, over the square root of their weights. The changed edit function
paired with the changed dependent function is set against the stage's
50th proposal.

- **One shares no rare word:** `ticket_office` 3. No ranking of shared
  words reaches it.
- **Six are near the cutoff,** at 0.64 to 0.96 of the 50th score. They
  share a distinctive name: `labour_rate`, `set_offset`, `loan_limit`,
  `"business_date"`, `no_show_fee`, `new_hold_id`. Three are copies of
  the rule.
- **Ten are far below,** at 0.09 to 0.51. Nine of them are data,
  contract or key changes. The words they share are mostly a record's
  field names: `payee`, `amount`, `credits`, `transaction`, `date`, or a
  bare `1`.

This puts numbers on the plan's earlier finding: shared rare words find
copies of a rule and miss format contracts between a writer and a reader.
A variant aimed at the six would again be shaped by these cases. The nine
contracts need a different signal, not a different weighting.
