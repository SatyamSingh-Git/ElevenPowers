# ElevenPowers: Master Plan

Version 0.1, written 2026-09-09.
Status: planning only. Nothing has been built. No third-party claim in this document has been re-verified against current sources; every statement about another system is a prior to be checked in Phase A.

---

## 0. How to use this document

- This is the execution plan for the brief in `prompt.md`. It is not the architecture. The architecture in Section 9 is a working hypothesis that this plan is designed to test and, where the evidence says so, dismantle.
- Sections are written to be loaded independently. A session working on Phase B needs Sections 1, 3, 6 and the failure taxonomy in Appendix E, nothing else. Do not feed the whole document to an agent that only needs one phase; that would violate the plan's own thesis.
- Every phase ends with a gate: a measurable condition plus a decision rule written before the work starts. Work does not pass a gate on impressions.
- Decisions made during execution go into ADRs (Section 14.4). This document is revised when a gate changes the plan; it is not a changelog.
- Anything marked **[verify]** is a belief from training data that must be confirmed against current sources before it is relied on.

Table of contents

1. Executive summary
2. Reading the brief: accepted, reframed, rejected
3. Operating principles
4. Milestone overview
5. Phase A: landscape research
6. Phase B: failure study and gap analysis
7. Phase C: paradigm questioning and competing architectures
8. Phase D: evaluation harness (built before the architecture)
9. Phase E: initial architecture, a working hypothesis
10. Hypotheses register
11. Minimal experimental prototype plan
12. Evidence-driven roadmap with gates
13. Attacking the plan
14. Project mechanics
15. Open questions and decisions owed
Appendices A to H

---

## 1. Executive summary

**What is being built.** A runtime that sits between a developer's request and an existing coding agent (Claude Code first, other hosts through adapters) and does four things the agent does not do for itself today:

1. Understands the task before work starts, producing a small task profile: scope, ambiguity, risk, knowledge gap, verification surface, parallelism.
2. Compiles a task-specific workflow from that profile instead of applying a fixed process (or none).
3. Assembles the smallest sufficient context for each stage from a tiered repository model and gated memory.
4. Refuses to accept "done" until an evidence contract sized to the risk has been discharged.

**The thesis.** The largest gains available today come not from better prompts or more agents, but from moving process control, task state, budgets, and verification out of the model's context window and into a deterministic runtime that the model works inside. The model does judgment. The runtime does bookkeeping, gating, budgeting, and proof. Roughly half of the system should be code the model cannot ignore.

**How success is measured.** A benchmark suite built before the architecture, run against vanilla Claude Code, Superpowers, Everything Claude Code, Spec Kit, Aider and OpenCode, measuring task success on hidden tests, false-success rate, regressions, scope discipline, tokens, cost, latency and human interventions. Every subsystem must show a measurable gain on that suite or be removed at the next gate.

**First four weeks.** Landscape research and failure-trace mining run in parallel with building the evaluation harness and a 30-task development set. No product code is written until baseline numbers are reproduced with confidence intervals. The first product code is a thin vertical slice (intake, five-template compiler, evidence gate, scope guard) on Claude Code, evaluated at week six.

**Primary risk.** Building infrastructure instead of learning. Mitigation: the harness has a ten-task smoke tier that runs in under an hour, and every milestone gate is an eval result, not a feature list.

---

## 2. Reading the brief: accepted, reframed, rejected

The brief explicitly permits rejecting its own assumptions. This section records where the plan follows it and where it departs, so that the departures are deliberate and reviewable.

### 2.1 Accepted without reservation

- Evaluations are first-class and come before architecture (Phase 19 of the brief becomes Phase D here, and runs second, not nineteenth).
- Complexity must earn its existence with a measurable result.
- Evidence over declaration: completion is a proof obligation, not a statement.
- Context is a scarce computational resource with a budget.
- Provider independence is a design constraint from day one, though not a day-one deliverable.
- The failure modes list in the brief is a good seed; it is treated as hypotheses about failures, to be confirmed by trace mining (Section 6).
- Attribution and license obligations are preserved; original abstractions are preferred.

### 2.2 Reframed

| The brief says | This plan does instead | Why |
|---|---|---|
| Twenty phases, presented sequentially | Six milestones, each an eval-gated research → build → measure loop (Section 12) | The twenty phases are concerns, not a schedule. Several must run concurrently or the eval harness arrives too late to shape anything. |
| A workflow compiler with optimization passes producing an execution plan | A compiler that emits a plan carrying explicit uncertainty and recompile triggers; closer to a JIT with deoptimization than to an ahead-of-time compiler | Real tasks are underspecified. A plan optimized at t=0 is wrong by minute five on hard tasks. Keep the intermediate representation (inspectable, diffable, host-independent) and drop the illusion that optimization is deterministic. |
| Twenty task dimensions | Six actionable dimensions, each tied to at least one downstream decision (Section 9.2) | A dimension that changes no decision is noise. A small set can be calibrated; twenty cannot. |
| A repository knowledge graph | A tiered repository model where each tier must show marginal gain before it is kept (Section 9.4) | Prior evidence suggests symbol-level maps give most of the localization benefit; richer graphs cost more than they return unless the task class needs them. Measure per tier. |
| Model routing as a subsystem | Routing only where the host permits it: subagent model selection, escalation on uncertainty, and any calls the runtime itself makes | In host-embedded mode the host owns the primary model. Pretending otherwise produces a subsystem with nothing to route. |
| Dynamic multi-agent roles | Single agent by default; ephemeral critics spawned only when the compiled workflow requires evidence that must be independent of the implementer's context | The value of a second agent is independence of evidence, not parallelism. Overhead is measured, not assumed. |
| "The user describes what they want and the system figures out everything" | The system figures out the process. On tasks with material trade-offs it surfaces those once, as a short contract, before implementation | Zero-interaction on ambiguous high-risk work is a false-success generator. Fewer, better questions is the goal, not zero questions. |
| Ten memory classes | One record schema with provenance, confidence, scope, decay and supersession; two kinds (facts, procedures); classes are tags | Ten classes with ten behaviors is configuration. One schema with good properties is architecture. |
| Skills retrieved as knowledge | Procedures retrieved as knowledge, with preconditions, expected evidence, and lazy expansion of steps | Same idea, with a shape the compiler can use. |

### 2.3 Rejected

- **Building the whole vision before evidence.** The brief's own Phase 20 forbids it; this plan enforces it with gates.
- **A static catalog of roles, agents or commands as the product.** Roles are generated; commands are an escape hatch, not the interface.
- **Learning by accumulating instructions.** Learning changes routing, verification and retrieval policy through replay-tested proposals. Instruction text grows only when a proposal survives replay.
- **The framework as something the model reads.** Instruction files are for judgment calls the runtime cannot make. Everything enforceable is enforced by hooks, gates and budgets.

### 2.4 Assumptions everyone else is making that may be wrong

Each of these becomes at least one hypothesis in Section 10.

| Common assumption | What becomes possible if it is removed |
|---|---|
| The context window is where the task lives | Task state lives in an external ledger; the model is a stateless worker invoked with a compact brief; resumption, host portability and observability come for free |
| Instructions are the mechanism for behavior | Enforcement moves to deterministic gates; instruction text shrinks to what needs judgment; adherence stops decaying with instruction length |
| "Done" is whatever the agent declares | Completion is the discharge of a typed evidence contract; false-success becomes a measured, reducible quantity |
| A skill is a prompt that gets loaded | A procedure is retrieved and expanded step by step; token cost scales with what is used, not what exists |
| More agents means more capability | Agents are spawned for independence of evidence; the default is one |
| Memory is notes | Memory is claims with provenance, verification state and decay; wrong memories are detectable and expire |
| The repository is a set of files | The repository is a model with confidence and freshness; blast radius is a computed number, not a guess |
| The same process fits every task | Process is compiled per task; a three-line CSS change and a payments redesign share no stages |
| Verification is a final stage | Every stage declares the evidence it must produce; verification is continuous and its depth is a function of risk |
| Learning means writing more rules | Learning means changing policy with replay evidence; the rule count can go down |

---

## 3. Operating principles

1. **Eval before architecture.** No component is designed without a metric it is expected to move and a baseline number for that metric.
2. **Deterministic where possible, model where necessary.** If a check can be code, it is code. Scope guards, budget limits, evidence parsing, secret scanning and destructive-command detection are never prompts.
3. **Outside the context window by default.** Task profile, workflow, evidence ledger, hypotheses, budgets and memory live in files or a local database. The model receives a stage brief, not the state.
4. **Every claim has a type and a contract.** "Bug fixed", "feature implemented", "refactor is behavior-preserving", "migration is safe" each map to required evidence kinds. Unmet contracts yield UNVERIFIED, never a softer status.
5. **Retrieval over injection.** Context packs are assembled per stage under a budget. Nothing is loaded because it exists.
6. **One agent until proven otherwise.** Critics and subagents are compiled into a workflow only when the profile justifies them.
7. **Remember little, verify what is remembered.** Memory writes are gated; records decay; conflicts are surfaced; untrusted origins cannot write memory without user confirmation.
8. **Trust is a property of the source, not the content.** System policy outranks user instruction, which outranks project configuration, which outranks repository content, which outranks tool output, which outranks web content. Instructions found in lower-trust content are data.
9. **Interoperate, do not replace.** Where Superpowers, Spec Kit or Aider do something better, the system uses it as a retrievable procedure or an evidence source rather than reimplementing it.
10. **Delete freely.** A subsystem with no winning experiment by its gate is removed. Removal is recorded as an ADR with the numbers.
11. **Attribution is kept.** Ideas are free; reused code, prompts or documentation carry their license and attribution in NOTICE.
12. **The plan is subject to its own rules.** This document is attacked in Section 13 and revised at every gate.

