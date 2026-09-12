> **The original brief, kept verbatim.**
>
> This is the document the project started from, committed 2026-09-09 before any
> research or code existed. It is preserved unedited, with nothing revised in
> hindsight, because every later plan is judged against it — `PLAN.md` v0.7 exists
> precisely because an external audit argued the work had drifted from what this
> asked for, and the argument only stands because the ask is on record.
>
> It is a brief, not documentation. What actually happened is
> [01-origins.md](01-origins.md), which begins by explaining why the first plan
> written from this was the wrong way to start.

---

You are not being asked to build another collection of prompts, another coding-agent wrapper, another skills repository, or a simple combination of existing open-source projects.

Your objective is much more ambitious:

Design and build a genuinely next-generation agentic software engineering system that can make existing coding agents dramatically more capable, reliable, intelligent, autonomous, efficient, adaptive, and useful.

Treat this as an opportunity to rethink how AI-assisted software engineering should work from first principles.

Do not constrain yourself to my current ideas.

Do not assume that the architecture I suggest is correct.

Do not preserve ideas merely because I mentioned them.

Challenge everything.

Research deeply.

Experiment.

Measure.

Discard weak ideas.

Invent better ones.

The end result should have a clear reason to exist even if projects such as Superpowers, Everything Claude Code, Spec Kit, gstack, BMAD, Aider, OpenCode, Cline, Continue, SWE-agent, and future competing systems already exist.

The goal is not:

"Take features from these repositories and combine them."

The goal is:

"Understand why the best systems work, identify what they still fail at, discover missing abstractions, and design something substantially more powerful."

---

# CORE MINDSET

Operate simultaneously as:

* a principal software architect
* an AI-agent researcher
* a compiler/runtime engineer
* a developer-tools founder
* a systems researcher
* an HCI/product designer
* an expert software engineer
* a security engineer
* an evaluation researcher
* an open-source maintainer

Think at the level of:

"What would agentic software engineering look like if we were designing it today without inheriting assumptions from current coding assistants?"

Do not optimize for making a flashy README.

Optimize for creating something that genuinely performs better.

---

# PHASE 1 — RESEARCH THE LANDSCAPE DEEPLY

Before deciding architecture, conduct a serious comparative study of the strongest relevant systems you can find.

At minimum investigate:

* obra/superpowers
* affaan-m/ECC
* github/spec-kit
* garrytan/gstack
* bmad-code-org/BMAD-METHOD
* Aider-AI/aider
* anomalyco/opencode
* cline/cline
* continuedev/continue
* swe-agent/SWE-agent

But do NOT limit research to this list.

Search aggressively for:

* emerging agent harnesses
* coding-agent frameworks
* autonomous software engineering systems
* agent memory systems
* agent orchestration research
* context-engineering systems
* repository understanding systems
* software-engineering benchmarks
* self-improving agents
* multi-agent systems
* LLM planning research
* tool-use architectures
* workflow engines
* compiler-inspired agent systems
* retrieval architectures
* verification systems
* agent security research
* model-routing systems
* long-horizon agent research

Include academic papers, benchmark systems, successful open-source projects, engineering blogs, and real-world lessons.

For every relevant system identify:

1. What problem is it solving?
2. What architectural decision makes it work?
3. What is genuinely innovative?
4. What is mostly presentation or prompt engineering?
5. What creates unnecessary complexity?
6. What scales poorly?
7. What wastes tokens?
8. What creates brittle behavior?
9. What does it fail to solve?
10. What concepts are transferable?
11. What should explicitly NOT be copied?
12. What can be generalized into a stronger abstraction?

Keep attribution and licenses in mind.

Learn from ideas freely.

If code, prompts, documentation, or substantial implementation is reused, preserve whatever attribution/license obligations apply.

Prefer original implementations and original abstractions.

---

# PHASE 2 — FIND THE UNSOLVED PROBLEMS

Do not start building until you understand the major weaknesses of current coding agents.

Investigate failures such as:

