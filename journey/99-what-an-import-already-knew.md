# 99 — What an import already knew

*2026-11-05. PLAN §13 B, open problem 1.*

[96](96-a-rule-a-person-certifies.md) built rule-group proposals on one
figure. Fifty proposals per project covered 20 of 51 never-read v3
dependents, against 11 for a control. [97](97-the-first-note-acted-on.md)
and [98](98-a-reviewer-in-place-of-a-perfect-one.md) then showed that a
declared rule is acted on. The discovery half had only ever been judged on
the twelve cases it was designed beside.

## Two variants, judged on the same 51

Two ideas for the 31 misses were each tried under a plan written first.

- **Module and class bodies as units**
  ([scopes](../results/rule-groups-scopes/README.md)). Fourteen misses keep
  their rule outside any function, such as `parcelpost`'s
  `STATUS_COLUMNS`.
  - Adding bodies reached 4 of those 14, but pushed 7 others out.
  - On `rich`, 37 of its 46 body pairs were generated Unicode tables.
  - Not built.
- **The other seventeen**, which have both sides in functions, were
  diagnosed, not fixed.
  - Six sit just under the 50th score.
  - Nine are data or format contracts that share only a record's field
    names.
  - A reweighting aimed at the six would be shaped by these very cases.

Both write-ups ended on the same sentence: a further variant needs other
cases to judge it.

## Other cases, from history

Real projects declare no dependents, but their history shows what changed
together. A file modified in a small commit counts as a quiet co-change
when it names none of what the rest of the commit changed. That is v3's
own quiet check, `eval/multistage_quiet.py`, run unchanged.

Four projects, `click`, `attrs`, `rich` and `pytest`, gave 160 such
files ([results](../results/rule-groups-history/README.md)). Before any
coverage was computed, a sample of thirty was read and sorted: 16 were
rules (a style key, an environment variable, an ini option, a return
contract), 10 were sweeps and 4 were unrelated.

**At K = 50 the proposals covered 60 of the 160. So did the control,**
which joins the same file to another commit's files. Co-change history,
the classic signal for coupling without shared names, covered 93 against
its control's 90.

## Why the controls kept up

Checking one case by hand showed why. In `attrs`, `_make.py` sits in 8 of
the top 10 proposals, and its place-1 pair is two `__call__` methods. A
hit there means the file is central, not that the edit was found. Small
projects keep changing their central files, so any commit's files pair
with them. In the two larger projects the top 100 rarely reached the
edit's files at all.

Split by the product's own import graph, chosen after seeing the totals:

- **90 of the 160 are already joined by an import.** There, both signals
  beat their controls.
- **The other 70 are not joined.** There, neither signal beat its
  control: the proposals won 1 and lost 9.

Those 70 are what rule groups were for. The import brief already names
the rest.

## What stays

The v3 figure is now qualified wherever it is published: PLAN, the
README, the guide and status. Agents acting on a declared rule stands:
that was measured with rules declared, not proposed. Who finds the rule
is back to the person who knows the project.

## Bounds

- The labels are quiet co-changes, not breakages shown as on v3.
- There are four projects, and the reader who sorted the sample also
  wrote the plan.
- The import split is exploratory.
