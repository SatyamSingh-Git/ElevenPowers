# Annotated reading list

Started 2026-09-09. Each entry: what it claims, how strong the evidence is, what it changes in the plan. Entries marked (abstract only) were read from the arXiv abstract page and need a full read before their numbers are relied on.

## Benchmarks and their reliability

**SWE-bench Verified is saturated and contested.** Leaderboard aggregators (llm-stats, benchlm, steel.dev, swebench.com, all checked 2026-09-09) show frontier models clustered at 95 to 97 percent. Secondary reporting states OpenAI stopped reporting the benchmark in February 2026 after an audit found a large share of tasks with flawed tests and evidence of gold-patch memorization. Evidence strength: leaderboards are primary; the audit claim is second-hand and must be traced to the original before citing. Plan change: SWE-bench Verified is dropped as a discriminating suite. It may still supply a few bug-fix tasks whose tests have been re-verified, but nothing is concluded from it.

**SWE-bench Pro** (Scale AI, arXiv 2509.16941; public leaderboard at scale.com and aggregators). 1,865 tasks, 41 actively maintained repositories, Python, Go, TypeScript, JavaScript; tasks are consecutive-commit pairs with tests; a commercial subset on private codebases prevents contamination structurally; a held-out set monitors overfitting. Public-set leaders were reported around 59 percent in August 2026, so it still discriminates. **SWE-Bench Pro Verified** (arXiv 2609.08149) is a cleaned subset. Plan change: SWE-bench Pro public set becomes the primary external source for bug-fix, feature, and multi-language categories; its held-out discipline is copied for our own suite.

**SWE-rebench V2** (arXiv 2602.23866; swe-rebench.com). Automated, language-agnostic, continuously refreshed task collection with decontaminated evaluation. Plan change: use as the source for the "unfamiliar repository" and "large repository" categories, since freshness defeats memorization.

**Terminal-Bench 2.0** (tbench.ai). 89 tasks, each attempted 5 times per agent; covers software engineering, sysadmin, data, security. Top scores in the 60 to 83 percent range depending on the aggregator, so it discriminates. Plan change: source for environment-heavy tasks (dependency upgrade, failing suites, build repair); its 5-attempt protocol is adopted as the run count for the smoke tier.

**Harness-Bench** (arXiv 2605.27922, abstract only). Defines the harness as "the system layer that manages context, tools, state, constraints, permissions, tracing, and recovery". 106 sandboxed tasks reviewed for realism, solvability, oracle-checkability and integrity; 5,194 trajectories; reports completion, process quality, efficiency and failure behavior; concludes capability must be reported per model-harness pairing. Plan change: this is the closest existing methodology to Phase D. Adopt its four metric families as top-level headings, and consider running our arms on its 106 tasks as an external cross-check once our harness works.

**ChainSWE** (arXiv 2607.02606): multi-bug maintenance chains. **TestEvo-Bench** (arXiv 2607.02469): test and code co-evolution, live. **REAP / Harvest** (arXiv 2604.01527): benchmark curated automatically from real developer-agent sessions, solve rates 43 to 58 percent across five frontier models. Plan change: candidate sources for the multi-service and failing-suite categories; REAP's idea of mining real sessions is the same idea as our trace mining and should be cited.

**Position: Coding Benchmarks Are Misaligned with Agentic Software Engineering** (arXiv 2606.17799, abstract only). Three misalignments: model, harness and environment are collapsed into one score; grading against a single reference penalizes equivalent solutions; no component-level signals. Plan change: the harness must (1) hold the model fixed across arms so the harness is the only variable, (2) grade by hidden tests plus a rubric rather than diff similarity to one reference, (3) log component-level signals (localization accuracy, evidence coverage, scope) alongside the end score. All three were already in v0.1; the paper is now cited as the reason.

## The false-success problem