* agents coding before understanding the task
* weak architectural reasoning
* unnecessary planning for trivial tasks
* insufficient planning for difficult tasks
* context-window pollution
* loading too many skills
* loading irrelevant instructions
* hallucinated repository understanding
* poor long-term memory
* stale memory
* inability to determine which memory matters
* agents claiming success without evidence
* incomplete testing
* shallow debugging
* fragile browser/UI verification
* repeated mistakes across sessions
* excessive token usage
* expensive models being used for trivial work
* weak model selection
* uncontrolled multi-agent overhead
* subagents duplicating work
* agents changing unrelated files
* requirement drift
* specification drift
* security regressions
* failure to reason about blast radius
* inability to predict downstream effects
* poor handling of huge repositories
* weak dependency understanding
* lack of confidence calibration
* tool misuse
* insufficient rollback strategies
* inability to learn from failed approaches
* long-running tasks losing direction
* enormous instruction files
* brittle slash-command workflows
* excessive human babysitting
* poor observability into agent decisions

Discover additional failure modes yourself.

Then identify which failures are fundamental versus merely implementation problems.

---

# PHASE 3 — QUESTION THE CURRENT PARADIGM

Do not assume the future architecture should consist of:

skills + agents + prompts + commands.

Those may be implementation details rather than the correct abstraction.

Explore radically different possibilities.

For example:

Could agent workflows behave more like compilers?

User Intent
↓
Semantic Analysis
↓
Risk Analysis
↓
Repository Analysis
↓
Workflow Intermediate Representation
↓
Optimization
↓
Execution Plan
↓
Runtime
↓
Verification

Could development tasks be compiled into an intermediate representation?

Could the system transform:

"Add Stripe subscriptions"

into something machine-readable like:

TaskGraph
{
requirements
dependencies
affected_components
security_constraints
verification_requirements
uncertainty
execution_strategy
}

Could workflow optimization then eliminate unnecessary stages?

Could agents be dynamically created rather than statically defined?

Could roles emerge from the task instead of living in an `/agents` directory?

Could skills be retrieved as knowledge rather than injected as full prompts?

Could workflow generation be learned from previous successful executions?

Could verification requirements be derived automatically from risk?

Could the system maintain a causal representation of the repository?

Could agent output be treated as hypotheses requiring evidence?

Explore these ideas and invent better ones.

---

# PHASE 4 — DESIGN A TASK INTELLIGENCE LAYER

The system should deeply understand a request before acting.

Consider dimensions such as:

* complexity
* ambiguity
* novelty
* blast radius
* reversibility
* security risk
* financial risk
* privacy risk
* migration risk
* architectural impact
* UI impact
* performance impact
* dependency impact
* testability
* research requirement
* repository familiarity
* confidence
* expected cost
* expected duration
* potential parallelism

Do not assume these dimensions are sufficient.

Design something better if appropriate.

The result should guide everything downstream.

A three-line CSS modification and a payment architecture redesign must not trigger equivalent workflows.

---

# PHASE 5 — DYNAMIC WORKFLOW COMPILATION

Investigate building a Workflow Compiler.

Instead of forcing users to execute:

/brainstorm
/spec
/plan
/tasks
/implement
/review
/qa

the system should determine what is actually necessary.

Example:

TASK:
"Change button border radius."

Possible compiled workflow:

inspect
→ modify
→ visual verification

TASK:
"Fix intermittent authentication race condition."

Possible compiled workflow:

reproduce
→ inspect execution path
→ generate hypotheses
→ instrument
→ isolate root cause
→ implement minimal fix
→ regression tests
→ concurrency verification

TASK:
"Introduce subscription billing."

Possible workflow:

research
→ requirements
→ threat/risk analysis
→ architecture
→ API/webhook design
→ migration plan
→ implementation plan
→ isolated implementation
→ tests
→ integration verification
→ security review
→ failure simulation
→ rollout strategy

Workflows should be generated, optimized, and adaptable.

They should be able to change while executing when evidence invalidates assumptions.

---

# PHASE 6 — CONTEXT INTELLIGENCE

Treat context as a scarce computational resource.

Do not blindly dump:

* repository files
* memory
* instructions
* skills
* documentation
* tool output
* chat history

into the model.

Design a Context Engine capable of selecting the smallest sufficient context.

Explore:

