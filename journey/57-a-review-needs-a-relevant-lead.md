# 57 — A review needs a relevant lead

2026-10-02. The previous comparisons had a working gate and no completed ordinary
patch for it to correct. Making four tasks harder produced three complete ties.
The next question was narrower: can the optional test-strength observations
help a reviewer add useful tests beyond an equally funded ordinary review?

Four already-correct upstream changes supplied real public contracts. We kept
production, existing tests and configuration fixed, then permitted only new test
files. ItsDangerous, Click and Jinja2 had historical sampled survivors; attrs
served as a preservation control. Each received one ordinary and one assisted
Claude Sonnet 5 medium subscription call, with alternating order and eight-minute
caps. All eight completed; no model call was repeated to seek a better outcome.

The important improvement is real but shared. Jinja2's original suite noticed
two of seven frozen changed-line faults. Both reviewers added behavioral tests
that noticed all seven, including all five previously missed faults that two
earlier blind model reviewers had called meaningful. Original behavior stayed
green and a cosmetic formatting control stayed accepted. Reading the additions
found attribute/item separation, undefined values, dynamic attributes and sandbox
behavior checks, rather than assertions about source spelling.

That earns a test-quality improvement for review. It earns no incremental
ElevenPowers advantage: the other three pairs also tied. Assisted native review
time exceeded ordinary review time in each selected pair, and mutation analysis
adds local work outside those review caps. These observations establish no
speedup, production repair or population effect.

Two qualifications changed how the numbers should be read. Click's two historical
dual-rater meaningful survivor faults concern descriptor capture, which is
unsupported on Windows. Added FD tests skipped here. An earlier semantic label
cannot make that behavior exercised on this machine. And the shipping engine
samples whole changed files in producer order. Jinja2's 32-attempt focused scan
never reached its edited `do_attr` function; its surviving observations concerned
earlier unrelated functions. attrs' single surviving lead concerned `attrib`,
not the changed ClassVar helper. A focused security suite can also miss behavior
that the full suite already covers. Leads need a relationship to the actual edit
and an honest command-coverage qualification before they deserve another review.

The evaluator itself needed correction. A traceback containing `1 failed` was
credited as detection despite collection exit 2. Long pytest summaries could lose
counts. Original `.claude` inputs were omitted from sealing. Saved slot budgets,
native model evidence and grades needed stronger validation, and an absent
formatting control passed a vacuous `all()` check. Each concrete regression was
seen failing and then passing. Actual submissions stayed sealed and all observed
native model lists were exact. A separate corrected-grader regrade was started,
then stopped when the user asked to conclude. Its full reproduction remains
unfinished; the original frozen producer hashes and grades remain historical.

At the 2026-10-02 stop, the next build was relevant evidence for any repository: prioritize
changed functions/hunks, report the relationship between a lead and the edit,
and qualify focused-command coverage. Keep engine bounds and incomplete states,
avoid raw mutant targets, and use free relevance controls before another model
comparison. A new comparison should use held-out active behavioral gaps and
retain every unchanged or adverse result. More features do not replace that
exit criterion. Further implementation and model calls wait for the next session.

Resumed on 2026-10-03: all twelve corrected grade sets completed, with three
explicit Click F03 setup corrections and nine exact matches. The generalized
relevance milestone is now delivered; no additional model sessions ran. The
original stopped-session account above remains historical. See
[journey 58](58-the-lead-must-belong-to-the-edit.md) for the implementation,
actual relevance samples and the still-open benefit exit.

See the [design](../docs/design/checkpoint-review-pilot.md),
[measured record](../docs/validation/2026-10-02-checkpoint-review.md),
[saved archive](../docs/validation/2026-10-02-checkpoint-review/README.md) and
[implementation provenance](../docs/research/checkpoint-review.md).