**Confident and Wrong: Silent Semantic Failures in Coding Agents** (Aman Mehta, arXiv 2603.25764, abstract only). 1,750 trajectories on 50 SWE-bench Verified tasks. Submission rate versus test-verified resolve rate: one frontier model submitted on 100 percent of runs and resolved 44 percent; another submitted 99 percent and resolved 18 percent; a third submitted 70 percent and resolved 50 percent. Silent semantic failures accounted for 68 to 80 percent of failures. Causes: action bias (editing when abstaining is correct), completion metrics that reward submission, monitoring that cannot detect the failures. Lightweight pre-edit prompts were insufficient. Plan change: the false-success metric is renamed and defined as the **submit-resolve gap** to match this paper; abstention becomes a first-class correct outcome in the task suite (tasks where the right answer is "cannot be done as asked" or "needs a decision"); the finding that prompts do not fix action bias is direct support for the plan's runtime-gate thesis and is cited under hypothesis H2.

## Harness design as a field

**From Question Answering to Task Completion: A Survey on Agent System and Harness Design** (Guo et al., arXiv 2606.20683, abstract only). Decomposes a harness into six coupled runtime responsibilities: Observation, Context, Control, Action, State, Verification. Argues agent quality emerges from the interaction of model, runtime, task structure and evaluation design. Open problems listed: value-aware evaluation, safety guarantees, harness generalization across domains, model-harness co-evolution. Plan change: the competitor map's axes are reorganized around these six responsibilities plus three the survey does not name (memory across sessions, security trust model, host coupling). The plan's own components map onto the taxonomy: Intake and Compiler are Control; Context engine is Context; Task ledger is State; Evidence engine is Verification; Repo model is Observation; adapters are Action.

**Natural-Language Agent Harnesses** (Pan et al., arXiv 2603.25723, abstract only). Represents run-level harness policy as an editable natural-language document executed by an "Intelligent Harness Runtime" that interprets it into calls, handoffs, state updates, validation gates and artifact contracts. Reports comparable performance to code harnesses with much shorter static policies on coding, terminal and computer-use benchmarks. Plan change: this is prior art for the workflow IR and must be cited. It also creates a real design question: should the compiled workflow be structured data (our v0.1) or a natural-language policy document interpreted by the runtime? Added as hypothesis H19: structured IR versus natural-language policy on the same runtime, measured on adherence, tokens and editability by users.

**Tmax: A simple recipe for terminal agents** (arXiv 2606.23321) and **What Makes Interaction Trajectories Effective for Training Terminal Agents** (arXiv 2606.03461): to be read for what minimal harnesses achieve, in the spirit of mini-SWE-agent; likely evidence that a small number of well-chosen mechanisms beats feature count.

**Efficient Benchmarking of AI Agents** (arXiv 2603.23749): to be read for the statistics of agent evaluation (how many runs, how to bound cost); directly relevant to the minimum-detectable-effect problem in Section 8.5 of the plan.

## Instruction files and repository guidance

**Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?** (Gloaguen et al., ETH SRI Lab, arXiv 2602.11988, February 2026; read via secondary summaries, full read pending). Across several models and agents, context files did not generally improve success while raising inference cost by more than 20 percent on average. LLM-generated context files lowered success by about 3 percent and raised cost over 20 percent; developer-written files raised success by about 4 percent but still raised cost up to 19 percent and added steps. Agents followed the files "too diligently": repository-specific tool usage jumped from near zero to several calls per task when mentioned. Plan change: this is the strongest external evidence for hypothesis H8 (instruction dilution) and for the design rule that repository guidance is retrieved when relevant rather than loaded at startup. BMAD v6 cites this work as its reason for retiring repository-scan skills, which is an example of a framework already acting on it. The plan's Context engine must be evaluated against a "no instruction file at all" arm, not only against "framework instruction file".

**Instruction Adherence in Coding Agent Configuration Files: A Factorial Study of Four File-Structure Variables** (arXiv 2605.10039). To be read: which structural properties of instruction files change adherence; informs how the runtime writes the short rules file it does ship.

**Probe-and-Refine Tuning of Repository Guidance for Coding Agents** (arXiv 2606.20512). To be read: automated tuning of repository guidance from probe runs; a possible mechanism for the learning loop's "proposal then replay" step applied to instruction text.

