# 40 — The assumption nobody ran

*2026-09-17 into 2026-09-18. Four commits that had no entry, and the pattern
underneath all of them.*

This entry exists partly because it was overdue. Four commits shipped without
one — the dirty-tree attribution fix, the nine-language proof, the turbo defect
and the de-naming pass — and the omission was the user's to point out, in a
repository whose own standing rule is to record what was tried and what was
wrong. Writing about discipline while skipping it is its own data point.

---

## What those four commits were

**A task that edited one file was credited with four.** `touched` came from
`git status`, so every already-uncommitted path a developer had in flight was
attributed to whatever they asked next. It inflated the risk tier, demanded
obligations for untouched code, and handed `radius.py` a blast radius computed
from somebody else's half-finished work. The ledger now records what was dirty
at task open and subtracts it.

**Four of nine languages were wrong.** Go attaches methods by receiver at the
top level and lost every one. Rust named the *trait* as the owner of an `impl`
block, which would have grouped siblings by the wrong thing entirely. PHP calls
its identifiers `name` and so dropped every base class. C# read nothing at all,
because the grammar is `csharp` and the table said `c_sharp` — the error
handling degraded to silence exactly as designed, and that is what hid it.
Bigger than any of those: only *classes* were read, so a functional TypeScript
file produced no symbols at all, and most TypeScript is functional.

**`turbo test` produced no records, and hid a failing package behind a passing
one.** It prefixes every line with the package it came from, and the TAP
patterns anchored hard at the line start. Behind that, the counts were
overwritten rather than summed, so a failing package followed by a passing one
reported `fail 0` — a red monorepo laundered into a green record. R10 arriving
by a new road, in code written *because* R10 had taught that lesson once.

**And the tool stopped naming a private project.** Four references gone. Two
over-fits found while checking: a line prefix fixed at the shape of the one
runner that had been looked at, and an import-graph cap of 1200 files sized from
Python's `ast` at 6ms a module when tree-sitter measures 3.8 — so a 1,700-file
TypeScript repository blew past a limit set for a different parser and the
feature silently did nothing on exactly the kind of repository it was built for.

---

## One shape, seven times

| assumption | how it was found |
|---|---|
| TAP counter format | ran `node --test`, looked |
| turbo's line prefix | ran `turbo test`, looked |
| Go methods nest inside their type | ran the parser, looked |
| Rust `impl Trait for Type` names the type first | ran the parser, looked |
| the C# grammar is called `c_sharp` | ran the parser, looked |
| a module costs ~6ms to parse | measured; it was 3.8 |
| turbo is the only prefix shape | looked at a second runner |

**Zero** were found by thinking harder. Every one surfaced the moment the real
producer was executed and its real output read.

Three other habits, all the same family:

- **A written rule was ignored.** The heredoc-backslash note exists, is in
  memory, and was violated **eight times in one day** — once inside the
  paragraph describing it, leaving a literal `0x08` in a sentence about a
  literal `0x08`.
- **Six probes passed for the wrong reason.** Only flipping them exposed it. A
  test that cannot fail is worse than no test, because it reports confidence.
- **Code was fitted to the single example that had been looked at.** Twice.

## Why "be more careful" is not the fix

Because it has been measured, and it does not work.

This is **API Knowledge Conflict** — 20.41% of hallucinations in the largest
taxonomy of the phenomenon (Zhang, Wang, Wang, Chen & Zheng,
[arXiv:2409.20550](https://arxiv.org/abs/2409.20550), 1,380 annotated snippets;
Task Requirement Conflicts 43.53%, Factual Knowledge Conflicts 31.91%, Project
Context Conflicts 24.56%).

And the obvious remedy barely moves: their own retrieval-augmented mitigation
improved Pass@1 by **0.87 to 3.05 percentage points**. Worse for the "just read
the docs" instinct:

> *"Documentation mainly helps models identify **what** APIs to use and remains
> insufficient for teaching **how** to use them correctly. Even with **oracle**
> API-document retrieval, LLMs still make recurring errors."*

So the fix is not more context, and it is not a better instruction — §5.14
already says constraint violation rises 0% to 78% across four compaction rounds.
What works is **execution**: grounding generation in execution feedback moved
pass@1 from ~70% to 89% ([RLEF, arXiv:2410.02089](https://arxiv.org/abs/2410.02089)).

Which is this project's whole thesis, pointed at a target it had never aimed at:
*a claim is not evidence until something ran*. It had been applied to the
agent's claims about its work, and never to the developer's claims about the
world.

## What shipped

`core/assumptions.py`, two rules the ledger can answer:

> **A pattern this task introduced, which never matched any output this task
> actually saw, is an assumption nobody verified.**

> **A test this task added, which passes on the tree as it was, did not test
> this change.**

Neither asks the agent anything. The runtime already watched every command and
kept what it printed, and `stress.py` already knew which tests were red on the
base commit. Both questions were answerable all along and nobody asked them.

The report says, at the end of the run:

```
unverified: '^\s*#\s*(pass|fail)\s+\d+\s*$' matched nothing this task ran.
A pattern is a claim about output; run the thing and look
```

## The forward control caught the checker

Both forward tests failed first. The patterns are written with `^` and `$` and
compiled with `re.MULTILINE` in real code; the checker matched without it, so a
pattern that *had* been confirmed was reported as unverified. That is the one
error this must never make — a check that accuses correct work is how the gate
once blocked 75% of runs.

And flipping found **two more vacuous probes**, in the module built to detect
vacuous probes. One guard did nothing and was removed; one was real but no test
reached the state it protects, so a test was written that does.

## What it does not catch, said now

- **Non-regex assumptions.** `"c_sharp"` was a plain string in a lookup table.
  This would not have caught it, and four of the seven above are of that kind.
- **A pattern confirmed in an earlier session.** The ledger is per task.
- **Running the command without reading the output.** Necessary, not sufficient
  — though it is the step that was skipped every single time here.

Half the family is now machine-checked. The other half is still a habit, and
habits decay; that is the honest state and it is written here rather than
implied to be solved.
