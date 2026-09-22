# Working on ElevenPowers

`PLAN.md` governs. `journey/` is the record of what was tried and what was
wrong. `docs/research/` is a source-read of fourteen agent systems at pinned
commits, plus the literature audits. Read those rather than re-deriving them.

## The architecture graph — standing instruction

> **After any work session that changes the architecture, data flow, or
> workflow, refresh [`architecture/`](architecture/) before finishing.**

Published at **<https://satyamsingh-git.github.io/ElevenPowers/architecture/>** (GitHub Pages, `main` / root).

`architecture/index.html` is the live source; `graph-data.js` is generated from
it. Edit the inlined `GRAPH` block and any affected structured view, bump
`meta.updated`, prepend a `meta.changelog` line, then:

```bash
python architecture/check.py --render
```

**Never skip `--render`.** Every structural check passed on a page that drew
nothing at all. [`architecture/README.md`](architecture/README.md) has the full
rule, including what does and does not count as an architecture change.

**This rule is no longer only a rule.** It was forgotten often enough to prove
the point it now makes: `core/atlas.py` computes it. A module this task added
that no map names is reported at the end of the run, and so is a document still
naming a path this task removed. `docs/design/` is documentation but is *not*
the map — writing about a module is not drawing it. The same check ships to
anyone using the plugin, against their repository's own architecture document.

A stale node is worse than a missing one. The Workflow tab's third lane is
labelled *planned, NOT built* — when one of those lands, move it out.

## Three rules this project learned expensively

**Test both directions, and conclude from four states.** *(PLAN §5.0 — the
single most productive rule in this repository.)* Every check runs forward —
the legitimate case is accepted, the rule still fires — and adversarially — the
system actively tries to defeat its own check. A check that survives none is not
evidence; one that survives all by refusing everything is not evidence either.

**This is not a habit to remember. It is enforced, and it is a product
feature.** Enforced: `test_every_runner_is_read_both_ways` asserts both
directions for every runner in one test, and a companion counts the dispatch
sites in the source so a new runner *cannot* be added with one direction. A
feature: the runtime runs its own checks both ways — forward, that the evidence
passes on the tree as it stands; adversarially, that it would not have passed
without the change.

Why it is enforced rather than trusted: R10 was fixed in one parser on
2026-09-15 and the identical defect sat in six siblings for the rest of that
hour, because one direction of one runner going green made the fix look done.
Nearly every defect this project has found was found by running both ways.

**A probe must be seen to flip.** A regression test is not evidence until it has
been watched failing before the fix and passing after. Fixing R6 without a
forward control would have looked exactly like reverting the work that cut
blocking from 75% of runs to 12%.

**Run the producer before you write the pattern.** Any claim about the *shape*
of something external — a runner's output, a parser's node names, a grammar's
spelling, a cost — is written **after** executing the real thing and reading
what came back, never from memory. On 2026-09-17 seven defects shipped in a day
and every one was of this kind; not one was found by thinking harder, and all
seven surfaced the instant the real producer was run.

This is not a local failing. It is **API Knowledge Conflict**, 20.41% of
hallucinations in the largest taxonomy of the phenomenon
([arXiv:2409.20550](https://arxiv.org/abs/2409.20550)), and the usual remedy is
measured to be nearly useless: retrieval-augmented mitigation moved Pass@1 by
**0.87–3.05pp**, and models misuse APIs *even with oracle documentation
retrieval*. Execution is what works.

So, like the rest: **enforced rather than trusted.** `core/assumptions.py`
reports a pattern this task introduced that never matched any output this task
actually ran, and a new test that passes on the tree as it was. Expect the
report to name your shortcuts — and note that it only covers patterns, so
non-regex assumptions like a misspelled grammar name are still yours to check by
running something.

**Borrow first, invent last.** *(PLAN §1.5, `docs/research/build-on.md`)* Every
component starts from the best existing implementation — named, with its licence
and its limit — and then states in one sentence what we add. If that sentence
cannot be written, the component is a reimplementation and the borrow wins.
Originality was never the goal.

## Numbers

Every figure published here carries the qualification that bounds it, and
anything withdrawn is listed in `PLAN.md` §10 rather than quietly deleted.
Sources are graded — prefer `arxiv.org/html/` or `/abs/` over `/pdf/`, because
PDF summarisers in this project's own audit fabricated numbers that do not exist
in the papers they were attributed to. See
`docs/research/audit_2026_09_15/sources.md`.

## Running things

```bash
python -m pytest -q                      # 794 tests, ~6 minutes
python -m pytest tests/test_audit_probes.py -q   # every reproduced defect, no xfails
python plugin/bin/ep_doctor.py --host    # is the runtime seeing what the host sends?
python architecture/check.py --render    # is the graph still true, and does it draw?
python -m eval.rehearse --corpus E:/ep-corpus/prevalence.json --tasks 16
```

**Run the rehearsal before spending anything.** It seeds all sixteen corpus
tasks at their real base commits, applies the gold patch and asks the runtime
the question a sweep would ask — **253 seconds, no agent, no money**. On
2026-09-22 it corrected two published figures in one sitting: a pytest node id
carrying shell metacharacters killed the confirmation command before pytest
started, and exit 1 is allowed through, so every selected test was credited as a
passing reproduction. And the harness never applied the task's declared
`PYTHONPATH`, so its checks imported the installed release instead of the
patched source, reporting 48 tests red on a base tree where the truth was 1.
Neither was caught by reading, by the suite, or by an external audit that
reproduced fourteen other probes. See `journey/43`.

Paid evaluation runs cost real money and are never started without asking.
**`claude-sonnet-5` at effort high** is the default model for them unless the
user says otherwise for that run, and the per-run `--budget` must match the
model — `$3.00` was sized for Sonnet and truncates most Opus runs mid-task,
which produces no evidence at all.

Size a sweep against **remaining capacity**, not against what the question
deserves: a 64-run, four-hour comparison was launched on 2026-09-17 with about
1% of the week left and had to be killed. State the estimated runs, wall time
and cost before starting. The next experiment worth running is planned and
**not yet run** in [`results/b6-paired/design.md`](results/b6-paired/design.md)
— read its warning before shrinking it, because the cheap version reintroduces
an error `PLAN.md` §10 has already withdrawn once.
