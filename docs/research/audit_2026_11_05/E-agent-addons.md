# E: Do add-ons help a frontier coding agent, and which kinds survive?

Read 2026-11-05. **Grades:**
- **read**: I read the page itself (for arXiv, the HTML body).
- **abs**: I read only the arXiv abstract page.
- **snippet**: I saw only a search summary.
- **vendor**: the vendor's own claim about its own product.

About 40 sources were read in all; the ones that matter are below.

## 1. Findings, ranked by strength of evidence × relevance

**F1. For rules that can be checked, enforcement beats text in several controlled studies.**
- **ContextCov** ([2603.00822v2](https://arxiv.org/html/2603.00822v2), read, May 2026).
  - *Setup:* AGENTS.md rules compiled into AST checks, PATH shims and architecture validators; SWE-bench Lite, 300 tasks, OpenCode + GPT-5.2.
  - *Effect:* compliance 67.0% with the prompt alone, 50.3% with LLM reflection, **88.3% enforced**. Resolve rate 53.0%→57.3% (p=0.031).
  - *Limit:* one model; synthetic AGENTS.md files; the compliance oracle reuses the enforced rules, so the comparison is partly circular.
- **Trace** ([2606.13174](https://arxiv.org/html/2606.13174v1), read, Jun 2026).
  - *Effect:* compliance with user corrections, averaged over six models: no rules 31.6%; rules as prompt text 55.0%; Mem0 42.5%; **compiled into hook enforcement 70.1%**.
  - *Limit:* one user's corrections, simulated users, no statistics.
- **RepoComplianceBench** ([2607.26819](https://arxiv.org/html/2607.26819v1), read, Jul 2026).
  - *Setup:* 4 agents, including Claude Code + Sonnet 4.6 and Codex + GPT-5.5.
  - *Rule text alone:* quoting the rule verbatim in AGENTS.md left the Verify rule unchanged (Sonnet 4.6 42%→42%, GPT-5.5 92%→92%).
  - *Harness feedback:* one round naming the violated clause raised Verify to **90–100%**.
  - *Retrieval:* agents opened the policy file in 3.5% of runs.
  - *Limit:* about 25–30 runs per cell; an LLM judge.
- **Anthropic's Claude Code best-practices page** ([best-practices](https://code.claude.com/docs/en/best-practices), read, vendor).
  - CLAUDE.md and skills are "non-deterministic": a typecheck line there "works most of the time, not every time".
  - Rules with no exceptions belong in hooks. A `Stop` hook that exits with code 2 sends Claude back to work, capped at 8 consecutive blocks.
  - *Limit:* no data is given.

**F2. Holding actions until structured evidence exists raised correctness; the same content as prose did worse than no guidance.**
- **ECLoop** ([2607.28815](https://arxiv.org/html/2607.28815v1), read, Jul 2026).
- *Setup:* SWE-bench Verified (500); mini-swe-agent and Codex CLI; GPT-5-mini and MiniMax-M2.5.
- *Mechanism:* edits and submissions are held until deterministic conditions are met (code viewed, command run, failure observed). An action is held at most 3 times, then released with an audit.
- *Effect:* Pass@1 rose **+4.8 to +11.8pp**, every configuration p<0.001, with fewer tokens.
- *Ablation* (100 instances, tasks solved):

  | Variant | Solved |
  |---|---|
  | Full ECLoop | 68 |
  | No guidance | 63 |
  | **Natural-language summary of the same conditions** | **58** |
  | Baseline | 47 |
- Self-Refine lowered Pass@1.
- *Limit:* not frontier Claude; the largest gain was on the weakest model; 9–16 regressions per configuration.

**F3. Generic skills are mostly null for software engineering; curated knowledge the model lacks helps.**
- **SkillsBench** ([2602.12670v1](https://arxiv.org/html/2602.12670v1), read; 7,308 trajectories).
  - *Overall:* curated skills +16.2pp (the abstract; a figure caption says +12.66, so the paper is inconsistent).
  - *By domain:* **software engineering smallest at +4.5pp**; healthcare +51.9pp.
  - *By skill type:* self-generated −1.3pp; 4 or more skills +5.9pp; "comprehensive" skills −2.9pp.
  - *Limit:* no length-matched control.
- **SWE-Skills-Bench** ([2603.15401](https://arxiv.org/html/2603.15401), read; 3,920 paired runs).
  - *Effect:* **92 of 98 skills had no significant effect**. Pass rate 76.59%→76.93%.
  - *Instability:* 40 of 98 skills flip sign between harnesses running the same model.
  - *How harm happens:* harmful skills override the task's own instructions.
  - *Limit:* Haiku 4.5, GPT-5.4-mini and Kimi, not frontier models.
- **Signal or Noise** ([2608.23067](https://arxiv.org/html/2608.23067), read). Web-development skills cut Pass@2 by 1.3–4.2pp while tokens rose 72–394%. For some models, an irrelevant skill of the same length reproduced most of the loss.

**F4. Information the model cannot get, delivered without the agent having to fetch it, is the clearest positive.**
- **Vercel** ([blog](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals), read, vendor). Next.js 16 APIs, newer than the model's training data:

  | Condition | Pass rate |
  |---|---|
  | Baseline | 53% |
  | Skill available | 53% (never invoked in 56% of cases) |
  | Skill + explicit instruction | 79% |
  | **8 KB docs index in AGENTS.md** | **100%** |

  *Limit:* task count and model not disclosed.
- **Gloaguen** ([2602.11988v2](https://arxiv.org/html/2602.11988v2), read).
  - Developer-written context files: +2.4pp, not significant.
  - LLM-generated files: negative, at about 20% more cost.
  - Overviews did not help agents find files.
  - Tools named in the file did get used (uv: 1.6 uses per instance vs under 0.01).
- **Khatri** ([2607.27250](https://arxiv.org/abs/2607.27250), abs): correctness equivalent within ≤10–15pp.

**F5. Model progress absorbs process scaffolding, and for Claude models the spread between harnesses is already small.**
- **Terminal-Bench 2.0** ([2601.11868](https://arxiv.org/html/2601.11868v1), read; 32,155 trials).
  - *Claim:* "model selection is usually more important than agent scaffold".
  - *Same-model spread across harnesses:*

    | Model | Spread | Example |
    |---|---|---|
    | Gemini 2.5 Pro | ~17pts | |
    | Opus 4.5 | ~6pts | |
    | Sonnet 4.5 | ~3pts | bash-only mini-swe-agent 42.5 vs Terminus 2 42.8 |
- **mini-swe-agent** ([README](https://github.com/SWE-agent/mini-swe-agent), read): about 100 lines, bash only, >74% on SWE-bench Verified.
- **Anthropic, "Harness design for long-running apps"** ([post](https://www.anthropic.com/engineering/harness-design-long-running-apps), read, vendor).
  - "Every component in a harness encodes an assumption about what the model can't do on its own."
  - Context resets were dropped for Opus 4.5 and sprints for Opus 4.6.
  - The **separate evaluator stayed**: agents "reliably skew positive when grading their own work".
- **Boris Cherny, YC interview** ([transcript](https://sozai.app/transcript/boris-cherny-cut-80-percent-claude-code-prompt/), secondary).
  - Over 80% of Claude Code's system prompt was deleted for Opus 5.
  - "every 6 months delete your Claude MD… Delete your skills. Delete your hooks."
- **Anthropic's docs** list as stop-doing:
  - emphasis;
  - "be thorough";
  - "keep going";
  - architecture descriptions in CLAUDE.md;
  - delegating to a subagent for a better answer.
- **Lessons Outlive Their Failures** ([2610.32578](https://arxiv.org/html/2610.32578), read).
  - Past failures were replayed on **Sonnet 5.5** with their fixes removed: 3 of the 4 it completed did not recur.
  - Only the failure fixed by a **lint check** recurred (3/3 without it vs 0/2 with it).
  - *Limit:* one repository; p=0.10.
- **Counter-evidence:** a GAIA study ([2606.08529](https://arxiv.org/abs/2606.08529), abs) found Opus 4.7 gained the most from structured scaffolds, up to 28pp. There, "scaffold" means agent architecture, and the tasks are not coding.

**F6. Superpowers changes process; outcomes are mostly unchanged on current Claude.**
- **superpowers-evals** ([RESULTS](https://raw.githubusercontent.com/bartek-890/superpowers-evals/main/docs/RESULTS.md), read, independent).
  - *Setup:* Sonnet 5.5, 12 cases × 8 runs.
  - *Process changed:* brainstorming asked questions first in 8/8 runs vs 0/8.
  - *Outcome changed once:* the TDD bug-fix case gained a regression test (+0.41), the only delivered-outcome change.
  - *No change:* debugging, verify-before-claim and verify-before-commit scored **1.00 without the plugin**.
  - *Cost:* **1.33×**, about 1.5× the turns.
  - *Limit:* small tasks; the judge is the same model family.
- **Codex 500-task test** (snippet): 47.8% resolved; no significant gain.
- **v6.0.0 release notes** (read, vendor): "roughly twice as fast" compares against earlier Superpowers, not against no plugin.
- **README** (read): no evaluations cited; 312.8k stars.

**F7. Intervening mid-run hurts runs that would have succeeded.**
- **Failure prediction ≠ prevention** ([2602.03338](https://arxiv.org/abs/2602.03338), abs).
  - A critic with AUROC 0.94 cost up to −26pp on one model.
  - It gained only +2.8pp, on high-failure ALFWorld.
  - The authors propose a 50-task pilot before deploying an intervention.
- **Instruction adherence** ([2605.10039](https://arxiv.org/abs/2605.10039), abs): in 1,650 Claude Code sessions, odds of compliance fall about 5.6% per generated function.
- **Governance Decay** ([2606.22528v2](https://arxiv.org/html/2606.22528v2), read): pinning about 47 tokens of constraint restored violations to 0%.
- **Tool count:** tool search took Opus 4.5 from 79.5% to 88.1% ([Anthropic](https://www.anthropic.com/engineering/advanced-tool-use), vendor, undisclosed evaluations).
- **Execution:** forbidding test execution cost only 1.25pp, not significant ([2606.26978](https://arxiv.org/abs/2606.26978), abs).

## 2. What helps, and what gets absorbed

**Helps:**
1. **Deterministic gates on checkable conditions,** with feedback that names the violation (F1, F2).
2. **Information the model cannot get, delivered passively** (F4; our declared rules took left-behind dependents from 31/50 to 15/50).
3. **Independent evaluators.** Self-reflection was neutral or negative (ContextCov, ECLoop).
4. **Few tools, and searchable.**

**Absorbed:**
- **Process prose:** verify before claiming, debug methodically, keep going.
- **Repository overviews.**
- **Emphasis.**
- **Generic SE skills.**
- **Context-management scaffolding.**
- **Prose lessons from past failures.**

TDD is the last process add-on with a delivered effect, and only at n=8.

## 3. What undercuts ElevenPowers' current form

1. **Briefs sit in the weakest tier.**
   - Text access is not compliance: Trace 55% vs compiled 70%, and RepoComplianceBench's quoted rule changed nothing.
   - A prose version of the same conditions scored *below no guidance* (ECLoop 58 vs 63).
   - v3's "delivered, not acted on" result reproduces this finding; it is not an anomaly.
2. **Injecting before every edit is the shape that harms runs that would have succeeded** (F7). Our 1.4× cost with no outcome benefit matches Superpowers' 1.33× (F6).
3. **Evidence records and the end report are reporting, not gates.** Anthropic's own split puts "a request for evidence" on the non-deterministic side and the `Stop` hook and CI on the enforced side.
4. **The held-out gain is process quality.** Non-discriminating patches fell from 84% to 37% with resolve rate flat, the same shape as Superpowers' TDD effect. That is the kind of benefit F5 says the next model absorbs.
5. **What survives model progress lines up with our one positive result.** Declared rules worked because they carry information the model cannot see. v3's finding that lost dependents are not reachable through imports points the same way: the gap is information, not process.

## 4. Lessons

**Borrow:**
- **ECLoop (F2).** Compile each brief into machine-checkable conditions, for example "dependent D was opened, and a check touching it ran after the last edit". A `Stop` hook (exit 2) holds "done" until they hold; release after 3 holds and log the release.
- **ContextCov / RepoComplianceBench (F1).** Every violation message names the file, line, clause and fix.
- **Constraint pinning (F7).** Keep about 50 tokens that survive compaction, rather than a long obligation list.
- **Vercel (F4).** Use a small always-present index for information the model lacks, rather than a skill it must decide to invoke.
- **A separate evaluator (F5)** for the end verdict.

**Stop:**
- **Pre-edit advisory notes as the primary channel** (F1, F2, v3).
- **Process prose the model already follows** (F6).
- **Injection on every edit.** Act only when a gate fails (F7).

**Try (each one run forward and adversarially, per §5.0):**
1. **Gate, not note, on the v3 cases where briefs failed.**
   - Report resolve rate, left-behind dependents and **harm stratified by baseline success**.
   - Run a 50-task pilot first (F7).
2. **A retirement ablation at each model release** (F5). Replay each rule's original failure with the rule removed, and keep the rule only while the failure recurs.
3. **Narrow the product to two things:**
   - capturing information the model can't see: declared couplings, dependents that imports don't reach;
   - deterministic enforcement over that information.

   Drop process guidance (F5, F6).

*Not read:* the OpenAI "harness engineering" post (403; snippet only: AGENTS.md kept to a ~100-line map, plus mechanical linters); the Codex test of Superpowers (403).