* semantic retrieval
* symbol graphs
* dependency graphs
* repository maps
* embeddings
* lexical retrieval
* call graphs
* git history
* ownership
* test relationships
* architectural boundaries
* recently modified code
* runtime evidence
* specification artifacts
* user preferences
* previous failures

Potential objective:

maximize useful information
while minimizing irrelevant tokens.

Consider dynamic context budgets based on model, task phase, uncertainty and cost.

Investigate context compression, hierarchical summaries, graph retrieval, selective expansion and just-in-time retrieval.

---

# PHASE 7 — REPOSITORY INTELLIGENCE

Move beyond flat file search.

Explore creating a living repository model containing relationships such as:

symbol → defined in
symbol → called by
component → depends on
component → tested by
service → writes table
route → invokes service
service → emits event
feature → touches files
module → recently changed
module → historical bugs
module → owner
module → architectural boundary

Potentially build a repository knowledge graph.

But do not build one simply because it sounds sophisticated.

Benchmark whether it actually improves agent performance.

Find the simplest architecture that provides meaningful gains.

---

# PHASE 8 — MEMORY THAT ACTUALLY HELPS

Do not implement memory as "save everything."

Design memory around usefulness.

Potential memory classes:

* project facts
* architectural decisions
* user preferences
* recurring mistakes
* debugging discoveries
* successful strategies
* failed strategies
* environment quirks
* deployment knowledge
* repository conventions

Memory should have properties like:

* source
* confidence
* timestamp
* scope
* relevance
* supersession
* verification state
* decay
* conflicts

Old or incorrect memories must not poison future tasks.

Explore automatic consolidation.

Explore forgetting.

Explore conflict resolution.

Explore deciding whether something is worth remembering at all.

---

# PHASE 9 — ROLE AND AGENT ROUTING

Do not spawn multiple agents just because multi-agent systems sound impressive.

Agents have overhead.

Determine when multiple independent reasoning processes actually provide value.

Possible perspectives include:

* implementer
* architect
* debugger
* security reviewer
* QA
* product thinker
* performance engineer
* database engineer
* researcher
* critic
* release engineer

But these should not necessarily be static personas.

Explore dynamic roles generated from the task.

Example:

A database migration may need:

Schema Safety Reviewer

rather than generic:

Database Agent.

A payment workflow may need:

Adversarial Payment Failure Analyst.

Roles could be task-specific and ephemeral.

---

# PHASE 10 — MODEL ROUTING

Treat models as interchangeable compute resources with different capabilities.

Build intelligence around choosing models based on:

* reasoning difficulty
* coding capability
* context size
* vision requirements
* latency
* cost
* tool use
* reliability
* parallel workload
* task importance

A trivial lookup should not consume the strongest reasoning model.

A difficult architecture decision should not be delegated to the cheapest model merely to save cost.

Explore model escalation:

cheap model
→ uncertainty detected
→ stronger model

Explore ensemble reasoning only where it measurably improves results.

---

# PHASE 11 — EVIDENCE-BASED SOFTWARE ENGINEERING

Agents must not be allowed to claim success merely because code was written.

Design an Evidence Engine.

Every meaningful completion claim should be supported.

For example:

CLAIM:
Authentication bug fixed.

EVIDENCE:

* failing test reproduced before fix
* regression test passes
* existing authentication tests pass
* relevant lint/type checks pass
* observed error condition cannot be reproduced

CONFIDENCE:
0.94

STATUS:
VERIFIED

If evidence is missing:

STATUS:
UNVERIFIED

Possible evidence sources:

* tests
* builds
* static analysis
* runtime output
* screenshots
* browser interactions
* logs
* benchmarks
* database assertions
* API responses
* security scanners
* diffs
* deployment health

Think beyond this list.

---

# PHASE 12 — ADAPTIVE VERIFICATION

Verification depth should scale with risk.

Changing documentation:

minimal verification.

Changing a payment webhook:

extensive verification.

Potential techniques:

* unit tests
* integration tests
* E2E tests
* property-based tests
* fuzzing
* mutation testing
* browser testing
* screenshot comparison
* accessibility checks
* static analysis
* security scanning
* load testing
* fault injection
* migration simulation
* rollback testing

Select intelligently rather than running everything.

---

