# Same state: do the fields an edit writes find the files that consume them? ($0)

PLAN §13 B, open problem 1. The lead is from CodeSpecWeave (arXiv 2610.40256,
[reading list](../../../docs/research/reading-list.md)). Its failure mode is
a patch that "satisfies one requirement while violating another that
constrains the same state", and it anchors requirements "to the same state
transitions or core components".

The [co-readers spike](../coreaders/README.md) anchored on the inputs an edit
reads. It found copies, but only 3 of the 14 contract dependents in the
held-out set. A contract dependent reads or formats what the changed code
produces, so here the anchor is the state the edit writes.

## Plan, written before `cowriters.py` exists

**Query.** From the functions the stage's edit touched, before and after,
take the state they write or shape:

- attribute names assigned (`row.total = …`, `self.due = …`);
- string keys stored or built (`d['qty'] = …`, `{'qty': …}`);
- keyword names passed to calls (`Line(qty=…)`), the fields of a record;
- string constants that carry a format (`%`, or `{` in a format string);
- string constants inside list or tuple literals (column headers and orders).

**Documents.** For each other non-test source file, the same five kinds, plus
the same keys and attributes *read*: a consumer reads what a producer
writes. Rarity weighting (IDF), ranking, controls and evaluation are exactly
the co-readers `run.py`, with only the scorer swapped.

**Decided in advance:**

- **The deciding test is held out:** top 3 must beat co-readers' 5 of 17
  and its own control. The 31 losses were all read before this plan, so
  in-sample is reported but decides nothing.
- **Worth a standing warning** only if some threshold warns on at most 25% of
  self-contained stages while naming at least a third of unedited
  dependents.
- **If it beats co-readers held out,** the next step is a union of the two
  rankings, planned separately before it is run.
- Otherwise it is recorded as tried, and nothing is built.

**Bounds known in advance:** 17 held-out rankings is small. A difference of
one or two is not a result, so "beats" means at least 7 of 17, two more
than co-readers.

## Result: it does not work in this form ([`run.py`](run.py), [output](run.txt))

| top 3 | same state | its control | co-readers |
|---|---|---|---|
| held out, of 17 | **0** | 1 | 5 |
| in-sample, of 31 (decides nothing) | 6 | 5 | 11 |

- Held out it finds none of the 14 contract dependents it was aimed at. In
  sample, another stage's edit does as well as the stage's own.
- No threshold makes a warning: at t = 0.5 it warns on 22% of self-contained
  stages and names 5 of 76 dependents.
- Recorded as tried, and nothing is built. The union planned for a win is
  not run.

What the sanity check showed before the run:

- The query holds field names (`term`, `credits`, `grade_decimals`), but
  many edits write no named field at all. The `household_budget` stage 7
  query was empty.
- The held-out contracts are not shared fields at all. The three distinct
  ones, as their `case.json` paths record, are assumptions about the data
  the changed code produces:
  - `greenhouse_monitor` s5: every reading has a number;
  - `hotel_desk` s7: reservations only ever grow, so `len + 1` is a new id;
  - `survey_tally` s5: rows arrive sorted by count.

  Each is found "following" what the changed producer returns to the code
  that uses it.

(A first version of this note said contracts were orders or formats kept by
position. That was written before reading these paths, and it was wrong.)

"Constrains the same state" may still be right as a description. Shared
field names are not a way to find that state. The paths point at data flow
from the changed producer to its consumers. That is the next thing to try,
under its own plan.
