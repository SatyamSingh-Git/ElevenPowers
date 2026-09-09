# The journey

A full record of how this project got from a prompt to a working thing: what was
asked, what was tried, what was wrong, what the measurements said, and what
changed as a result.

It is written so that someone who was not here can reconstruct the reasoning,
including the parts that were mistaken. Every number quoted was produced by a
command in this repository and can be reproduced.

## Read in order

| File | Covers |
|---|---|
| [01-origins.md](01-origins.md) | The original brief, the first plan written from memory, and why that was the wrong way to start |
| [02-research.md](02-research.md) | Reading fourteen systems from source: method, what each one actually does, and the findings that overturned assumptions |
| [03-architecture.md](03-architecture.md) | Two rewrites of the plan, the pivot from classifying tasks to deriving proof obligations, and what the thing actually is |
| [04-build.md](04-build.md) | Building the first working version, and the three defects that only appeared when it was used |
| [05-measurement.md](05-measurement.md) | Measuring the gate as a classifier: 75 percent false blocks, every fix, and the honest limits of the result |
| [06-intermittency.md](06-intermittency.md) | The flaky-bug gap: a false verification found by reasoning, and the arithmetic that decides how many clean runs are enough |
| [decisions.md](decisions.md) | Every significant decision, its reasoning, and whether it still stands |
| [mistakes.md](mistakes.md) | Every mistake made, what caused it, and what it changed |

## The shape of it, in one page

**The ask.** Build an agentic software engineering system that makes existing
coding agents measurably better, without being another collection of prompts.
Research first, challenge everything, measure, discard weak ideas.

**First attempt, and its flaw.** A 522-line plan was written in about an hour
from recollection of the named projects. It was well organised and largely
unfounded: no repository had been read. Asked directly whether it was the best
possible plan, the honest answer was no, and the reasons were specific.

**Research.** Fourteen systems were cloned and read from source at recorded
commits, with three host extension surfaces documented and the 2026 literature
checked. About 3,000 lines of cited notes. Several assumptions did not survive:
the benchmark everyone quotes is saturated, published work already measures the
problem this project targets, and the mechanism the design needs is standard
industrial practice under a different name.

**The pivot.** An external critique argued the project was becoming a research
laboratory rather than a product, and proposed deriving the workflow backwards
from what would prove the work. That survived scrutiny, and for a better reason
than the one given: obligations are stable while plans are contingent. Adopting
it made the system smaller, not larger.

**What it became.** Not a framework, an agent, or a harness. The closest
analogue is `make`. Evidence is bound to the state of the files it observed, so
editing a file invalidates it the way a build system invalidates an object file.
Completion stops being something the model asserts and becomes something the
runtime computes.

**Building it.** About 1,400 lines, working end to end on a real repository on
day one rather than week four. Three defects appeared immediately, and none of
them would have been found by testing: they only showed up when the whole cycle
ran in order.

**Measuring it.** The gate is a classifier, so it was measured as one. The first
honest measurement was a 75 percent false-block rate: the tool would have been
uninstalled within an hour. Nine fixes later it is zero on 42 scenarios,
including twelve written afterwards specifically to break it. That number is
real but narrow, and [05-measurement.md](05-measurement.md) says exactly what it
does not prove.

**The flaky-bug gap.** A seventh core piece had been listed and never built, and
its absence let one lucky run satisfy "repeated runs are stable", which is a
false verification on the exact task class the project claims as its
differentiator. Building it raised a better question than the runner itself: how
many clean runs are enough. That has an arithmetic answer, computed from the
failure rate the agent measures while reproducing the bug.

## The one thing worth taking away

Two measurements changed the design more than any amount of reasoning did.

The 75 percent false-block rate turned an elegant idea into an obviously
unusable one in a single command, and every fix that followed came from asking
why a specific case failed rather than from thinking harder about the
architecture.

The held-out set mattered just as much. After tuning, the score on the original
scenarios was zero. On twelve fresh ones written to break it, the same code
scored 43 percent. Without that second set the project would have believed a
number that was three-quarters overfitting.
