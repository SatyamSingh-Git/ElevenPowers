# 1. Origins

## The brief

The project began with [`00-brief.md`](00-brief.md), a long and deliberately
ambitious document, kept here in full because later plans are judged against it.
Its core instruction:

> Design and build a genuinely next-generation agentic software engineering
> system that can make existing coding agents dramatically more capable,
> reliable, intelligent, autonomous, efficient, adaptive, and useful.

It was explicit about what it did not want: not another prompt collection, not a
coding-agent wrapper, not a combination of existing open-source projects. It
named ten systems to study (Superpowers, Everything Claude Code, Spec Kit,
gstack, BMAD, Aider, OpenCode, Cline, Continue, SWE-agent) and set a test the
result had to pass:

> The end result should have a clear reason to exist even if projects such as
> [those] and future competing systems already exist.

It listed twenty areas to think about: task intelligence, workflow compilation,
context engineering, repository understanding, memory, agent routing, model
routing, evidence-based completion, adaptive verification, self-correction,
observability, failure recovery, security, provider independence, cost, and
evaluation. It insisted evaluations be first-class and that ideas be discarded
when measurement did not support them.

It also said, twice, that its own architecture suggestions should not be
preserved merely because they were mentioned.

The user's own framing, given separately, was more concrete: the first goal was
to combine the strengths of those repositories so that each one's weaknesses
would be covered by another's strengths.

## The first plan, and what was wrong with it

The first response produced `PLAN.md` v0.1: 522 lines covering research method,
a failure taxonomy, six competing architectures, an evaluation harness design,
an initial architecture, eighteen hypotheses, a prototype plan, and a
twenty-six week roadmap.

It looked thorough. It was built on air.

Not one of the fourteen repositories had been opened. Every statement about
Superpowers, Aider, Cline and the rest came from recollection. The plan marked
those claims with a "verify" tag, which was honest but insufficient: a plan
whose foundations are all marked unverified is not a plan, it is a
questionnaire.

Three specific failures, visible in hindsight:

**It designed before looking.** The architecture proposed an evidence ledger, a
task ledger surviving compaction, a repository model, and blind review ordering.
Every one of those already existed somewhere in the systems it had not read. The
design was reinventing rather than building on.

**It was shaped like a research programme.** Three weeks of evaluation
infrastructure before any code touched a repository. Nothing would have been
usable in the first month.

**Its statistics did not support its own decision rules.** It specified
confidence intervals excluding zero on three tasks per category with three runs
each. That design cannot produce those verdicts.

## The question that changed the direction

The user asked one question:

> so, are you sure, this plan of yours is the best possible plan, and will surely
> bring out something ambitious?

The honest answer was no, and the useful part was the specifics: stale priors,
defensive design that could delete every ambitious component and call it
discipline, statistics that did not match the claims, a fantasy timeline past
week ten, and portability weaker than claimed.

The user's reply set the standard for everything after:

> dont remember, use web and study them thoroughly, each and every one of them

That was correct, and it is the point at which the project actually started.

## What this cost, and what it bought

Writing v0.1 from memory cost about an hour and produced a document that had to
be replaced twice. But it was not wasted: it produced the scaffolding of
questions that the research then answered, and having a concrete wrong answer
made it much easier to see what the right one needed.

The lesson recorded in [mistakes.md](mistakes.md) is narrower than "do research
first". It is this: when a plan's every load-bearing claim carries a marker
saying it has not been checked, that is not a caveat. That is the finding, and
it should stop the work until it is resolved.
