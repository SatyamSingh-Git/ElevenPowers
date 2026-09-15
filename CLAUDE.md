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

A stale node is worse than a missing one. The Workflow tab's third lane is
labelled *planned, NOT built* — when one of those lands, move it out.

## Three rules this project learned expensively

**Test both directions, and conclude from four states.** *(PLAN §5.0)* Every
check runs forward — the legitimate case is accepted, the rule still fires —
and adversarially — the system actively tries to defeat its own check. A check
that survives none is not evidence; one that survives all by refusing
everything is not evidence either. Every narrowing fix ships a control
asserting the rule still fires.

**A probe must be seen to flip.** A regression test is not evidence until it has
been watched failing before the fix and passing after. Fixing R6 without a
forward control would have looked exactly like reverting the work that cut
blocking from 75% of runs to 12%.

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
python -m pytest -q                      # 513 tests, ~6 minutes
python -m pytest tests/test_audit_probes.py -q   # every reproduced defect, no xfails
python plugin/bin/ep_doctor.py --host    # is the runtime seeing what the host sends?
python architecture/check.py --render    # is the graph still true, and does it draw?
```

Paid evaluation runs cost real money and are never started without asking.
