# What already works, and what it means for ElevenPowers

*2026-11-05. Five research passes ran in parallel, with no paid runs.*

The five track reports in this folder each read 28–45 sources and grade them:
- **read:** the page itself was read;
- **abs:** only the arXiv abstract was read;
- **snippet:** only a search summary was seen.

I re-read seven of the central claims against their pages (listed
[at the end](#claims-re-read-against-the-page)). The shared search budget ran
out during two tracks, so some topics went unsearched; see
[gaps](#gaps).

| Track | Question |
|---|---|
| [A](A-harness-interventions.md) | Which harness interventions have measured, controlled effects on real repositories? |
| [B](B-products-practices.md) | What products and practices work in the field, and why they won |
| [C](C-reviewing-agent-output.md) | What makes agent changes mergeable, and does attached evidence help reviewers? |
| [D](D-regressions-coupling.md) | What prevents regressions and keeps coupled code in step, in industry and with agents? |
| [E](E-agent-addons.md) | Do plugins, skills, hooks and instruction files help a frontier agent, and which survive model progress? |

## The answer

The field's evidence explains ElevenPowers' own results rather than
contradicting them. On frontier models, add-ons rarely change whether a
task gets solved; they change what it costs. What does change an agent's
behaviour is narrower:
- **a deterministic check** that holds "done" and names the violation;
- **information the model cannot get**, supplied by a person;
- **a judgement people cannot make themselves:** whether a test actually
  tells the change from its absence.

ElevenPowers has the second and third in its code. But it delivers them in
the form the evidence says fails: advisory notes before edits, and reports
after. The change this points to is **from advice to gates, and from the
reviewer to the author.**

## What the evidence agrees on

### 1. On frontier models, harness changes move cost, not results

- **Harness or Model?** ([2609.11987](https://arxiv.org/abs/2609.11987), A).
  Paired runs of the same model compared its native harness with a neutral
  one, on 80 private tasks:
  - Opus 4.8: −1.25pp (CI −10.0 to +7.5);
  - GPT-5.5: +1.25pp;
  - the neutral harness cost 1.2–1.6× more per solved task.
- **An empirical study of harness design**
  ([2609.20804](https://arxiv.org/html/2609.20804v1), A). Planning added
  11.6pp to a 30B model, and −2.0 and −0.4pp to the two strongest.
- **A reviewer loop**
  ([SWE-Review, 2607.06065](https://arxiv.org/html/2607.06065), A). Its gain
  fell as the generator got stronger:

  | Generator's baseline | Gain |
  |---|---|
  | 27.5% | +25.1pp |
  | 72.2% | +3.0pp |

- **Terminal-Bench 2.0** (E). The same model, Sonnet 4.5, varied by about
  3 points across harnesses.
- **Anthropic** says it removes harness parts as models improve (vendor, E).
- **ElevenPowers' own results fit:**
  - the held-out sweep resolved the same share at 1.4× the cost;
  - v3 found no benefit at 1.7× the wall time.
- **The exception:** restarting an agent that stopped early gained more on
  stronger models (LoopsBench, +8.04pp for Opus 4.7). Compute was not
  matched between arms.

### 2. A rule enforced as a check beats the same rule as text, and text can do worse than nothing

- **ECLoop** ([2607.28815](https://arxiv.org/html/2607.28815v1), re-read).
  On a 100-task ablation:

  | Configuration | Solved |
  |---|---|
  | Structured conditions, enforced | 68 |
  | No guidance | 63 |
  | Prose summary of the same conditions | 58 |
  | Baseline | 47 |

  On 500 SWE-bench Verified tasks it gained +4.8 to +11.8pp, p<0.001 in
  all four agent and model pairs. *Limit:* GPT-5-mini and MiniMax-M2.5, not
  Claude.
- **ContextCov** ([2603.00822v2](https://arxiv.org/html/2603.00822v2),
  re-read). Rules from AGENTS.md compiled into 788 checks:

  | Configuration | Compliance |
  |---|---|
  | Compiled checks | 88.3% |
  | Prompt alone | 67.0% |
  | LLM reflection | 50.3% |

  The resolve rate went from 53.0% to 57.3% (p=0.031). *Limit:* GPT-5.2
  only.
- **RepoComplianceBench** (E). Quoting the rule verbatim in AGENTS.md
  changed nothing. One round of harness feedback naming the violated clause
  raised compliance to 90–100%.
- **Google, with humans** (Sadowski et al., CACM 2018, D):
  - **Rejected formats:** a warnings dashboard "saw little use", and new
    compiler checks ship as errors because warnings were ignored.
  - **Timing:** 74% of issues flagged at compile time were judged real,
    against 21% of those found in checked-in code.
  - **Precision bar:** a code-review check must stay under 10% effective
    false positives.
- **A regression gate**
  ([2607.01855](https://arxiv.org/html/2607.01855v1), A). Re-running earlier
  tests after each turn and rejecting a regression cut the share of tasks
  that regressed from 43.2% to 12.5% (DeepSeek-V3). A recap of earlier
  requirements gained about 4pp. *Limit:* the gate's tests are also the
  grader's, so the comparison is circular.
- **FeatureArc** ([2610.37434](https://arxiv.org/html/2610.37434),
  re-read). Of 367 stages ending on a red self-test, agents called the
  failure "unrelated or pre-existing" in 321 (87.5%). Only 23 of those 321
  checked the claim on the starting code.
- **ElevenPowers' v3:** the 4 dependents its notes named were delivered and
  not acted on. Same finding.
- **The counterweight:** intervening mid-run harms runs that would have
  succeeded. A critic with AUROC 0.94 cost up to −26pp
  ([2602.03338](https://arxiv.org/abs/2602.03338), abs). So a gate fires at
  the end, on one specific violation, with a way out.
- **Claude Code's own docs** (re-read). They place "a request for evidence"
  on the non-deterministic side. A `Stop` hook that exits with code 2 is
  enforced.

### 3. Knowledge a person supplies helps; knowledge the model writes for itself does not

- **SkillsBench** ([2602.12670v4](https://arxiv.org/abs/2602.12670v4)).
  Curated skills: +16.6pp (33.9% to 50.5%), re-read from the abstract.
  Self-generated skills were negative. That figure comes from the body,
  which I did not re-read, and it changed between versions of the paper
  (A, E).
- **SWE-Skills-Bench** (E): 92 of 98 skills had no significant effect.
- **Vercel** (vendor, E). For APIs newer than the model's training, an 8 KB
  docs index took the pass rate from 53% to 100%. A skill that was merely
  available was not invoked in 56% of cases.
- **Ask or Assume?** ([2603.26233](https://arxiv.org/html/2603.26233), A).
  With Sonnet 4.5:

  | Condition | Resolved |
  |---|---|
  | Missing requirement | 54.8% |
  | Agent may ask, or always interacts | 61.2–70.4% |
  | Fully specified | 70.8% |

- **ElevenPowers:**
  - declared rules cut left-behind dependents from 31/50 to 15/50;
  - automatic discovery of rules failed.

### 4. Finding coupled code automatically has a low ceiling everywhere

- **ROSE** (ICSE 2004, D). Recovering a change held out of a commit from
  history: about 4% recall at about 50% precision.
- **Ripple** (ICSE 2026, D). The best method scored F1 25%, even when given
  the change's intent and a seed edit. Evolutionary coupling's precision
  was 4.9%.
- **LSP find-references** (D). Recall stayed near 0.66 in every arm. Opus
  4.8 made no LSP calls when grep was available
  ([2608.13568](https://arxiv.org/html/2608.13568), A).
- **TDAD** (D). Giving the agent a map from code to tests cut test-level
  regressions, but instance-level regressions rose (30.2% to 33.3%) and
  resolution fell. *Limit:* n=100, no significance test.
- **So ElevenPowers' failed discovery matches the field,** not only its own
  implementation.
- **Declared co-change rules are used at scale and never evaluated.** About
  2,140 files in Chromium carry `LINT.IfChange`. That count comes from the
  GitHub code-search API, run by track D on 2026-11-05, and is approximate.
  Chromium and Fuchsia use the rules as advisory, with a
  `NO_IFTTT=<reason>` bypass. No effectiveness study was found.

### 5. Reviewers: attached evidence does not move outcomes; whether a test discriminates is what matters, and people cannot judge it

- **Meta's randomized trial**
  ([2507.13499](https://arxiv.org/html/2507.13499v1), re-read). Showing AI
  patches to reviewers added 6.7% to time spent (p≪.001), and the feature
  was rolled back. Shown only to authors, the patches had no significant
  cost.
- **Attaching tests does not change merges** (C):
  - across 31,284 agent PRs, merge rates were about the same with and
    without tests;
  - in 80K PRs from before AI, explaining the tests in the description had
    a merge odds ratio of 1.009.
- **Agent tests are mostly weak** (C). 80.2% of 86,156 agent test patches
  have a weak oracle or none. The classifier is a regex.
- **People cannot judge machine-made assertions**
  ([2607.08885](https://arxiv.org/abs/2607.08885), abs, n=86). They were
  right 74% of the time on correct ones and 49% on wrong ones, at similar
  confidence.
- **An LLM review anchored reviewers** (Tufano et al., ICSE 2025, C). They
  caught no more seeded issues and saved no time.
- **A false claim in the PR description is the one strong penalty**
  (23,247 PRs, C). Such PRs were accepted 28.3% of the time against 80.0%.
- **Merged agent PRs need more follow-up fixes**
  ([2609.26847](https://arxiv.org/abs/2609.26847), abs). They draw verified
  follow-up fixes at 1.62× the odds of human PRs in the same repositories.
- **AI review lands only at high precision** (C). Its comments were
  addressed 0.9–19.2% of the time, against 60% for human comments.

### 6. Where things get acted on: the agent's own loop, and the PR

- **The host now ships the generic receipts layer** (re-read). Claude Code
  has:
  - `Stop` hooks;
  - `/goal`, whose evaluator "doesn't run commands or read files
    independently";
  - `/code-review`;
  - a documented "ask Claude for *evidence*".
- **Review is the bottleneck** (B).
  - Vendor telemetry (Faros): time in review rose 441.5% under high AI
    adoption.
  - An independent difference-in-differences study of Cursor adoption: a
    persistent +30.3% in static-analysis warnings.
- **Distribution follows first-party agents** (B). Single-feature add-ons
  get absorbed or shut down. Receipt checkers have almost no adoption; TDD
  Guard's 2.4k stars is the high-water mark.
- **Generating the missing test is accepted at scale** (D):
  - Google's mutation testing serves more than 24,000 developers, and
    suppression raised the share of productive mutants from 15% to 89%;
  - engineers accepted 73% of the tests Meta's ACH generated (abs).

### 7. ElevenPowers' staleness rule is the weakest method measured

**Impact Is Not Invalidation**
([2609.25130](https://arxiv.org/html/2609.25130), re-read) compares ways to
decide whether a claim like "this test passes" still holds after a change:

| Method | Precision | Recall |
|---|---|---|
| Re-check when the claim's file changes | 0.21 | 0.30 |
| Re-check when a referenced symbol changes | 0.39 | 0.54 |
| pytest-testmon | 0.41 | 0.87 |
| Ask a model about the specific claim (pooled; Opus 5 alone: precision 0.974) | 0.79 | 0.72 |
| Ask "does the diff preserve behaviour?" | about 0.3 | — |

*Limit:* a single author, with 151 held-out flips.

## What this means for ElevenPowers

**Keep:**
- **The discrimination (vacuity) check.**
  - It is the one measured effect.
  - It is a judgement people cannot make, and one most agent tests fail.
  - Discriminating against the base is necessary but not sufficient: 62%
    of an AI reviewer's false approvals included tests the agent wrote
    (SWE-Review). Mutation adequacy is the stronger form.
- **Declared rules,** `LINT.IfChange` included. They are the one form of
  coupling knowledge that worked.
- **Hash-bound evidence, as protection against forgery.** PR text is an
  attack surface: refined metadata flipped reviews on 32 of 33 CVEs (C).
  But hash-bound evidence should not decide staleness.

**Change:**
- **Advice to gates.**
  - Some end-of-task findings become a `Stop` hook:
    - a rule left behind;
    - a patch no test discriminates;
    - a declared check that regressed;
    - a "pre-existing failure" that the baseline contradicts.
  - The hook sends the agent back once, naming the violation.
  - A cap releases it, and the release is logged.
  - This borrows from ECLoop, ContextCov, and Chromium's
    `NO_IFTTT=<reason>`.
- **Reviewer to author.** Verdicts go to the agent and the author before
  the PR exists. A reviewer sees at most one line and a command to
  reproduce it.
- **Staleness by file hash to re-checking the claim.** Later: the evidence
  is a single-author paper.

**Stop:**
- **Briefs whose information the model can find itself.** The import
  neighbourhood was delivered and ignored in v3. The declared-rule note
  stays until a gate beats it.
- **Automatic rule discovery.**
- **Leading with the PatchProof bundle** for human reviewers.
- **New layers that strong models don't use:** LSP, memory and planning.
- **Resolve rate as the outcome.** It does not move. Measure the specific
  harm, plus harm to runs that would have succeeded.

## Directions considered

1. **Gates in the agent's loop** (recommended first).
   - It reuses existing code: `left_behind`, the vacuity probe and the
     ledger.
   - It is testable with the existing harness at a known cost.
2. **A CI check for agent PRs, sold to teams.**
   - That is where the pain and the budgets are, and it costs CI time
     instead of model time.
   - The market is crowded (CodeRabbit, Bugbot, Qodo), but no one was
     found checking discrimination against the base.
   - It depends on the first test below.
3. **Weaker models.**
   - Harness gains are larger there, so the claim would be "makes a cheap
     model safe to maintain a repository".
   - Supported by trend data, but it changes who the tool is for.
4. **Park the project.**
   - An honest option: the generic layer now ships with the host.

## Cheapest tests first

1. **Does non-discrimination matter in the wild?** $0, no model.
   - Run the vacuity check on merged agent PRs from public datasets
     (AIDev; the 6,774 PRs in 2609.26847).
   - Ask whether non-discriminating patches draw more verified follow-up
     fixes.
   - If they don't, both the reviewer path and the CI product lose their
     premise.
2. **A "pre-existing failure" check.** $0, no model.
   - Record which tests fail when the task opens.
   - At stop, flag a claim of a pre-existing failure that this record
     contradicts.
   - Rehearse it on the corpus.
3. **A declared-rule gate against the declared-rule note.** Paid.
   - Same v3 cases, about 100 runs. The last comparable run (100 runs) cost
     $16.35.
   - Pre-register a secondary outcome: harm on stages the note arm already
     got right.
4. **The human-reviewer study,** only if test 1 holds.
   - Design in [C §4](C-reviewing-agent-output.md#4-concrete-lessons): at
     least 60 developers.
   - Not possible without recruiting reviewers.

**What came of tests 1 and 2 (2026-11-06):**
- **Test 1 is inconclusive.** Within repositories the odds ratio was 0.91
  (0.54–1.54), with power 0.39 at 1.5. It neither supports nor removes the
  premise, so nothing is built on it
  ([results](../../../results/wild-followup/README.md)).
- **Test 2 found the check was already there, and wrong.** The ledger certified
  a test the agent broke as "pre-existing" on its first sighting. It now needs
  proof from the tree the task opened ([status](../../status.md)).

## Claims re-read against the page

Each of these was re-read on 2026-11-05 and matched the track report:
- **Claude Code's own docs:** [`/goal`](https://code.claude.com/docs/en/goal)
  and [best practices](https://code.claude.com/docs/en/best-practices).
- **ECLoop:** the ablation and the four Pass@1 gains.
- **Meta's MetaMateCR trial:** both experiments. The paper's text says
  5.5% for time spent, while its table says 6.7%.
- **Impact Is Not Invalidation:** the table above.
  - Pooled precision for the claim-level question is 0.79.
  - The 0.974 is Opus 5 alone.
- **FeatureArc:** all four figures.
  - The page says nine of its ten agents ran in Claude Code without naming
    them.
  - So "Opus 5.5 in Claude Code" is an inference.
- **ContextCov:** all figures.
- **SkillsBench:** the abstract's +16.6pp only.

My re-reads went through the same fetch summariser as the tracks. Before
any of these figures enters `PLAN.md`, read the HTML directly.

## Gaps

- **Unsearched when the search budget ran out:**
  - CODEOWNERS;
  - Launchable and Microsoft's test impact analysis;
  - snapshot and golden tests;
  - design by contract;
  - ArchUnit and import-linter effectiveness;
  - Spadini's test-driven-review figures;
  - a 385-participant experiment on provenance labels;
  - the primary Octoverse 2026 page;
  - Martian's review leaderboard, which needs JavaScript.
- **Vendor numbers only:** Bugbot, Copilot review, Faros and Anthropic's
  Code Review.
- **Few Claude results:** most gate results are on non-Claude models. On
  Claude, the closest evidence is Claude Code's own guidance (vendor, no
  data) and ElevenPowers' declared-rules run.

## Corrections to earlier records

- **Governance Decay** (reading list). The two "constraint survived vs
  dropped" pairs come from different scorers:
  - an LLM judge gives 0% and 38%;
  - a keyword heuristic gives 1% and 43%.

  Cite the scorer with each pair (E).
- **SkillsBench:** its software-engineering and self-generated-skill
  figures changed between v1 and v4. Cite the version (A).
- **Claims circulating online that the sources do not support** (A):
  - "3% false success with an independent verifier" (2606.09863);
  - a pass@64 figure presented as a deployable gain;
  - "a GAIA study rejected scaffold insensitivity".