---

## 4. Milestone overview

Time estimates assume one engineer working with coding agents. They are rough and exist to force sequencing decisions, not as commitments.

| Milestone | Weeks | Goal | Gate (must be true to proceed) |
|---|---|---|---|
| M0 Foundations | 0 to 2 | Research map, failure taxonomy, harness skeleton, 30-task dev set, baselines run | Baseline numbers for at least three systems on the dev set with 95% bootstrap CIs; competitor map and gap analysis published in `docs/research/` |
| M1 Vertical slice | 3 to 6 | Intake, five-template compiler, evidence gate, scope guard on Claude Code | On the dev set: false-success rate at least halved vs vanilla; tokens on trivial and small tasks reduced at least 30% vs Superpowers; task success not worse than either (CI overlap allowed) |
| M2 Context and repository model | 7 to 10 | Repo model tiers, context packs with budgets, just-in-time retrieval | Each retained tier shows a marginal gain on localization or regressions; large-repo category success improves over M1 |
| M3 Verification and critics | 11 to 14 | Risk-scaled evidence contracts, verification runners (tests, static, browser, runtime), ephemeral critics | Regression rate on risky categories improves; critic spawn rate on low-risk tasks is near zero; override rate of gates below an agreed threshold |
| M4 Memory and learning | 15 to 18 | Gated memory, retrospectives, replay-gated promotion | Multi-session eval improves over single-session; no poisoning cases in the adversarial memory suite |
| M5 Portability and routing | 19 to 22 | Second and third host adapters, model routing and escalation | Dev set passes on two hosts with comparable numbers; routing reduces cost on low-complexity tasks without success loss |
| M6 Hardening and release | 23 to 26 | Security suite, observability UI, docs, held-out evaluation | Held-out set (never seen during development) confirms M1 to M5 gains; security suite passes; public release |

The loop inside every milestone: research → hypothesis → prototype → benchmark → redesign or delete.

---

## 5. Phase A: landscape research

Time box: two weeks, in parallel with harness construction (Section 8). Research does not end at week two; it continues as a standing activity feeding hypotheses, but the competitor map and gap analysis are frozen as v1 at the M0 gate.

### 5.1 Method

Reading the README is not research. For each Tier 1 system:

1. **Read the source**, not the documentation. Specifically the prompt files, the hook or plugin code, the context assembly code, the tool definitions, and anything that decides what goes into the model.
2. **Run it** on the five probe tasks (Section 5.4) with full trace capture (every model call, every tool call, tokens per turn). Record the token profile: what fraction of input tokens was instructions, repository content, tool output, chat history.
3. **Fill the twelve-question card** (Appendix F) with citations to specific files or commits.
4. **Record license and attribution requirements** in `docs/research/licenses.md`.
5. **Extract transferable abstractions** into `docs/research/abstractions.md`, each with: the abstraction, where it appears, what it costs, what it fails at, whether it generalizes.

Tier 2 systems get steps 1, 3 and 4. Tier 3 (literature) gets a one-paragraph note per item: claim, evidence quality, relevance, what to test.

### 5.2 Tier 1 systems and current priors

Priors below come from training data and are stated so they can be falsified. Every row is **[verify]**.

| System | Prior: what makes it work | Prior: where it is weak | What to test in probe runs |
|---|---|---|---|
| obra/superpowers | A meta-skill that forces skill lookup before acting; strong process discipline (brainstorm → plan → execute, TDD, systematic debugging, subagent-driven development, worktrees); good prompt craft | Process weight on small tasks; Claude Code specific; no evidence ledger; no repo model; memory minimal; token overhead of skill injection | Tokens on trivial task; whether TDD skill actually produces a failing test first; behavior when plan is invalidated mid-task |
| affaan-m/ECC (Everything Claude Code) | Breadth: agents, skills, hooks, rules, commands; hooks for memory persistence and "continuous learning"; token-optimization guidance; strategic compaction | Breadth is the weakness: instruction volume, configuration surface, many static personas; learning is instruction accumulation | Instruction token share; adherence to its own rules on probe tasks; what its learning hooks actually write |
| github/spec-kit | Spec-driven artifacts (constitution, spec, plan, tasks) as source of truth; templates that work across hosts | Fixed pipeline regardless of task size; artifact drift; no verification beyond task checklists | Overhead on a one-line change; whether spec and implementation diverge on a probe feature |
| garrytan/gstack | Opinionated founder workflow as skills (plan reviews, review, QA, ship, browse); headless browser QA | Persona-heavy; command-driven; Claude Code specific | Quality of browser verification; what its QA skill checks versus misses |
| bmad-code-org/BMAD-METHOD | Agile persona pipeline (analyst, PM, architect, scrum master, dev, QA) with document handoffs; brownfield and greenfield workflows | Heavy ceremony; role-play overhead; poor fit for small or debugging tasks; large token cost | Cost of a normal feature end to end; whether handoff documents contain hallucinated repo facts |
| Aider-AI/aider | Repository map: tree-sitter symbols ranked by reference graph (PageRank-style), token-budgeted; edit formats tuned per model; architect/editor two-model mode; auto lint and test loop; benchmark-driven culture | Not autonomous; no planning; no verification beyond lint and tests; context selection is reference-based only, no test or ownership edges | Localization accuracy of repo map on probe tasks; tokens per task; how it fails on multi-service change |
| anomalyco/opencode | Multi-provider terminal agent; LSP integration; agent modes (build, plan); plugins; sessions; AGENTS.md | Methodology-light; it is a harness, not a process | Plugin hook surface (for the adapter); headless run mode for the eval harness |
| cline/cline | Plan and Act modes; checkpoints via shadow git; browser tool; MCP marketplace; approvals | Token heavy; no repo model; no evidence; hard to run headless | Checkpoint semantics (for recovery design); whether headless execution is feasible |
| continuedev/continue | Composable context providers (@codebase, @docs, @file), rules, hub of reusable blocks; CLI for headless agents | No autonomous process; context providers are user-driven | Context provider design as a model for retrieval tools |
| SWE-agent/SWE-agent | Agent-computer interface research: tool design matters as much as the model; bounded file viewer, search tools, lint guardrails on edits; mini-SWE-agent shows a minimal bash-only agent is competitive; SWE-smith for data | Research harness; single task, single agent; no process for open-ended work | ACI lessons for tool design; mini-SWE-agent as a lower-bound baseline on SWE-bench tasks |

### 5.3 Tier 2 systems and Tier 3 literature

Tier 2 (source read, card filled, no probe runs unless cheap): OpenHands (event stream, sandboxed runtime, context condenser, microagents), Agentless (localization → repair → validation without an agent loop; evidence that a structured pipeline beats free agency for a task class), AutoCodeRover (program-structure-aware search, spectrum-based fault localization), Claude Code itself (hooks, subagents, skills, plan mode, compaction, memory files, OpenTelemetry export), Codex CLI (AGENTS.md, sandboxing), Gemini CLI (extensions, hooks **[verify]**), Cursor (rules, hooks **[verify]**, background agents), Amp (threads, subagents, oracle model), Roo Code (modes, orchestrator/boomerang tasks), Goose (extensions), Serena (LSP-backed symbol tools over MCP), Devin's published engineering notes on context engineering and against naive multi-agent, Manus's context-engineering notes (KV-cache stability, file system as context, todo recitation), Anthropic's "building effective agents" and context-engineering guidance, Sourcegraph's context engine (SCIP-based).

Tier 3 literature is listed by topic in Appendix C with what each item is expected to contribute.

Search beyond these lists is mandatory. Search terms and venues: arXiv cs.SE and cs.AI for "repository-level", "SWE-bench", "agent memory", "context compression", "LLM routing", "long-horizon agents", "prompt injection agents"; the SWE-bench, Terminal-Bench and Aider leaderboards for systems not yet known; GitHub trending for harnesses; engineering blogs of the agent vendors. New items are added to `docs/research/reading-list.md` with a one-line reason.

### 5.4 Probe tasks

Five tasks from the dev set, one each of: trivial change, normal feature, hard debugging, database migration, ambiguous feature. Each Tier 1 system runs each probe once with trace capture. This is qualitative; the quantitative comparison is Section 8. Purpose: see how each system spends its tokens and where it breaks, with the traces as evidence for the gap analysis.

### 5.5 Deliverables and gate contribution

- `docs/research/competitor-map.md`: one table across all Tier 1 and Tier 2 systems on twelve axes (task understanding, planning, context selection, repo model, memory, verification, multi-agent, model routing, recovery, security, host coupling, observability), each cell a one-line assessment with a citation.
- `docs/research/cards/<system>.md`: the twelve-question card per system.
- `docs/research/abstractions.md`: transferable abstractions with cost and failure notes.
- `docs/research/licenses.md`: license and attribution obligations per system.
- `docs/research/reading-list.md`: annotated literature.
- Token profiles from probe runs in `eval/results/probes/`.

---

## 6. Phase B: failure study and gap analysis

Time box: overlaps weeks 1 to 3. Depends on baseline runs from Section 8.

### 6.1 Method

Speculating about failure modes is cheap and mostly wrong in the details. The plan uses three sources, in order of weight:

1. **Trace mining.** Every failed or degraded baseline run on the dev set is labeled with root-cause codes from the failure taxonomy (Appendix E). Labeling is done by a human reading the trace, assisted by a model that proposes codes; the human decides. Each label cites the turn where the failure became inevitable.
2. **Literature failure analyses.** SWE-bench error analyses, OpenHands and SWE-agent papers' failure sections, published post-mortems from agent vendors, and the security incident literature (rules-file backdoors, tool poisoning, MCP injection).
3. **The brief's list and this plan's additions**, treated as hypotheses to be confirmed or discarded by 1 and 2.

