# A: Harness interventions with measured effects (track A, 2026-11-05)

**Grading.** "(read)" means I fetched the arXiv /abs/ or /html/ page, or the vendor page itself, through WebFetch's summariser, the risk class the project has flagged before. Check one figure against the page before it goes in `PLAN.md`. I used no PDFs. Nothing below repeats the reading list.

## 1. Most important findings, ranked by strength of evidence × relevance

**F1. On frontier bases, harness changes mostly move cost, not resolution.**
- *Harness or Model?* ([2609.11987](https://arxiv.org/abs/2609.11987), Sep 2026, read). Design: paired same-model runs on a private, contamination-controlled suite of 80 tasks, with 792 runs graded by an isolated oracle. Native harness against a neutral one: −1.25pp on Opus 4.8 (CI −10.0 to +7.5) and +1.25pp on GPT-5.5 (CI −4.4 to +6.9). The neutral harness cost 1.2–1.6× more per solved task. *Limit:* wide CIs, and the cost ordering is unresolved because of a telemetry defect.
- *Don't Blame the LLM* ([2607.03691](https://arxiv.org/html/2607.03691v1), TOSEM 2026, read). Design: 35 Qwen Code releases with the model fixed, 3,500 runs. No resolve-rate trend (ρ=0.208, p=0.231), while tokens rose more than 70%. *Limit:* 50 tasks, one scaffold, one model.
- *Rethinking Agent-Generated Tests* ([2602.07900v2](https://arxiv.org/html/2602.07900v2), read). Design: SWE-bench Verified, 500 tasks, mini-SWE-agent. Prompting four models to write more or fewer tests moved resolution by 0 to −2.6pp, and none of the four shifts was significant (McNemar p=0.23–1.0). Suppressing tests cut input tokens 33–49%. Within each model, resolved and unresolved tasks wrote tests at similar rates. *Limit:* one benchmark, a light scaffold.

This is the shape of ElevenPowers' held-out result: resolution unchanged, cost 1.4×.

**F2. Harness gains shrink as the base gets stronger, measured, not assumed.**
- *Empirical Study of Harness Design* ([2609.20804](https://arxiv.org/html/2609.20804v1), Sep 2026, read). Design: 176 matched settings on SWE-bench Verified and Terminal-Bench 2.1.
  - Planning: +11.6pp for Nemotron-30B, but −2.0 and −0.4pp for the two strongest models, which also saved about 30% of cost.
  - Context management: the gap over no management fell from 35.7pp at a 32k window to 2.7pp at 128k.
- *SWE-Review* ([2607.06065](https://arxiv.org/html/2607.06065), read). An Opus 4.6 reviewer in a review-revise loop added +25.1pp to a generator at 27.5%, +16.4pp to one at 50.9%, and +3.0pp to one at 72.2%. False rejections of correct patches ran 4.2–10.8%; the paper's introduction and table disagree slightly.
- Epoch ([why-benchmarking-is-hard](https://epoch.ai/gradient-updates/why-benchmarking-is-hard), Dec 2025, read): scaffolds matter "especially on weaker models"; switching scaffold moved GPT-5 up to 11%, Kimi K2 up to 15%.
- **Counter-example:** LoopsBench ([2608.00267v2](https://arxiv.org/html/2608.00267v2), read).
  - Design: 112 dependency-DAG tasks.
  - Effect: outer continuation, meaning restarting the agent when it stops, added +2.68pp under mini-swe-agent and +5.36pp under Claude Code (both GPT-5.4), and +8.04pp for Opus 4.7 in Claude Code.
  - So keeping a strong agent working longer gains *more*. *Limit:* continuation is undefined, and compute matching is not stated.

**F3. Curated procedural knowledge helps; self-generated knowledge hurts.**
- SkillsBench ([2602.12670v4](https://arxiv.org/html/2602.12670v4), NeurIPS 2026, read). Design: 87 tasks, 18 model-harness configurations, 9,396 trajectories.
  - Curated skills: +16.6pp on average (33.9% → 50.5%). Software-engineering domain: +11.6pp, but on only 16 tasks.
  - Self-generated skills: −8.1, −11.3 and −11.5pp, below baseline in all three configurations tried.
  - *Limit:* v1 reported +4.5pp for software engineering and −1.3pp for self-generated skills, so the figures moved between versions.
- This independently replicates ElevenPowers' own split: declared rules left 15/50 dependents behind against 31/50 without them, and automatic discovery failed.

**F4. File-anchored staleness is the weak form of invalidation.**
- *Impact Is Not Invalidation* ([2609.25130](https://arxiv.org/html/2609.25130), Sep 2026, read). Design: 10,369 test-function claims and 184 flips confirmed by execution, across 23 Python libraries.

| Way of deciding a claim needs re-checking | Precision | Recall |
|---|---|---|
| Re-check when the claim's file changes ("file anchoring") | 0.21 | 0.30 |
| Re-check when a referenced symbol changes | 0.39 | 0.54 |
| pytest-testmon (coverage-based test selection) | 0.415 | 0.868 |
| Ask a model "does *this claim* still hold after this diff?" (Sonnet 5 / Opus 5) | 0.952 / 0.974 | about 0.72 |

- Under file anchoring, precision falls to 0.014 at the natural flip rate. Asking a model whether the diff preserves behaviour, rather than about the specific claim, gave only 0.29–0.33 precision.
- *Limit:* one author, 151 held-out flips, two repositories supply 84 of them, Python only.
- This is the closest external test of ElevenPowers' "evidence goes stale when its files' hashes change" mechanism, and of reachability-based blast radius.

**F5. A regression gate works where the earlier behaviour has an executable check.**
- *Regression Accumulation* ([2607.01855](https://arxiv.org/html/2607.01855v1), ASE 2026, read). Design: 542 tasks run through 8-turn chains.
- The gate: rerun the earlier tests after each turn, reject if they regress, allow one retry.
- Effect on tasks with a regression: DeepSeek-V3 43.2% → 12.5%, Llama-8B 72.9% → 54.8%. A plain recap of earlier requirements gave only about +4pp.
- *Limit:* function-level tasks, weak models, no significance tests, and the gate uses the same tests as the grader, so it is circular.
- LoopsBench (F2): no loop design eliminated regressions, and stronger loops regressed more (Claude Code 7.11%), having more passing work to break.

**F6. Detection without action is a measured failure mode.**
- FeatureArc ([2610.37434](https://arxiv.org/html/2610.37434), Oct 2026, read). Design: 73 tasks with 2–10 stages, 10 agents including Opus 5.5 in Claude Code.
  - After a failed stage, agents never noticed the earlier error in 94.9% of later stages.
  - 87.5% of the agents' explanations for a red final self-test dismissed the failure as unrelated or pre-existing. Only 7.2% of those were checked against the starting code.
  - 73.8% of stages ended on a green self-test, but only 52.7% of those passed the real tests.
  - *Limit:* observational, with LLM-judge labels adjudicated by the first author.
- This matches ElevenPowers' v3 result exactly: 4 losses detected, none acted on.

**F7. Agent-written tests can confirm the agent's own mistake.**
- SWE-Review (as in F2): 62% of the reviewer's false approvals included AI-written test files.
- ExecCritic ([2609.09133](https://arxiv.org/abs/2609.09133), Sep 2026, read). Against a no-test baseline of 61.2%, tests from the same weak Qwen model lowered resolution to 57.3%, and tests from GPT-5.6 raised it to 65.3%. An RL-trained test writer plus repairer reached 72.6%. *Limit:* abstract only, n not stated.
- So ElevenPowers' fall in vacuity (84% → 37%) shows that a guard exists, not that the patch is correct.

**F8. Missing information is where the large deltas are.**
- *Ask or Assume?* ([2603.26233](https://arxiv.org/html/2603.26233), EMNLP 2026, read). Design: 500 underspecified SWE-bench Verified issues, Sonnet 4.5.
  - No access to the missing information: 54.8%. Uncertainty-aware single agent: 61.2%. Multi-agent: 69.4% (p<0.001). Always-interactive baseline: 70.4%. Fully specified issue: 70.8%.
  - *Limit:* the simulated user (GPT-5.1) holds the full issue, which flatters asking.

**F9. Selection and critics: real gains, but on subsets or oracle scoring.**
- OpenHands critic ([blog](https://openhands.dev/blog/20260305-learning-to-verify-ai-generated-code) and [2603.03800](https://arxiv.org/abs/2603.03800), vendor, read).
  - Best@8 was +15.9 over random on the "rerankable" subset only, meaning tasks where at least one run succeeds and one fails.
  - Critics trained only on benchmark data scored AUC about 0.45–0.48 on production outcomes, which is worse than chance. Trained on code survival, a critic reached 0.69.
- General-agent test-time scaling ([2602.18998](https://arxiv.org/html/2602.18998v1/), read): the model's own choice among samples saturates quickly against pass@K, and a GPT-5 external verifier did worse than self-choice.
- The Doubleword "+19.5pp" ([blog](https://blog.doubleword.ai/swe-bench-pro-64-deepseek-agents), vendor, read) is pass@64, an oracle, not a deployable selector.

**F10. Memory, LSP and semantic search: null or marginal on strong models.**
- VibeMemBench ([2609.23570](https://arxiv.org/html/2609.23570v1), read): 111 SWE-rebench-V2 targets. Eleven of twelve memory-system/solver pairings were at or below memory-off. Frozen verified experience gave +0 to +4.5pp, and every CI crossed zero. The harm came from transcript volume, not from what the records said.
- LSP:
  - [2608.13568](https://arxiv.org/html/2608.13568), read: offered LSP alongside grep, Opus 4.8 made 0% semantic calls for localisation. Forcing semantic-first cut success to 89%. Small N.
  - SWE-Master ([2602.03411v2](https://arxiv.org/html/2602.03411v2), read): +1.4 to +2.0pp on open models, no significance test.
- Cursor semantic search ([blog](https://cursor.com/blog/semsearch), vendor, read): +0.3% code retention, 2.6% on 1,000+-file repositories. No n.

## 2. What demonstrably works that ElevenPowers does not do

1. **Claim-specific re-verification** (F4). Ask "does this claim still hold?" instead of "did its file change?". Precision 0.95–0.97 with Sonnet 5 and Opus 5 (0.71 with Haiku 4.5), against 0.21 for file anchoring.
2. **A reject-and-retry gate on earlier checks** (F5). The checks run, a regression is refused, and the agent retries. ElevenPowers briefs and reports instead.
3. **Curated knowledge fed in at the point of use** (F3). The +11.6pp to +16.6pp comes from focused skills of at most three modules, not exhaustive bundles.
4. **Obtaining the missing requirement** (F8): +8 to +15pp, the largest controlled delta on a frontier model here.
5. **A critic trained on downstream outcomes** (F9), for early stopping (83% fewer attempts) rather than for gating. Vendor result.
6. **Continuation when the agent stops early** (F2, LoopsBench): +2.7 to +8.0pp on long tasks, with compute not matched.

## 3. What contradicts or undercuts the current approach

- **Hash-bound staleness** is the arm F4 measured worst: it fires constantly and still misses 70% of flips. Coverage reach is not falsification either (testmon precision 0.415), which also limits blast-radius maps.
- **"Assisted runs added a test"** is weak evidence of value. Test volume does not change solves (F1). Self-written tests feature in false approvals (F7). Model-generated knowledge is negative (F3).
- **Process cost without accuracy is the field's default outcome** on frontier bases (F1, F2). The 1.4× cost and 3.1× model time need a payoff measured somewhere other than resolution, not yet shown.
- **Briefing and reporting are not enough** (F6, F5). Agents dismiss red results as "pre-existing"; only a mechanical gate moved regressions.
- **Prompt-level quality guidance** does not change how fast quality degrades. SlopCodeBench ([2603.24755](https://arxiv.org/abs/2603.24755), read; 36 problems, 15 agents): initial verbosity and erosion fell by up to a third, but the degradation rate did not change.
- **Context-poor quiet dependents are unsolved everywhere.**
  - LoopsBench says its own dependency DAG misses configuration, data formats and cross-service edges.
  - No 2026 benchmark tested an intervention for such dependents.
  - SWE-CI ([2603.03823v2](https://arxiv.org/html/2603.03823v2), read): most models have a zero-regression rate below 0.25. No intervention was tested.

## 4. Concrete lessons

**Borrow**
- **Replace file-hash invalidation with claim-specific re-checking** (F4). For each evidence item, store the claim, such as "test X passes because of Y". On a change, ask a cheap model "does this diff falsify this claim?" and rerun only on yes. Keep hashes as a cheap pre-filter. *Measure it as their A3 against A6 on our own ledger.*
- **Turn milestone checks into a gate** (F5). At Stop, rerun the declared checks, refuse a regression, allow one retry. Evaluate it against a held-out oracle, not the gate's own checks.
- **Mechanise the "pre-existing" claim** (F6). Snapshot the failing-test set at task start. When the agent calls a red test pre-existing or unrelated, check it against the snapshot and reject the claim if false.

**Stop**
- **Stop automatic rule discovery** (F3 plus ElevenPowers' own null). Put the effort into making declaring a rule cheap: candidate files proposed once, a person accepts or rejects.
- **Stop counting added tests as the benefit** (F1, F7). Score a test by whether it fails on plausible wrong patches (mutants), not only on the empty patch.
- **Do not build LSP, memory or planning layers for frontier models** (F2, F10).

**Try**
- **Test the gate where checks exist,** where F5 says the effect is large. v3's dependents were mostly not import-reachable and unchecked, the hardest case for any tool.
- **Run one arm on a weaker model** (for example Haiku). F2 predicts that is where a harness shows headroom. "Makes a cheap model safe to maintain a repository" is a product claim the data supports in kind.
- **Ask about conflicts.** When a declared rule conflicts with the request, ask the user rather than brief (F8).
- **Continue instead of block.** When the verification state is incomplete, re-enter the agent with the specific unmet obligation (LoopsBench), and budget-match the arms.
