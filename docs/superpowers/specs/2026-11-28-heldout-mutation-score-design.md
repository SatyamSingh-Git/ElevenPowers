# Mutation score on the changed lines, per arm

2026-11-28. Written before anything was computed. VACUOUS, the measure behind both
held-out sweeps, is the coarsest mutant there is: undo the whole change. A reviewer
will ask for the standard measure, mutation score: how many small changes to the
lines the agent changed would the tests notice?

## The measure, borrowed

Mutants come from **Cosmic Ray 8.7.0**, through `core.strength.engines.cosmic`, the
generator the product already uses, confined to the patch's changed lines (`build-on.md`
names Cosmic Ray; the B7 spike's own header says not to promote it). Each mutant is
judged like the vacuity probe judges the revert (`eval/heldout_vacuity.py`): the task's
interpreter and environment, the task's whole test directory, tests already failing on
the agent's patched tree deselected, `-x`; killed on a new failure, an error exit or a
timeout.

Checked on six real patches before writing this: one-line and data-only changes give
no mutant at all (string and constant edits are outside Cosmic Ray's operators), and
the generator also mutates the rest of the enclosing function (`changed_function`).

For each graded, resolved run of the four-arm sweep:

- the agent's whole patch on the base tree; its changed lines in non-test `.py` files;
- up to 16 Cosmic Ray candidates, in its own order; the first 8 whose relevance is
  `changed_lines` are run; enclosing-function candidates are not run;
- **score** = killed / run. A run with no `changed_lines` candidate is `no mutant`,
  counted per arm and not scored.

## Analysis (fixed now)

- **Primary:** per task and arm, the mean score over scored runs; the five pairs of the
  four-arm study, two-sided signed-rank over tasks where both arms of the pair have a
  scored run, Holm-adjusted together.
- **Secondary:** per arm, the pooled share of mutants killed and the count of `no mutant`
  runs; October's two arms the same way, descriptive.

## Bounds

A surviving mutant can be equivalent (behaves as the original), so a score is a lower
bound on pinning. Operators are Cosmic Ray's; string and data changes go unmeasured,
and so do runs whose change has none. Eight mutants per run is a sample.
