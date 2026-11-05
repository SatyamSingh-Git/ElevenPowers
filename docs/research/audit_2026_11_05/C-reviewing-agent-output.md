# C: Reviewing coding-agent output (2026-11-05)

**Grades.** *(read)* means the page itself was read: an arXiv /html/ page, a vendor post or a listing. *(abs)* means only the arXiv abstract page was read. *(snippet)* means only a search summary was seen.

**Not checked.** The search budget ran out before the 385-participant provenance-label experiment, Spadini's test-driven-review figures and the primary Octoverse 2026 page could be read. Martian's leaderboard is JavaScript-only.

## 1. Findings, ranked by strength × relevance

**F1. People are poor judges of verification artifacts a machine made, and a weak one makes them worse.**
- **Kaufman et al.** ([2607.08885](https://arxiv.org/abs/2607.08885), abs, 2026-07):
  - Design: a controlled experiment with 86 programmers, plus a think-aloud study with 10.
  - Accuracy was **74% on correct LLM assertions and 49% on incorrect ones** (OR 2.94), with similar confidence on both.
  - Explanations gave no overall benefit.
  - Low-quality explanations lowered accuracy (OR 0.58, p=.037).
- **Tao et al., FSE 2014** ([page](https://gpbib.cs.ucl.ac.uk/gp-html/Tao_2014_FSE.html), read): with 95 participants, low-quality generated patches pushed debugging correctness **below the control** that was given only the bug's location.
- **Tufano et al., ICSE 2025** ([2411.11401v3](https://arxiv.org/html/2411.11401v3), read):
  - Design: 29 professionals, 72 reviews and 48 seeded issues, in three arms.
  - Reviewers kept 89% of the LLM's issues and stayed on the lines it had flagged.
  - Detection of injected issues had a **median of 50% with or without** the LLM review, and the review saved no time.
  - The arm given an oracle review found 100%.
- *Limit:* small lab tasks; Tufano is underpowered by its own account.
- *Bearing:* a receipt a human must judge is worth only its discrimination, and judging that is what humans demonstrably cannot do.

**F2. Putting more AI artifacts in front of reviewers costs them time, and an RCT measured it.**
- **MetaMateCR** ([2507.13499](https://arxiv.org/html/2507.13499v1), read, FSE 2026 industry track): randomized safety trials in production at Meta.
- Showing AI patches to reviewers:
  - time in review rose 5.5% (p=.029);
  - time spent rose 6.7% (p≪.001);
  - reviewers felt compelled to "read and vet any AI patches", and the feature was **rolled back**.
- Showing the patches to authors only, collapsed for reviewers: +0.42% (p=.86), with the same apply rate.
- *Limit:* arm sizes are not reported, and these were fix patches, not test evidence.

**F3. Attaching tests, or explaining them, does not move merge outcomes.**
- **Haque et al.** ([2601.03556](https://arxiv.org/html/2601.03556), read, MSR 2026): 31,284 closed agent PRs. Merge rates without tests / with tests:

  | Agent | Without tests | With tests |
  |---|---|---|
  | Claude | 70.6% | 72.1% |
  | Codex | 86.2% | 85.2% |
  | Copilot | 53.8% | 56.8% |
  | Cursor | 75.6% | 71.6% |
  | Devin | 60.6% | 44.1% |

  PRs with tests are larger and slower; for Devin the median turnaround was 3.43 h against 38.72 h.
- **Pirouzkhah et al.** ([2602.14611](https://arxiv.org/html/2602.14611v1), read): 80K PRs from 2019, before AI, analysed with mixed-effects models and controls.
  - Explaining the tests in the description had merge OR **1.009**.
  - Explicitly asking for feedback had OR 1.721.
- *Limit:* observational, and a merge is not a measure of quality.

**F4. Oracle strength is the evidence that does track outcomes, and agents mostly lack it.**
- **Banik et al.** ([2606.18168](https://arxiv.org/html/2606.18168v1), read, 2026-06): 86,156 agent test patches.
  - **80.2% have a weak oracle or none.**
  - PRs with strong oracles draw **2.4× the review effort**, and the gap holds within size buckets.
  - Adjusted merge OR is 1.28.
  - *Limit:* the classifier is a regex over diff lines, and confounders are unobserved.
- **dotnet/runtime** ([Toub](https://devblogs.microsoft.com/dotnet/ten-months-with-cca-in-dotnet-runtime/), read, vendor practitioner, 2026-03):
  - 65.7% of the lines added by merged agent PRs were test code.
  - Toub warns that agent-written tests can lock in incorrect behaviour.
  - The repo's policy: no performance PR merges without empirical evidence.

**F5. Most agent-PR rejection is about relevance and attention, not correctness.**
- **Ehsani et al.** ([2601.15195](https://arxiv.org/html/2601.15195), read, MSR 2026): 33,596 PRs.
  - Of 600 coded rejections: **38% abandoned** without human engagement, 23% duplicates, 17% CI or test failure, **3% incorrect implementation**.
  - Each failed CI check cut the odds of a merge by about 15%.
- **Nakashima et al.** ([2602.04226](https://arxiv.org/html/2602.04226), read): 69.0% of agent rejections came with no feedback.
- **Peralta et al.** ([2605.22534](https://arxiv.org/html/2605.22534), read):
  - only 35.7% of rejections were clear failures by the agent;
  - 79.1% of merges had no feedback loop.
- **Abujadallah et al.** ([2606.13468](https://arxiv.org/html/2606.13468), read):
  - 46.41% of agent fixes were rejected;
  - incorrect fixes were 5.6% of the rejections;
  - 49.3% had no recoverable reason.
- *Limit:* ≥100-star repositories, Dec 2024 to Jul 2025 agents.

**F6. Merged agent code does need more follow-up fixing, and that population has already been mined.**
- **Takerngsaksiri et al.** ([2609.26847](https://arxiv.org/abs/2609.26847), abs, 2026-09):
  - 6,774 merged agent PRs against 5,044 human PRs from the same repositories and period;
  - agent merges attract verified fixes at **1.62× the odds**, and 69.6% of those fixes come from the same agent;
  - the judge reached κ 0.78.
- **Oukay et al., MSR 2026** ([listing](https://2026.msrconf.org/details/msr-2026-mining-challenge/27/), read):
  - 2.66% of 33,580 agent PRs contain a reverting commit, from 0.7% for Codex to 7.6% for Copilot;
  - top causes: side effects and over-engineering, 22.33%; functional incorrectness, 22.13%.
- **Against:**
  - dotnet's revert rate was 0.6% for the agent against 0.8% for humans, not significant;
  - [2607.21832](https://arxiv.org/html/2607.21832) (read) found no meaningful difference in bug-inducing commits, but its SZZ tooling has precision 0.39.

**F7. AI review only works at high precision; noise kills uptake.**
- **Independent studies:**
  - **Sun et al.** ([2508.18771v2](https://arxiv.org/html/2508.18771v2), read): comments from AI review actions were addressed **0.9–19.2%** of the time, against **60.0%** for humans. Concise, code-heavy, hunk-level and manually triggered comments did better.
  - **CR-Bench** ([2603.11078](https://arxiv.org/html/2603.11078v1), read): precision 3–5%. Reflexion raised recall from 27% to 33% while signal-to-noise fell from 5.11 to 1.95.
  - **SWE-PRBench** ([2603.26130](https://arxiv.org/html/2603.26130v1), read): models caught 21–31% of the issues humans flagged, and adding context mostly lowered scores.
- **Vendor reports:**
  - **OpenAI** ([post](https://alignment.openai.com/scaling-code-verification/), vendor, read): "Precision is more important for usability than recall."
  - **Cursor Bugbot** ([forum](https://forum.cursor.com/t/building-a-better-bugbot/149040), vendor, read): the resolution rate rose from 52% to over 70% through majority voting over shuffled passes and an agentic loop.
  - **RovoDev at Atlassian** ([2601.01129v2](https://arxiv.org/html/2601.01129v2), read, ICSE-SEIP): 38.70% of its comments were resolved, against 44.45% for humans. Removing its actionability filter cost **20 points** of alignment with human comments.
  - **Anthropic** ([post](https://claude.com/blog/code-review), vendor): under 1% of findings were marked incorrect.

**F8. Reviewers are often absent or rubber-stamping.**
- **Li et al., ICSE-JAWS 2026** ([listing](https://conf.researchr.org/details/icse-2026/jaws-2026-papers/17/Silent-Reliance-or-Diligent-Review-Human-Agent-Engagement-and-Interaction-Patterns-i), read): over 212,297 agent PRs, **73.9% were merged without modification**, with a median triage time of 0.2 h.
- **Duma et al.** ([2605.02273](https://arxiv.org/abs/2605.02273), abs): most AI PRs receive no review, and what review they get is mostly done by AI.
- **Khojah et al., ASE 2026** ([2606.26505v2](https://arxiv.org/html/2606.26505v2), read): an eye-tracking study with 32 practitioners.
  - A label saying the code was LLM-generated raised fixation time.
  - **Thoroughness was flat** (μ=0.01, CI [−0.07, 0.10]).
- *Limit:* Agarwal et al. ([2607.07980](https://arxiv.org/abs/2607.07980), abs) found the direction of "reviewed less" flips under different analysis choices.

**F9. A false claim in the description is the one signal that is strongly penalised.**
- **Gong et al.** ([2601.04886v2](https://arxiv.org/html/2601.04886v2), read): 23,247 agent PRs.
  - PRs whose description disagreed with the code, 1.7% of them, were accepted **28.3% vs 80.0%** of the time.
  - They took 55.8 h vs 16.0 h to merge, and the gap held under regression controls.
  - **45.4%** of the mismatches were phantom changes: claimed but never made.
- *Limit:* a heuristic detector (F1 0.63), observational.

**F10. Evidence written in PR text is an attack surface.** Alexopoulos et al. ([2603.18740](https://arxiv.org/abs/2603.18740), abs, ICSE 2027): refined PR metadata flipped Claude Code and CodeRabbit security reviews on **32 of 33 CVEs**. Evidence that is hash-bound and can be re-run resists this; prose does not.

## 2. What demonstrably works for reviewers that ElevenPowers does not do

- **Silence by default; findings only at high precision.** Evidence: F7 (majority voting, the actionability filter, signal-to-noise). ElevenPowers reports a state on every run.
- **Hand over an artifact the reader can apply, not prose.** Evidence: Go Home Copilot (OR 1.62, already read) and Sun's code-to-text ratio.
- **Show AI output to the author, not the reviewer.** Evidence: F2.
- **Check the description's claims against the code.** Evidence: F9.
- **Keep the change small and scoped.** dotnet: changes of 1–50 lines succeeded 76–80% of the time, against 64% for 101–500 lines. Ehsani: merge odds fall with each line added.
- **Have a human push commits to the agent's branch.** dotnet: 86.2% success with human commits, against 55.1% without.
- **Demand evidence only where reading cannot verify the claim.** dotnet's performance rule.

## 3. What contradicts or undercuts "receipts for the reviewer"

- **Merges don't move when evidence is present** (F3), and reviewers don't open what's attached (F8).
- **Most rejections are not about correctness** (F5).
- **Humans can't evaluate receipts;** a weak receipt misleads, and extra artifacts cost reviewer time (F1, F2).
- **Vendors already ship artifacts but publish no effect:**
  - Cursor (Feb 2026, [post](https://cursor.com/blog/agent-computer-use), read): videos, screenshots and logs, with no measured effect;
  - Antigravity's artifacts (snippet).
- **Provenance standards carry no verification fields:**
  - Agent Trace is at v0.1.0 RFC ([agent-trace.dev](https://agent-trace.dev/), read);
  - git-ai has 2.9k stars and its own standard ([repo](https://github.com/git-ai-project/git-ai), read).

  There is demand for attribution, but nothing shows it changes outcomes.
- **What survives:** F1, F4 and F6 support the *discrimination* core: humans can't do it, agent tests lack it, and defects that slip past it exist after merge.

## 4. Concrete lessons

**Borrow**
1. **Precision gating** (F7): surface a reviewer-facing line only when a check is non-discriminating, stale or contradicted; otherwise say nothing. Use majority-of-passes before speaking.
2. **Author-first routing** (F2): feed the verdict to the agent before the PR exists. The reviewer gets at most one line plus a reproduction command.
3. **Claim checking** (F9): diff the PR description's claims ("tests pass", "adds X") against the ledger ElevenPowers already holds, and flag phantom claims.
4. **Applicable output** (F7): when a test doesn't discriminate, emit the mutant or the missing assertion as code.
5. **Standards** (§3): carry evidence in Agent Trace `metadata`/`related` or in git notes, rather than in a bespoke PatchProof format.

**Stop**
- Stop leading with the full PatchProof bundle for humans (F1, F2).
- Stop treating resolve or merge rate as the outcome; neither is driven by correctness (F3, F5).

**Try first, with no humans and no model spend: a predictive-validity test** (F6).
- Replay the discrimination check on merged agent PRs with and without a verified follow-up fix (Takerngsaksiri's 6,774 PRs, or Oukay's 500 reverts).
- If "non-discriminating" doesn't predict later fixes, no reviewer study can show value; stop there.

**Then run the human-reviewer study.** It is modelled on Tufano (arms with seeded issues and an oracle condition), Kaufman (correct vs incorrect, n=86) and Khojah (crossover, PRs of about 77 LOC).
- **Material:** 24 real agent PRs of at most 100 changed lines.
  - 12 carry a defect that a later verified fix repaired, or are held-out-failing resolved patches from the sweep.
  - 12 are correct, with no later fix, so that false rejections are scored and both directions are tested.
- **Arms, within-subject in a Latin square:**
  - A: diff plus the agent's description;
  - B: A plus a one-line ElevenPowers verdict and a reproduction command;
  - C: A plus the full PatchProof bundle;
  - optional D: an oracle saying which test exposes the defect, as an upper bound like Tufano's oracle arm.
- **Outcomes:**
  - sensitivity *and* specificity of approve/reject;
  - time per review, since C tests the cost Meta found;
  - calibration of confidence;
  - whether the requested change names the defect.
- **Size and cost:**
  - Tufano's 29 participants were underpowered.
  - Target **≥60 developers × 3–4 PRs (about 200 reviews)**, with an 8-person pilot.
  - Sessions of about 60 minutes; Tufano's reviews averaged 42–57 minutes, so keep PRs small.
  - Pre-register B vs A on specificity-adjusted detection, with a 10-point smallest effect of interest (the validation-evidence paper's practice).
