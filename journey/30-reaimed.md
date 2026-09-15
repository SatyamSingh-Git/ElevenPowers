# 30. The plan already contained the answer, twice

Five parallel research passes, no paid runs, one day. The result is `PLAN.md`
v0.8, and the thing worth recording is not any single finding. It is that **the
two highest-value interventions in the 2026 literature were already written in
v0.7 and neither had been built.**

§5.0, 2026-09-12: *"revert the candidate's source change and confirm the new
test goes red; mutate the patch and confirm something notices."* That is
mutation testing, and it is the answer to the discrimination problem below. It
was applied to this project's own test suite and never to the product's check.

§5.6, same revision: *"a long attempt ends at its latest patch, not its best."*
That is the ratchet, and it is the intervention with the largest measured
recovery in the field.

The plan was not wrong. It was unexecuted, and the unexecuted parts were the
ones that mattered.

## The number that re-aimed everything

The gate asks whether evidence exists and is current. Someone measured what
that misses:

> **46.0% of positive validation evidence carries no bug-discriminating
> information.** 23.8% of rollouts close with an entirely non-discriminating
> evidence base. A further 26.9% of bug-detecting tests fail on the developer's
> own correct fix.

3,730 validation events, 643 rollouts, 110 tasks — and the best methodology in
the whole sweep, with a prespecified smallest effect size declared before
measuring. Alongside it: **77% of SWE-bench Verified instances admit a
semantically incorrect patch that passes every existing test.**

So `PASS` and `FRESH` are two facts about a record and neither is the one that
matters. This is entry 29's finding with a number on it, and the number is
large enough that it reorganises the plan rather than qualifying it.

**The honest correction to entry 29:** P22 is no longer ours to discover. What
`Phase B2.1` buys is the figure for *our own ledger*, which is still the only
way to know whether what we ship is inside that 46% or outside it.

**And the obvious repair does not work.** The same study fed the contrast back
to the agent and reported it against its own threshold: −7.8pp evidence-
inadequate closures, +7.4pp discriminating evidence, **both below the 10pp
smallest effect size declared in advance.** Detecting vacuity is established.
Fixing it by telling the agent is not. Which is the same shape as our own four
blocks that changed nothing, arriving from a completely different direction.

## The receipt was the artifact all along

`core/obligations.py:149` has said *"that test failed before the fix"* since M1.
Held the agent fixed, injected one oracle signal at a time from a 35% baseline:

| Signal | Resolve | Delta |
|---|---|---|
| **reproduction test** | 63% | **+28pp** |
| execution context | 50% | +15pp |
| perfect localisation | 43% | +8pp |
| regression test | 37% | +2pp |

We ask for the +28pp artifact **at Stop**, which is the moment it is worth
least. And a test seen red before and green after is **discriminating by
construction** — so the largest measured lever in the field and the answer to
the 46% are the same object.

Two corrections fall out of the same table. Localisation, which §5.2 treated as
a principal bottleneck, is worth 8pp — and across 7,745 traces, *prohibiting*
execution during repair costs **1.25pp, not significant**. It was never about
running tests. It is about having the right test.

## Why the gate changed nothing, in one sentence

Across 1,184 failed trajectories: **median decisive error at step 7 of 27**,
median recovery window **one step**, observable signals about **ten steps
later**, and **82% of doomed runs keep executing** past the point of no return.

A Stop hook sits at the far end of that lag by construction. Entry 28 explained
the null by corpus difficulty. That was half of it. The other half is that the
mechanism fires roughly twenty steps after the die was cast.

The same paper puts **57.9% of failures in the epistemic class, with false
premises at 30.7%** — the largest single category, and the exact thing the
thesis was written to catch. And 48 implementations against one specification,
a million inputs: **429 coincident failures against 115 predicted under
independence, z = 29.20.** Agents converge on the same misreading. Voting
cannot touch a shared false premise. A reproduction test can.

**So the thesis is right and better supported than it has ever been.
"Computed" was implemented as "collected."**

## What was withdrawn, and one thing that was restored

Withdrawn: that fresh passing evidence establishes an obligation is met; that
localisation is a principal bottleneck; that free execution during repair is
what grounds the work; that a gate detecting a real defect will improve the
outcome; that our benchmark can resolve a few points — it over-reports by
**6.2**; and that none of the surveyed systems computes completion from
evidence, which was true on 2026-09-09 and is not a description of the field
now.

Also withdrawn, and this one is uncomfortable: **there is no controlled
evidence that spec-driven frameworks improve agent task success.** Not for Spec
Kit, BMAD or Kiro. A survey paper says plainly that no peer-reviewed study has
defined, delimited or measured them. That is the same absence this project
criticised the fourteen for, and honesty requires recording it at the front of
the pipeline as well as the back.

Restored: **§2**, which v0.7 demoted. It is now the best-supported claim here.

## What it cost to learn, against what the sweeps cost

$0, and one day. Against $195 across two paid sweeps that bought a diagnosis.

That is not an argument that reading beats measuring — the reading only became
legible *because* the sweeps produced a null that needed explaining. But it is
worth noticing that the answer to "why did nothing change" was available in
public, and that the two things worth building next were in our own plan.

The next experiment costs nothing either. `results/` holds over a hundred paid
runs with candidates, bases and grades preserved since entry 20. Asking how
many of our passing records also pass on the reverted tree needs no agent, no
API and no money — only the discipline to run the control in both directions.

## A correction to this entry, the same day

The section above ends by naming what is "unclaimed" — discrimination and the
ratchet. That framing was wrong, and it was corrected immediately:

> it was never the idea to come up with something new, idea was always to use
> their work, their findings, why re invent the wheel.

Which is what [complementarity-matrix.md](../docs/research/complementarity-matrix.md)
has said since 2026-09-09: its purpose is to map each system's weakness onto
another's strength, and its §7 says outright that ideas with prior art *"must be
cited and built on rather than reinvented."* The matrix was written for v0.7's
architecture. v0.8's three builds never got the same treatment, and the gap
showed up as novelty language.

[build-on.md](../docs/research/build-on.md) fixes it. Every v0.8 component now
names its prior art, licence and limit before its design. The checkpoint store
is **Cline's**, the revert-and-recheck loop is **SWE-agent's**, reproduce-first
is **Superpowers'**, the when-to-ask rule is **BMAD's**, bounded clarify is
**Spec Kit's**, the repository map is **Aider's**, the `--no-verify` block is
**ECC's**, and the mutation engines already exist.

**The best thing reading both halves produced.** The recoverability paper's
warning is that a saved state may be an unsuitable place to resume, and that
task success cannot detect a bad recovery decision. **Cline had already shipped the answer** — a compare-and-swap restore that refuses when HEAD
moved underneath it, which is an eligibility check on the restore rather than a
check on its outcome. A paper named the gap; a product read from source in this repo's own survey had closed it.
Neither half alone gets you there, and that is the whole argument for doing both.

What is left as ours is three things, and the list is short on purpose:
invalidation as an *economic* mechanism rather than a correctness detail,
discrimination as a stored fact, and obligations that survive compaction.

---

*The audit this entry summarises is
[docs/research/audit_2026_09_15/findings.md](../docs/research/audit_2026_09_15/findings.md);
every source is credited in
[sources.md](../docs/research/audit_2026_09_15/sources.md), and the borrowing
map is [build-on.md](../docs/research/build-on.md).*
