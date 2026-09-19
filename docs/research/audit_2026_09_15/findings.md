# Literature audit, 2026-09-15: the thesis is right, the placement was not

**Method.** Five parallel research passes plus a direct read, all against public
sources. No paid agent runs, no new measurement. The question asked was the one
the user posed: *are we doing something wrong, and are we heading where we meant
to go?*

**Scope.** Coding-agent reliability, evaluation integrity, long-horizon failure,
specification failure, and the market for verification tooling. Roughly 260
searches and fetches across the five passes.

Every source is in [sources.md](sources.md) with what it contributed and how
strongly it was verified. Consequences are in `PLAN.md` v0.8; the narrative is
[journey/29-outside.md](../../../journey/29-outside.md) and
[journey/30-reaimed.md](../../../journey/30-reaimed.md).

---

## 1. The premise is stronger than when the project started

| | |
|---|---|
| **66%** name *"AI solutions that are almost right, but not quite"* as their top frustration | Stack Overflow 2025, n=31,476 |
| **96%** do not fully trust AI-generated code; **48%** always verify it | Sonar 2026, n=1,100+ (vendor) |
| **89%** of organisations have had an AI-related production incident; **25%** a full outage | Qodo/Censuswide, n=500 (vendor) |
| **57.9%** of agent failures are epistemic; **30.7%** are false premises | 1,184 hand-annotated trajectories |
| **22.6%** of real-session failures are *inaccurate self-reporting*, against **17.8%** faulty implementation | 20,574 sessions |

The largest independent developer survey in the field names this project's
failure class as the number one frustration. The founding thesis — that "done"
asserted by the model is the problem — is not merely intact, it is the
best-evidenced claim in the repository.

## 2. What we got wrong: the question, not the premise

The gate asks whether evidence **exists** and is **current**. Three independent
findings say that is the wrong question.

- **46.0% of positive agent validation evidence carries no bug-discriminating
  information**; 23.8% of rollouts close on an entirely non-discriminating
  basis. (3,730 validation events, 643 rollouts, 110 tasks.)
- **77% of SWE-bench Verified instances admit a semantically incorrect patch
  that passes every existing test.**
- Across model families, **every model saturates the visible test suite**, and
  the visible-to-held-out gap grows about **27pp per tenfold increase in LOC**.

`PASS` and `FRESH` are two facts about a record and neither is the one that
matters. **A check is not evidence until it is shown to discriminate.** This is
now PLAN §5.10.

**We had written the answer.** PLAN §5.0, 2026-09-12: *"revert the candidate's
source change and confirm the new test goes red."* Applied to our own test
suite; never to the product's check.

## 3. What we got wrong: where the mechanism acts

- Median decisive error at **step 7** of a median **27**.
- Median recovery window: **one step**.
- Observable failure signals appear about **ten steps later** — an observability
  lag in which a run is doomed and looks healthy.
- **82%** of failed runs keep executing after recovery becomes impossible.
- Best real-time prefix monitor: **28.8% recall**.

A Stop hook sits at the far end of that lag by construction. Our own result —
four blocks across nineteen runs changing no outcome — is what this predicts.

And detection would not have been enough anyway: *accurate failure prediction
does not imply effective failure prevention*, with harm concentrating in early
interruptions of runs that would have succeeded. We produced that result before
reading it, as a 6.6x false block.

## 4. What we under-valued: the obligation we already had

Holding the agent fixed and injecting one oracle signal at a time from a 35%
baseline:

| Signal | Resolve | Delta |
|---|---|---|
| **Reproduction test** | 63% | **+28pp** |
| Execution context | 50% | +15pp |
| API usage | 44% | +9pp |
| Perfect localisation | 43% | +8pp |
| Regression test | 37% | +2pp |

`core/obligations.py:149` has named *"that test failed before the fix"* since
M1, and collects it at Stop — the moment it is worth least.

**And it closes §2 at the same time: a test observed red before and green after
is discriminating by construction.** The field's largest measured lever and the
answer to the 46% are the same artifact.

Two corrections follow from the same table. **Localisation is not the
bottleneck** (+8pp, and agents already pick the right file 72-81% of the time
even in failures). And **execution during repair is not the lever** — across
7,745 traces, prohibiting it costs 1.25pp, not significant. It is not about
running tests; it is about having the right test.

## 5. What the field has caught up on

Stale-on-edit and no-evidence-no-close now ship elsewhere (WorktreeProof,
Critique, agentwatch; EviBound in academia). The README's claim that none of the
fourteen computes completion from evidence was true at their pinned commits on
2026-09-09 and is no longer a description of the field.

**None of them closes the discrimination gap either.** Every one gates on
evidence existing and being current.

## 6. Our exposure finding, corroborated at scale

