# The 16-task rehearsal, after the base fix

`python -m eval.rehearse --corpus E:/ep-corpus/prevalence.json --tasks 16`

Same 16 tasks as the paid B3 sweep, same corpus, no agent and no cost. Run
2026-09-16, after `ffeb959` (base recorded at task open) and `9dd72d7` (the
rehearsal drives the real hook instead of hand-building the ledger).

## The precondition is fixed

| | paid sweep | rehearsal after the fix |
|---|---|---|
| runs where the check was asked | **8 of 16** | **16 of 16** |
| runs with no base commit | 6 | 0 |

Every task now opens with a base and reaches the check. That is the whole of
what this rehearsal establishes, and it is what it was run to establish.

## What it does NOT establish, and cannot

Every one of the 16 came back `verdict=yes` and `reproduced=True`. That is not a
result. The rehearsal applies the **gold patch** — a known-correct fix — and a
correct fix discriminates by construction. `eval/rehearse.py` says so in its own
docstring: *a rehearsal where every task discriminates is a rehearsal, not a
result.* The interesting verdict is `VACUOUS`, and by definition it only appears
when an agent's evidence is weak, which is exactly what is absent here.

So the discrimination *rate* remains unmeasured. Only a paid sweep can measure
it, and the one that ran measured it on 8 runs with 1 hit, which is no rate at
all.

## A second thing the rehearsal did surface, unasked

`red_before` is large and concentrated:

| task | red_before | collection errors | individual test ids |
|---|---|---|---|
| `click-d340b0c1` | 48 | 0 | 48 |
| `jinja2-065334d1` | 1 | 0 | 1 |

The 48 are real test identities, not collection errors, and all of them live in
`tests/test_arguments.py` — the single file the task carried onto the old
source. Carrying an updated test file onto old code makes **every test in that
file** red, not merely the one that targets the change.

That qualifies `reproduced=True` on 16 of 16. §5.13's reproduction is satisfied
here by *the whole carried file having been red*, not by a targeted test having
been red and then green. It is still true — a test red before and green now is a
reproduction — but it is much cheaper to satisfy than the phrasing suggests, and
the same coarseness already noted for the `yes` verdict applies to it.

**Not changed unilaterally.** Tightening what counts as a reproduction would
move a published figure, so it is recorded here as a question rather than
answered: should a reproduction require a test that targets the change, or is
whole-file redness enough?

## Standing before any further spend

- Fixed: the missing base, and a pre-flight that can now see that class of defect.
- Open: the two runs that had a base and still skipped — the staleness gate at
  `core/stress.py:157`, untouched by this work.
- Open: `config` is not serialised into a bundle, so the `config.commands` gate
  cannot be diagnosed after a run at all.
- Open: both computed signals saturate under a correct patch, so their rates
  cannot be estimated without paying.
