# `ep_review --functions` on real changes ($0, 2026-11-22)

[`rehearse.py`](rehearse.py), [JSON](rehearsal.json).
Design: [spec](../../docs/superpowers/specs/2026-11-22-review-functions-design.md).

Six recent fix commits of charset_normalizer (each with its own tests),
each reviewed against its parent, in the project's prepared environment
(coverage.py 7.16.2), with `PYTHONPATH=src`.

## What the first run found

Two of the six said `baseline timed_out`. The review gave TestMiner its
overall budget but not its time per run, so TestMiner kept its own 15 s
default, and this suite under coverage takes longer. TestMiner now gets
the review's `--timeout` (82d9dc0). The message also said neither how long
it waited nor what to raise; it now does, and tells a per-run limit apart
from the overall budget (cc2a84d).

## Second run

| commit | review verdict | functions the change touched |
|---|---|---|
| 3985662 output encoding cache | pinned (2 tests) | `CharsetMatch.output`: checked (`None`, `b''`, `b'A'`) |
| 45dc0e3 UTF-8 declarations | pinned (10) | `CharsetMatch.output`: checked |
| 8e8f8c7 GB18030 signature | pinned (4) | `CharsetMatch.__str__`: checked (`None`, `''`, `'A'`) |
| f9f92be ASCII whitespace | pinned (19) | `CharInfo.__init__`: unknown (`__init__` cannot be emptied) |
| 3c560f1 language names | pinned (4) | `filter_alt_coherence_matches`: checked (`None`) |
| e52699e CLI exit status | pinned (8) | none: the change is module-level `if __name__ == "__main__":` code |

The last two were checked by hand against the diffs: f9f92be changes only
`CharInfo.__init__`, and e52699e only the two `__main__` guards.

## Reading

No false alarms on six well-tested fixes, which is what a reviewer needs
from a section that runs on every change they ask about. It found no
unchecked function here either; that says nothing about how often it
catches one. The reviewer's report has one project and six commits behind
this: an illustration, not a rate.

The reviewer's checkout was left as it was (no state file, no leftover
worktree).
