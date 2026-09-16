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

## The 2026-09-15 sweep — what re-aimed the plan

**The complete source list for this sweep is [audit_2026_09_15/sources.md](audit_2026_09_15/sources.md)** — every source with what it contributed, organised by topic. What follows here is the subset that changed the plan; the audit folder is the credit record.


Five parallel research passes, no paid runs. Sources below drive PLAN v0.8
sections 5.10 to 5.14 and the withdrawals added to section 10.

**A reading-fidelity warning that is part of the method now.** Two arXiv PDF
fetches in this sweep returned **fabricated numbers** — one produced a complete
table of per-model half-lives that does not exist in the paper. Entries below
are marked **(html)** where read from arXiv HTML or the abstract page, and
**(snippet)** where only a search summary was available. **No number in PLAN
v0.8 rests on a PDF summariser.** A snippet-only figure may not be quoted in
the plan without being promoted to html first.

### Discrimination: the finding that re-aimed the project

- [Validation evidence in agent rollouts](https://arxiv.org/abs/2607.28871) (html) — **46.0% of positive validation evidence carries no bug-discriminating information**; 23.8% of rollouts close with an entirely non-discriminating evidence base; 26.9% of bug-detecting tests fail on the developer's own correct fix. 3,730 validation events, 643 rollouts, 110 tasks. **The best methodology in the sweep**: prespecified smallest effect size, pre/post measurement. *Limit, and it is the important half:* their repair — feeding the contrast back to the agent — came in at −7.8pp and +7.4pp, **below their own prespecified 10pp threshold**. Detection is established; repair by feedback is not. Plan change: §5.10 exists because of this entry, and §5.12 applies to it. **Not replicated on our corpus, 2026-09-17:** 22 runs over 16 real tasks with two models produced **one** non-discriminating check, and it did not survive the other model being given the identical task. Their result stands on their corpus - 3,730 validation events against our 22 - and ours is recorded beside it rather than used to argue with it. The likeliest reason is the corpus: ours is well-specified tasks from well-maintained repositories, which is not where non-discriminating evidence would be expected to live. PLAN §10 withdraws our *frequency* claim, not theirs. `results/b4-discriminate/findings.md`.
- [PROBE](https://arxiv.org/abs/2604.01518) (snippet) — **77% of SWE-bench Verified instances admit a semantically incorrect patch that passes every existing test**; augmenting tests costs top-ten agents 4.2 to 9.0pp. *Limit:* snippet-only; corroborates the entry above by a different method, so the direction is safe and the figure is not yet quotable.
- [SpecBench](https://arxiv.org/html/2605.21384v1) (html) — every model saturates the visible test suite; the visible-to-held-out gap grows **~27pp per tenfold increase in LOC** (≤21pp under 10K LOC, up to 100pp over 25K). Neither more coverage nor more search removed it. *Limit:* single paper, and its tasks are built rather than mined. Plan change: it is why a SWE-bench-shaped corpus cannot show our effect (§0).
- [SWE-Mutation](https://arxiv.org/html/2605.22175v1) (html) — best model **10.2% verification, 36.15% mutant detection** when generating suites. *Limit:* single paper; non-Python degrades sharply.
- [PatchDiff / "Are Solved Issues Really Solved Correctly?"](https://arxiv.org/abs/2503.15223) (snippet, ICSE 2026, peer-reviewed) — **29.6%** of plausible patches diverge behaviourally from gold, **7.8%** counted correct while failing the developer suite, resolution rates **inflated 6.2 absolute points**. Plan change: §6 and §10 — no claim on a delta smaller than the instrument's validity error.

### Where the failure actually happens

- [Failure as a Process](https://arxiv.org/html/2607.09510) (html) — 1,184 failed trajectories, >63,000 steps, 7 models × 3 harnesses. **Epistemic 57.9%** (false premise **30.7%**, specification neglect 14.9%), competence 32.8%, environment 9.4%. **Median decisive error at step 7 of 27**; median recovery window one step; observable signals ~10 steps later; **82% keep executing past the point of no return**; best real-time recall 28.8%. *Limit:* Terminal-Bench, not repository issue-fixing, so transfer is assumed. Plan change: §5.11, and the strongest external support the thesis in §2 has ever had.
- [20,574 real coding-agent sessions](https://arxiv.org/abs/2605.29442) (snippet) — constraint violation 38.3%, misread intent 27.0%, **inaccurate self-reporting 22.6%**, faulty implementation 17.8%. Causes: instruction-following failure 36.5% against **underspecified instruction only 15.4%**. *Limit:* LLM-assisted labelling of logs, unreplicated, and **26.9% "cannot determine"** is a large hole. Plan change: §2's note that adherence, not specification, is the lever.
- [Coherence Collapse](https://arxiv.org/abs/2603.24631) (html abstract) — **60-69% of failures reach and edit the correct functions** and still produce a wrong patch; 5 cases produced a patch identical to the reference mid-trajectory and corrupted it; edit-commit checkpointing recovered all 5. Stated cost of the naive implementation: **10-40x test invocations**. *Limit:* 5 cases is an existence proof, not a rate; its edit-quality taxonomy is computed on one agent. Plan change: §1.2, and the cost line is why this architecture is the one that can afford it.
- [Accurate Failure Prediction Does Not Imply Effective Failure Prevention](https://arxiv.org/abs/2602.03338) (snippet) — harm concentrates in early interventions on runs that would have succeeded. *Limit:* I could not extract its tables; the qualitative claim is corroborated by this project's own 6.6x false block, which is why it is used as framing rather than as a figure. Plan change: §5.12.

### What actually improves outcomes

- [ORACLE-SWE](https://arxiv.org/abs/2604.07789) (snippet) — one oracle signal at a time from a 35% baseline: **reproduction test +28pp**, execution context +15pp, API usage +9pp, **perfect localisation +8pp**, regression test +2pp. *Limit:* single paper, snippet-read, and these are *oracle* signals — an upper bound, not a delivered gain. Plan change: §5.13, and the demotion of localisation in §8. The figure is quoted in the plan as a ranking, which is what it robustly supports.
- [Spec-first test generation](https://arxiv.org/abs/2608.17177) (snippet) — extract pre/post-condition contracts, then generate tests: **+9.8pp bug detection (p = 0.035)** on **90 real production bug-fix pairs**, four languages, 450 runs. *Limit:* single paper. Plan change: the shape Phase C1 copies — it helps at **oracle construction**, not at patch writing.
- [To Run or Not to Run](https://arxiv.org/abs/2606.26978) (snippet) — 7,745 traces, 3,000 repair attempts: prohibiting execution during repair costs **1.25pp, not significant**, while saving substantial tokens. Plan change: §5.13 — the lever is having the right test, not the freedom to run tests.
- [CodeMonkeys](https://arxiv.org/html/2501.14723v2) (html) — pool coverage **69.8%** against selected success **57.4%**, with **5.8% of spend** on selection. Corroborates §5.1.
- [Oracle Gap and Signal Fidelity](https://arxiv.org/html/2607.17531v1) (html) — selector gain *and harm*: public-test execution +8.14pp at 0% harm; same-model LLM judge +3.50pp at 4.69% harm; on a benchmark with only 3.03pp of oracle gap **every selector underperformed the baseline**. Plan change: the four-point rule in §0 and Phase B2.2 — measure the gap before building the selector.
- [N-Version Programming with Coding Agents](https://arxiv.org/abs/2606.20158) (html) — 48 implementations, 1,000,000 inputs, all 17,296 triplets. Voting cuts mean failures 66%, **but independence is decisively rejected: 429 coincident failures against 115 predicted, z = 29.20.** Agents converged on the same misreading of the spec. Plan change: §2 — voting cannot touch a shared false premise.

### Negative results the plan now defers on, rather than on judgement

- [Evaluating AGENTS.md v2](https://arxiv.org/html/2602.11988v2) (html) and an [independent 288-run ablation](https://arxiv.org/abs/2607.27250) (snippet) — context files null on correctness, **+20% cost**. Two populations, same direction. Plan change: §11.
- [Rethinking the Value of Multi-Agent Workflow](https://arxiv.org/html/2601.12307v1) (html) — a single agent running the same workflow sequentially matched or beat the multi-agent system across seven benchmarks at roughly a tenth the cost. Plan change: §8 drops role decomposition.
- [Measure Before You Manage](https://arxiv.org/html/2608.31057) (html) — the best-controlled agent-memory study: **no held-out contrast survives Holm correction**, and delivered-context parity failed in all ten constrained-arm pairs. Plan change: §11 defers memory with evidence.
- [Spec-driven development, surveyed](https://arxiv.org/abs/2609.00252) (snippet) — states plainly that no peer-reviewed study has defined, delimited or measured these frameworks. The one Spec Kit "study" is an uncontrolled 14-person before/after. Plan change: §10. **Absence of evidence, recorded as absence** — the same standard this project applied to the fourteen.
- [FixedBench / abstain-or-fix](https://arxiv.org/abs/2605.07769) (snippet) — agents make undesirable changes on **35-65%** of already-fixed tasks, but a caution prompt raising abstention 60→80% **collapsed repair of partially-broken code from 27.3% to 6%**. Plan change: §10 — `cannot_complete` has a measured price and must be evaluated on both populations.
- [TDAD](https://arxiv.org/abs/2603.17973) (snippet) — naive TDD prompting raised test-level regression **6.08% → 9.94%**; impact analysis first brought it to 1.82%. *Limit:* n=100 and n=25, no significance tests, authors say so. Plan change: a warning attached to Phase C1, not a figure relied on.

### Compaction, context, and the long horizon

- [Governance Decay](https://arxiv.org/html/2606.22528v2) (html) — 1,323 episodes, 7 models: constraint violation **0% full-context → 78% after four compaction rounds**; 1% when the constraint text survived the summary against 43% when dropped; **soft organisational policy decays ~8.3x more than hard safety norms**. Plan change: §5.14. An obligation list is soft organisational policy.
- [LOCA-bench](https://arxiv.org/html/2602.07962v1) (html) — same task, context varied 8K to 256K: **Claude-4.5-Opus 96.0% → 14.7%**. Programmatic tool calling recovers 10-13pp at 128K. Plan change: context *management*, not larger windows.
- [SWE-Milestone](https://arxiv.org/html/2603.13428) (html) — isolated >80% against **13.37%** under continuous evaluation; **recall grows near-linearly while precision saturates** — agents keep adding features and stop preventing regressions. Plan change: direct support for preservation sets as a first-class grade.
- [AgentRewind](https://arxiv.org/html/2608.14380v1) (html) — checkpoint and resume-with-learnings: **62.2% → 87.8%** on GPT-5.4. *Limit:* single paper, **no token budget imposed**, so part of +25.6pp may be bought with compute. Corroborated in direction only by LoopsBench's +8pp continuation delta.
- [Recoverability as a System Primitive](https://arxiv.org/html/2609.13672) (html) — tiny-N, and its value is the negative: **"a saved state is not necessarily a suitable place to resume."** Checkpoint-only recovery selected an *ineligible* source in every eligibility challenge while restoring bytes exactly and satisfying final invariants 20/20. Plan change: the trap recorded in Phase C0 — **task success cannot detect a bad recovery decision**, so a green restore test is green for the wrong reason.
- [Is there a half-life for the success rates of AI agents?](https://arxiv.org/abs/2505.05115) (html abstract) — constant per-minute failure hazard; long tasks fail because any one subtask failure kills the task. *Limit:* single-author theory fitted to one suite. **Do not quote per-model half-lives attributed to this paper — they do not exist in it; a PDF extractor in this sweep fabricated a full table of them.**

### Evaluation integrity and the boundary

- [Cursor, reward hacking](https://cursor.com/blog/reward-hacking-coding-benchmarks) — 731 audited trajectories: **63% of successful Opus 4.8 Max resolutions retrieved rather than derived the fix** (57% upstream lookup, 9% git history). Lockdown: Opus **87.1% → 73.0%**, Composer **74.7% → 54.0%**, and the gap is *larger* for newer models. *Limit:* vendor blog, no code or harness released; the auditor's model is undisclosed. Corroborates our own exposure finding independently.
- **pip has no flag that forbids VCS requirements** ([pip VCS support](https://pip.pypa.io/en/stable/topics/vcs-support/)) — `--no-index` disables the index and a direct-URL requirement never goes through it. Plan change: §4.1, and the reason denial-by-name was withdrawn.
- **A registry allowlist is not a closed book** — PyPI serves the upstream project's own post-fix releases. This is an unpatched hole in the published designs, ours included.
- SWE-bench [PR #471](https://github.com/SWE-bench/SWE-bench/pull/471) (merged 2025-09-11, not early 2026 as previously recorded here) purges commits and tags newer than the base commit; [PR #533](https://github.com/SWE-bench/SWE-bench/pull/533) is a **timezone bugfix** — the comparison sorted timestamp strings and shipped broken for roughly six months; [issue #578](https://github.com/SWE-bench/SWE-bench/issues/578) shows the Multilingual images still exposing 116 future-dated tags. Plan change: delete `.git` and re-init rather than prune by timestamp.
- [Agentic Benchmark Checklist](https://arxiv.org/abs/2507.02825) (NeurIPS 2025) — task validity, outcome validity, reporting. Applied to ten benchmarks: 7 with outcome-validity flaws, 7 with task-validity flaws, **all 10 with reporting limitations**. Plan change: adopt as the checklist for our own suite.
- [Rollout Cards](https://arxiv.org/abs/2605.12131) (snippet) — report rollout records, views, reporting rules and a **drops manifest** alongside scores; changing only the reporting rule moved scores **20.9 absolute points**. Plan change: §4.1 — a task whose dependencies cannot be pre-staged is a drop, not a denominator entry.
- [BenchJack](https://arxiv.org/abs/2605.12673) (snippet) — automated red-teaming of benchmarks; 219 vulnerabilities across 10 popular benchmarks. Plan change: point it at our own harness. §5.0 says prevention never attacked is prevention never tested.
- [SWE-rebench](https://arxiv.org/abs/2505.20411) (snippet) — mine tasks from post-training-cutoff commits and the contamination question largely dissolves. We already mine; pinning to post-cutoff commits is nearly free.

### The market, for the shape of the product rather than its correctness

- [Stack Overflow 2025](https://survey.stackoverflow.co/2025/ai) (independent, n=31,476 on the frustration item) — **66% name "AI solutions that are almost right, but not quite" as the top frustration**; only 3.1% highly trust AI output. The largest independent sample found, and it names this project's failure class.
- [CodeRabbit reviews in the wild](https://arxiv.org/abs/2607.03316) (independent) — 31,073 review/feedback pairs, 10,191 PRs, 239 repos: **36.4% accepted, 56.3% rejected**. Rejection is predictable at 76% F1.
- [Go Home Copilot, You're Drunk](https://arxiv.org/html/2607.21997v1) (independent) — 54,713 agent review comments: of unresolved ones, **55.6% "intentional design decision"**, 26.5% incorrect. Strongest predictor of a comment being acted on is **an inline applicable code suggestion (OR 1.62)**. Plan change: §1.3 — most rejection is context failure, which favours a local tool; and prose loses to an applicable artifact.
- [Sonar State of Code 2026](https://www.sonarsource.com/company/press-releases/sonar-data-reveals-critical-verification-gap-in-ai-coding/) (vendor, n=1,100+) — 96% do not fully trust AI code, 48% always verify, 38% say reviewing it costs more than reviewing a colleague's. *Limit:* vendor sells code quality, and trust percentages are highly framing-sensitive — a second vendor asking a near-identical question got 94% *confident*. Direction only.
- **METR: the correction.** The [2025 RCT](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) found experienced developers **19% slower** with AI. The [2026-02-24 update](https://metr.org/blog/2026-02-24-uplift-update/) finds returning developers **18% faster** and new ones 4% slower, both CIs crossing zero, with the authors flagging severe selection bias and redesigning the methodology. **The 19% figure is not cited anywhere in this repository and must not be** — checked 2026-09-15, and recorded here because it is the most quoted number in the field and the authors own follow-up does not support it.

**The standing correction this section exists to make.** Several entries above
were written from secondary summaries and stated more than their sources
support. Every entry added from here carries its limit in the same breath as its
claim, and an entry that contradicts an earlier one says so explicitly rather
than being quietly appended.
