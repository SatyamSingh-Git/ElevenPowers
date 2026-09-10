# Proof-or-Stop (arXiv 2607.14890)

Read 2026-09-10 from `https://arxiv.org/html/2607.14890v1`. Found while looking
for how the field builds discriminating task suites, not while looking for prior
art, which is how prior art is usually found.

**This is the closest work to this project's thesis, and it is closer than
anything in the original fourteen.**

## What it does

The spine is `Actor output -> Claim -> Evidence -> Gate -> Lifecycle transition`.
Agent output is treated as a claim requiring structured evidence before any
consequential transition (review, test, done, merge). The gate advances on
admissible evidence, loops for bounded retry when evidence is incomplete, or
stops.

That is the same spine as this project, arrived at independently and published
first.

## The part that overlaps most

Evidence is bound to source state through a `materialHash` (SHA256 over the
tracked source tree), a `headHash` (commit identity), and a `storyFilesHash`,
with `policyHash` and `commandSetHash` alongside. The freshness rule is explicit:

> "evidence produced against an earlier source state is rejected the instant the
> source tree changes, because materialHash_E != materialHash(H)"

This project's `Evidence.freshness` does the same thing with a stat-based tree
hash and a git-status tie-breaker. **The invalidation mechanism this project
treated as its distinguishing feature is published prior art.**

They also name the failure mode this project was built around:

> "an unattended coding agent can generate the code, retry until a visible check
> turns green, and narrate completion in the same workflow that will be asked to
> advance the work"

## What is measured, and how

Primary endpoint: **visible-pass/hidden-fail amplification** — work shipped
despite passing the visible tests. That is exactly the structure of this
project's task suites, independently arrived at, which is reassuring about the
instrument and unflattering about the novelty.

Powered ablation: 9,240 cells over 24 tasks.

| arm | amplified |
|---|---|
| Proof-or-Stop | 2/1800 (0.11%) |
| compute-budgeted naive retry | 31/1800 (1.72%) |

Effect +1.6pp, 95% CI [0.8, 2.5], excluding zero. Cost about 1.2x tokens and
1.5x wall clock against the retry baseline.

## What is still different here

Stated narrowly, because the overlap is large.

- **Granularity of invalidation.** `materialHash` is a whole-tree hash, so any
  edit invalidates everything. That is this project's coarse tier, and the
  planned static test-impact tier (M3) would be finer. Unbuilt, so it is a plan
  rather than a difference today.
- **Attestation versus inference.** Their admissibility requires signatures,
  digest chains, producer authorisation and execution attestation, which is a
  governance posture. This project infers claims from ordinary intent and
  captures evidence by parsing tool output the agent already produced, with no
  cooperation required from the agent and nothing for a user to adopt.
- **Process footprint.** Theirs assumes a lifecycle with stories and policies.
  This attaches to an existing agent and prescribes no process.

## What it costs this project

The bounded novelty claim in PLAN.md section 11 does not survive. "Obligations
derived from inferred intent, discharged by automatically captured evidence,
invalidated by repository change, gating completion" is now found prior art in
all but the automatic-capture and no-process parts.

## What it gives this project

- The endpoint has a name and published comparators: visible-pass/hidden-fail
  amplification, 1.72% for naive retry.
- Base rates are small, so effects are small: 9,240 cells for a CI that excludes
  zero. This corroborates the 252-runs-per-comparison estimate rather than
  contradicting it, and argues for task suites engineered to raise the base rate.
- Their cost figures (1.2x tokens, 1.5x time) sit just below the 1.4x to 2.5x
  measured here, which is a useful sanity check on both.
