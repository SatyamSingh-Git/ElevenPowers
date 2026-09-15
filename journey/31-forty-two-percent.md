# 31. Forty-two percent of the passing evidence was not passing

Phase B2, the first experiment this project ever ran for nothing. No agent, no
API, no money — a hundred and more runs were bought months ago and their ledgers
were still on disk.

It set out to ask §5.10's question: *of the checks we recorded as passing, how
many would have passed anyway?* It never got there, because it hit a prior
question first.

## The defect

`core/parsers.py`, deciding a suite record:

```python
result=Result.PASS if exit_code == 0 else Result.FAIL,
```

Two lines above, the same function parses `passed` and `failed` out of the
runner's own summary. Then it ignores them.

A shell pipeline exits with the status of its **last** command. So:

```
python -m pytest tests -q 2>&1 | tail -80
```

returns `tail`'s zero however pytest finished.

**288 of the 295 passing suite records in `results/` were run through exactly
that shape.** Agents pipe to `tail` because suite output is enormous and they
are being careful with context. It is a sensible habit, and it silently
destroyed the signal.

> **123 of 295 passing suite records — 42 percent — say `PASS` while holding a
> non-zero failure count.** The worst reads `failed=87, passed=1339`.

Eighty-seven failing tests, recorded as a passing suite.

## The family it belongs to

R5 established that *a completed process* and *an executed test* are different
facts — `echo pytest` exits zero and contains a runner's name. The fix added
`counted`, so a record now knows whether it counted tests and looked.

This is the third fact in the same family: **an executed test and a *passing*
test are also different things.** The record counted correctly. It looked
correctly. Then the verdict was taken from somewhere else entirely.

R5 is why the counts were sitting right there, unused, for the decision to
ignore. Getting closer to a defect is not the same as closing it.

## How it was found, which is the part worth copying

Not by reasoning, and not by a test. By printing two sample records while
building something else, and noticing that one of them said `'result': 'pass'`
next to `'failed': 2`.

Everything after that was arithmetic on data already on disk. **The corrected
result is a pure function of the preserved counts**, so the whole history could
be re-derived without re-running a single test — which is the entire reason
Phase B2 was free, and a direct dividend of [entry 20](20-reconstructible.md)
making runs survive their workspaces.

## Both directions, before the fix

The probe went in first and was watched failing:

```
assert suite[0].result is Result.FAIL
E  assert <Result.PASS: 'pass'> is <Result.FAIL: 'fail'>
```

Then a control, because the lazy fix is *treat anything piped as failed* and
that would delete the feature rather than repair it: a genuinely green suite
behind the same pipe must still be recorded green.

The fix is one clause — a counted failure outranks the exit code, and the exit
code still decides when nothing could be counted, because an unrecognised runner
is exactly the case that rule is for. Probe passed, control held, 515 tests
green.

## What it did to the record, and what that does not prove

**61 percent of gated runs — 43 of 70 — carry at least one falsely-passing
suite record.** And the outcome split is striking:

| | n | outcomes |
|---|---|---|
| carried one | 43 | resolved 36, unfixed 5, regressed 1, setup 1 |
| carried none | 27 | resolved 27 |

Every run that failed carried one. None of the clean runs failed.

**That is not evidence the defect caused the failures, and it must not be read
that way.** Affected runs ran a median of **five** suite records against **two**
for unaffected ones. A run that never ran a failing suite cannot exhibit this
defect, and a run in trouble runs more suites looking for the trouble. Exposure
is confounded with difficulty, and the arrow may point entirely the other way:
failing → more suites → more chances to hit it.

`eval/discriminate.py` prints that confound directly under the table rather than
in a footnote, because the table is the tempting thing to quote.

What *is* established, without any causal claim: **for 43 runs, the obligation
"the related test suite passes" could be satisfied by a suite that did not
pass.** Those runs were not measuring what their ledger says they measured.

One row is worth naming. `click-c2ed4149`, `regressed` — the single regression
[entry 28](28-nothing-changed.md) recorded the gate meeting and letting through
— carried **three** falsely-passing suite records. Suggestive, not proof, and
subject to exactly the confound above. But entry 28 called that pass-through
unexplained, and it is less unexplained now.

## The other half of B2

`eval/pool.py` answered B2.2, the question with the power to cancel Phase C:
what is our oracle gap, and is it above the four-point line below which measured
selectors do more harm than good?

**It does not settle it.** Comparable pools give +2.0, +4.0, +4.4 and +20.0
points. The `mixed` column says why: the gap is produced *entirely* by tasks
whose attempts disagree, and there are between one and five of those per pool.

The sharpest version of it — the same fifteen tasks, three replicates each, two
passes of one sweep:

| | coverage | random pick | gap | tasks whose attempts disagree |
|---|---|---|---|---|
| pass A | 73.3% | 68.9% | **+4.4** | 1 |
| pass B | 93.3% | 73.3% | **+20.0** | 5 |

Same tasks. Same corpus. The entire difference is **three tasks that went 0/3 in
one pass and 1/3 in the other** — five single lucky runs.

So the oracle gap here is not a property of the pool. It is a measurement of
per-run flakiness on a handful of tasks, at a sample size where that is noise.
Phase C is not cancelled and not justified; the question is simply not answered,
and saying so is cheaper than picking whichever number suits.

There is a sharper reading underneath. On this corpus, "select the best
candidate" mostly means "notice the one run in three that happened to work" —
and running the tests already does that. The selection problem worth solving is
choosing between candidates that *all* pass the visible tests, which is §5.10's
discrimination problem wearing a different hat. The two halves of B2 turn out to
be the same question.

## What B2 cost and what it bought

$0, one sitting. Against $195 for the two sweeps that bought a diagnosis.

It bought a reproduced soundness defect with a probe and a fix, a corrected
census of 295 records, an honest non-answer on the oracle gap, and a confound
stated in the output rather than discovered later by somebody else.

The §5.10 question it set out to ask is still open, and now it is askable:
**of the records that really did pass, how many would have passed with the
change reverted?** That needs execution against the base tree rather than
arithmetic on saved counts. The repositories are cached at their base commits
and `eval/live.py` already knows how to build one.

---

*Reproduce with `python -m eval.discriminate --bundles results --verbose` and
`python -m eval.pool --from-bundles results/chunks results/bundles-A
results/bundles-B`. Both outputs are preserved in
[`results/b2/`](../results/b2/).*
