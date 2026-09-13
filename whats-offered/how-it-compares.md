# How it compares

[← What's Offered](README.md)

Fourteen agent systems were cloned, pinned to a commit, and read from source before a line of this runtime was written. Not the READMEs — the source: where the loop exits, what is enforced in code versus merely requested in a prompt, where each one is genuinely excellent and where it quietly gives up.

The full study is in [`docs/research/`](../docs/research/), with every claim cited to a file at a recorded commit. This page is the summary, and it is written to be fair rather than flattering — **every one of these systems is better engineered than this project, most are years older, and this borrowed from all of them.**

---

## Where each one is strong, and where it stops

| | Where it's genuinely great | Where it stops |
|---|---|---|
| **Aider** | the best repository map in the field — tree-sitter tags, symbol graph, personalized PageRank, budgeted render | tests are off by default |
| **Continue** | a real index: FTS5 trigrams, embeddings, collapsed-AST chunks, incremental | done = the loop ended |
| **Cline** | checkpoints that survive anything — three-parent stashes in private refs | no verification mechanism at all |
| **OpenCode** | the message list *is* the state machine; resume, fork and revert fall out for free | done = finish reason |
| **OpenHands** | append-only event log, condensers, resumes cleanly after anything | done = the model stopped |
| **SWE-agent** | full queryable trajectories, revert-on-lint | the patch *is* the deliverable |
| **mini** | 190 lines, one `bash` tool, a score that embarrasses scaffolds ten times its size | that's rather the point |
| **Agentless** | no agent at all — 40 candidates, execution-based selection, majority vote | hard-wired to one benchmark, one language |
| **AutoCodeRover** | an AST-aware search API a model can actually aim | not open source; ideas only |
| **gstack** | evidence bound to a working-tree hash — the closest thing to a contract anyone ships | exactly one declared command |
| **Superpowers** | real discipline: TDD, file handoff, a ledger that survives compaction | enforced by prose — its own `CLAUDE.md` admits agents ignore the rules |
| **ECC** | hooks that fire whether or not the model cooperates; a shell classifier that catches `sh -c` bypasses | 21–23k tokens loaded before you type anything |
| **Spec Kit** | one template source rendered to 41 hosts; exit-code prerequisite gates | a completion checklist it ticks itself |
| **BMAD** | blind review — reviewers see the diff, never the author's story | prose, plus a finding floor that guarantees noise on tiny diffs |

---

## The pattern

Read fourteen in a row and one shape appears in every one:

> ### "Done" means the model said so, or the model stopped.

One of the fourteen binds a single declared command to a tree hash. **None computes completion from evidence.** None ships tooling for intermittent bugs. Nine of ten enforce their process through text the model is free to ignore — and three admit it in their own repositories.

---

## Where this is genuinely ahead, today

Four claims, each with what backs it.

**1. Completion is computed, not asserted.** Typed claims, obligations that scale with risk, evidence parsed automatically from tool output, and four honest states including `UNVERIFIED`. The nearest prior art is gstack's verify-gate, which binds one declared command to a tree hash — real, and a starting point this built from rather than a competitor.

**2. Evidence expires.** Records are fingerprinted against what they observed, so editing a file invalidates the tests that covered it. Nothing else in the field does this. The mechanism is not invented — Test Impact Analysis has tracked test-to-source dependencies in industry for years — but nobody had pointed it at agent completion.

**3. Intermittent bugs get arithmetic.** A repeat runner that derives its own run count from the measured failure rate. **No cover at all** in the survey: every card's hard-task trace ends with the race analysis left to the model.

**4. The seam is tested.** `ep-doctor` checks that the runtime still hears the host, because three defects in that layer each failed by doing nothing while every unit test passed. No surveyed system tests its own host integration.

---

## Where this is behind — plainly

Being fair costs nothing and lying costs everything, so:

| | Who does it better, and by a lot |
|---|---|
| **Repository understanding** | Aider and Continue. This has none — no index, no symbol graph, no blast radius. Aider's map is Apache-2.0 and portable, and borrowing it is on the roadmap rather than reinventing it |
| **Checkpointing and recovery** | Cline and OpenCode. Three-parent stashes, side-gitdir snapshots, revert — this has nothing comparable |
| **Long-horizon state** | OpenHands' event log, OpenCode's message-list state machine. This does not resume the way they do |
| **Maturity and breadth** | all of them. Weeks against years, one host against many, one author against communities |
| **Candidate generation** | Agentless generates 40 and selects by execution. This generates none — Phase C |
| **Security engineering** | gstack, by a wide margin: nonce-bound instruction blocks, egress receipts, redaction, untrusted envelopes |

---

## The method, which is the actual contribution

The survey was not a feature checklist. Each system was read to separate what it enforces in **code** from what it merely requests in **prose**, then every strength was mapped against every weakness to see which system's strength covers which other system's weakness. Whatever remained uncovered by all fourteen was the only honest place to build something new.

That produced ten residual gaps, in [`complementarity-matrix.md`](../docs/research/complementarity-matrix.md). This runtime attacks three of them: process-stage gates enforced by code, typed claims with risk-scaled evidence contracts, and tooling for intermittent bugs.

The other seven are open, documented, and available to anyone who wants them.

---

## The claim this page will not make

That any of this makes a coding agent measurably better.

Twelve real bugs, gate against plain agent: **identical outcomes on all twelve, at 1.4× the cost.** That result stands. It is why the plan changed — the evidence layer is now understood as something valuable *inside* a stronger search-and-selection system, rather than as an independent oracle that decides done.

So the honest comparison is:

- **Against the fourteen on verification mechanism** — this is ahead, and that is a narrow, defensible claim about a mechanism.
- **Against the fourteen on making agents better** — unproven, and the project says so on its own front page.

Phases C and D exist to close that gap or to kill the idea. [What would falsify it](roadmap.md#what-would-falsify-this-whole-direction) is written down in advance, which is the only time it is worth writing down.

---

## If you maintain one of these fourteen

The card on your system is pinned to a commit and every claim cites a file. If I have misread your code, please open an issue — I would much rather be corrected than cited wrongly, and a correction from you is worth more than anything I could re-derive myself.

**[satyambcnrk@gmail.com](mailto:satyambcnrk@gmail.com)** · [issues](https://github.com/SatyamSingh-Git/ElevenPowers/issues)
