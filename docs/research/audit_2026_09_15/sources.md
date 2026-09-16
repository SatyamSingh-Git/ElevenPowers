# Sources consulted, 2026-09-15

Every paper, article, blog, repository, dataset and documentation page that
contributed to [findings.md](findings.md), PLAN v0.8,
[build-on.md](../build-on.md), and journey entries 29 and 30.

**This list exists to give credit.** Anything that changed a decision here is
named, whether or not it was quoted, and whether or not it agreed with us. Work
that we relied on and then *disagreed with* is listed too — being argued with is
still a contribution.

## How to read the grades

| Grade | Meaning |
|---|---|
| **(html)** | Read from arXiv HTML, a publisher's HTML, or the abstract page |
| **(pdf)** | Read from a PDF extractor — **see the warning** |
| **(snippet)** | Search-result summary only; direction usable, figures not quotable |
| **(primary)** | Repository source, official documentation, or a dataset read directly |

**The warning, because it bit us in this very sweep.** Two PDF fetches returned
**fabricated numbers**, one inventing a full table of per-model half-lives that
does not exist in the paper it was attributed to. No pdf-grade figure was
carried into the plan. Prefer `arxiv.org/html/<id>` or `/abs/<id>`. A
snippet-grade number may not be quoted as established without being promoted
first. See [verify-numbers-via-html](../reading-list.md).

Corroboration by a second independent method promotes a *direction*, not a
decimal place.

---

## 1. Evidence sufficiency and the oracle problem

*The finding that re-aimed the project.*

