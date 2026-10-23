# 90 — nothing better was left behind

Journey 89 ended with 240 runs paid for and graded. Two questions in the
experiment queue had waited since Phase B2 for data that could answer them, and
that sweep was the data. Both were asked for nothing.

## The oracle gap, again, on tasks nobody here chose

Journey 31 found the gap unsettled: +2 to +20 points across comparable pools,
produced entirely by the one to five tasks whose attempts disagreed. `eval.pool`
read bundles; the held-out sweep keeps one record per slot in `collected.json`, so
the pool now reads that too. Three runs per arm, 40 tasks:

| arm | coverage | random pick | gap | disagreeing tasks |
|---|---|---|---|---|
| ordinary | 80.0% | 73.3% | +6.7 | 5 |
| assisted | 80.0% | 75.8% | +4.2 | 3 |

The same shape as before. The gap sits near the four-point reference line and is
made by three to five tasks. Still not settled.

Counting success as resolved *and* not VACUOUS (`--pinned`) gives the reading
worth keeping: a perfect selector over three ordinary runs finds a tested fix on
17.5% of tasks, and a blind pick from the assisted runs on 47.5%. Choosing among
more ordinary attempts does not get you what the assisted arm writes.

## A better state left behind, at edit granularity

B2.3 asked whether a run ever held something better than it submitted. The saved
bundles recorded candidates only at proposed stops, and the phase wrote down in
advance that the effect, if any, should live at single edits. That stayed
unanswerable until now: the sweep kept each run's host transcript, and the
transcript records every Edit and Write in full.

`eval/heldout_checkpoints.py` rebuilds the base tree, applies the edits that
succeeded in order, and grades every distinct state the way the final patch was
graded. A replay counts only if its last state is the submitted patch. That check
did its job twice before anything was graded:

- **90 of 238 runs edited through the shell.** `sed -i`, `cat > file`, a Python
  heredoc. Zero recorded edits and a non-empty patch is not a parser bug; the
  first one inspected was `sed` rewriting a default in `uvicorn/config.py`. Those
  runs are reported as not replayable, never graded from a guess.
- **Five assisted runs differed only in line endings.** Each ran `git stash` and
  `stash pop`, which under autocrlf writes whole files back with CRLF. Same
  content, different bytes; accepted as a match and labelled as one.

Then the first launch died on its first state: `materialise` writes the task's
archive beside the tree it builds, and the per-state scratch folder did not exist.
A test pins it now.

**One run in 85 passed through a better state than it submitted** —
`cachetools-bcf9e817--ordinary--1`, resolved untested and then regressed. On these
tasks a ratchet back to the best earlier state would have almost nothing to do.

The by-product is the mechanism behind journey 89. Of assisted runs that finished
resolved and tested, 34 resolved untested first and wrote the test afterwards;
ordinary runs did that 4 times. The fix comes first in both arms. What differs is
that one arm keeps going.

## What bounds both

Descriptive, not pre-registered, one model, small fixes. The replayable runs are
the ones that edited through the editor tools, a selected subset. Neither reading
says anything about tasks that take more than a few edits.

*Reproduce: `python -m eval.pool --from-bundles
results/heldout/sweep-2026-10-22/collected.json [--pinned]` and `python -m
eval.heldout_checkpoints --sweep results/heldout/sweep-2026-10-22 --corpus
results/heldout/corpus.json --out <journal>`.*