# PHASE 13 — SELF-CORRECTION AND LEARNING

Design mechanisms by which the system becomes more effective over time without silently accumulating bad behavior.

After tasks, analyze:

* What assumptions were wrong?
* Which context was unnecessary?
* Which missing information caused failure?
* Which workflow stages helped?
* Which workflow stages were wasteful?
* Which model performed well?
* Which tool calls were unnecessary?
* What reusable discovery was made?
* What mistake should never be repeated?
* Should a new reusable capability emerge?

Do not automatically convert every experience into permanent instructions.

Use evidence.

---

# PHASE 14 — OBSERVABILITY

Humans should understand what the agent system is doing.

Consider exposing:

Task classification

Complexity: HIGH
Security risk: MEDIUM
Research requirement: HIGH

Selected workflow:

Research
→ Architecture
→ Implementation
→ Integration Tests
→ Review

Selected context:

14 files
2 architecture decisions
1 previous failure
3 relevant tests

Selected execution:

primary implementation model
security critic
browser verification

Estimated reasoning cost:
...

Actual:
...

Potentially expose why a stage was selected.

But balance observability against noise.

---

# PHASE 15 — FAILURE RECOVERY

Plan for agents to fail.

Build recovery mechanisms.

Possible strategies:

* checkpoints
* atomic changes
* git worktrees
* reversible edits
* automatic snapshots
* hypothesis tracking
* rollback
* alternative-plan generation
* escalating model strength
* fresh-context retries
* critic intervention
* human escalation

Avoid endless retry loops.

Detect when repeating the same strategy will not help.

---

# PHASE 16 — SECURITY

Agentic coding introduces new security problems.

Investigate:

* prompt injection from repository content
* malicious dependency instructions
* poisoned documentation
* malicious MCP/tool results
* secret leakage
* destructive commands
* excessive permissions
* supply-chain risks
* data exfiltration
* unsafe shell execution
* untrusted web content
* malicious issue descriptions
* compromised memory
* privilege boundaries

Consider trust levels for information sources.

Repository documentation should not automatically have authority over system-level policy.

---

# PHASE 17 — PROVIDER-INDEPENDENT ARCHITECTURE

Do not make the conceptual framework dependent on Claude Code.

Design a core runtime that could theoretically work across:

* Claude Code
* Codex
* OpenCode
* Cursor
* Gemini CLI
* Cline
* future coding agents

Use adapters.

For example:

```
                CORE
                 │
      ┌──────────┼───────────┐
      ↓          ↓           ↓
   Claude      Codex      OpenCode
      ↓          ↓           ↓
   Cursor      Cline       Future
```

Separate:

methodology

from:

agent implementation.

---

# PHASE 18 — PERFORMANCE AND COST

Maximize intelligence should be main goal, but you should slightly focus on cost optimization, if it dosnt reduces the performamnce. Main focus should be performance. 

Optimize:

quality
×
reliability
÷
cost
÷
latency

Explore:

* caching
* reusable artifacts
* incremental repository analysis
* parallel retrieval
* selective model escalation
* context deduplication
* token budgeting
* subagent limits
* redundant-work detection

Measure actual improvements.

---

# PHASE 19 — EVALUATIONS MUST BE FIRST-CLASS

Do not rely on personal impressions.

Create an evaluation system early.

Compare:

vanilla coding agent

vs

Superpowers

vs

ECC

vs

Spec Kit

vs

other appropriate systems

vs

our system.

Use representative tasks:

* tiny code change
* normal feature
* ambiguous feature
* bug fixing
* hard debugging
* refactor
* frontend task
* backend task
* database migration
* security-sensitive change
* large-repository task
* unfamiliar repository
* failing test suite
* performance optimization
* dependency upgrade
* multi-service change

Measure things like:

* task success
* hidden-test success
* regressions
* unnecessary modifications
* code quality
* test quality
* instruction adherence
* human interventions
* tokens
* cost
* latency
* failed tool calls
* number of retries
* context size
* verification completeness

Invent better metrics.

Benchmarks should shape architecture.

If an impressive-sounding feature does not improve measurable outcomes, remove or redesign it.

---

# PHASE 20 — BUILD THROUGH EXPERIMENTS

