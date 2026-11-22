# 106 — The signature that never runs

*2026-11-22. `ep_review --functions` and `--strength` on real changes
([results](../results/review-functions/README.md)).*

The reviewer's report gained a section yesterday: TestMiner's verdicts for
the Python functions a change touched. Before calling it useful, it was
run on real changes, at $0: six maintainer fixes of charset_normalizer,
then nine agent changes from the held-out sweep.

## Two faults, found by running it

- **TestMiner kept its own 15 s per run.** The review passed its overall
  budget but not `--timeout`, and charset_normalizer's suite under
  coverage takes longer, so 2 of 6 reviews said `baseline timed_out`. That
  message named neither the limit nor the flag; now it does, and tells the
  per-run limit from the overall budget apart.
- **An interpreter that could not start was reported as "coverage.py not
  importable, install it".** A Git Bash `/e/...` path inside `--command`
  cannot start on Windows. The report now names the interpreter.

## What function-level verdicts can and cannot see

On the agent changes, eight of nine measured were NOT PINNED: undoing the
change is noticed by nothing. The functions section listed one function.
That is not a contradiction. The agents edited functions their tests
already check as a whole, so emptying them fails tests; what nothing pins
is the edit inside. The one it listed was real: `multi_byte_usage` feeds
only a tie-break comparison, so any constant passes every test.

## The finding that mattered more

`--strength` was run on the same changes to compare. On two pyjwt changes
nearly every survivor was the same thing: Cosmic Ray had turned
`key: str | bytes` into `str + bytes`. Both files start with
`from __future__ import annotations`, so that line never runs, the mutant
survives whatever the tests do, and the reviewer was told the signature
was a line no test noticed. This had shipped in `--strength` since it was
built. Positions inside argument and return annotations are now skipped;
those two changes went from 8 and 11 survivors to 2 and 1, all in real
code.

A variable's annotation was going to be skipped too, until the producer
was run without that branch: Cosmic Ray 8.7.0 makes no operator mutant
there at all. The branch was removed rather than kept looking
load-bearing.

## Bounds

One project's maintainers, nine agent changes on three projects; no rate.
Line mutation is a sample (20 mutants) and most of these runs ended at
that cap.