### 6.2 Classification: fundamental versus implementation

A failure is classified **fundamental** if it persists across all baselines and its cause is a missing abstraction (no notion of evidence, no external task state, no risk model). It is **implementation** if at least one baseline avoids it, or if it is a matter of tuning (a better prompt, a bounded tool output). Fundamental failures shape architecture; implementation failures shape stage templates and tool design.

A third class, **host-imposed**, covers failures caused by the host agent (compaction amnesia, inability to select models) that an adapter can only partially mitigate. These are recorded so they are not mistaken for problems the system can solve.

### 6.3 Additional failure modes to look for

Beyond the brief's list, the trace review specifically looks for:

- Premature convergence: first plausible hypothesis is treated as the cause.
- Test modification to pass: the agent edits or skips the test instead of the code.
- Verification theater: tests are run, but not the ones related to the change.
- Silent partial completion: three of five subtasks done, reported as done.
- Environment hallucination: assuming commands, tools or versions that do not exist.
- Self-poisoning: the agent's own earlier wrong output remains in context and steers later turns.
- Compaction amnesia: state lost at context compaction, then reconstructed wrongly.
- Tool output flooding: multi-thousand-line logs dumped into context.
- Diff drift: several partial edits leave the code in an inconsistent intermediate state.
- Dependency shadowing: a new dependency is added where an existing one already does the job.
- Cross-package blindness in monorepos.
- Flaky test misattribution: a flaky failure is "fixed" by changing unrelated code.
- Strategy loops: the same failing command or edit is retried with trivial variations.
- Git state corruption: detached heads, lost stashes, partial commits.
- Secret exposure in logs and context.
- Success masked by skipped tests.
- Conflicting instruction files (nested CLAUDE.md, AGENTS.md, rules) with no resolution order.
- Stale memory contradicting current code.
- Plan theater: a plan is written, then not followed, with no detection.
- Over- and under-asking: clarifying questions on trivial tasks, none on ambiguous ones.

### 6.4 Deliverables

- `docs/research/failure-taxonomy.md`: the taxonomy with codes, definitions, and counts per baseline from trace mining.
- `docs/research/gap-analysis.md`: per capability area, what the best current system does, what it still fails at (with trace citations), and whether the gap is fundamental, implementation, or host-imposed.
- `docs/research/unsolved-problems.md`: the ranked list of the most important unsolved problems, ranked by (frequency in traces × severity × whether an abstraction can address it). This ranking is the input to Section 7 and Section 10.

---

## 7. Phase C: paradigm questioning and competing architectures

Time box: week 2 to 3, decision at the M0 gate. Revisited at M1 and M3.

### 7.1 Competing approaches

Six candidate architectures are set out so that the choice among them is explicit. Each is stated in its strongest form.

**A. Process library, done better (Superpowers++).**
Better-triggered skills, tighter TDD and debugging procedures, better prompts.
For: cheapest to build; users already understand it; composes with hosts today.
Against: everything is prompt text the model may ignore; no state outside context; no evidence; token cost scales with the library; cannot scale process to task size without more prompt logic. Does not answer the brief's "reason to exist" test.

**B. Spec pipeline, done better (Spec Kit++).**
Artifacts as source of truth (spec, plan, tasks, acceptance criteria), with hosts executing against them.
For: host-independent by construction; artifacts are inspectable; good for large features.
Against: fixed pipeline; ceremony on small tasks; artifacts drift from code; no repo understanding; verification is a checklist. Good component, wrong spine.

**C. Compiler and runtime.**
Task profile → workflow intermediate representation → optimization → execution by a runtime with gates and budgets.
For: process scales to task; the IR is inspectable and portable; gates are deterministic; workflows can be learned from successful executions.
Against: risk of building a rigid workflow engine in disguise; the "optimizer" is mostly a model call; underspecified tasks defeat ahead-of-time planning; significant infrastructure before any user value.

**D. Search-based agent.**
Tree search over action sequences with a verifier (test outcomes) as reward, in the style of LATS or SWE-search.
For: strong on tasks with a crisp verifier (bug fixing with tests); principled handling of uncertainty.
Against: cost multiplies with branching; no verifier for most feature work; users cannot follow a tree; hosts do not expose the control needed.

**E. Externalized-state controller.**
The model is a stateless worker. A controller keeps a task ledger (profile, plan, hypotheses, evidence, budget), assembles a compact brief each turn from ledger plus repository model, invokes the model, and records what happened.
For: resumable, portable, observable by construction; context never accumulates junk; compaction is a non-event; learning has clean data to work with.
Against: fights the host's own loop; briefs may lose nuance the chat history carried; more model calls of smaller size; requires the host to allow per-turn injection (hooks) or it degrades to a tool the model must remember to call.

**F. Deterministic pipelines per task class (Agentless-style).**
For known task classes (bug fix with failing test), a fixed sequence: localize → generate candidates → validate → select, with no agent loop.
For: cheap, reproducible, strong on its class.
Against: does not generalize to open-ended work; needs a class detector; brittle when the class is misjudged.

### 7.2 Working choice

The working hypothesis is **C + E**: the compiler produces the IR; the runtime executes it as an externalized-state controller. **F**-style deterministic pipelines become stage templates where a task class is well understood (bug localization, dependency upgrade). **D**-style bounded search is used only inside stages that have a verifier (hypothesis generation in debugging, candidate patch selection). **A** and **B** are interoperability targets: existing skills become retrievable procedures, and spec artifacts become typed inputs to the compiler.

This choice is provisional. The M1 gate tests the thinnest possible C + E slice against A (Superpowers) and vanilla. If the slice does not beat A on false-success and tokens without losing success, the choice is wrong and Section 7 is reopened.

### 7.3 Questions the paradigm must answer before M1

- How much of the runtime can run through hooks alone, with no model cooperation? (Determines how much of the system is unignorable.)
- What is the smallest IR that is still useful? (Determines whether "compiler" is a real abstraction or a JSON plan.)
- Can the intake stage be cheap enough that trivial tasks pay under 5k tokens and under ten seconds of overhead? (Determines whether the system is usable for everyday work.)
- What happens when the profile is wrong? (Determines whether recompile triggers are real.)

---

## 8. Phase D: evaluation harness

Built in weeks 0 to 3, before any architecture code. Extended continuously. This is the most important section of the plan.

### 8.1 Design goals

- Reproduce a baseline number for vanilla Claude Code in week two.
- Run a ten-task smoke tier in under an hour and under an agreed cost, so it can run on every meaningful change.
- Capture full traces for failure labeling.
- Produce paired, per-task comparisons with confidence intervals, not leaderboard averages.
- Keep a held-out set that is never inspected during development.

### 8.2 Task suite

Sixteen categories from the brief. Target counts: 48 tasks in the dev set (three per category) by M0, 96 by M2, plus a held-out set of 48 frozen at M1 and evaluated only at milestone gates. Appendix A holds the category matrix with sources and hidden-check types.

Task sources:

- **Existing benchmarks** for bug fixing, hard debugging, failing test suites, and large-repo work: SWE-bench Verified subset, SWE-bench Multilingual or Pro subset, SWE-bench Multimodal subset for frontend, Aider polyglot for small changes, Terminal-Bench for environment-heavy tasks **[verify current versions and licenses]**. Reuse their Docker images and graders.
- **Seed repositories built for this project** for categories benchmarks do not cover: ambiguous feature, database migration, security-sensitive change, multi-service change, dependency upgrade, performance optimization, refactor. Four seed repositories: a TypeScript web application with PostgreSQL, a Python service with a queue, a Go or Rust CLI, and a monorepo with three services. Each seed carries hidden tests, a hidden Playwright suite where there is a UI, and an "expected touch set" for scope scoring.
- **Real-repository synthesis** for the unfamiliar-repository and large-repository categories: tasks derived from merged pull requests in real projects, in the style of SWE-smith or SWE-rebench, with hidden tests from the PR.

Each task ships with: the prompt as a developer would write it, the environment image, hidden checks, the expected touch set, a risk label, and a category label. Tasks are versioned; changing a task creates a new task ID.

### 8.3 Systems under test and how each runs headless

| System | Headless mechanism | Notes |
|---|---|---|
| Vanilla Claude Code | `claude -p` with a fixed model and permissions mode | The primary baseline |
| Claude Code + Superpowers | Same, with the plugin installed | |
| Claude Code + ECC | Same, with the plugin installed | |
| Claude Code + Spec Kit | Same, with Spec Kit initialized; the prompt runs the standard command sequence | |
| Aider | `aider --message` with a fixed model | Requires an API key for the same model family |
| OpenCode | `opencode run` **[verify]** | |
| mini-SWE-agent | Its own runner | Lower-bound baseline on SWE-bench tasks only |
| ElevenPowers on Claude Code | `claude -p` with the adapter installed | From M1 |

Cline, Continue and BMAD are studied in Phase A but not run in the quantitative suite unless a reliable headless path exists; they are not worth a fragile harness. gstack is included only if its skills install cleanly as a plugin.

All Claude Code based systems use the same model and the same permission mode. Model versions are pinned per evaluation run and recorded.

### 8.4 Metrics

Definitions in Appendix B. Headline set:

- **Resolved**: hidden checks pass. Reported as pass@1 over n runs, with n at least 3.
- **False-success rate**: the system reported completion, hidden checks fail. The single most important metric for this project.
- **Regressions**: previously passing tests that now fail.
- **Scope discipline**: files changed outside the expected touch set, and total diff size relative to the reference solution.
- **Verification completeness**: fraction of the system's completion claims that carry evidence (test run, build, screenshot). For baselines this is computed from traces.
- **Calibration**: Brier score of any stated confidence against the outcome. Baselines that state no confidence get no score.
- **Human interventions**: in headless mode, the number of clarifying questions asked, and whether each was necessary (judged against the task's ambiguity label).
- **Cost**: input and output tokens, cache reads, dollar cost, wall time, model calls, failed tool calls, retries of an identical action.
- **Context size**: mean and peak input tokens per turn; share of input that is instructions, repository content, tool output, history.
- **Code quality and test quality**: lint and type-check deltas, cyclomatic complexity delta, mutation score of any tests the system added, and a rubric-based model judgment that is itself calibrated against a human-labeled sample of 40 diffs before it is trusted.
- **Instruction adherence**: rubric checks for task-specific constraints ("do not change the public API").

### 8.5 Statistical protocol

- Minimum three runs per (system, task). Headline comparisons use paired per-task differences with bootstrap 95% intervals. Pass/fail differences use McNemar's test.
- Results are reported per category, never only as an overall mean; the overall mean hides the point of the project (that process should differ by task).
- Hypotheses and decision rules are written into the experiment protocol (Appendix G) before runs begin.
- The held-out set is evaluated only at milestone gates, by a script that does not expose per-task traces to the developer until the gate decision is recorded.
- Model nondeterminism is a known noise floor; it is measured once with vanilla Claude Code at n=10 on the smoke tier and reported as the minimum detectable effect.

### 8.6 Harness architecture

- Runner: Python, one Docker container per task run, pinned images, per-run resource limits, timeouts.
- Trace capture: Claude Code's OpenTelemetry export where available **[verify]**, plus hook-based capture of every tool call and its output size; for other systems, their own logs normalized into one trace schema.
- Results store: SQLite for runs, DuckDB or Parquet for analysis; a report generator producing per-category tables and a per-run trace viewer.
- Cost accounting from provider usage fields, with a hard per-run cap.
- Task authoring tooling: a template and a validator that confirms hidden checks fail before the reference solution and pass after it.

### 8.7 Cost planning

A rough per-run cost is measured in week two. The plan budgets three tiers: smoke (10 tasks, one run each, cheap model where the system allows it), standard (48 tasks, three runs), full (all tasks, all systems, three runs). Full runs are milestone-only. The exact budget is a decision owed in Section 15.

### 8.8 Adversarial and multi-session suites (added at M3 and M4)

- **Security suite**: tasks whose repositories contain prompt injection in README files, comments, dependency documentation, test fixtures and fake tool outputs; tasks with planted secrets; tasks that tempt destructive commands. Scored on whether the injection changed behavior, whether secrets reached context or logs, whether destructive actions were gated.
- **Multi-session suite**: sequences of three to five related tasks on the same repository, where earlier tasks produce knowledge (an environment quirk, a convention, a failed approach) that later tasks can use. Scored on later-task success and cost with memory enabled versus disabled, and on whether a deliberately wrong earlier memory poisons later tasks.

---

## 9. Phase E: initial architecture, a working hypothesis

This section describes the system as currently hypothesized. Every component is tagged with the hypotheses (Section 10) that justify it. A component with no surviving hypothesis at its gate is removed.

### 9.1 Component overview

```
Developer request
      │
      ▼
┌─────────────┐   ┌──────────────────┐
│   Intake    │──▶│  Task profile    │  (H1, H11, H16)
└─────────────┘   └──────────────────┘
      │                    │
      ▼                    ▼
┌─────────────┐   ┌──────────────────┐   ┌────────────────┐
│ Repo model  │◀─▶│ Workflow compiler│──▶│  Workflow IR   │  (H1, H4, H13)
└─────────────┘   └──────────────────┘   └────────────────┘
      │                                          │
      ▼                                          ▼
┌──────────────┐  ┌──────────────────┐   ┌────────────────┐
│Context engine│◀─│     Runtime      │──▶│  Task ledger   │  (H3, H9, H12, H17)
└──────────────┘  └──────────────────┘   └────────────────┘
                     │        ▲
                     ▼        │
              ┌────────────────────┐
              │  Host adapter      │  hooks, MCP tools, rules file
              └────────────────────┘
                     │
                     ▼
              Coding agent (Claude Code, OpenCode, ...)
                     │
                     ▼
┌──────────────┐  ┌──────────────────┐   ┌────────────────┐
│Evidence eng. │◀▶│   Verification   │   │ Memory (gated) │  (H2, H5, H6, H14)
└──────────────┘  └──────────────────┘   └────────────────┘
                     │
                     ▼
              Retrospective → proposals → replay → promote or reject
```

### 9.2 Intake and task profile

The profile is deliberately small. Each dimension exists because it changes at least one downstream decision.

| Dimension | How it is determined | Decisions it drives |
|---|---|---|
| Scope class: trivial, small, medium, large, epic | Request features (verbs, nouns, counts) plus a repo-model estimate of the touched set, plus one cheap model call | Planning depth; whether a spec artifact is produced; token and cost budget |
| Ambiguity: low, medium, high, with the list of open choices | Model identifies unresolved choices; repo model checks which choices are already constrained by conventions or existing patterns | Whether to surface a contract before implementation; whether a research stage is compiled |
| Risk: blast radius × reversibility × domain sensitivity | Blast radius from repo model (dependents, ownership, test coverage of touched set); reversibility from change type (schema migration, external API, data, infra); domain sensitivity from policy rules on paths and terms (auth, payment, PII, secrets, deploy) refined by the model | Verification depth; critic spawn; checkpoint strategy; permission gates; whether human sign-off is compiled in |
| Knowledge gap: familiarity and novelty | Memory hits and repo-model coverage for the touched area; unknown libraries or APIs in the request | Research stage; documentation retrieval; model class |
| Verification surface | What evidence is obtainable: tests exist, build exists, browser reachable, runtime reproducible | Composition of the evidence contract; whether tests are written first; whether browser verification is compiled |
| Parallelism | Independent subgraphs in the touched set | Whether the task is split into worktrees or subagents |

Each dimension carries a confidence. A low-confidence dimension triggers a cheap probe (run the test suite, grep for the feature, read one file) before the workflow is compiled, rather than guessing. The profile is revised at every stage boundary; a revision that changes a decision triggers recompilation.

Budget for intake on a trivial task: under 5k tokens, under ten seconds. If this cannot be met, the intake design is wrong.

### 9.3 Workflow compiler and intermediate representation

The IR is a directed acyclic graph of stages. It borrows from hierarchical task network planning: stages are instantiated from templates (methods) that declare preconditions, produced artifacts, required evidence and invalidation triggers. Sketch:

```yaml
task: t-2026-09-09-001
profile:
  scope: medium
  ambiguity: low
  risk: {blast: 0.42, reversible: true, domains: [auth]}
  knowledge_gap: low
  verification_surface: [tests, runtime]
  parallelism: none
budget: {tokens: 400000, usd: 6.00, wall_minutes: 40}
stages:
  - id: reproduce
    template: debug.reproduce
    goal: Reproduce the race deterministically, or show it cannot be reproduced in this environment
    context: [pack:auth-flow, memory:env-quirks]
    exit: {evidence: [runtime.failing_repro]}
    on_exit_fail: {recompile: true, hint: not-reproducible-path}
    model_class: reasoning-high
    budget: {tokens: 60000}
  - id: hypothesize
    template: debug.hypotheses
    needs: [reproduce]
    exit: {artifact: hypotheses, min: 2, each_with: [prediction, discriminating_test]}
  - id: isolate
    template: debug.isolate
    needs: [hypothesize]
    exit: {evidence: [runtime.root_cause_demonstrated]}
  - id: fix
    template: change.minimal
    needs: [isolate]
    guard: {allow: ["src/auth/**", "tests/auth/**"], deny: ["migrations/**", "**/*.lock"]}
    exit: {evidence: [test.regression_added, diff.within_guard]}
  - id: verify
    template: verify.risk_scaled
    needs: [fix]
    contract: [test.regression_passes, test.suite:tests/auth, static.typecheck, runtime.repro_no_longer_fails]
    critic: {when: "risk.blast > 0.3", role: concurrency reviewer, fresh_context: true}
invalidate_when:
  - any evidence CONTRADICTED
  - edits outside guard
  - profile.ambiguity increases
  - budget.tokens exceeded by 20%
```

Compiler passes, each a candidate for deletion if it shows no gain:

1. **Template selection** from the profile (initially five templates, Section 11).
2. **Elision**: remove stages whose preconditions are already satisfied (tests already exist, spec already provided).
3. **Verification insertion** from the risk dimension and the verification surface (H13).
4. **Guard synthesis** from the repo-model touched set (H12).
5. **Parallel split** when the parallelism dimension is non-trivial and worktrees are available.
6. **Budget allocation** across stages from the scope class and observed history.

The compiler is mostly deterministic given the profile; the one model call is in template selection for medium-confidence profiles. The IR is written to the task ledger and shown to the user at start (Section 9.10).

### 9.4 Repository model

Tiers, each benchmarked for marginal gain (H4):

- **T0**: nothing beyond the host's own search tools.
- **T1**: symbol map from tree-sitter (definitions, references), file-level, ranked by relevance to the request terms and token-budgeted, in the spirit of Aider's map.
- **T2**: T1 plus import and dependency edges, test-to-source mapping (by import, by naming convention, by coverage data when available), git churn and ownership.
- **T3**: T2 plus cross-service edges (route → handler → service → table, event producers and consumers), architectural boundaries inferred from directory structure and import cuts, historical bug hotspots from commit messages and issue links.

The model is built incrementally and cached across sessions, keyed by commit and file hashes, with freshness recorded per node. Queries: touched-set estimate for a request, dependents of a set, tests for a set, owners of a set, blast radius (a scalar computed from dependents, ownership spread and coverage). The blast-radius scalar is validated against observed regressions (H13); if it does not predict regressions it is dropped and risk falls back to the policy rules.

### 9.5 Runtime and task ledger

The ledger is a directory per task (or a SQLite database) holding: profile, IR, current stage, hypotheses, evidence, budget consumption, checkpoints, decisions, and a compact "brief" regenerated per stage. The runtime:

- Injects the stage brief into the host at stage boundaries.
- Enforces guards and budgets through host hooks (deterministic).
- Captures evidence from tool outputs (test runners, builds, linters, screenshots) by parsing, not by asking the model.
- Detects strategy loops by fingerprinting actions (same command, same edit region, same error) and forces a hypothesis change or escalation after a bounded number of repeats.
- Creates checkpoints (git worktree or snapshot commit on a task branch) at stage boundaries; rollback is a ledger operation.
- Recompiles when an invalidation trigger fires, carrying forward evidence that remains valid.
- Escalates: stronger model class, fresh-context retry, critic intervention, then the human, in that order, each bounded.

Mapping onto Claude Code hooks **[verify hook names against current documentation]**:

| Hook | Runtime action |
|---|---|
| SessionStart | Load or resume ledger |
| UserPromptSubmit | Intake, compile, inject stage brief |
| PreToolUse (Edit, Write, Bash) | Scope guard, destructive-command guard, secret guard, budget check; deny with a one-line reason |
| PostToolUse (Bash) | Parse test, build and lint output into evidence records; truncate flooding outputs with a pointer to the full log |
| SubagentStart / SubagentStop | Inject role spec; merge subagent evidence |
| PreCompact | Persist ledger; on next turn, re-inject a brief |
| Stop | Evidence-contract check; if unmet, block with the specific missing items; after a bounded number of blocks, return an UNVERIFIED report to the user instead of looping |

MCP tools exposed to the agent: `task_status`, `retrieve` (context query against the repo model and memory), `record_hypothesis`, `record_evidence`, `request_recompile`, `memory_propose`. The agent is told about these in a short rules file; the hooks work whether or not the agent uses them.

### 9.6 Context engine

Per stage, a context pack is assembled under a token budget set by the compiler: repo-model results for the touched set, relevant test files, relevant memory records, specification artifacts, and the stage's procedure steps. Rules:

- Deduplicate against what the host already has in context (tracked by the ledger).
- Prefer symbol-level excerpts over whole files; expand on request through `retrieve`.
- Tag every item with its source and trust level (Section 9.9).
- Hierarchical summaries for large components, with the full text one `retrieve` away.
- Budgets vary by model class, stage and uncertainty (H9).

The engine is measured on precision (fraction of pack tokens later referenced by edits or reasoning) and on the success delta versus the host's own retrieval.

### 9.7 Evidence engine and verification

Claim types and their default contracts, scaled by risk tier (low, medium, high, critical):

| Claim type | Low risk | High risk (adds) |
|---|---|---|
| bug_fixed | Regression test added and passing; related suite passes | Reproduction shown failing before fix; runtime demonstration; critic review |
| feature_implemented | Tests for the feature pass; build and typecheck clean | Integration tests; browser evidence for UI; scope within guard; spec acceptance criteria mapped to tests |
| refactor_behavior_preserving | Full relevant suite passes; diff within guard | Mutation score unchanged or better; public API diff empty |
| migration_safe | Migration applies and reverts on a fresh database | Applies on a seeded database; rollback tested; data-shape assertions; downtime analysis |
| performance_improved | Benchmark before and after with the numbers | Repeated runs with variance; no regression on a secondary benchmark |
| docs_changed | Build of docs (if any) | None |

Evidence record:

```yaml
claim: {type: bug_fixed, stage: verify, statement: "Double login no longer occurs under concurrent refresh"}
evidence:
  - {kind: test, id: "tests/auth/test_race.py::test_no_double_login", before: FAIL, after: PASS, run: r17}
  - {kind: test_suite, scope: tests/auth, result: "84 passed", run: r18}
  - {kind: static, tool: mypy, result: clean, run: r18}
  - {kind: runtime, note: "repro script, 10000 iterations, 0 failures", run: r19}
status: VERIFIED        # VERIFIED | UNVERIFIED | CONTRADICTED
coverage: 1.0           # fraction of the contract discharged
```

Confidence is computed from contract coverage and evidence strength, not from the model's self-report. The model's self-reported confidence is recorded separately for calibration (H11).

Verification runners: test runners (pytest, jest, vitest, go test, cargo test), builds, type checkers, linters, mutation testing (for refactor and test-quality claims), property-based test scaffolds, Playwright for browser evidence with screenshot capture, database migration simulation on a throwaway database, security scanners (secret scan, dependency audit, a small set of static rules). Selection is by the compiler from the verification surface; running everything is a failure of the compiler, not a safety feature.

### 9.8 Memory

One schema, two kinds:

```yaml
id: m-0173
kind: fact | procedure
scope: {repo: "org/app", paths: ["services/billing/**"], global: false}
statement: "Billing tests require STRIPE_MOCK=1 or they hit the network and hang"
source: {task: t-2026-09-02-014, evidence: [r41], author: system}
trust: user | derived | untrusted_origin
confidence: 0.85
verified: {at: 2026-09-02, method: "observed hang, then pass with variable set"}
supersedes: null
decay: {half_life_days: 60, last_used: 2026-09-09, uses: 3}
conflicts: []
```

Rules: writes are proposals from the retrospective and must cite evidence; records from untrusted origins require user confirmation; retrieval is by scope and profile, budgeted; a record that contradicts observed evidence is marked CONTRADICTED and stops being retrieved; unused records decay out; consolidation merges near-duplicates and keeps the best-evidenced statement. Procedures are retrieved as steps with preconditions, not injected whole.

### 9.9 Security model

- Trust levels on every context item and tool result: system policy, user, project configuration (only when the user has confirmed it), repository content, tool output, web content. Lower-trust content cannot change policy, guards, budgets or memory.
- Injection screening on tool outputs and retrieved content: deterministic patterns for imperative instructions addressed to the agent, plus a small-model classifier on suspicious items; flagged content is wrapped as quoted data with a warning, never dropped silently.
- Destructive-command guard in PreToolUse with an allowlist per task risk tier; overrides require a reason recorded in the ledger.
- Secret scanning on context packs, diffs and logs before they reach the model or disk.
- Permission budget: the set of tools and paths the task may touch is compiled from the profile; expansion is a recompile with a visible reason.
- MCP tool allowlist per task; tool descriptions are treated as untrusted content.
- Memory writes from untrusted-origin content are held for user confirmation.

The security suite (Section 8.8) is the gate for this component.

### 9.10 Observability

At task start, a short banner: profile with confidences, compiled workflow, context pack summary (counts, not contents), budget, estimated cost. At each stage boundary, a one-line status. At the end, the evidence ledger, actual cost versus estimate, what was learned and what was proposed for memory. Every decision (stage selected, elided, critic spawned, gate blocked, recompile) has a stored reason available on request. An `explain <stage>` command prints it. Verbosity is configurable; the default is the banner and the end report. Traces export through OpenTelemetry.

### 9.11 Learning loop

After every task: a budgeted retrospective (cheap model) answers the brief's questions (wrong assumptions, unnecessary context, missing information, wasteful stages, model performance, unnecessary tool calls, reusable discovery, mistake to never repeat, new capability). Outputs are typed proposals: memory record, stage-template change, routing-policy change, new procedure. Proposals are promoted only after replay on the relevant eval subset shows no regression and, for template and policy changes, a gain. Unpromoted proposals stay as candidates with narrow scope and decay. Rule count is a metric that is allowed to go down.

### 9.12 Host adapters

The core depends on three host capabilities: inject text at turn boundaries, intercept tool calls, expose tools. Where a host lacks interception, the adapter degrades to MCP tools plus a rules file and the gates run at commit time instead of edit time. Appendix D holds the capability matrix. The second host is chosen at M5 to maximize difference from Claude Code, so that portability claims are tested rather than assumed.

---

## 10. Hypotheses register

Each hypothesis has an experiment, a metric, a decision rule, and the consequence of failure. Protocols follow Appendix G. "Dev set" means the current development suite; category subsets are named.

| ID | Hypothesis | Experiment | Primary metric | Decision rule | If false |
|---|---|---|---|---|---|
| H1 | Profile-driven workflow selection matches fixed process (Superpowers) on success and cuts tokens at least 30% on trivial and small tasks | Dev set, three arms: vanilla, Superpowers, slice | Resolved; tokens; false-success | Success CI overlaps or better, tokens down 30% on trivial+small | Compiler becomes a template picker with two templates, or is removed |
| H2 | Evidence-gated completion halves false-success rate versus vanilla | Dev set, gate on versus off | False-success rate | At least 50% relative reduction, CI excluding zero | Gate is redesigned; if still no effect, the evidence engine is a reporting tool only |
| H3 | Procedures retrieved lazily match loaded skills on success with fewer tokens | Dev set, Superpowers skills loaded versus the same content retrieved by the context engine | Resolved; instruction tokens | No success loss; instruction tokens down 40% | Retrieval is kept only for memory; skills stay host-native |
| H4 | Repo-model tiers give diminishing marginal gains; T1 captures most localization benefit | Large-repo and unfamiliar-repo subsets, T0 through T3 | Localization accuracy (touched set overlap); resolved; regressions; index cost | Keep a tier only if it improves resolved or regressions with CI excluding zero | Drop tiers that show nothing; possibly the whole model beyond T1 |
| H5 | A fresh-context critic improves regressions on high-risk tasks and adds only cost on low-risk tasks | Risky subset and trivial subset, critic on versus off | Regressions; cost | Regression reduction on risky with CI excluding zero; no success gain on trivial | Critics compiled only where shown; otherwise removed |
| H6 | Gated memory beats both no memory and save-everything on multi-session sequences, without poisoning | Multi-session suite, three arms, plus a poisoned-memory arm | Later-task resolved; cost; poisoning incidents | Gated arm best on resolved and cost; zero poisoning incidents accepted | Memory reduced to user-authored facts only |
| H7 | Model escalation cuts cost on low-complexity tasks at least 25% with no success loss | Trivial and small subsets, escalation on versus fixed strong model, where the host allows | Cost; resolved | Cost down 25%, success CI overlaps | Routing removed; the host's model is used everywhere |
| H8 | Instruction adherence falls as instruction length rises (dilution) | Fixed task set; the same constraints embedded in instruction files of 500, 2000, 8000, 20000 tokens | Adherence rubric | Monotone decline with CI | The system may keep larger rules files; the argument for gates over text weakens |
| H9 | Stage-level context budgets improve success on large repositories versus unbudgeted retrieval | Large-repo subset; budgets on versus off | Resolved; peak context | Resolved up with CI excluding zero | Budgets become a soft hint |
| H10 | Recompile triggers improve hard-debugging success versus static plans | Hard-debugging subset; triggers on versus off | Resolved; retries | Resolved up; strategy loops down | IR becomes static and recompile is removed |
| H11 | Evidence-derived confidence is better calibrated than model self-report and can drive escalation | Dev set; record both; escalate on evidence-derived confidence below threshold in one arm | Brier score; resolved | Evidence-derived Brier lower; escalation arm resolved up | Confidence is reported but not used for control |
| H12 | Deterministic scope guards reduce unrelated-file changes more than prompt instructions do | Dev set; three arms: no instruction, instruction only, hook guard | Out-of-scope files; resolved | Guard arm lowest with no success loss | Guard kept as a warning rather than a block |
| H13 | Computed blast radius predicts observed regressions | All runs; blast radius versus regression occurrence | AUC | AUC at least 0.7 | Risk falls back to policy rules; blast radius removed |
| H14 | Replay-gated learning improves over sessions without regressions | Multi-session suite over four rounds; promoted proposals versus none | Resolved per round; regressions | Monotone or flat improvement, no round worse than baseline | Learning reduced to memory proposals only |
| H15 | A hypothesis-driven debugging template beats a generic fix template on hard debugging | Hard-debugging subset, two templates | Resolved; retries | Resolved up with CI excluding zero | Template dropped |
| H16 | Intake overhead on trivial tasks can be held under 5k tokens and ten seconds without profile accuracy loss | Trivial subset; profile compared to human labels | Tokens; seconds; profile accuracy | All three thresholds met | Intake is bypassed for requests under a length threshold with a heuristic profile |
| H17 | Externalized briefs survive compaction better than host-native context | Long tasks forced through compaction; ledger re-injection on versus off | Resolved; post-compaction errors | Errors down, resolved up | Re-injection kept only as a resume aid |
| H18 | Bounded search over candidate patches inside the fix stage improves bug-fix success at acceptable cost | Bug-fix subset; k=1 versus k=3 candidates with test-based selection | Resolved; cost | Resolved up, cost within 2x | Search removed |

Hypotheses are added, retired and revised in `experiments/REGISTER.md`. Each experiment directory holds its protocol, runner and results.

---

## 11. Minimal experimental prototype plan

Weeks 3 to 6, gated at M1. The point is to test the paradigm choice with the least code that can do so.

### 11.1 In scope for the slice

- **Intake**: heuristic features plus one cheap model call producing the six-dimension profile with confidences. A cheap probe (run the test suite once, list the touched-set estimate) when confidence is low.
- **Compiler** with five templates: `trivial-change` (inspect → modify → minimal verify), `small-feature` (inspect → implement with tests → verify), `bugfix` (reproduce → hypothesize → isolate → fix → verify), `risky-change` (research → contract → plan → isolated implementation → risk-scaled verify → critic), `research-needed` (research → contract → then one of the above). Elision and guard synthesis passes only.
- **Runtime** on Claude Code hooks: brief injection, scope guard, destructive-command guard, evidence capture from test and build output, Stop-hook contract check with a bounded number of blocks, loop detection.
- **Task ledger** as a directory of YAML files under the repository's ignored state directory.
- **Repository model T1** only (tree-sitter symbol map, budgeted, ranked by request terms), used for the touched-set estimate and the context pack.
- **Evidence engine** with four claim types: bug_fixed, feature_implemented, refactor_behavior_preserving, docs_changed.
- **Observability**: start banner and end report as plain text.

### 11.2 Explicitly excluded from the slice

Memory, learning loop, critics and subagents, model routing, repo model T2 and T3, browser verification, mutation testing, security screening beyond the destructive-command and secret guards, any host other than Claude Code, any user interface beyond text.

### 11.3 Acceptance

The slice is accepted only by the M1 gate numbers (Section 4). A secondary acceptance: a developer using it for a day on real work reports that trivial tasks feel no slower and that the end report was worth reading. That is recorded, not scored.

### 11.4 Order of work

1. Ledger schema and IR schema, with a validator (day 1 to 2).
2. Hook adapter skeleton on Claude Code with tracing to the ledger (day 2 to 4).
3. Evidence capture parsers for pytest, jest and vitest, plus the Stop-hook contract check (day 4 to 7).
4. Intake and the five templates (day 7 to 11).
5. T1 repo model and touched-set estimate (day 11 to 15).
6. Scope guard from touched set; loop detection (day 15 to 17).
7. Banner and end report (day 17 to 18).
8. Smoke-tier runs daily from day 7; standard-tier at day 20; M1 gate at day 24 to 28.

---

## 12. Evidence-driven roadmap with gates

Expanding Section 4. Each milestone lists its hypotheses, what gets built only if they hold, and what gets removed if they fail.

**M0 Foundations (weeks 0 to 2).**
Research map and gap analysis (Sections 5, 6). Harness with smoke and standard tiers; 48-task dev set; baselines for vanilla, Superpowers, ECC, Aider (Spec Kit and OpenCode if headless works in time). Noise-floor measurement. Competing architectures decided provisionally (Section 7).
Gate: baselines with CIs; failure taxonomy with counts; unsolved-problems ranking; ADR for the paradigm choice.

**M1 Vertical slice (weeks 3 to 6).**
Hypotheses: H1, H2, H12, H16.
Built: Section 11.
Gate: Section 4 numbers. If H1 fails but H2 holds, the product pivots to an evidence gate that composes with other frameworks; if both fail, Section 7 is reopened.

**M2 Context and repository model (weeks 7 to 10).**
Hypotheses: H3, H4, H9, H17.
Built if hypotheses hold: T2 and possibly T3 of the repo model; context packs with budgets; `retrieve` tool; ledger re-injection after compaction.
Held-out set frozen at the start of M2.
Gate: per-tier marginal gains; large-repo success up; instruction tokens down.

**M3 Verification and critics (weeks 11 to 14).**
Hypotheses: H5, H10, H11, H13, H15, H18.
Built if hypotheses hold: risk-scaled contracts; verification runners (browser, migration simulation, mutation testing); ephemeral critic roles generated from the profile; recompile triggers; bounded candidate search in the fix stage; security suite v1 and the injection screen.
Gate: regressions down on risky categories; critic spawn rate near zero on trivial tasks; gate override rate under threshold; blast radius AUC.

**M4 Memory and learning (weeks 15 to 18).**
Hypotheses: H6, H14.
Built if hypotheses hold: memory store with the record schema; retrospective; proposal pipeline with replay gating; consolidation and decay.
Multi-session suite built at the start of M4.
Gate: multi-session gains; zero poisoning; rule count not growing without evidence.

**M5 Portability and routing (weeks 19 to 22).**
Hypotheses: H7, and the portability claim (dev set on two hosts).
Built: second adapter (candidates: OpenCode for its plugin hooks, Codex for its lack of hooks as a stress test; choose one, then the other if time allows); model router with escalation where the host permits.
Gate: comparable numbers on two hosts; routing cost reduction without success loss.

**M6 Hardening and release (weeks 23 to 26).**
Held-out evaluation. Security suite v2. Observability UI (a local web page over the ledger). Documentation that fits in one screen for the default path. Attribution audit. Release.
Gate: held-out confirms gains; security suite passes; the "50% removal" review (Section 13.3) has been performed and its removals applied.

---

## 13. Attacking the plan

### 13.1 Pre-mortem: why this fails

| Failure | Likelihood | Mitigation in the plan |
|---|---|---|
| The eval suite is too small or too noisy to detect effects, so every gate is "inconclusive" | High | Noise floor measured first; paired per-task comparisons; category-level reporting; minimum detectable effect published; task count grows each milestone |
| Harness building consumes the schedule and no product emerges | High | Harness is time-boxed to three weeks with a smoke tier at week one; benchmark reuse (SWE-bench images, graders); seed repos start small |
| Host APIs change (hook names, plugin surfaces) and adapters break | Medium | Adapter is a thin layer over three capabilities; host-specific code is isolated; a compatibility test runs in the smoke tier |
| Cost blows up (n=3 across six systems across 96 tasks) | Medium | Tiered runs; full runs only at gates; per-run caps; cheaper model for harness-internal calls |
| The compiler becomes a rigid workflow engine with more templates every week | Medium | Template count is a tracked metric; every template must win a hypothesis; elision is measured |
| Evidence gates annoy users and get disabled | Medium | Gates scale with risk; overrides are one command with a recorded reason; override rate is a gate metric; trivial tasks have almost no gate |
| The repo model goes stale and misleads | Medium | Freshness per node; incremental rebuild on file hash change; a stale answer is tagged and the runtime prefers a probe |
| Memory gets poisoned or fills with noise | Medium | Gated writes, provenance, decay, contradiction marking, the poisoning arm of the multi-session suite |
| Overfitting to the dev set | Medium | Frozen held-out set evaluated only at gates by a script that hides traces |
| The research phase never ends | Medium | Two-week time box; the map is frozen as v1 and revised only at gates |
| Intake adds latency and tokens to every request, so daily use feels worse | High | H16 is a gate; below-threshold requests bypass intake with a heuristic profile |
| The externalized brief loses nuance and the agent performs worse than with raw chat history | Medium | H17 tests this directly; the brief includes a pointer to the full ledger and the agent can `retrieve` |
| Single engineer, twenty-six weeks, too much scope | High | Every milestone has a delete list; M1 alone is a usable product (evidence gate plus scope guard) |

### 13.2 Expert critiques and answers

- **Researcher:** "Your task profiler is an LLM prompt in disguise. Where is the calibration data?" Answer: profiles are compared against human labels on the dev set (H16); dimensions that cannot be labeled reliably are dropped; the profile carries confidences that are themselves scored.
- **Researcher:** "Repository graphs have shown small gains in the literature; why build one?" Answer: only T1 is built by default; each further tier must show a marginal gain (H4). The plan expects T3 to lose.
- **Developer:** "Another layer between me and my agent. More latency, more things to configure." Answer: zero configuration by default; intake budgeted; trivial tasks bypass; the only visible artifacts are a start banner and an end report. If H16 fails the plan says so and the intake is redesigned.
- **Developer:** "Gates will block me when I know better." Answer: one-command override with a reason; the override rate is tracked; a high rate is treated as a defect in the compiler, not the user.
- **Maintainer:** "Six hosts, six adapters, endless breakage." Answer: two hosts by M5, chosen for maximal difference; the adapter contract is three capabilities; anything beyond that is optional.
- **Security engineer:** "Hooks run arbitrary code; your runtime is itself an attack surface." Answer: the runtime reads repository content as data only; its own configuration lives outside the repository; the security suite includes attacks on the runtime's parsers.
- **Founder:** "What is the one-sentence reason to exist?" Answer: it is the only system that will refuse to say "done" without evidence, and it decides the engineering process per task instead of making the developer choose it.

### 13.3 The 50% removal test

Applied at M1 and again at M6. The minimum that keeps most of the value, as currently believed: intake, a two-template compiler (light and heavy), the evidence gate, the scope guard, and the end report. Everything else (repo model beyond T1, context engine, critics, memory, learning, routing, observability UI, extra adapters) must have earned its place with a hypothesis by the time the test runs. The test is performed by listing every component with its winning hypothesis ID; components without one are removed in that milestone.

### 13.4 What competitors do better, and the response

- Aider's repository map and edit-format tuning: adopt the idea for T1 with attribution; do not compete on editing.
- Superpowers' procedural discipline and prompt craft: interoperate; its skills are candidate procedures for retrieval (license permitting).
- Spec Kit's artifacts and multi-host templates: accept spec artifacts as compiler inputs.
- OpenCode's provider breadth and terminal experience: not a target; the system is a layer, not a host.
- Cline's checkpoints and approvals: borrow the checkpoint semantics for the ledger.
- SWE-agent's interface rigor and benchmark discipline: adopt the discipline; reuse mini-SWE-agent as a baseline.
- Agentless's cost efficiency on bug fixing: use its pipeline shape as the bug-fix stage template.

---

## 14. Project mechanics

### 14.1 Repository layout

```
ElevenPowers/
  PLAN.md
  prompt.md
  docs/
    research/        competitor map, cards, abstractions, licenses, reading list,
                     failure taxonomy, gap analysis, unsolved problems
    adr/             one file per decision, numbered
    design/          IR schema, ledger schema, evidence contracts, memory schema
  eval/
    harness/         runner, trace schema, graders, report generator
    tasks/           one directory per task: prompt, env, hidden checks, touch set, labels
    seeds/           the four seed repositories
    results/         run databases and reports (large files ignored by git)
  experiments/
    REGISTER.md      hypotheses with status
    H01-.../         protocol.md, run script, results
  core/
    intake/  repo_model/  compiler/  runtime/  context/  evidence/  memory/  security/  observe/
  adapters/
    claude_code/  opencode/  codex/
  procedures/        stage templates and retrievable procedures, with provenance headers
  NOTICE
  LICENSE
```

### 14.2 Technology

- Python 3.12 with `uv` for the core, harness and adapters. Reason: the evaluation ecosystem (SWE-bench, Terminal-Bench, mini-SWE-agent) is Python, tree-sitter bindings are mature, and the MCP SDK is available. The alternative (TypeScript, matching Claude Code and OpenCode) would ease plugin authoring for those hosts; a TypeScript shim is acceptable for a host plugin if the host requires it, but the core stays in one language. This decision is confirmed by a one-day spike in week 1 (ADR-001).
- tree-sitter for symbol extraction; SQLite for the ledger, repo model cache and memory; DuckDB or Parquet for results analysis.
- Docker for task environments; Playwright for browser evidence; mutation testing via the language's standard tool (mutmut, Stryker).
- OpenTelemetry for traces.

### 14.3 Working agreements

- No product code before the M0 gate.
- Every experiment has a protocol committed before its first run.
- Every subsystem directory contains a `WHY.md` naming the hypothesis that justifies it and the number it moved.
- Changes to the dev set are versioned; the held-out set is never edited after freezing.
- The smoke tier runs before any merge to the main branch.

### 14.4 Decision records

ADRs are short: context, options, decision, evidence (a link to a results table), consequences, revisit condition. Planned early ADRs: language choice; paradigm choice; benchmark reuse versus custom tasks; first second-host; license.

### 14.5 Licensing and attribution

The project license is proposed as Apache-2.0 (patent grant, compatible with most sources). Before any code, prompt or template is adapted from another project, its license is recorded in `docs/research/licenses.md` and the obligation is met in NOTICE and in a provenance header on the file. Priors to verify: Superpowers MIT, ECC MIT, Spec Kit MIT, gstack unknown, BMAD MIT, Aider Apache-2.0, OpenCode MIT, Cline Apache-2.0, Continue Apache-2.0, SWE-agent MIT. Ideas and abstractions are used freely; verbatim reuse is the exception and is documented.

### 14.6 Documentation

The default-path documentation must fit on one screen: install, run, what the banner means, how to override a gate. Everything else is reference. The absence of a large instruction file is a feature that the documentation states.

---

## 15. Open questions and decisions owed

| Question | Owner | Needed by | Default if undecided |
|---|---|---|---|
| Evaluation budget per month | user | week 1 | Smoke daily, standard weekly, full at gates only |
| Core language: Python or TypeScript | ADR-001 spike | week 1 | Python |
| Reuse SWE-bench subsets or build custom only | ADR-003 | week 1 | Reuse for bug-fix categories, custom for the rest |
| Second host: OpenCode or Codex | ADR at M5 | week 19 | OpenCode (has hooks), then Codex (stress test) |
| Open-source from day one or at M6 | user | week 2 | Private until M1 numbers exist, public after |
| Which model family and version is pinned for the first evaluation series | ADR-002 | week 1 | The most capable generally available model the host supports at the time, pinned by ID |
| Whether the multi-session suite uses synthetic or real task sequences | ADR at M4 | week 15 | Synthetic on seed repos |
| Human labeling capacity for failure taxonomy and quality rubric | user | week 2 | The engineer labels; model proposes |

---

## Appendix A: task suite matrix

| Category | Source | Hidden check | Risk label | Dev count (M0 / M2) | Held-out |
|---|---|---|---|---|---|
| Tiny code change | Seed repos, Aider polyglot | Tests, touch-set | low | 3 / 6 | 3 |
| Normal feature | Seed repos | Tests | medium | 3 / 6 | 3 |
| Ambiguous feature | Seed repos with two valid readings; rubric for whether the question was asked | Tests for both readings, question rubric | medium | 3 / 6 | 3 |
| Bug fixing | SWE-bench Verified subset | Fail-to-pass and pass-to-pass tests | medium | 3 / 6 | 3 |
| Hard debugging | SWE-bench hardest subset; seed repos with concurrency and state bugs | Fail-to-pass, reproduction script | high | 3 / 6 | 3 |
| Refactor | Seed repos | Full suite, public API diff empty, mutation score | medium | 3 / 6 | 3 |
| Frontend | SWE-bench Multimodal subset; seed web app | Playwright, screenshot compare | medium | 3 / 6 | 3 |
| Backend | Seed service | Integration tests | medium | 3 / 6 | 3 |
| Database migration | Seed repos | Apply, revert, seeded-data assertions | high | 3 / 6 | 3 |
| Security-sensitive change | Seed repos (auth, permissions, input handling) | Tests, security scanner, injection rubric | critical | 3 / 6 | 3 |
| Large repository | Real repositories, PR-derived | PR tests | medium | 3 / 6 | 3 |
| Unfamiliar repository | Real repositories in less common stacks | PR tests | medium | 3 / 6 | 3 |
| Failing test suite | Seed repos with several planted failures | Suite green, no test edits | medium | 3 / 6 | 3 |
| Performance optimization | Seed repos with benchmark harness | Benchmark threshold, correctness suite | medium | 3 / 6 | 3 |
| Dependency upgrade | Seed repos pinned to old major versions | Suite green, lockfile sanity | medium | 3 / 6 | 3 |
| Multi-service change | Seed monorepo | Cross-service integration tests | high | 3 / 6 | 3 |

## Appendix B: metric definitions

- **Resolved**: all hidden checks pass in a clean environment after the run, with no edits to hidden checks or to existing tests unless the task permits.
- **False-success rate**: runs where the system's final message asserts completion (rubric: claims done, fixed, implemented, passing) and Resolved is false, divided by runs asserting completion.
- **Regressions**: tests passing before the run that fail after, counted per run and per task.
- **Out-of-scope files**: files changed that are not in the expected touch set and not tests or documentation for files in the touch set.
- **Diff ratio**: changed lines divided by changed lines in the reference solution.
- **Verification completeness**: completion claims with at least one evidence record of the required kind, divided by completion claims.
- **Brier score**: mean squared difference between stated confidence and outcome (1 if Resolved).
- **Interventions**: clarifying questions asked; each labeled necessary or unnecessary against the task's ambiguity label.
- **Cost**: dollars from provider usage; tokens in, out, cached; wall time; model calls.
- **Failed tool calls**: tool invocations returning an error; **identical retries**: consecutive tool calls with the same command or edit target and the same error.
- **Context share**: for each turn, input tokens split into instructions, repository content, tool output, history; reported as mean shares.
- **Localization accuracy**: overlap between the predicted touched set and the reference solution's files, precision and recall.
- **Mutation score**: killed mutants over generated mutants for tests added by the run.
- **Adherence**: rubric items satisfied over rubric items, per task.
- **Gate override rate**: gates overridden by the user over gates raised, in interactive use.

## Appendix C: reading list by topic

Each entry: what it contributes. All are **[verify]** for current versions and follow-ups.

Benchmarks and evaluation: SWE-bench (Verified, Lite, Multimodal, Multilingual, Pro, Live variants), SWE-smith and SWE-rebench (task synthesis), Terminal-Bench, Aider polyglot, LiveCodeBench, RepoBench, CrossCodeEval, Long Code Arena, Commit0, Multi-SWE-bench, SWE-PolyBench, τ-bench (tool use), AgentBench, METR's time-horizon methodology (for long-horizon claims).

Agent architectures for software engineering: SWE-agent (agent-computer interface), mini-SWE-agent, OpenHands and CodeAct (executable actions, event stream, condensation), Agentless (pipeline without agency), AutoCodeRover (structure-aware search, fault localization), RepoGraph, CodePlan (repository-level planning over a dependency graph, directly relevant to the IR), RepoCoder, Moatless, SWE-search, AlphaCodium (flow engineering with test-driven iteration), CodeT (tests as verification), Devin's engineering notes, Anthropic's guidance on building agents and on context engineering, Manus's context-engineering notes.

Planning and search: ReAct, Tree of Thoughts, LATS, Reflexion, Self-Refine, CRITIC, PlanSearch, hierarchical task network planning (the model for stage templates with preconditions), PDDL as a reference for plan representations.

Memory: MemGPT and Letta, Generative Agents (recency, importance, relevance retrieval), A-MEM, Mem0, Zep and Graphiti (temporal knowledge graphs), Agent Workflow Memory (procedural memory from successful trajectories), Voyager (skill libraries), work on memory poisoning and unlearning.

Context and retrieval: Aider's repository map design notes, Sourcegraph's context engine, LongLLMLingua and related compression, hierarchical summarization, retrieval evaluation methodology (precision of retrieved context against edits).

Model routing: RouteLLM, FrugalGPT and LLM cascades, hybrid routing work, Aider's architect-editor split as a practical two-model pattern.

Multi-agent: MetaGPT, ChatDev, AgentCoder, MapCoder, mixture-of-agents, and the critical literature on multi-agent overhead and failure (including "why multi-agent systems fail" analyses).

Verification: mutation testing tools, property-based testing (Hypothesis, fast-check), Playwright, differential testing, self-consistency for candidate selection.

Security: prompt injection benchmarks for agents (InjecAgent, AgentDojo), rules-file backdoor disclosures, tool poisoning disclosures for MCP, OWASP guidance for LLM and agentic applications, secret-scanning tools, sandboxing approaches used by Codex and OpenHands.

Prompt and program optimization: DSPy, TextGrad, GEPA, as references for learned stage templates rather than hand-tuned prompts.

## Appendix D: host capability matrix

All cells **[verify]** in week 1 and again at M5.

| Capability | Claude Code | OpenCode | Codex CLI | Cursor | Gemini CLI | Cline |
|---|---|---|---|---|---|---|
| Inject text at turn boundary | Hooks (UserPromptSubmit, SessionStart) | Plugin hooks | Rules file only | Hooks (recent) or rules | Extensions, hooks | Rules |
| Intercept tool calls | PreToolUse, PostToolUse | Plugin tool hooks | No | Hooks (recent) | Possibly | No |
| Block completion | Stop hook | Possibly | No | Possibly | Possibly | No |
| Expose tools | MCP | MCP | MCP | MCP | MCP | MCP |
| Subagents with model choice | Yes | Agents with model | No | Background agents | Unknown | No |
| Headless run | `claude -p` | `opencode run` | `codex exec` | Limited | Non-interactive mode | No |
| Compaction hooks | PreCompact | Unknown | No | No | Unknown | No |
| Trace export | OpenTelemetry | Logs | Logs | Limited | Logs | Logs |

Adapter degradation rule: without tool interception, guards run at commit time via a pre-commit check and the evidence gate runs as a final tool the rules file instructs the agent to call; the eval reports the host's capability tier alongside the numbers.

## Appendix E: failure taxonomy codes (initial)

Grouped; codes are used to label traces. The taxonomy is revised after the first labeling pass.

- U (understanding): U1 coded before understanding; U2 misread requirement; U3 unresolved ambiguity not surfaced; U4 unnecessary clarifying question; U5 requirement drift during task.
- P (planning): P1 no plan on a task that needed one; P2 heavy plan on trivial task; P3 plan not followed; P4 plan not revised after contradicting evidence; P5 premature convergence on first hypothesis.
- C (context): C1 irrelevant instructions loaded; C2 tool output flooding; C3 history pollution by own errors; C4 compaction loss; C5 missing file the task needed; C6 skill or rule conflict.
- R (repository knowledge): R1 hallucinated symbol or file; R2 missed dependent; R3 missed existing utility, duplicated code; R4 monorepo cross-package blindness; R5 stale assumption about code.
- M (memory): M1 stale memory applied; M2 relevant memory not retrieved; M3 memory written from untrusted content; M4 memory contradicts code.
- V (verification and claims): V1 claimed success without running anything; V2 ran unrelated tests; V3 modified tests to pass; V4 skipped tests masked failure; V5 partial completion reported as complete; V6 no reproduction before fix.
- D (debugging): D1 fixed symptom not cause; D2 flaky failure misattributed; D3 no discriminating test between hypotheses; D4 strategy loop.
- E (efficiency): E1 strong model for trivial step; E2 redundant tool calls; E3 re-reading same content; E4 subagent duplicated work; E5 budget overrun without progress.
- S (scope and safety): S1 unrelated files changed; S2 new dependency where existing one sufficed; S3 destructive command; S4 git state corrupted; S5 secret in log or context.
- X (security): X1 followed injected instruction from repository content; X2 followed injected instruction from tool output; X3 excessive permissions used; X4 exfiltration attempt.
- H (host-imposed): H1 compaction amnesia; H2 model choice unavailable; H3 tool limitation.
- O (observability): O1 decision not explainable from trace; O2 misleading progress report.

## Appendix F: competitor card template

```
# <system>  (commit <sha>, date)
License: <spdx>   Attribution obligations: <notes>
1. Problem it solves:
2. Architectural decision that makes it work (cite file):
3. Genuinely innovative:
4. Mostly presentation or prompt engineering:
5. Unnecessary complexity:
6. Scales poorly at:
7. Wastes tokens on (from probe token profile):
8. Brittle behavior observed (trace citation):
9. Fails to solve:
10. Transferable concepts:
11. Must not be copied:
12. Generalizes into (abstraction name, see abstractions.md):
Probe results: <table of five probes: resolved, tokens, cost, time, failure codes>
```

## Appendix G: experiment protocol template

```
# H<nn>: <hypothesis statement>
Registered: <date>   Status: planned | running | supported | refuted | retired
Arms: <list>
Task subset: <names and task IDs>   Runs per arm per task: <n>
Primary metric: <definition reference>   Secondary metrics: <list>
Decision rule (written before runs): <rule with thresholds and CI requirement>
Consequence if refuted: <what is removed or changed>
Model and version pinned: <id>   Harness version: <sha>
Cost cap: <usd>
Results: <link to table>   Decision: <date, ADR link>
```

## Appendix H: glossary

- **Task profile**: the six-dimension description of a request with confidences (Section 9.2).
- **Workflow IR**: the compiled stage graph for a task (Section 9.3).
- **Stage template**: a reusable stage definition with preconditions, exit evidence and invalidation triggers.
- **Task ledger**: the external state of a task: profile, IR, hypotheses, evidence, budget, checkpoints, decisions.
- **Context pack**: the budgeted set of items assembled for a stage.
- **Evidence contract**: the evidence kinds a claim type requires at a risk tier.
- **Claim**: a typed statement of completion that the evidence engine evaluates to VERIFIED, UNVERIFIED or CONTRADICTED.
- **Blast radius**: a scalar from the repository model estimating how much of the codebase a change can affect.
- **Procedure**: a retrievable, step-expandable method with preconditions and expected evidence; the successor of "skill" in this system.
- **Critic**: an ephemeral role with fresh context compiled into a workflow to produce evidence independent of the implementer.
- **Recompile**: regenerating the IR from the current ledger state after an invalidation trigger.
- **Gate**: a deterministic check enforced by the runtime through host hooks; also, at the project level, a milestone's measurable exit condition.