- **Validation evidence in agent rollouts** — arXiv [2607.28871](https://arxiv.org/abs/2607.28871) (html). 46.0% of positive validation evidence carries no bug-discriminating information; 23.8% of rollouts close on a non-discriminating basis; 26.9% of bug-detecting tests fail on the developer's own fix. 3,730 events / 643 rollouts / 110 tasks. Prespecified smallest effect size — **the best methodology in the sweep**, and its negative half (feedback repair below threshold) is as load-bearing as its positive half. → PLAN §5.10.
- **PROBE** — arXiv [2604.01518](https://arxiv.org/abs/2604.01518) (snippet). 77% of SWE-bench Verified instances admit a wrong-but-passing patch.
- **SpecBench** — arXiv [2605.21384](https://arxiv.org/html/2605.21384v1) (html). Every model saturates the visible test suite; visible-to-held-out gap grows ~27pp per 10x LOC. → PLAN §0, §5.10.
- **SWE-Mutation** — arXiv [2605.22175](https://arxiv.org/html/2605.22175v1) (html). 10.2% verification, 36.15% mutant detection for generated suites.
- **Are "Solved Issues" in SWE-bench Really Solved Correctly?** (PatchDiff) — arXiv [2503.15223](https://arxiv.org/abs/2503.15223), ICSE 2026 (snippet). 29.6% behavioural divergence; 7.8% pass while failing the developer suite; **6.2pp inflation**. → PLAN §6, §10.
- **UTBoost** — arXiv [2506.09289](https://arxiv.org/abs/2506.09289) (snippet). 345 erroneous patches wrongly marked passing; leaderboard rank changes.
- **SWE-bench+** — arXiv [2410.06992](https://arxiv.org/html/2410.06992v2) (snippet). 32.67% solution leakage; 31.08% passed only on weak tests.
- **SWE-ABS** — arXiv [2603.00520](https://arxiv.org/pdf/2603.00520) (snippet). Adversarial benchmark strengthening.
- **Towards Verified Code Reasoning by LLMs** — arXiv [2509.26546](https://arxiv.org/pdf/2509.26546) (snippet).

## 2. Where and when agents fail

- **Failure as a Process: An Anatomy of CLI Coding Agent Trajectories** — arXiv [2607.09510](https://arxiv.org/html/2607.09510) (html). 1,184 failed trajectories, >63,000 steps. Epistemic 57.9% (**false premises 30.7%**, specification neglect 14.9%); competence 32.8%; environment 9.4%. Median decisive error step 7 of 27; recovery window one step; signals ~10 steps later; **82% continue past the point of no return**; best real-time recall 28.8%. **The single most useful paper in the sweep.** → PLAN §2, §5.11.
- **Accurate Failure Prediction in Agents Does Not Imply Effective Failure Prevention** — arXiv [2602.03338](https://arxiv.org/pdf/2602.03338) (pdf, qualitative claim only). Harm concentrates in early interruptions of runs that would have succeeded. → PLAN §5.12.
- **Coherence Collapse: Diagnosing Why Code Agents Fail After Reaching the Right Code** — arXiv [2603.24631](https://arxiv.org/abs/2603.24631) (html abstract). 60-69% of failures edit the correct functions and still fail; 5 cases produced the reference patch mid-trajectory then corrupted it; edit-commit checkpointing recovered all 5; naive cost 10-40x test invocations. → PLAN §1.2, [build-on.md](../build-on.md) C0.
- **Coding agents in 20,574 real developer sessions** — arXiv [2605.29442](https://arxiv.org/abs/2605.29442) (snippet). Constraint violation 38.3%, misread intent 27.0%, **inaccurate self-reporting 22.6%**, faulty implementation 17.8%; instruction-following failure 36.5% vs underspecified instruction 15.4%. → PLAN §2.
- **N-Version Programming with Coding Agents** — arXiv [2606.20158](https://arxiv.org/abs/2606.20158) (html). 48 implementations, 1,000,000 inputs, all 17,296 triplets. **429 coincident failures vs 115 predicted, z = 29.20.** Agents converge on the same spec misreading. → PLAN §2.
- **MAST: Multi-Agent System Failure Taxonomy** — arXiv [2503.13657](https://arxiv.org/abs/2503.13657), NeurIPS 2025 (snippet). Specification & system design 41.8%; inter-agent misalignment 36.9%; task verification 21.3%.
- **Model or Harness? An Interaction-Centric Taxonomy** — arXiv [2607.28802](https://arxiv.org/html/2607.28802) (html). Repetitive action 12.4% vs 28.9% by model; 88%/12% model- vs harness-attributable.
- **SWE-bench Pro** — arXiv [2509.16941](https://arxiv.org/html/2509.16941) (snippet). Per-model failure buckets; Sonnet 4 context overflow 62.6%, endless file reading 57.4% — harness failures larger than most scaffold deltas.
- **Localization in failed trajectories** — arXiv [2511.00197](https://arxiv.org/abs/2511.00197) (snippet). Right file 72-81% even in failures; hunk-level exact match 0.5-1.6%.
- **SWE-bench Verified hand study** — arXiv [2509.13941](https://arxiv.org/abs/2509.13941) (snippet). Phase-level failure split; flawed reasoning ~65%.
- **Beyond the Leaderboard** — arXiv [2607.05775](https://arxiv.org/pdf/2607.05775) (snippet).
- **TrajAudit** — arXiv [2605.26563](https://arxiv.org/pdf/2605.26563) (snippet). **AgentForesight** — arXiv [2605.08715](https://arxiv.org/html/2605.08715) (snippet). **When Should Users Check?** — arXiv [2510.05307](https://arxiv.org/pdf/2510.05307) (snippet). **Towards Self-Improving Error Diagnosis** — arXiv [2604.17658](https://arxiv.org/html/2604.17658v1) (snippet).
- **Agentic Uncertainty Reveals Agentic Overconfidence** — arXiv [2602.06948](https://arxiv.org/pdf/2602.06948) (pdf, direction only).
- **Agentic Abstention: Do Agents Know When to Stop Instead of Act?** — arXiv [2606.28733](https://arxiv.org/pdf/2606.28733) (snippet).
- **Is there a half-life for the success rates of AI agents?** — Toby Ord, arXiv [2505.05115](https://arxiv.org/abs/2505.05115) (html abstract). Constant per-unit-work failure hazard; long tasks fail because any subtask failure kills the task. **Do not quote per-model half-lives attributed to this paper — they do not exist in it.**

## 3. What measurably improves outcomes

- **ORACLE-SWE** — arXiv [2604.07789](https://arxiv.org/abs/2604.07789) (snippet). Oracle signal ablation from a 35% baseline: reproduction test **+28pp**, execution context +15pp, API usage +9pp, localisation +8pp, regression test +2pp. → PLAN §5.13, and the demotion of localisation.
- **Spec-first test generation** — arXiv [2608.17177](https://arxiv.org/abs/2608.17177) (snippet). Contract extraction before test generation: **+9.8pp bug detection, p = 0.035**, on 90 real production bug-fix pairs across four languages. The cleanest positive result found. → [build-on.md](../build-on.md) C1.
- **To Run or Not to Run** — arXiv [2606.26978](https://arxiv.org/abs/2606.26978) (snippet). 7,745 traces: prohibiting execution during repair costs **1.25pp, not significant**. → PLAN §5.13, §10.
- **TDFlow** — arXiv [2510.23761](https://arxiv.org/abs/2510.23761) (snippet). Reproduction tests as the primary obstacle. Headline 94.3% flagged as an extraordinary claim needing independent replication.
- **CodeMonkeys** — arXiv [2501.14723](https://arxiv.org/html/2501.14723v2) (html). Pool coverage 69.8% vs selected 57.4%; **5.8% of spend on selection**. Barrel-of-Monkeys ensemble coverage 80.8%. → PLAN §5.1, Phase B2.2.
- **Oracle Gap and Signal Fidelity** — arXiv [2607.17531](https://arxiv.org/html/2607.17531v1) (html). Selector gain *and harm*: execution +8.14pp at 0% harm; LLM judge +3.50pp at 4.69% harm; **below ~4pp oracle gap every selector underperformed**. → the four-point rule, PLAN §0 and Phase B2.2.
- **SWE-RM** — arXiv [2512.21919](https://www.arxiv.org/pdf/2512.21919), ICLR 2026 (snippet). Execution-free verifier, +7.6 to +10.4pp; beats execution-based reward by +3pp in RL.
- **R2E-Gym** — arXiv [2504.07164](https://arxiv.org/abs/2504.07164) (snippet). Execution-based and execution-free verifiers ≈42-43% each; **hybrid 51%**.
- **Scaling Test-Time Compute for Agentic Coding** — arXiv [2604.16529](https://arxiv.org/abs/2604.16529) (snippet). Recursive tournament voting + parallel-distill-refine; +6.7pp SWE-bench Verified, +12.2pp Terminal-Bench v2.0. Already cited in [reading-list.md](../reading-list.md).
- **How Many Tries Does It Take?** — arXiv [2604.10508](https://arxiv.org/html/2604.10508v1) (html). Two repair rounds capture 76-95% of achievable gains; assertion/logic errors repaired only ~45%.
- **SHERLOC** — arXiv [2606.24820](https://arxiv.org/abs/2606.24820), EMNLP 2026 (snippet). Training-free localisation, +5.95pp with −23.1% total tokens.
- **Agentless** — arXiv [2407.01489](https://arxiv.org/abs/2407.01489) (snippet). Cost anchor: 32.00% SWE-bench Lite at $0.70/issue. Prior art for execution-based selection.
- **SWE-agent** — arXiv [2405.15793](https://arxiv.org/pdf/2405.15793) (snippet). **mini-SWE-agent** — the lower-bound baseline any harness must beat.
- **TestPrune** — arXiv [2510.18270](https://arxiv.org/abs/2510.18270) (snippet). Minimised regression tests; ~+3.2pp and +2.6pp absolute (reported as relative percentages).
- **REAgent** — arXiv [2604.06861](https://arxiv.org/abs/2604.06861) · **CodeScout** — arXiv [2603.05744](https://arxiv.org/abs/2603.05744) · **Plan compliance** — arXiv [2604.12147](https://arxiv.org/abs/2604.12147) (all snippet). Requirement-derivation methods reporting gains; all author-evaluated and unreplicated.
- **SWE-Replay** — arXiv [2601.22129](https://arxiv.org/pdf/2601.22129) · **Deterministic fusion of repair candidates** — arXiv [2607.01597](https://arxiv.org/abs/2607.01597) · **SWE-Shepherd** — arXiv [2604.10493](https://arxiv.org/abs/2604.10493) · **No silver bullet for reward design** — arXiv [2606.26300](https://arxiv.org/abs/2606.26300) (all snippet).
- **Self-Evolving Agents with Anytime-Valid Certificates** — arXiv [2607.00871](https://arxiv.org/pdf/2607.00871) (pdf, concept only). E-values and confidence sequences for valid sequential claims — a candidate replacement for our fixed-n `ep-repeat` arithmetic.

## 4. Negative results, held as evidence

*These changed decisions by telling us not to build things.*

- **Evaluating AGENTS.md** — arXiv [2602.11988](https://arxiv.org/html/2602.11988v2), ETH Zurich + LogicStar.ai (html). Context files do not generally improve success; **+20% cost**. Already in [reading-list.md](../reading-list.md); now corroborated.
- **Context files ablation, 288 runs** — arXiv [2607.27250](https://arxiv.org/abs/2607.27250) (snippet), with an independent write-up at [Developers Digest](https://www.developersdigest.tech/blog/context-files-coding-agents-ablation-2026). Equivalence-tested null.
- **Rethinking the Value of Multi-Agent Workflow** — arXiv [2601.12307](https://arxiv.org/html/2601.12307v1) (html). A single agent running the same workflow matched or beat multi-agent across 7 benchmarks at ~1/10 cost. → PLAN §8, §11.
- **Measure Before You Manage** — arXiv [2608.31057](https://arxiv.org/html/2608.31057) (html). Agent working memory: **no held-out contrast survives Holm correction**; delivered-context parity failed in all 10 pairs. → PLAN §11.
- **SWE-MeM** — arXiv [2606.28434](https://arxiv.org/html/2606.28434v1) (html) and the [pre-registered memory benchmark](https://github.com/SaravananJaichandar/coding-agent-memory-benchmark), Zenodo [10.5281/zenodo.21076824](https://doi.org/10.5281/zenodo.21076824). Positive memory results, each with a context-budget or leakage confound. Credit for pre-registering.
- **Spec-driven development, surveyed** — arXiv [2609.00252](https://arxiv.org/abs/2609.00252) (snippet). No peer-reviewed study has defined, delimited or measured these frameworks. → PLAN §10.
- **Spec Kit pilot** — arXiv [2605.01160](https://arxiv.org/abs/2605.01160) · **Spec Kit Agents** — arXiv [2604.05278](https://arxiv.org/abs/2604.05278) (snippet). The only two studies; uncontrolled and narrow respectively. Listed so the absence is checkable.
- **FixedBench / abstain-or-fix** — arXiv [2605.07769](https://arxiv.org/abs/2605.07769) (snippet). Agents change already-fixed code in 35-65% of cases; abstention prompting collapses partial-fix repair 27.3% → 6%. → the `cannot_complete` qualification, PLAN §10.
- **TDAD** — arXiv [2603.17973](https://arxiv.org/abs/2603.17973) (snippet). Naive TDD prompting raised regressions **6.08% → 9.94%**. → the warning on Phase C1.
- **Scope mismatch in LLVM repair** — arXiv [2607.02370](https://arxiv.org/abs/2607.02370) (snippet). "Generalize this" instructions failed to improve alignment across all four models.
- **When Can LLMs Actually Correct Their Own Mistakes?** — arXiv [2406.01297](https://arxiv.org/html/2406.01297v3) (snippet). Intrinsic self-correction does not improve, and can degrade, code generation.
- **Recoverability as a System Primitive** — arXiv [2609.13672](https://arxiv.org/html/2609.13672) (html). *"A saved state is not necessarily a suitable place to resume"*; **task success cannot detect a bad recovery decision**. → the trap recorded in Phase C0.
- **Rejected agentic PRs** — arXiv [2606.13468](https://arxiv.org/abs/2606.13468), MSR'26 · arXiv [2605.22534](https://arxiv.org/abs/2605.22534) (snippet). Contradicting evidence: real-world PR rejections rarely cite ambiguity. Listed because it argues against §2, and half its cases have no stated reason.

## 5. Long-horizon and context

- **Governance Decay** — arXiv [2606.22528](https://arxiv.org/html/2606.22528v2) (html). 1,323 episodes, 7 models. Constraint violation **0% → 78%** over four compaction rounds; 1% when the text survived vs 43% when dropped; **soft policy decays 8.3x more than hard norms**. → PLAN §5.14.
- **LOCA-bench** — arXiv [2602.07962](https://arxiv.org/html/2602.07962v1) (html). Same task, 8K → 256K: Claude-4.5-Opus **96.0% → 14.7%**; programmatic tool calling recovers 10-13pp.
- **TRACE / execution instability under compression** — arXiv [2608.06503](https://arxiv.org/html/2608.06503v1) (html). Full context 85.7% → 4K summary 72.8%, FIFO 42.2%. Compression converts reliably-solved tasks into intermittently-solved ones.
- **Compaction as Epistemic Failure** — arXiv [2607.13071](https://arxiv.org/html/2607.13071) (html). A killed process's partial output recorded into a summary as a confirmed result. **n=1, self-observed, unreplicated** — a well-described hypothesis, and the mechanism it names is exactly our concern.
- **Generalization bias in LLM summarization of scientific research** — *Royal Society Open Science* 12(4):241776 (snippet). Hedging down 22.8%; ~5x more broad generalizations; **prompting for accuracy made it worse**. Off-domain, used as mechanism transfer only.
- **SWE-Milestone** — arXiv [2603.13428](https://arxiv.org/html/2603.13428) (html). Isolated >80% → **13.37%** under continuous evaluation; recall grows while **precision saturates**. Direct support for preservation sets.
- **LoopsBench** — arXiv [2608.00267](https://arxiv.org/html/2608.00267v1) (html). Regression rates by harness — Claude Code 7.11% down to mini-swe-agent 0.24%; **more capable harnesses regress more**. External continuation worth +8pp.
- **AgentRewind** — arXiv [2608.14380](https://arxiv.org/html/2608.14380v1) (html). Checkpoint + resume-with-learnings: 62.2% → 87.8%. No token budget imposed, so partly bought with compute.
- **Long-horizon degradation** — arXiv [2603.24755](https://arxiv.org/abs/2603.24755) (snippet). Strict solve rate to 0.5% by final checkpoint; cost 2.9x with no correctness gain.
- **When Agents Do Not Stop** — arXiv [2607.01641](https://arxiv.org/html/2607.01641v1) (html). 6,549 repositories scanned; 68 confirmed infinite-loop failures; common root cause: **no strong bound on the repeated path**.
- **NoLiMa** — arXiv [2502.05167](https://proceedings.mlr.press/v267/modarressi25a.html), Adobe Research, ICML 2025 (snippet). At 32K, 11 of 13 models fall below 50% of their own short-context baseline.
- **Context Rot** — [Chroma](https://www.trychroma.com/research/context-rot) (primary, vendor-affiliated). 18 models; degradation at every length increment, not only near the limit.
- **AutoRefine** — arXiv [2601.22758](https://arxiv.org/abs/2601.22758) · **HiAgent** — arXiv [2408.09559](https://arxiv.org/abs/2408.09559) · **MemGovern** — arXiv [2601.06789](https://arxiv.org/abs/2601.06789) (snippet).
- **METR**: [Time Horizon 1.1](https://metr.org/blog/2026-1-29-time-horizon-1-1/), [limitations note](https://metr.org/notes/2026-01-22-time-horizon-limitations/), [2025 RCT](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/), [2026 uplift update](https://metr.org/blog/2026-02-24-uplift-update/) (primary). **Credit especially for the update**, which publicly reverses the most-cited number in the field and documents its own selection bias.

## 6. Evaluation integrity and the information boundary

- **Cursor — Reward hacking is swamping model intelligence gains** — [cursor.com](https://cursor.com/blog/reward-hacking-coding-benchmarks) (primary, vendor). 731 audited trajectories; **63% retrieved rather than derived**; lockdown 87.1% → 73.0%. Independently corroborates our own exposure finding.
- **BenchJack** — arXiv [2605.12673](https://arxiv.org/abs/2605.12673) (snippet). 219 vulnerabilities across 10 benchmarks; an Agent-Eval Checklist. **To be pointed at our own harness.**
- **BenchShield** — arXiv [2609.11028](https://arxiv.org/abs/2609.11028) (snippet). Phase-aware taint analysis; detection recall lifted to 77-100%.
- **Agentic Benchmark Checklist (ABC)** — arXiv [2507.02825](https://arxiv.org/abs/2507.02825), Zhu et al., NeurIPS 2025 (snippet). All 10 audited benchmarks had reporting limitations. **Adopted as our checklist.**
- **Rollout Cards** — arXiv [2605.12131](https://arxiv.org/abs/2605.12131) (snippet). Drops manifests; changing only the reporting rule moved scores 20.9 points. → PLAN §4.1.
- **SWE-rebench** — arXiv [2505.20411](https://arxiv.org/abs/2505.20411), NeurIPS 2025 (snippet). Post-cutoff mining dissolves much of the contamination question.
- **Cross-Context Verification** — arXiv [2603.21454](https://arxiv.org/pdf/2603.21454) (snippet). Memorised solutions reproduce identically across isolated sessions.
- **Do Coding Agents Deceive Us?** — arXiv [2606.07379](https://arxiv.org/pdf/2606.07379) (pdf). Capped evaluation with randomized tests.
- **Capability Gates Are Not Authorization** — arXiv [2606.28679](https://arxiv.org/html/2606.28679v1) (snippet). Confused-deputy failures; the security-side statement of our D108.
- **SWE-bench maintenance, read directly** (primary): [issue #465](https://github.com/SWE-bench/SWE-bench/issues/465), [PR #471](https://github.com/SWE-bench/SWE-bench/pull/471), [PR #533](https://github.com/SWE-bench/SWE-bench/pull/533), [issue #578](https://github.com/SWE-bench/SWE-bench/issues/578); SWE-bench Pro OSS [issue #93](https://github.com/scaleapi/SWE-bench_Pro-os/issues/93) / [PR #94](https://github.com/scaleapi/SWE-bench_Pro-os/pull/94). Corrects our earlier dating and shows timestamp pruning shipped broken for ~6 months.
- **Harbor** — [task/network policy docs](https://www.harborframework.com/docs/tasks), [issue #3162](https://github.com/harbor-framework/harbor/issues/3162), [PR #3219](https://github.com/harbor-framework/harbor/pull/3219) (primary). `no-network` / `allowlist` modes over gost + nftables — the most mature implementation of what §4.1 needs.
- **SWE-ReX** — [github](https://github.com/SWE-agent/swe-rex) · **OpenHands Docker sandbox** — [docs](https://docs.openhands.dev/openhands/usage/sandboxes/docker) (primary).
- **Claude Code sandboxing** — [docs](https://code.claude.com/docs/en/sandboxing) (primary). `strictAllowlist`, and its own documented caveats.
- **pip** — [VCS support](https://pip.pypa.io/en/stable/topics/vcs-support/), [index mirrors and caches](https://packaging.python.org/en/latest/guides/index-mirrors-and-caches/), [proxpi](https://github.com/EpicWink/proxpi), [devpi-findlinks](https://pypi.org/project/devpi-findlinks/) (primary). **Confirms no flag forbids VCS requirements.**
- **Docker** — [`network create --internal`](https://docs.docker.com/engine/reference/commandline/network_create/) (primary).
- **Microsoft** — [Hyper-V Firewall](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/hyper-v-firewall), [New-NetFirewallHyperVRule](https://learn.microsoft.com/en-us/powershell/module/netsecurity/new-netfirewallhypervrule), [Windows Sandbox .wsb](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file), [platform security for AI agents](https://blogs.windows.com/windowsdeveloper/2026/06/02/windows-platform-security-for-ai-agents/) (primary).
- **INNOQ — Restricting network access for AI coding agents with a proxy allowlist** — [innoq.com](https://www.innoq.com/en/blog/2026/03/dev-sandbox-network/). Credit for publishing the rule-ordering and persistence problems they hit.
- **OpenAI — SWE-bench Verified** — [openai.com](https://openai.com/index/introducing-swe-bench-verified/) (primary). 93 developers annotated 1,699 samples; **38.3% flagged underspecified**; 68.3% filtered out.

## 7. Ambiguity, clarification and requirements

- **Ambig-SWE** — arXiv [2502.13069](https://arxiv.org/abs/2502.13069) (snippet). Removing detail drops Sonnet 4 ~65% → ~42%; interaction recovers up to +74% relative; **models detect underspecification at 89% down to chance**.
- **ClarifyGPT** — arXiv [2310.10996](https://arxiv.org/abs/2310.10996), FSE 2024 (snippet). GPT-4 70.96% → 80.80% on MBPP-sanitized.
- **CLARITI** — arXiv [2604.14624](https://arxiv.org/abs/2604.14624) · **ClarifyCodeBench** — arXiv [2607.00711](https://arxiv.org/abs/2607.00711) (snippet). Models **under-ask**, not over-ask.
- **Issue quality and Copilot merge** — arXiv [2512.21426](https://arxiv.org/abs/2512.21426) (snippet).

*Standing caveat on this whole section: every clarification study simulates the
user from the gold patch. **No clarification study with real users on real
repository issues exists.** That is the largest gap in this literature.*

## 8. Regressions, mutation and test adequacy

- **TensorBench** — arXiv [2606.05570](https://arxiv.org/abs/2606.05570) (snippet). **16-37% of applied patches introduce a regression in pre-existing tests**; pass rate and regression-resistance do not improve together.
- **Agent regression-test execution** — arXiv [2506.08311](https://arxiv.org/abs/2506.08311) (snippet). Gold-test execution rate ACR 100%, Agentless 45%, MASAI 4%.
- **Test evolution at repo scale** — arXiv [2605.06125](https://arxiv.org/abs/2605.06125) (snippet). Agents identify which tests need updating at 45.7-49.4% F1.
- **Test vs Mutant** — arXiv [2602.08146](https://arxiv.org/html/2602.08146) · **Do Coverage and Mutation Scores Correlate?** — arXiv [2607.22880](https://arxiv.org/html/2607.22880v1) · **PRIMG** — arXiv [2505.05584](https://arxiv.org/pdf/2505.05584) · Mutation-Guided LLM-based Test Generation at Meta (snippet). Mutation testing as the established measure of test adequacy.
- **LGMT** — arXiv [2605.23965](https://arxiv.org/abs/2605.23965) · **ARMeta / metamorphic testing for REST APIs** — arXiv [2605.28321](https://arxiv.org/html/2605.28321v1) (snippet). Oracle-free metamorphic relations.
- **Execution-calibrated LLM judges** — *Journal of Cybersecurity and Privacy* 6(5):153, [doi](https://doi.org/10.3390/jcp6050153) (snippet). Judge-judge agreement κ=0.75 but judge-execution κ≤0.26: *"judge-judge agreement measures reliability, not validity."*
- **mutmut**, **cosmic-ray**, **PIT** — existing mutation engines. Named so we do not write one.

## 9. Adjacent systems doing the same thing

*Listed because they arrived independently at mechanisms we thought were ours.*

- **EviBound** — arXiv [2511.05524](https://arxiv.org/abs/2511.05524) (html abstract). Dual approval/verification gates on machine-checkable evidence; 100% → 0% false claims on 8 tasks, ~8.3% overhead.
- **WorktreeProof** — `no evidence = no close`, fixed terminal ledger, evidence marked stale when edits change the workspace. [Write-up](https://dev.to/nedalelbaz/vibe-fast-ship-with-proof-building-guardrails-for-ai-coding-agents-245l).
- **Critique** — independent finish pass in a disposable workspace; [their survey of the category](https://www.critique.sh/blog/best-coding-agent-verification-tools-2026).
- **agentwatch** — records claim-versus-action mismatch.
- **Constant-Size Cryptographic Evidence Structures for Regulated AI Workflows** — arXiv [2511.17118](https://arxiv.org/html/2511.17118v1) (snippet).
- **Pramana** — arXiv [2605.20312](https://arxiv.org/pdf/2605.20312) · **Pre-Deployment Assurance for Enterprise AI Agents** — arXiv [2606.04037](https://arxiv.org/pdf/2606.04037) (snippet).
- **Verify Before You Fix** — arXiv [2604.10800](https://arxiv.org/pdf/2604.10800) (pdf, direction only). Grounding repair in execution before editing.

## 10. Market, adoption and the review bottleneck

- **Stack Overflow Developer Survey 2025** — [survey.stackoverflow.co](https://survey.stackoverflow.co/2025/ai) (primary, independent, n=49,000+). **66% name "almost right, but not quite" as the top frustration**; 3.1% highly trust AI output. The single most important market datapoint here.
- **Is Agentic Code Review Helpful? Mining Developers' Feedback to CodeRabbit Reviews in the Wild** — arXiv [2607.03316](https://arxiv.org/abs/2607.03316) (independent). 31,073 review/feedback pairs, 10,191 PRs, 239 repos. **36.4% accepted, 56.3% rejected.**
- **Go Home Copilot, You're Drunk** — arXiv [2607.21997](https://arxiv.org/html/2607.21997v1) (independent). 54,713 comments. **55.6% of unresolved are "intentional design decision"**; inline applicable suggestion is the strongest adoption predictor (OR 1.62).
- **CR-Bench** — arXiv [2603.11078](https://arxiv.org/html/2603.11078v1). Usefulness rate and signal-to-noise as first-class metrics.
- **DORA 2025** — [dora.dev](https://dora.dev/dora-report-2025/) (independent, ~5,000 respondents). AI as amplifier; adoption correlates with higher throughput *and* higher instability.
- **Sonar State of Code 2026** — [press release](https://www.sonarsource.com/company/press-releases/sonar-data-reveals-critical-verification-gap-in-ai-coding/), [report](https://www.sonarsource.com/state-of-code-developer-survey-report.pdf) (vendor, n=1,100+).
- **Faros AI** — [AI acceleration whiplash](https://www.faros.ai/blog/ai-acceleration-whiplash-takeaways) (vendor telemetry, 22,000 developers). Within-org before/after, not controlled — direction only.
- **Harness / Sapio Research** — [press](https://www.harness.io/press-and-news/ai-has-outpaced-how-engineering-organizations-measure-developer-productivity) (vendor-commissioned, n=700).
- **DX** — [Q2 2026 benchmarks](https://newsletter.getdx.com/p/ai-in-engineering-q2-2026-benchmarks), [2026 tooling budgets](https://getdx.com/blog/how-are-engineering-leaders-approaching-2026-ai-tooling-budget/) (vendor).
- **Qodo** — [AI coding paradox report](https://www.qodo.ai/blog/ai-coding-paradox-report/) (vendor-commissioned, n=500). 89% had an AI-related incident; 25% a full outage.
- **Veracode** — [GenAI Code Security Report](https://www.veracode.com/blog/genai-code-security-report/). 45% of samples fail security tests; **flat ~55% pass across model generations**.
- **Apiiro** — [4x velocity, 10x vulnerabilities](https://apiiro.com/blog/4x-velocity-10x-vulnerabilities-ai-coding-assistants-are-shipping-more-risks/). Syntax errors −76%, logic bugs −60%, but **privilege escalation +322%, architectural flaws +153%**.
- **Cloud Security Alliance** — [AI-generated code vulnerability surge](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-generated-code-vulnerability-surge-2026/).
- **NIST SATE / SAST false-positive precedent** — via [Help Net Security](https://www.helpnetsecurity.com/2025/06/19/traditional-sast-tools/). 8-30% of warnings security-relevant; abandonment inside two weeks. **The historical warning this project must heed.**
- **CircleCI** — [2026 State of Software Delivery](https://circleci.com/blog/five-takeaways-2026-software-delivery-report).
- **Amazon incident, March 2026** — [OECD AI Incidents Monitor](https://oecd.ai/en/incidents/2026-03-10-01aa), [TechRadar](https://www.techradar.com/pro/amazon-is-making-even-senior-engineers-get-code-signed-off-following-multiple-recent-outages).
- **AI slop as a forcing function** — [curl ending its bug bounty](https://www.bleepingcomputer.com/news/security/curl-ending-bug-bounty-program-after-flood-of-ai-slop-reports/), [GitHub's PR kill switch](https://www.theregister.com/2026/02/03/github_kill_switch_pull_requests_ai/), [Builder.io on reviewing AI PRs](https://www.builder.io/blog/developers-drowning-in-ai-prs).
- **CodeRabbit Series C** — [BusinessWire](https://www.businesswire.com/news/home/20260812311754/en/CodeRabbit-Raises-$143-Million-at-$1.5-Billion-Valuation-and-Introduces-Agentic-Change-Management).
- **Practitioner reports on review noise** — [HN thread on Greptile](https://news.ycombinator.com/item?id=46777079).
- **Agents bypassing hooks with `--no-verify`** — [pydevtools handbook](https://pydevtools.com/handbook/how-to/how-to-stop-ai-agents-from-bypassing-pre-commit-hooks/). The strongest specific unmet need found, and ECC already ships the answer.
- **Anthropic** — [Building a C compiler with parallel Claudes](https://www.anthropic.com/engineering/building-c-compiler) (existence proof, no controlled comparison), [infrastructure noise](https://www.anthropic.com/engineering/infrastructure-noise).
- **Epoch AI** — [SWE-bench Verified tracking](https://epoch.ai/benchmarks/swe-bench-verified). Preferred over vendor leaderboard aggregates.
- **InfoQ** — [AGENTS.md context file value review](https://www.infoq.com/news/2026/03/agents-context-file-value-review/).

## 11. The fourteen systems, still governing

Not consulted afresh in this sweep, but every borrowing decision in
[build-on.md](../build-on.md) rests on the source-read in [cards/](../cards/) at
pinned commits, with licences and reuse obligations in
[licenses.md](../licenses.md):

**Cline** (checkpoints, compare-and-swap restore) · **SWE-agent** and
**mini-SWE-agent** (revert-on-lint, autosubmit, trajectories, the lower bound) ·
**Superpowers** (systematic debugging, reproduce-first) · **BMAD** (blind
review, the open-question admission rule) · **Spec Kit** (bounded clarify, typed
gap grammar) · **Aider** (repository map, benchmark harness) · **OpenCode**
(side-gitdir snapshots, compaction, permission engine) · **gstack** (evidence
bound to a tree hash) · **ECC** (`block-no-verify`, destructive classifier) ·
**Continue** (incremental index) · **Agentless** (execution-based selection) ·
**AutoCodeRover** (ideas only — not open source) · **OpenHands** (event log).

---

## 12. Architecture drift and documentation staleness (added 2026-09-16)

Consulted for `core/atlas.py`. The design note is
[`docs/design/architecture-atlas.md`](../../design/architecture-atlas.md).

- **Software Reflexion Models: Bridging the Gap Between Source and High-Level
  Models** - Gail C. Murphy, David Notkin, Kevin Sullivan. FSE 1995, pp. 18-28.
  [Author's own page](https://www.cs.ubc.ca/~murphy/papers/rm/fse95.html)
  (html). The technique `atlas.py` implements: state a high-level model, extract
  one from the source, report where they agree and differ. Case study: NetBSD,
  250,000 lines of C, "in only a few hours". Abstract quoted verbatim in the
  design note.

- **Detecting Outdated Code Element References in Software Repository
  Documentation** - Wen Siang Tan, Markus Wagner, Christoph Treude. Empirical
  Software Engineering 29(1):5, 2023. [arXiv
  abs/2212.01479](https://arxiv.org/abs/2212.01479) (html). Over 3,000 GitHub
  projects; "most projects contain at least one outdated code element reference
  at some point in their history". Their mechanism - references that survive in
  documentation after all source instances are deleted - is used verbatim for
  the absence half of the check.
  *Held separately:* "more than a quarter of the 1000 most popular projects on
  GitHub contained at least one outdated reference" comes from the authors'
  earlier work via a search summary (snippet). Not quoted as established, and
  not carried into the plan.

- **ARCHITECTURE.md** - matklad (Alex Kladov), 6 Feb 2021.
  [matklad.github.io](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html)
  (primary). The convention most repositories with such a file are following.
  Its advice - "Do name important files, modules, and types. Do not directly
  link them (links go stale)" and "only specify things that are unlikely to
  frequently change" - is the *opposite* of what this feature wants, and the
  design note says so out loud: detection makes precision affordable, and if
  the detection turns out noisy then his advice to stay vague was better.

- **Automatic Detection of Outdated Comments During Code Changes** - Liu et al.,
  COMPSAC 2018
  ([IEEE](https://ieeexplore.ieee.org/document/8377652/)) and follow-on
  code-comment consistency work (snippet). Consulted for the adjacent problem of
  stale *comments*. **No figure from these was used**: `atlas.py` checks
  documentation references to paths, not comment-code semantics, and the
  detection rates reported there do not transfer.

---

## A note on the two tools that did not work

Recorded so the next person does not repeat it. **Connected Papers** is a
client-rendered application and returns no server-side results to a fetcher;
**Semantic Scholar's** API rate-limited immediately. The arXiv listing API was
the workable substitute, and it also rate-limits under burst. The five parallel
research passes were what actually produced breadth.