**Harness Engineering for Agentic AI Coding Tools: An Exploratory Study** (arXiv 2602.14690) and **Cheap Code, Costly Judgment: A Case Study on Governable Agentic Software Engineering** (arXiv 2607.01087). To be read: practitioner-level evidence on where harness effort pays off and where judgment, not code generation, is the bottleneck.

## Adjacent systems studied from source (cards in `cards/`)

**OpenHands** (now `OpenHands/software-agent-sdk`, MIT, commit 6a1e4d0, 2026-09-09; the original repository is only a frontend). Append-only event log with condensation as a tombstone event and legal cut points derived from provider message-shape invariants; HARD versus SOFT condensation with a hard reset; cache-tiered prompt sections; three-layer security (actor self-rating, shell-AST policy rails, optional guardrail model); a `/goal` loop with an evidence-demanding judge; two-tier MEMORY.md with a 6,000-character budget; can drive Claude Code, Gemini CLI, or Codex as the agent over ACP. Weaknesses: summaries built from 500-character previews; stuck detector halts on deliberate test re-runs; 10 to 15k tokens of prompt per turn. Plan change: the tombstone-condensation pattern and the evidence-demanding judge are prior art for the ledger and the evidence engine; the stuck-detector failure on flaky re-runs is added to the failure taxonomy (D4 needs a "deliberate repeat" exemption).

**Agentless** (MIT, commit 5ce5888, 2024-12-22). Fixed pipeline: file localization by structure plus embeddings with vote fusion, element and line localization, 4 by 10 repair samples, LLM-pruned regression suite, 40 blind reproduction tests, AST-normalized majority vote. Reported cost about $0.34 per issue with a 2024 model. Python-only, SWE-bench-only. Plan change: sample-then-select with AST-normalized voting and the "which tests to exclude" prompt become the bug-fix stage template; its regression filter keeps the minimum failure count rather than zero, which is a false-success source to avoid.

**AutoCodeRover** (commit 585d3e6, 2025-04-24). Search-agent loop over an AST index with eight typed search APIs, a grounded bug-location contract (file, class, method, intended behavior re-resolved to line ranges), optional spectrum-based fault localization, reproducer and reviewer agents. License is Sonar Source-Available v1.0, not open source, and its non-competitive-purpose clause reads as forbidding use with external AI tooling. Plan change: ideas only, no code reuse; the grounded bug-location contract is adopted as the output schema of the debugging isolate stage.

**Hook standard across hosts** (from `hosts/`). Codex CLI (Apache-2.0, commit b4d4205, 2026-09-09) has a full Claude-Code-style hook engine (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `SessionStart`, `Stop`, `SubagentStop`, `PreCompact` and more) whose engine struct is named after Claude hooks, plus `codex exec --json` with usage per turn and `--output-schema`. Gemini CLI (Apache-2.0, commit ed2ac40, 2026-09-08) has `BeforeAgent`, `BeforeTool`, `AfterTool`, `AfterAgent` (which can deny completion and retry), `BeforeModel` (which can rewrite the whole request), a TOML policy engine, and `gemini -p --output-format stream-json`. Cline and Continue CLIs copy the Claude Code hook schema verbatim. OpenCode has tool hooks but no session-end block. Plan change: the adapter contract's three capabilities exist natively on Claude Code, Codex, Gemini, Cline CLI and Continue CLI; only OpenCode needs the degraded path. Portability is a week of adapter work per host, not a milestone.

## Still to read (from v0.1 list, unchanged priority)

Agent architectures: SWE-agent, mini-SWE-agent, OpenHands and CodeAct, Agentless, AutoCodeRover, RepoGraph, CodePlan, Moatless, SWE-search, AlphaCodium, CodeT. Planning: ReAct, Tree of Thoughts, LATS, Reflexion, PlanSearch, hierarchical task networks. Memory: MemGPT and Letta, Generative Agents, A-MEM, Mem0, Zep and Graphiti, Agent Workflow Memory, Voyager. Context: Aider's map notes, LongLLMLingua. Routing: RouteLLM, FrugalGPT. Multi-agent failure analyses. Security: InjecAgent, AgentDojo, rules-file backdoor and MCP tool-poisoning disclosures. Optimization: DSPy, TextGrad, GEPA.

