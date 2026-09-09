# 2. Reading the field

## Method

Fourteen systems were cloned and read from source. Reading a README does not
count as research, so each study followed the same procedure:

1. Clone at a specific commit, record the commit, date, licence, language and
   file count.
2. Read the code that decides what text reaches the model: prompt files, skill
   and agent definitions, hook scripts, context assembly.
3. Count tokens with `wc -w` rather than estimating: what is loaded on every
   turn, what is loaded on demand.
4. Trace two requests through the control flow by reading, not running: a
   trivial change (a button's border radius) and a hard one (an intermittent
   authentication race).
5. Fill a twelve-question card, citing a file path for every claim, marking
   inferences as inferences.
6. Record licence obligations for anything reusable.

Fourteen studies ran in parallel, one agent each. Three host extension surfaces
were documented the same way. The output is about 3,000 lines in
`docs/research/`, where every claim traces to a file at a recorded commit.

## What each system turned out to be

| System | The thing it actually does well | What it cannot do |
|---|---|---|
| Superpowers | Process discipline as instruction text, plus scripts that pass task briefs and diffs to subagents by path so the controller's context stays clean. A plan-scoped ledger exists specifically to survive compaction | No enforcement at all. Its own instructions file admits agents ignore its rules |
| Everything Claude Code | The most serious hook engineering in the field: profile gating, pass-through on error, atomic writes, batched checks at stop time | Loads roughly 21 to 23k tokens on every turn, including descriptions for skills about energy procurement and customs compliance |
| Spec Kit | One template source rendered to 41 hosts, and prerequisite gates that are shell exit codes | No task-size triage. A one-line CSS change gets user stories and a checklist the agent grades itself |
| gstack | Evidence bound to a working-tree hash and graded fresh, stale or missing. The closest thing in the field to this project's core idea | 12 to 28k tokens per skill invocation, with a 6.5k preamble repeated in every one |
| BMAD | Review ordering that resists self-confirmation: reviewers see only the diff, and the change's own narrative reaches one lens last | Three near-identical copies of its pipeline, already drifting. A reviewer with a mandatory finding floor |
| Aider | A real repository model: tree-sitter symbols, a reference graph, personalized PageRank, budgeted rendering | No investigation loop. Hard tasks reduce to guessing from signatures |
| OpenCode | A permission engine that parses shell commands with tree-sitter, and snapshots in a side git directory | Done means the model stopped calling tools |
| Cline | Checkpoints as three-parent stash commits in private refs, with a compare-and-swap restore that refuses when HEAD moved | No repository understanding beyond regex. Auto-approve on by default in the CLI |
| Continue | Content-addressed incremental indexing shared by four artifacts, and a chunker that keeps class skeletons | Two divergent agent loops. Retrieval stages shipped commented out |
| SWE-agent | Tool bundles as self-describing directories, and edits reverted when they introduce new lint errors | Python-only guardrails. No context management beyond truncation |
| mini-SWE-agent | 190 lines, one bash tool, messages are the trajectory. Reported above 74 percent on SWE-bench Verified | Nothing else, deliberately |
| OpenHands | Condensation as a tombstone event over an immutable log, cut only at points the provider's message shape allows | Summaries built from 500-character previews. Its stuck detector halts on deliberate test re-runs |
| Agentless | A fixed pipeline that beats agent loops on its task class, at about a third of a dollar per issue | Python only, and wired to one benchmark |
| AutoCodeRover | A grounded bug-location contract: file, class, method, intended behaviour, re-resolved to line ranges | Its licence is source-available, not open source, so ideas only |

## The findings that changed the plan

**The benchmark everyone quotes is saturated.** Frontier models cluster at 95 to
97 percent on SWE-bench Verified across four leaderboards, and reporting says an
audit found widespread flawed tests and gold-patch memorization. Continuing to
target it would have measured nothing. The suite moved to SWE-bench Pro,
SWE-rebench and Terminal-Bench.

**The problem this project targets is already measured.** A 2026 study of 1,750
trajectories found one model submitting a patch on every run and resolving 44
percent of them, with silent semantic failures accounting for 68 to 80 percent
of failures, and found that pre-edit prompting did not fix it. That gave the
headline metric a real definition and, more importantly, external evidence that
prompting is the wrong instrument.

**Instruction files cost more than they return.** A study across models and
agents found repository context files raised inference cost by more than 20
percent on average while model-written ones lowered success by about 3 percent.
One of the studied frameworks, BMAD, cites this work as its reason for retiring
its own repository-scanning skills.

**Portability is far cheaper than assumed.** v0.1 budgeted five weeks for
adapters. In fact Codex, Gemini CLI, Cline's CLI and Continue's CLI all ship
Claude-Code-shaped hooks, and Codex's hook engine struct is literally named after
them. Only OpenCode lacks a way to block session end.

**Nine of ten enforce process with text.** And three admit it in their own
repositories. Spec Kit's "mandatory hooks" are executed by the model reading a
YAML block and emitting a command line, while the code that would run them
returns metadata only.

**The humility constraint.** mini-SWE-agent reports above 74 percent with 190
lines and one tool, and its authors now recommend it over their own full
harness. Any added complexity has to beat that.

## The complementarity matrix

Because the user's stated first goal was combining strengths, the research
produced `docs/research/complementarity-matrix.md`, which does that mapping
explicitly rather than by assertion.

Every strength is tagged by how it is enforced: code, protocol, or prose. That
distinction turned out to be the most useful thing in the document, because a
prose strength composes for free and can be ignored for free, while a code
strength costs integration work and cannot be ignored.

Sixteen weakness classes were identified, each mapped to whichever system's
strength covers it, with a coverage rating. Ten gaps survived that mapping, and
those ten became the only places new architecture was justified. The largest:
every gate in the field is tool-level, so nothing can enforce "reproduce before
editing" or "this claim needs this evidence"; and no system tracks that a
verification was invalidated by a later edit.

## What the research cost

Fourteen parallel agents, roughly three million tokens, about an hour of
wall-clock time. It replaced a plan built on recollection with one built on
citations, and it prevented at least four pieces of reinvention: the evidence
ledger, the compaction-surviving task state, the repository map, and blind review
ordering all already existed in some form.
