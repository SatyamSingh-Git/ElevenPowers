# 59 — A roadmap contributors can open

2026-10-04.

The request was for another view beside architecture, workflow and data flow:
small boxes for everything planned but unfinished, expanding to explain exactly
what a contributor could help build. It also invited useful additional ideas.

The existing viewer had four tabs, and its Workflow introduction still called
the third lane unbuilt even though that lane's mechanisms had shipped. A new
roadmap could have repeated the same mistake by treating old planning prose as
current delivery status.

The fifth tab, **Planned**, therefore separates four kinds of unfinished work:

- 3 **open milestones**: an independently checked useful intervention, full
  installed-host acceptance and representative normal-session overhead.
- 17 **planned research** items: remaining measurements and experiments for
  discrimination, containment, strong baselines, edit-level proven states,
  candidate selection, reproduction, repair, early lock-in and compute allocation.
- 14 **conditional extensions**: per-test invalidation, dynamic coverage,
  workflow/context/memory/routing, additional critics, expanded evaluation,
  browser evidence, state/child replay, property checks, differential behavior
  and probing unchanged dependencies. Each keeps its documented trigger.
- 7 **proposals**: ImpactGraph, PatchProof, OpenCodeMap, TestMiner, verification
  across development milestones, CI evidence import with provenance and a
  reusable contributor exercise kit.

The four named capabilities came from the previous architecture discussion.
The remaining three proposals are additions for contributors to discuss.
Publishing a proposal does not approve its implementation, spend or correctness
claim. Everything still has to work across projects.

Each card explains why the work matters, what remains, what counts as done,
a small first contribution, prerequisites where relevant and the repository
sources behind it. Search covers the full card, and topic/status filters combine.
Native `details` elements make cards expandable by mouse or keyboard. Several
can stay open, and a `#planned/<id>` link opens a particular card directly.
The viewer remains self-contained; source links load GitHub only when chosen.

`architecture/check.py` first failed with **missing contributor roadmap data**
and **planned tab is missing**. After implementation it checks the JSON's
required fields, stable ids, dependency references, conditional triggers and
source-file existence, then exercises the actual page. The existing four views
still render. The fifth has checks for expansion/collapse, search and empty
results, topic/status filters, direct links, theme retention and narrow layout.
Visual inspection also exposed the old theme toggle's first click keeping the
initial dark theme when the operating system preferred light; that mismatch was
corrected and the actual first light transition is now checked.

Independent read-only review reproduced a filtered prerequisite link that did
nothing when its destination already matched the URL, and measured insufficient
contrast for small green/amber text in light mode. The same-hash link now opens
the target and clears its hiding filter, navigation moves keyboard focus to its
summary, and light-mode card text uses darker colors. The browser check includes
that exact link sequence and computes at least 4.5:1 contrast for small card
badges and links. Review also found the missing P26 lock-in entry; its addition
brings the final total to **41 cards**. It distinguishes prefix-only detection
from separately justified interruption policies.

The current graph remains **107 nodes and 246 edges**. No proposed component was
added as if it were real runtime code. The graph mirror is regenerated from the
live HTML, and the README, readable roadmap, master-plan entry, postponed notes
and status link back to the contributor view. A contradictory old Python-only
radius paragraph now agrees with the shipped optional polyglot implementation.

This delivery makes the remaining work easier to find and assess. It does not
change the existing four tied review comparisons, establish a coding advantage,
close installed acceptance or launch new model sessions.
