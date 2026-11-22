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

## On agent-made changes from the held-out sweep

[`agents.py`](agents.py), [JSON](rehearsal_agents.json). The first
ordinary-arm run of every held-out task whose environment has coverage.py
and which the sweep graded resolved: 14 runs on charset_normalizer,
oauthlib, pyjwt and uvicorn. The agent's work is committed on top of the
seed in a copy and reviewed against the seed.

| | runs |
|---|---|
| review verdict NOT PINNED | 12 |
| PINNED | 1 |
| UNKNOWN (uvicorn's suite disagreed with itself) | 1 |
| functions section not measured (uvicorn's pytest addopts run parallel workers; the message says to pass `-n 0`) | 4 |
| functions section measured | 10 |
| a function listed (`partly checked`) | 1 |
| the agent changed only functions that are `checked` | 6 |
| the agent changed no function | 3 |

The one listed function was checked by hand. charset_normalizer-017c75c2
added an empty-payload guard to `CharsetMatch.multi_byte_usage`
(`-> float`). It is used only in `__lt__`'s tie-break,
`self.multi_byte_usage > other.multi_byte_usage`, so returning a constant
`0.0` or `1.0` makes every comparison tie and no test notices; only
`None` is noticed, because comparing it raises. Its value is unchecked.

### What this shows about the instrument

Nine of the ten measured changes were NOT PINNED, yet the functions
section listed one. That is not a contradiction: those functions were
already tested as a whole before the agent touched them, so emptying them
fails tests, while the agent's edit inside them is what nothing pins.
Function-level extreme mutation finds untested *functions*; it does not
find an untested *edit* inside a tested one. For that, the review's
verdict (whole change undone) and `--strength` (line mutations) are the
instruments. Ten agent changes on three projects: an illustration, not a
rate.