---

## Added 2026-09-11, from the external audit

These eight are the audit's recommended additions. Each carries the limit on what
may be inferred from it, which is the part this list has previously been worst at
recording.

**[mini-SWE-agent](https://mini-swe-agent.com/latest/).** A small, current,
reproducible worker harness. *Take:* use it as a baseline in Phase B. *Limit:*
its simplicity is a useful comparison, not proof that custom tooling never helps.

**[SWE-agent: Agent-Computer Interfaces](https://arxiv.org/abs/2405.15793).**
*Take:* the interface offered to a model is itself an experimental variable, so
it belongs in the treatment description rather than the background. *Limit:* its
historical scores are not today's ceiling.

**[SWE-Search](https://arxiv.org/abs/2410.20285).** *Take:* search over
alternative actions and trajectories is an established direction, which is
evidence the v0.7 outer loop is not eccentric. *Limit:* do not build a full
search tree before a candidate-pool baseline shows remaining headroom.

**[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).**
*Take:* targeted retrieval, compact working state, recoverable references — the
shape of §5.3. *Limit:* engineering guidance, not a measured intervention here.

**[SWE-smith](https://arxiv.org/abs/2504.21798).** *Take:* large executable task
and trajectory datasets are a route to training a specialised worker later.
*Limit:* synthetic generation is not independent evaluation, and training is a
Phase E investment.

**[Proof-or-Stop](https://arxiv.org/html/2607.14890v1).** *Take:* the
claim/evidence/gate precedent and its narrowly measured fault detection. *Limit:*
its injected-fault, single-family design does not calibrate the natural failure
rate or the power requirement of this project's experiment. Previously cited here
as though it did.

**[Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
(OpenAI, July 2026).** *Take:* substantial task and test defects reported in
SWE-bench Pro public, with an earlier recommendation withdrawn. **This directly
contradicts the entry above in this file**, which made SWE-bench Pro public the
primary external source. *Limit:* a vendor audit is evidence to inspect and
version, not licence to discard inconvenient benchmark outcomes.

**[SWE-Bench Pro Verified](https://arxiv.org/html/2609.08149v1).** *Take:*
proposed task refinements and protections against answer leakage, including
channels beyond local git history. *Limit:* first posted 8 September 2026;
validate the chosen release independently before adopting it.

**Supporting the search direction, with their limits:**

- [Scaling Test-Time Compute for Agentic Coding](https://arxiv.org/html/2604.16529v1) — structured rollout summaries, recursive tournament voting, parallel-distill-refine; reported 70.9 to 77.6 percent on SWE-Bench Verified and 46.9 to 59.1 on Terminal-Bench v2.0. *Limit:* substantial extra inference on specific older model and harness combinations. Supports running the experiment, not an expected uplift.
- [Infrastructure noise](https://www.anthropic.com/engineering/infrastructure-noise) — material score changes with model and harness held fixed, around six percentage points across Terminal-Bench configurations. *Limit:* not an estimate for this project, but it makes environment control a competing investment rather than hygiene.
- [Roulette-mode model mixing](https://www.swebench.com/post-250820-mini-roulette.html) — complementary benefits in some model combinations, none in another. *Limit:* an illustrative older experiment.
- [Towards a Science of Scaling Agent Systems](https://arxiv.org/abs/2512.08296) — multi-agent benefit depends strongly on task structure and coordination. *Limit:* not a direct coding-benchmark effect estimate.
- [GEPA](https://arxiv.org/abs/2507.19457) — prompt and procedure optimisation from execution feedback. *Limit:* does not show that optimising this controller improves repository-level patch selection. Phase E at the earliest.
- [Evaluating AGENTS.md, v2](https://arxiv.org/html/2602.11988v2) — generated and developer-provided context files generally did not improve success while increasing cost. *Revises* the stronger developer-file benefit suggested by the older secondary summary previously recorded here.

**The standing correction this section exists to make.** Several entries above
were written from secondary summaries and stated more than their sources
support. Every entry added from here carries its limit in the same breath as its
claim, and an entry that contradicts an earlier one says so explicitly rather
than being quietly appended.