Do not attempt to implement the entire vision immediately.

Create hypotheses.

Example:

Hypothesis:
Dynamic skill retrieval reduces token usage without reducing task success.

Experiment:
Run 50 representative tasks.

Compare:

all skills loaded

vs

retrieved skills only.

Measure:

success
tokens
latency
errors.

Then make the architectural decision based on results.

Do this repeatedly.

Build scientifically.

---

# OPEN-ENDED INNOVATION DIRECTIVE

Everything above is a starting point, not a specification.

You have permission to propose ideas radically different from mine.

If you discover:

* a better architecture
* a new abstraction
* an unknown research direction
* an unexpected optimization
* a new type of memory
* a better workflow representation
* a better agent interaction model
* a new verification paradigm
* a compiler architecture
* a planning representation
* an adaptive runtime
* a learning mechanism
* a better evaluation strategy

pursue it.

Do not suppress good ideas because they fall outside this prompt.

Actively look for ideas that neither I nor current frameworks have considered.

Ask:

"What assumption is everyone else making that might be wrong?"

"What becomes possible if we remove that assumption?"

"What would a system designed for agents—not humans pretending agents are developers—look like?"

---

# AVOID THESE FAILURE MODES

Do not produce a project whose main selling point is:

* 500 skills
* 100 agents
* lots of slash commands
* an enormous CLAUDE.md
* massive prompt files
* flashy terminology
* copying competitors
* unnecessary abstraction
* multi-agent orchestration everywhere
* complexity presented as sophistication

Complexity must earn its existence.

Every subsystem should answer:

"What measurable problem does this solve?"

---

# PRODUCT PHILOSOPHY

The framework should ideally make the user feel:

"I describe what I want, and the system figures out the engineering process required to accomplish it safely."

Not:

"I must learn 47 slash commands before my coding agent works properly."

Favor intelligence over configuration.

Favor adaptation over rigid workflows.

Favor evidence over confidence.

Favor retrieval over context dumping.

Favor tools over hallucination.

Favor verification over declarations.

Favor architecture over prompt accumulation.

Favor measurable outcomes over hype.

---

# POSSIBLE LONG-TERM NORTH STAR

A developer provides:

"Add organization-level SSO."

The framework independently determines:

* relevant repository architecture
* ambiguous requirements
* affected services
* likely security implications
* required research
* implementation strategy
* migration implications
* tests
* security validation
* rollout requirements

It retrieves only relevant information.

It constructs an optimized workflow.

It selects the appropriate models.

It delegates independent subtasks when beneficial.

It continuously verifies assumptions.

It adapts when evidence contradicts the plan.

It completes the implementation.

It proves what was verified.

It records only valuable reusable discoveries.

And it does all this with substantially less unnecessary context, cost, and human intervention than existing systems.

---

# YOUR IMMEDIATE TASK

Do NOT begin by generating hundreds of files.

Start by deeply researching the landscape.

Then produce:

1. A competitor architecture map.
2. A detailed gap analysis.
3. A list of the most important unsolved problems.
4. A set of potentially novel ideas.
5. Several competing architectural approaches.
6. Arguments for and against each.
7. An initial system architecture.
8. Explicit hypotheses that need benchmarking.
9. A minimal experimental prototype plan.
10. An evaluation strategy.
11. A roadmap driven by evidence rather than feature count.

Before accepting the architecture, attack it.

Ask:

* Why will this fail?
* Where is unnecessary complexity?
* Which components are speculative?
* What will consume excessive tokens?
* What will agents misuse?
* What won't scale?
* What competitors already do better?
* What would an expert researcher criticize?
* What would an expert developer hate using?
* Can 50% of the architecture be removed while retaining 90% of the value?

Then revise it.

Continue this research → hypothesis → prototype → benchmark → redesign loop throughout development.

---

# FINAL PRINCIPLE

Do not try to make the largest agent framework.

Try to make the smartest one.

The objective is not to create something that appears advanced.

The objective is to create something that causes coding agents to produce measurably better software with less supervision.

If achieving that requires rejecting major assumptions in this prompt, reject them.

If a better idea emerges, follow it.

You are authorized to rethink the entire problem.

Build the system you believe should exist.
