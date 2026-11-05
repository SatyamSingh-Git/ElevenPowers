# D: What prevents regressions and keeps coupled code in sync

28 sources read (page itself; arXiv via /abs/ or /html/; non-arXiv PDFs read through `pdftotext`). Grades: **(read)** means I read the page, **(snippet)** means a search summary only. **Coverage gap:** the shared web-search budget ran out before I searched CODEOWNERS studies, Launchable or Microsoft test impact analysis, snapshot/golden/approval tests, design-by-contract, or ArchUnit and import-linter effectiveness. Treat those as unsearched, not as negative.

## 1. Findings, ranked by strength × relevance

**F1. Discovering impact sets has a low ceiling everywhere. ElevenPowers' failed discovery matches the field, not just its own implementation.**
- *Ripple / "From Seed to Scope"* (Yadavally & Nguyen, ICSE 2026; [PDF](https://aashishyadavally.github.io/assets/pdf/pub-icse2026-(2).pdf), read). Setup: 100 untangled Apache Java bug-fix commits; method-level impact sets; the method is **given the change intent and a seed edit**. Results:
  - evolutionary coupling: P 4.9%, R 17.1%, F1 5.2;
  - dependence coupling: P 7.6%, R 64.7%;
  - best LLM hybrid (GPT-4o): P 28.2%, R 36.3%, F1 25.0.
  History found locations that dependence analysis missed in 21% of commits. *Limit:* Java bug fixes only; seeds recovered by a proxy.
- *ROSE* (Zimmermann et al., ICSE 2004; [PDF](https://www.st.uni-trier.de/diehl/pubs/icse04.pdf), read). Setup: 8 projects, 10,761 transactions. When one change is held out of a commit, ROSE finds it with **recall ~4%** at ~50% precision. It falsely warns on ~2% of complete commits. *Limit:* 2004-era CVS histories.
- *LSP reference completeness* (arXiv [2608.13568](https://arxiv.org/html/2608.13568v1), June 2026, read). Pyright raised precision from 0.76 to 1.00, but **recall stayed 0.66–0.67 in every arm**. On multi-file renames, grep scored 1.00 and the LSP 0.67/0.83, because the LSP misses comments and strings. *Limit:* preliminary; 3 repositories, 2–3 rollouts.
- *CoEdPilot's* 79.5% precision / 72.9% recall (ISSTA 2024; [html](https://arxiv.org/html/2408.01733v1), read) does not compare. Its candidate pool is the commit's own files plus randomly sampled negatives, not the whole project.

**F2. Human advice outside the blocking path gets ignored; checks inside the path get acted on (Google, years of data).**
*Lessons from Building Static Analysis Tools at Google* (Sadowski et al., CACM 2018; [PDF](https://6826.csail.mit.edu/2020/papers/google-analysis-cacm.pdf), read).
- The FindBugs dashboard "saw little use".
- In the 2009 Fixit, of 3,954 reviewed warnings only **16% (640) were fixed**.
- New Clang diagnostics ship as errors, "not a warning, which the Clang team found Google developers ignored."
- Developers rated **74%** of compile-time issues "real problems", against 21% of issues found in checked-in code.
- Code-review checks must stay **below 10% effective false positives**. An analyzer whose "Not useful" ratio passes 10% is disabled. Reviewers click about 5,000 "Please fix" a day against 250 "Not useful".

*Limit:* experience report; the survey is uncontrolled; the users are humans.

**F3. Agents show the same pattern: rules as executable checks beat the same rules as prose.**
- *ContextCov* (arXiv [2603.00822v2](https://arxiv.org/html/2603.00822v2), May 2026, read). Setup: SWE-bench Lite, 300 tasks; OpenCode with GPT-5.2. AGENTS.md rules were compiled into 788 executable checks, and violations were fed back after each patch, up to 5 rounds.
  - Clean patches: **88.3%**, against 67.0% prompt-only and **50.3% with an LLM critique** (worse than no feedback).
  - Resolved: 57.3% against 53.0% (McNemar p=0.031).
  - *Limit:* one coding model; AGENTS.md files were generated, not native; no multiple-comparison correction; Python only. It does not measure dependents.
- *Prose levers are weak* (arXiv [2602.07900v2](https://arxiv.org/html/2602.07900v2), read). Prompting four models to write more or fewer tests changed resolved tasks by 0 to −13 on SWE-bench Verified. None was significant; 83.2% of outcomes did not change.
- *Corroboration (weak):* *Architecture as Capability Equalizer* (arXiv [2608.21747](https://arxiv.org/html/2608.21747v1), read). TypeScript interface contracts were the only guidance format all six models complied with fully. *Limit:* n=3 per cell, no significance tests, one task.
- ElevenPowers' own v3 result fits this pattern: all 4 detected losses went unacted on.

**F4. Industry chooses which existing checks to run from a dependency graph that is complete because the build forces it.**
- *Google TAP* (Memon et al., ICSE-SEIP 2017; [PDF](https://web.eecs.umich.edu/~xwangsd/courses/w23/readings/googletest.pdf), read).
  - Of 5.5M affected test targets, only 63K ever failed; 1.23% of executions found a breakage.
  - Running only targets within build-graph distance 10 saved 42% of resources (55% at distance 6) and **missed no breakage** in their simulation.
  - The CACM paper explains why the graph can be trusted: Bazel builds are hermetic, so "all inputs must be explicitly declared."
  - *Limit:* one dataset, simulation only.
- *Meta predictive test selection* (arXiv [1810.05286](https://arxiv.org/abs/1810.05286), read abstract). It halved testing infrastructure cost while still reporting >95% of individual test failures and >99.9% of faulty changes. *Limit:* company self-report, not replicated.
- *PatchDiff* (ICSE 2026; arXiv [2503.15223](https://arxiv.org/abs/2503.15223), read abstract). 7.8% of "plausible" SWE-bench patches fail the full developer-written suite.
- These methods select among checks that already exist. They cannot help a dependent that no check covers, which describes 27 of v3's 31 losses.

**F5. At scale, the strongest evidence for catching what tests miss is generating the missing check at the change.**
- *Google mutation testing* (arXiv [2102.11378](https://ar5iv.labs.arxiv.org/html/2102.11378), read).
  - Mutants are surfaced during code review, at most one per line and at most 7× the number of files changed.
  - More than 24,000 developers used it.
  - Suppression heuristics raised productive mutants from **15% to 89%**; 82% of mutants that got feedback were labelled productive.
  - The ICSE 2021 follow-up (arXiv [2103.07189](https://arxiv.org/abs/2103.07189v1), read abstract) studied ~15M mutants: developers who see mutants write more tests, and mutants couple to real faults.
  - *Limit:* observational.
- *Meta ACH* (arXiv [2501.12862](https://arxiv.org/abs/2501.12862), Jan 2025, read abstract). Covered 10,795 Kotlin classes and generated 9,095 mutants and 571 tests. Engineers **accepted 73%** of the tests. The equivalent-mutant detector scored P 0.79 / R 0.47, rising to 0.95 / 0.96 with preprocessing.
- *Meta JiT catching tests* (arXiv [2601.22832](https://arxiv.org/abs/2601.22832), Jan 2026, read abstract).
  - Across 22,126 generated tests, diff-aware generation produced **4×** the candidate catches of hardening tests.
  - Of 41 catches reported to engineers, 8 were true positives (≈20% by my arithmetic) and 4 were serious.
  - *Limit:* company self-report; low absolute yield.

**F6. Agents really do leave dependents behind, and the error is omission.**
- *ChainSWE* (arXiv [2607.02606v2](https://arxiv.org/html/2607.02606), Sep 2026, read). Setup: 100 chains, 304 bugs, 7 models. Per-bug accuracy fell from 58.9% (oracle) to 36.5% (sequential), and 48% of downstream failures were chain errors. Under-edits outnumber over-edits "roughly nine to one", stated only in a figure caption.
- *SWE-Bench ProMax* (arXiv [2608.09802](https://arxiv.org/html/2608.09802), read). Setup: 170 refactors in 7 languages; the best model resolved 41.2%. The paper names "the dominant failure mode" as "*incomplete refactoring*": agents miss "peripheral call sites, documentation, configuration files". It gives no percentage and tests no intervention.
- *RefactorBench* (ICLR 2025, [abs](https://arxiv.org/abs/2503.07832), read). Agents solved 22% of tasks; a time-limited human solved 87%.
- *SWE-CI* (arXiv [2603.03823v3](https://arxiv.org/html/2603.03823v3), read). For most of the 18 models, fewer than 25% of tasks finish with no regression.
- *Breaking changes in agent PRs* (MSR 2026, [abs](https://arxiv.org/abs/2603.27524), read). Across 7,191 agent PRs, agents broke compatibility less often than humans overall (3.45% vs 7.40%). In maintenance work the rate rose to 6.72% for refactoring and 9.35% for chores. *Limit:* Python only; breaks detected by AST.

**F7. Structural tooling helps only with structural coupling, and only modestly.**
- *CodePlan* (FSE 2024, [abs](https://arxiv.org/abs/2309.12499), read). Dependency analysis plus may-impact analysis got 5 of 6 repositories through the validity checks; baselines got 0 of 6. The tasks are driven by compile errors (C# migration, Python temporal edits).
- *SWE-Master* (arXiv [2602.03411](https://arxiv.org/html/2602.03411), read). Twelve pyright LSP tools added +2.0pp (68.4→70.4) and +1.4pp (66.2→67.6) on SWE-bench Verified. Single runs, no significance test.
- *Types.* Gao et al. (ICSE 2017, snippet): TypeScript or Flow would detect ~15% of 400 public JavaScript bugs. Type-constrained decoding "reduces compilation errors by more than half" (arXiv [2504.09246](https://arxiv.org/abs/2504.09246), read abstract).

**F8. Declared co-change rules: adopted by large codebases, advisory, and never evaluated.**
- *Chromium* ([guide](https://www.chromium.org/chromium-os/developer-library/guides/development/keep-files-in-sync/), read). IfThisThenThat "generates findings in Gerrit". It "should not replace testing or basic DRY principles", and `NO_IFTTT=<reason>` in a commit message bypasses it.
- *Fuchsia* ([presubmit](https://fuchsia.dev/fuchsia-src/development/source_code/presubmit_checks), read). It "leaves *warnings* and so does not block".
- *Adoption.* I queried the GitHub code-search API on 2026-11-05: **2,140** files in the chromium/chromium mirror and 200 in tensorflow contain `LINT.IfChange`. GitHub's counts are approximate and cover the default branch only.
- *Effectiveness.* No study found.
- *TDAD* (arXiv [2603.17973v2](https://arxiv.org/html/2603.17973), read). A test map plus a 20-line skill cut the test-level regression rate from 6.08% to 1.82%. Instance-level regressions went from 30.2% to 33.3% and resolution from 31% to 29%. *Limit:* n=100, small local model, no significance tests.
- *CodeScene* (vendor docs, snippet) publishes no accuracy data for change coupling.

## 2. What demonstrably works that ElevenPowers does not do

1. **Blocking where it now advises.** Executable checks returned to the agent until the patch is clean beat the same rules written as prose (F3). Google learned this over a decade with humans (F2). ElevenPowers names dependents in a brief and a report. Both are dashboard-shaped.
2. **Writing the missing check.** Mutation-guided and diff-aware test generation produce tests engineers accept: 73% acceptance at Meta, productive-mutant ratio 15%→89% at Google (F5). A quiet dependent is exactly an unchecked behaviour.
3. **Measuring whether surfaced notes get acted on, and turning off the noisy ones** (Tricorder's 10% rule, F2).
4. **Removing the coupling.** Chromium tells authors not to use IfThisThenThat in place of DRY (F8). This is guidance only; I found no measured effect.

## 3. What contradicts or undercuts warning the agent about dependents

- **The detector caps the warning.** Even with the intent and a seed, the best impact-set predictor reaches F1 25%. History-only recall of a missing change is ~4% (F1). This is the same wall ElevenPowers hit, so more discovery work is unlikely to clear it.
- **Even a correct warning is not enough.** Prose rules got 67% compliance against 88% for executable feedback. An LLM critique made compliance worse (F3). Humans ignored compiler warnings until they became errors (F2). This matches the 4-of-4 unacted detections in v3.
- **Structural reach is the wrong axis.** LSP recall plateaus around 0.66 (F1), and CodePlan's gains are on compile-driven tasks (F7). Meanwhile 22 of v3's 31 losses are not import-reachable.
- **For balance:** declared rules did help in ElevenPowers' own test (15/50 vs 31/50 left behind). Declaration works. What is weak is advising where it could block, and the lack of any check on the dependent itself.

## 4. Lessons

**Borrow**
- **ContextCov's loop for declared rules (F2, F3, F8).** Compile each declared rule, `LINT.IfChange` included, into a diff check that runs at end of task. If a guarded block changed and its target did not, the check returns the violation. It stays unresolved until the target is edited or the agent records a reason, as `NO_IFTTT=<reason>` does. Rerun the declared-rules experiment as *gate vs name*. Also measure false gates on cases whose target genuinely needs no change, as ROSE's closure test does (F1).
- **Hardening tests from Meta JiT/ACH (F5).** For each declared dependent, generate a characterization test of its current behaviour before the edit. Keep it only if it kills a mutant of the shared contract, then rerun it after the edit. This turns a quiet dependent into a loud one, and v3's dependents are, by construction, the behaviours the public suite does not pin.
- **Tricorder's acted-on metric (F2).** Log, per note type, whether the agent changed anything in response. Suppress any type whose effective false-positive rate is above 10%.

**Stop**
- **Discovery as the headline mechanism (F1).** History and co-reading should only *propose* declarations for a person to confirm. At ROSE's 0.9 confidence threshold, false alarms are ~2% but recall is ~4%: a suggestion source, not coverage.
- **More prose in the brief or report as a fix for inaction (F3).**
- **Deeper import or LSP graphs as the answer to this failure class (F1, F7).** Keep them for structural breakage, where compilers and types already do most of the work.

**Try**
- **A "remove the coupling" proposal (F8).** When a declared rule ties two copies of a format or constant, propose a single source (import or codegen). No agent evidence exists, so this needs its own trial.
- **Keep test-selection advice, but don't expect it to help here (F4).** It is industry-proven for choosing among existing checks. It cannot reach unchecked dependents, which were 27 of v3's 31 losses.
