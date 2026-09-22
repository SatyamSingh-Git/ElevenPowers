# 42 — The thing nobody recorded

*2026-09-22. Four items left open from the audit, and an adversarial pass over
the fixes that closed the others.*

The previous entry ended with a list headed *"still not done, and I'm not going
to claim otherwise"*. This is that list, plus the part that came first: going
back over the fixes already shipped and asking where they stop working, rather
than whether they work.

---

## The pass over my own fixes found four more

Not by reading them. By running them against shapes nobody had tried.

| probe | what it showed |
|---|---|
| `scrub_values` on a tuple | **not scrubbed at all** — and `json.dumps` writes a tuple out as an array, so it reaches the file exactly as a list would |
| `scrub` on `https://user:pass@host` | **untouched** — the way a credential reaches a git remote, a `pip install` line and half the CI logs in existence |
| `_targeted` on `pytest -rA` | emitted `-rA -rA`; harmless, verified against real pytest, still sloppy |
| `runs_tap("npx prove t/")` | **False** — a legitimate harness one word behind a launcher |

The first is the same defect as the two before it, in a third form. *Which
fields hold text* was wrong twice; this is *which types hold text*. The fix each
time was to stop choosing: scrubbing happens at the write boundary, over every
string in the structure, whatever shape it is in.

---

## F7 — a bounded store was claiming to be a complete one

The check says **"matched nothing this task ran"**. That sentence is only true
if everything the task ran is still there, and the store is bounded twice over:
twelve commands, head-and-tail within each. A pattern matching a discarded
middle is reported as unverified on the strength of a gap.

The bound stays — an unbounded store is a different and worse problem. What
changed is that the record now counts what fell out of it and the sentence
carries it:

```
unverified: '^ok \d+' matched nothing this task ran. A pattern is a claim
about output; run the thing and look - though this record is partial
(1 earlier output(s) evicted, 2 truncated), so it cannot rule out a match
```

It still cannot tell you whether the missing text would have matched. It can
stop implying it could.

---

## F12 — and the dimension that was recorded nowhere

The audit said *a directory name is not sufficient experimental provenance*. The
fix looked obvious: key pools on what the manifest records — model asked for,
time limits, task environment — instead of on the folder.

Then it was run against `results/closedbook`, this repository's standing example
of a different experiment, quoted in `eval/pool.py`'s own docstring as *"a
different condition by construction"*.

```
bundles-A    claude-sonnet-5|agent=900|suite=900|env=PYTHONPATH=src
chunks       claude-sonnet-5|agent=900|suite=900|env=PYTHONPATH=src
closedbook   claude-sonnet-5|agent=900|suite=900|env=PYTHONPATH=src
```

**Identical.** What made closedbook different was what the run could *reach*,
and no manifest recorded it — not in `env`, not in `environment`, which holds
only tool versions. The `PIP_NO_INDEX` that shut the registry was set on a
subprocess and written down nowhere.

So the audit was more right than it knew: the directory name was not *sufficient*
provenance, it was the **only** provenance, and no fingerprint can recover it for
bundles already written.

What shipped: runs from now on record an `access` block, and existing bundles
read `access=unrecorded` — which is treated as **distinct from `open`**, because
nobody writing it down is not a measurement. Pooling them is now labelled:

```
UNVERIFIABLE POOL: ALL POOLED / vanilla joins 3 sweeps whose bundles do not
record what each run could reach. They agree on model, limits and task
environment, and that is not enough - `results/closedbook` agrees on all
three and is a different experiment.
```

No published figure changes. What changes is that a paragraph naming one folder
by hand has been replaced by something that would also catch the sweep somebody
adds next year.

---

## R1 — the numbers were right; the benchmark was the problem

Three figures had been carried for a week without being read. All three are
verbatim correct (arXiv 2607.17531): **+8.14pp at 0/2089 = 0% harm** for
public-test execution, **+3.50pp while harming 98/2089 = 4.69%** of
first-sample-correct cases for a same-family LLM judge, and *"the oracle gap is
only 18/594 = 3.03pp"* where every selector went net-negative.

**The first two are LiveCodeBench. The third is GPQA-Diamond.**

So the "below four points, do not build a selector" line — which this plan used
as grounds to cancel a phase — was imported from a **multiple-choice science
benchmark**, while the same paper's **coding** benchmark is exactly where
execution-based selection posted its best result, at zero harm.

That does not make selection a good idea here; the rescued-minus-damaged mass is
still unmeasured on this corpus. It does mean the number was pointing the wrong
way, and that reading the paper was worth more than three re-readings of the
sentence quoting it.

---

## §6 — the half that was missing was attribution

Most of the audit's boundary section was already answered honestly in PLAN
§4.1, which says plainly that tool denial *"closes the doors it names and a
package manager walks through the wall"*.

One part was not. Regrades are kept side by side — `b4-passA.json` beside
`b4-passA-regraded.json` — but `grade.json` recorded **nothing about which
grader produced a verdict**. So an outcome that changed between passes could not
be attributed to a changed grader rather than a changed candidate.

It now carries a content fingerprint of the grading code. Content, not a version
string, for the same reason evidence carries a tree hash: a hand-maintained
number is a claim about the code, and a hash is a measurement of it.

Writing it produced one more instance of the running theme. The first version
fingerprinted `grade.py`, which **does not exist** — grading lives in `live.py`.
It would have silently covered less than it claimed. Caught by listing the
directory, which is the whole trick and always has been.

---

## The tally

Nine fixes, nine probes watched red with the fix removed and green with it
restored. One of the nine had no guard at all until the flip run said so — the
`npx prove` case passed with the fix deleted, because the forward test only
covered runners that never needed it.

Five defects found today, every one by running something against a shape nobody
had tried: a tuple, a URL, a doubled flag, a launcher prefix, and a filename
that was never there.