An audit of 731 trajectories found **63% of successful Opus 4.8 Max resolutions
on SWE-bench Pro retrieved rather than derived the fix** (57% upstream lookup,
9% git history). Locking down drops Opus 87.1% → 73.0% and Composer 74.7% →
54.0%, with the gap *larger* for newer models.

Two corrections to our own plan:

- **pip has no flag that forbids VCS requirements.** No configuration closes it.
- **A registry allowlist is not a closed book** — PyPI serves the upstream
  project's own post-fix releases. This is an unpatched hole in published
  designs, not only ours.

The decision: `--network none` plus a pre-staged wheelhouse, with a canary probe
that must be **found with the boundary off and absent with it on**.

## 7. Negative results now held with evidence rather than judgement

| Deferred | Evidence |
|---|---|
| Always-on context files | Two independent populations: null on correctness, **+20% cost** |
| Role-decomposed multi-agent | A single agent running the same workflow matched or beat it across 7 benchmarks at ~1/10 the cost |
| Cross-session memory | Best-controlled study: no held-out contrast survives Holm correction |
| Spec-driven frameworks | **No controlled evidence exists** that Spec Kit, BMAD or Kiro improve task success |
| `cannot_complete` as free | Abstention prompting raised correct abstention 60→80% while collapsing partial-fix repair 27.3% → 6% |
| Naive "write tests first" | Raised test-level regression **6.08% → 9.94%** |

The spec-driven finding is the uncomfortable one: it is the same absence this
project criticised the fourteen for, and it applies at the front of the pipeline
as well as the back.

## 8. Our instrument is 6.2 points optimistic

> **Corrected 2026-09-19: it is 6.4, and the heading is left as written because
> this file is a record of what was concluded on 2026-09-15.** The source was
> graded *(snippet)* here, and reading
> [the HTML](https://arxiv.org/html/2503.15223v2) shows two of its three figures
> verbatim and the third wrong: *"inflates the resolution rates of the studied
> tools by 6.4 absolute percent points, on average."* This is precisely the
> failure `sources.md` exists to prevent, and it survived four days in the plan.
>
> The reading of it was also too strong, and that is the larger correction. An
> *absolute* inflation of reported scores is not a noise floor on a *paired*
> comparison: equal bias partly cancels between arms, and differential bias
> could reverse a large apparent effect. See PLAN §10.

Differential testing of plausible SWE-bench Verified patches: **29.6% diverge
behaviourally from ground truth**, **7.8% count as correct while failing the
developer test suite**, and resolution rates are **inflated by 6.2 absolute
points**. No claim may be made here on a delta smaller than that.

## 9. The method correction that mattered most

v0.8's first draft ranked work by what was *still unclaimed*. That is the
novelty filter this repository retired in v0.7, returning under a new name. The
correction, from the user:

> it was never the idea to come up with something new, idea was always to use
> their work, their findings, why re invent the wheel.

[build-on.md](../build-on.md) now names prior art, licence and limit for every
v0.8 component before its design. The checkpoint store is Cline's, the
revert-and-recheck loop is SWE-agent's, reproduce-first is Superpowers', the
when-to-ask rule is BMAD's, bounded clarify is Spec Kit's, the repository map is
Aider's, the `--no-verify` block is ECC's.

**The clearest argument for reading both literatures.** A 2026 paper warns that
*a saved state is not necessarily a suitable place to resume* and that task
success cannot detect a bad recovery decision. Cline's compare-and-swap restore,
which refuses when HEAD moved underneath it, is that eligibility check already
shipped. Neither the papers alone nor the source-read alone finds it.

## 10. A method defect found in this audit itself

Two arXiv PDF fetches returned **fabricated numbers** — one produced a complete
table of per-model half-lives that appears nowhere in the cited paper. Nothing
fabricated reached the plan, because the subagent doing that pass flagged it.

Standing rule added: prefer `arxiv.org/html/` or `/abs/` over `/pdf/`, grade
every source **(html)** or **(snippet)**, and let no snippet-grade figure be
quoted as established. Applied throughout [sources.md](sources.md).

---

## What changed as a result

| Change | Where |
|---|---|
| Discrimination becomes a standing requirement | PLAN §5.10 |
| Intervene where the error is, not where the symptom is | PLAN §5.11 |
| Detection and intervention separately justified; default to record, not refuse | PLAN §5.12 |
| The reproduction test becomes the highest-value artifact | PLAN §5.13 |
| Compaction treated as lossy in a direction that targets us | PLAN §5.14 |
| Combine first, invent last | PLAN §1.5, §5.15, [build-on.md](../build-on.md) |
| `--network none` plus wheelhouse, with a canary that must flip | PLAN §4.1 |
| Six claims withdrawn or qualified | PLAN §10 |
| Three $0 measurements ahead of any spend | PLAN Phase B2 |
