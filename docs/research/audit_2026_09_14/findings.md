# ElevenPowers after Phase B: findings and next experiments

**Do not purchase a larger version of the current gate comparison yet. First correct the diagnosis: the recorded runs contain upstream solution retrieval, the 12% figure counts blocking events rather than blocked runs, and the treatment differs before Stop.** These are different problems from an insufficiently difficult corpus. Changing task wording or buying more tasks would not, by itself, resolve them.

The project has made substantial progress since the previous review. Candidate patches, bases, grades and host session IDs now survive. That made it possible to investigate this sweep without buying another one. The next investment should use that capability to study decisions at saved checkpoints and to evaluate candidate selection. P1 should become a bounded component experiment rather than a prerequisite for developing the broader coding system.

This report distinguishes observations from proposals. Its empirical basis is the two saved chunks, their 100 bundles, associated host transcripts, the current plan and relevant implementation inspected from revision `51d3165`. Commit `fd4e8ec` landed during the review; its process-containment change is addressed in §5.7. Detailed counts, transcript references, arithmetic and input hashes are in [evidence.md](E:/ElevenPowers/docs/research/audit_2026_09_14/evidence.md). This review changed no existing implementation files or plans.

## 1. Corrections to the current explanation

### 1.1 The sweep contains answer exposure, not just solution hints

The strongest finding is in the actual returned tool results:

- Three `attrs-6fda0a4e` attempts retrieved `gh pr diff 1328 --repo python-attrs/attrs`. The results contain the converter adapter implementation and its tests.
- A gated `click-bec59289` attempt retrieved the changed files for click PR #3582. Returned file URLs identify the exact target fix commit, `bec59289d8cf9b9b4010642b2fee483e5f8eeefc`, and the response includes patch hunks.
- Successful `attrs-0f758fe5` attempts also retrieved the upstream PR #1541 diff.

These observations come from tool-result records, not from an agent's unsupported assertion that it matched upstream. For example, the [click transcript](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpmsxu0bb0/13e7973c-53a9-4f82-964d-ef0d1c051337.jsonl:37) contains the returned target-commit URLs; the [attrs transcript](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmp88loj5gg/0e6f7f66-cb41-476d-8c04-937351c40846.jsonl:35) contains the returned source diff.

A broader read-only screen found **54 returned GitHub results containing diff hunks across 42 of 100 runs**. That screen does not prove all 42 retrieved their exact solution, and a negative screen does not prove absence of exposure. The confirmed examples are already sufficient to reject the stronger interpretation that this was a benchmark free of answer leakage.

The agents were asked to make a described upstream change. Fetching that change is a reasonable way to satisfy such a task. This is an evaluation-boundary problem, not evidence of agent misconduct. The result can describe performance at applying upstream changes with solution access; it cannot establish a 92% success rate at independently solving previously unseen repository tasks.

The existing protection addresses a different issue. [_sandboxed](E:/ElevenPowers/eval/live.py:290) sets `PIP_REQUIRE_VIRTUALENV`; `shared_site` compares user-site directory entries. Those measures do not prevent access to upstream patches, local corpus repositories or evaluator assets, nor do they certify every installed file's contents remained unchanged.

**Recommendation:** define and enforce permitted information before recalibrating difficulty. For a closed repair benchmark, use a worker environment with only the base snapshot, authorized task context and prepared dependencies. Keep target fixes, hidden tests, corpus metadata, other attempts and upstream answer access outside it. Supply model API connectivity through the host or a constrained proxy; do not give the worker general access to the solution source. Network permissions are part of the benchmark definition, not an incidental machine setting.

This is also a known failure mode in recent benchmark research: the SWE-Bench Pro Verified authors identify Git history, local files and online repositories as answer channels. Their protections and task refinements are useful references, not proof that any particular replacement corpus is automatically clean. [SWE-Bench Pro Verified](https://arxiv.org/html/2609.08149v1).[^1]

Do not delete the exposed runs, relabel their patches as incorrect, or calculate a supposedly corrected score by simply dropping the 42 flagged runs. Retrieval is a behavior that may depend on task difficulty and treatment. Such filtering would create a selected population. Retain the sweep under its actual information-access conditions and rerun a separately declared comparison if a closed-task score is needed.

### 1.2 The blocking rate is 8% of gated runs

The raw rows contain:

| Quantity | Recorded value |
|---|---:|
| Gated runs | 50 |
| Stop-block events | 6 |
| Runs receiving at least one Stop block | 4 |
| Tasks with at least one blocked gated run | 4 of 25 |
| Blocked-run fraction | **4/50 = 8%** |
| Blocking events per gated run | **6/50 = 0.12** |

Two runs were blocked twice. The four gated replicate block-count pairs are `(1,0)`, `(0,1)`, `(0,2)` and `(2,0)`. [Chunk 1](E:/ElevenPowers/results/chunks/chunk1.json), [chunk 2](E:/ElevenPowers/results/chunks/chunk2.json).

The function [blocks_recorded](E:/ElevenPowers/eval/live.py:628) counts events; that value cannot be used as a run-level eligibility probability. The claim that this independently confirms a 12% probability needs revision, including D94's arithmetic.

This is not mainly a two-versus-three-task issue. It demonstrates why the exposure unit must be explicit: events, stopping points, attempts and repository tasks are different denominators.

### 1.3 Zero Stop blocks does not mean identical treatments

The gate arm installs the hook package; vanilla does not. The package can inject opening obligations, guide an edit, ask a scope question and run declared commands before issuing a Stop block. See [_install](E:/ElevenPowers/eval/live.py:163), [on_prompt](E:/ElevenPowers/core/hook.py:83) and [on_stop](E:/ElevenPowers/core/hook.py:208).

The archive contains three runs with automatic command execution and two with scope questions. Most decisively, the gated `click-bec59289--1789341614289` bundle records **four scope questions and four permission denials**, despite zero Stop blocks. See its [ledger](E:/ElevenPowers/results/chunks/bundles-chunk1/click-bec59289--gate--1789341614289/ledger.json) and [host answer](E:/ElevenPowers/results/chunks/bundles-chunk1/click-bec59289--gate--1789341614289/answer.json).

This does not establish that the intervention caused the successful patch. It establishes that “the configurations were identical on these tasks” is false. The observed difference could reflect chance, pre-Stop interventions, unequal solution retrieval or their interactions. The existing comparison cannot separate them.

There are consequently two different questions:

1. Does the complete ElevenPowers package improve the selected patch under a specified information and compute policy?
2. Does refusing a particular Stop improve the patch beyond the same system without that refusal?

A vanilla-versus-package comparison addresses the first. A common-prefix, decision-point experiment can address the second. Block counts alone cannot turn one into the other.

### 1.4 The statistical conclusion should be narrower

The preserved rates are 46/50 and 49/50. Twenty-three tasks have equal arm-level rates, but only **22** were solved in all four attempts. `attrs-0f758fe5` was solved once and failed once in each arm. Calling every concordant task universally solved loses this distinction.

The current task-level sign comparison gives **p = 0.5** for two positive differences and no negative ones. That is a measurement with little precision under the experiment's actual conditions. It neither establishes a benefit nor establishes equivalence. Answer exposure additionally prevents interpreting it as a clean novel-repair result.

Several rules in D92–D94 need qualification:

- **31 discordant pairs is not a universal minimum.** Six independent discordant pairs all favoring one arm give two-sided exact p = 0.03125. The 31 figure is an approximate power calculation for a particular alternative, a 75% win probability among disagreements. Exact conditional power at 31 is about 77.1%; see the appendix.
- **Expected engagement is not a hard maximum.** Under an illustrative independent 8% per-run probability, two attempts yield `1 - 0.92² = 15.36%` probability of at least one block. Thirteen tasks then produce about two affected tasks in expectation. Task heterogeneity and correlated repeats can change that probability.
- **Concordant observations are not worthless.** They provide information about prevalence, aggregate effect size and harm under a representative design, even though the conditional sign/McNemar calculation uses discordant units. Their value depends on the question and sampling distribution.
- **A final successful gated patch does not show its earlier block was unnecessary.** The candidate at the first proposed stop might have been wrong and subsequently repaired. An independent vanilla success on the same task is not that candidate's counterfactual.
- **More difficult tasks are not sufficient.** A corpus with 50% baseline accuracy can still be useless for a particular gate if every failure satisfies its visible obligations.

The useful correction to D94 is to size an experiment for a declared estimand, intervention boundary, outcome distribution and smallest worthwhile effect. Engagement is one input, with uncertainty, rather than a replacement universal sizing formula.

## 2. Three viable directions

| Direction | What it would establish | Tradeoff |
|---|---|---|
| **Recommended: checkpoint experiments plus selection development** | Whether specific interventions repair particular states; whether the system chooses better candidates | Needs checkpoint and information-access discipline, but reuses existing infrastructure |
| Larger representative package comparison | Whether the complete product improves final selected correctness on the chosen workload | Important later; expensive and poor at explaining a weak or null effect |
| Verification/provenance product as the primary scope | Reliable reports, fresh evidence and fewer unsupported completion claims | A coherent product, but narrower than maximum benchmark performance |

The first direction preserves the larger mission accepted in Plan v0.7. The plan already contains candidate pools and repair, but [Phase C is again blocked on fixing the corpus](E:/ElevenPowers/PLAN.md:287). Separate developing the selection machinery from publishing its performance. Development can proceed on the preserved archive while an independent, properly isolated evaluation track is prepared.

## 3. The next gate experiment: intervene at the stopping point

### 3.1 Create a common decision point

Run a worker under one fixed configuration until its **first proposed final patch**. Before feedback or continuation:

1. Save an immutable candidate snapshot, the visible evidence, host messages and environment identity.
2. Compute a predefined eligibility condition using only authorized, visible information.
3. Randomly assign the intervention at that point, rather than assigning a different full package at the start.
4. Grade the original and final patches separately in the held-out evaluator. Keep those grades unavailable to the worker and selector.

For a pure Stop experiment, earlier guidance, scope behavior and command execution must be identical. The easiest first version randomizes only the first eligible decision per task. Multiple later randomized decisions introduce history-dependent effects and should wait until the simpler experiment is understood.

This adapts an established experimental idea: microrandomized trials assign interventions at relevant decision points to study their local effects. The source field is adaptive health interventions; transfer to coding agents is a proposed design, not a published coding-performance result. [Klasnja and colleagues](https://dept.stat.lsa.umich.edu/~tewaria/research/klasnja15microrandomized.pdf).[^2]

### 3.2 Compare useful actions, not just permission to stop

Begin with two alternatives, then add a compute control when there is a signal:

| Alternative | Behavior after the common checkpoint |
|---|---|
| Submit | Preserve and submit the checkpoint patch |
| Evidence-directed continuation | Present the exact unmet check or counterexample and allow a fixed repair budget |
| Generic continuation, subsequent comparison | Give the same additional budget with a neutral request to review and improve |
| Fresh-worker repair, subsequent comparison | Give another worker the snapshot and evidence, under the same information policy |

Submit versus continuation measures the value of spending additional work. Evidence-directed versus generic continuation measures whether the evidence adds value beyond that work. Fresh-worker repair tests whether continuing the same interpretation is the limitation.

If the host supports faithful forking, branches can share the saved prefix. If it does not, randomize one continuation from each live checkpoint. Reconstructing a fresh worker from a summary is a different treatment and should be labelled accordingly; copying files alone does not reproduce an agent's conversation state.

### 3.3 Measure the gate's error targeting and repair value separately

The key quantities are:

- How often the first proposed patch is wrong.
- How often the eligibility rule identifies those wrong patches.
- How often the same rule selects already-correct patches.
- How often the chosen continuation repairs an eligible wrong patch.
- How often it damages an eligible correct patch.

For an intervention applied only at this common point, define `p` as original error probability, `d` as eligibility among wrong patches, `r` as repair probability, `f` as eligibility among correct patches and `h` as damage probability. Relative to submitting the original patch:

```text
Expected change in correctness = p × d × r − (1 − p) × f × h
Eligibility probability       = p × d     + (1 − p) × f
```

These identities show why firing rate alone is inadequate. A rule can fire often on correct patches and contribute little. A rare rule can be valuable if it reliably finds repairable errors. The observed 92% baseline and 8% blocking figure cannot simply be inserted here: they were measured under a different intervention boundary and information policy.

Classify the original checkpoint's correctness only for offline evaluation. Hidden tests must never become the runtime's eligibility rule. If collecting a failure-enriched development bank using known outcomes, label it as such and measure population prevalence on a separate representative stream.

### 3.4 Avoid selection after treatment

Do not compare “gated runs where a block happened” with arbitrary vanilla failures. Earlier treatment can change which states reach Stop, so those groups need not be comparable.

Use eligibility assessed before randomizing the local intervention, or a correctly implemented shadow trigger under a common policy. Microsoft describes this as counterfactual logging: identify observations that would have triggered in either arm, and check the non-triggered complement. Its work also emphasizes separating a component from the full package and accounting for limited exposure. [Pre-experiment guidance](https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-pre-experiment-stage/), [post-experiment guidance](https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-post-experiment-stage/).[^3][^4]

Within a common-prefix design where the noneligible policy is identical, an eligible-state effect can be combined with representative eligibility prevalence to estimate the overall effect. That requires the same underlying population and treatment definition; it is not a licence to multiply arbitrary rates from different sweeps.

## 4. Use the archive now: candidate selection has not been tried

Across the 25 paired tasks:

- The two vanilla attempts include a graded success on **24/25** tasks.
- The four combined attempts include a graded success on **25/25** tasks.

These are retrospective **oracle pool coverage** values. They are not achieved selector scores, and answer exposure limits what they say about generation capability. Nevertheless, the archive already supplies candidates with different quality for developing and diagnosing a selector.

Freeze a development pool and compare selectors using only the permitted issue/context, base code, candidate patch and runtime-visible execution evidence. Withhold grades, gold file lists, hidden test names, exact upstream patches and host summaries that disclose the answer. Preserve provenance and record what material was removed or unavailable.

Start with simple comparisons: a fixed/random candidate baseline, visible-check ranking, and a blinded model comparison. Then test structured summaries with references to primary execution evidence. Retain easier pools to detect damage; inspect the three tasks with mixed outcomes for mechanisms without treating them as an untouched test set.

Do not tune on all 25 and then claim a generalization result on them. The archived pool is a development asset. A subsequent clean holdout must validate the chosen selector. Nor should a filtered subset of historically exposed candidates be relabelled a clean solver benchmark.

Structured summaries, tournament selection and refinement already have coding-specific research support. Kim and colleagues report gains from representing and reusing multiple coding trajectories; the important transfer is the experimental separation of generation, selection and reuse. Their results do not predict the gain in ElevenPowers. [Scaling Test-Time Compute for Agentic Coding](https://arxiv.org/html/2604.16529v1).[^5]

## 5. Product changes with the highest prospective value

### 5.1 Make a candidate, not a session, the unit of completion

A session can contain a correct candidate, a failed follow-up experiment and a final patch worse than the earlier one. The product should retain an incumbent candidate with snapshot-bound evidence, and return it when further exploration does not improve selection.

Represent every proposed stop as a candidate. Store parent/branch relationships, visible checks and unresolved assumptions. This makes rollback, independent repair and comparison ordinary operations. The current final-patch bundles are the foundation; saving only the final state still loses the transition the gate is supposed to improve.

### 5.2 Replace a generic refusal with an actionable next step

For each unmet obligation, attach the observation that would resolve it and the smallest useful action:

| Observed state | Useful action |
|---|---|
| Declared suite has not run on this snapshot | Execute it without another reasoning round |
| A specific test fails | Supply the failing input, expected/actual output and relevant code |
| Two plausible candidates disagree on behavior | Probe that input and retrieve supporting contract evidence |
| The same repair repeats without new evidence | Try a fresh diagnosis or another worker |
| All checks pass but important interpretation remains unsupported | Investigate that interpretation; another identical suite run adds little |

Hard blocking can remain appropriate for concrete unmet checks. The larger product should choose the action most likely to improve the patch. Do not add obligations merely to raise engagement: that can manufacture more interruptions without increasing the number of errors caught.

### 5.3 Build a bank of natural decision states

Store proposed-stop states from representative tasks, including correct ones. Label them offline for investigation: missing evidence, visible regression, incorrect semantics despite green tests, incomplete implementation, environmental confusion, or ambiguous requirement.

This supports a much faster development cycle than restarting every experiment from an empty repository. Candidate assessors can be evaluated on frozen states; continuation policies can be evaluated on saved prefixes. Keep a deliberately injected-fault suite for wiring and sensitivity checks, while reporting natural-state and injected-state results separately.

The bank also reveals whether the existing gate is even aimed at the failures occurring. If most wrong states are green and semantically incomplete, improving the suite trigger is the wrong investment. If wrong states are detectable but repair repeatedly fails, invest in diagnosis and implementation.

### 5.4 Preserve exposure and transitions as well as final patches

[bundle.write](E:/ElevenPowers/eval/bundle.py:114) preserves patches, manifests, answers and ledgers. The successful investigation here additionally depended on host transcripts living outside the bundles. A deleted profile or another machine would lose that evidence.

Extend the bundle contract to include or durably reference:

- Exact task text and authorized context snapshot.
- Effective worker configuration and all model-visible intervention messages.
- Tool calls and results, including retrieval provenance.
- Proposed-stop and post-intervention candidate snapshots.
- Trigger eligibility before assignment, assigned action and randomization probability.
- Grader version, environment identity and complete grade revisions.

These are prerequisites for the next causal experiment, not a request for a general observability platform. Capture the fields needed for the question being tested. Keep evaluator-only information physically and logically out of worker-visible artifacts.

### 5.5 Apply evidence invalidation to experimental conclusions

The project's original idea can prevent the next D94: make important research conclusions depend on their actual inputs.

```text
Eligibility estimate
  depends on task prompts, worker model/configuration, trigger implementation

Required experiment size
  depends on estimand, uncertainty, effect target, clustering, eligibility

Performance claim
  depends on frozen runs, information-access policy, grading version, analysis
```

When prompts are reframed, the old difficulty estimate becomes stale. When package behavior changes before Stop, a pure-block interpretation becomes invalid. When the exposure policy changes, the old success rate is a different population/configuration result. The current corpus lock is valuable, but it cannot on its own certify these conclusions.

Implement this initially as a small experiment manifest and generated report. Require explicit units and distinguish a screening pilot from a confirmatory test. A preflight should flag arithmetic contradictions and missing assumptions, while allowing an explicitly labelled exploratory run. Avoid turning experimental rigor into another chain that prevents building useful product capabilities.

### 5.6 Improve labels that currently imply more than the evidence establishes

Two examples matter for choosing what to build:

- [eval/failures.py](E:/ElevenPowers/eval/failures.py:59) labels a failed patch `localised` when its changed files overlap the gold files. That proves overlap, not that the agent found the right symbol or causal defect. Label the mechanical fact as file overlap; assign a causal diagnosis only after inspecting the attempt.
- [eval/baseline.py](E:/ElevenPowers/eval/baseline.py:149) treats input-token totals as a proxy for what reached the model. Different tool outputs, conversation lengths and caching can change totals. Capture the actual loaded interventions instead of treating token-count differences as a delivery test.

The same distinction applies to “no contamination.” A directory-membership check supports a narrowly named observation. It cannot support a statement about all environment mutation, all answer access and training-data contamination at once.

### 5.7 Finish the new process-containment boundary

Commit `fd4e8ec` correctly moves descendant cleanup toward an operating-system mechanism. However, static inspection of [contained and _bind_to_job](E:/ElevenPowers/eval/live.py:327) finds three remaining gaps in the guarantee that no descendant survives:

- `Popen` starts an executable process before `_bind_to_job` assigns it. `CREATE_NEW_PROCESS_GROUP` does not suspend execution. A descendant created during that interval need not belong to the new job. Assignment must be effective before worker code runs, using an appropriate suspended-launch or creation-time job-assignment mechanism.
- `SetInformationJobObject` and `AssignProcessToJobObject` return values are ignored. A non-null job handle does not prove that kill-on-close was configured or that the worker was assigned. If opening the process fails, the function still returns the empty job. Fail the run explicitly if containment cannot be established, and verify membership before permitting work.
- The Win32 calls have no declared `ctypes` argument/return types. Declare pointer-sized handle signatures and check errors explicitly instead of relying on default C integer conversion. This is a correctness gap in the binding; this review did not reproduce a handle-conversion failure on this machine.

Microsoft documents descendant inheritance after job assignment and a zero return on assignment failure. Python documents the default integer conversions. These support the static findings; the successful grandchild test does not cover the launch race or API-failure paths. [Job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [assignment API](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject), [ctypes](https://docs.python.org/3/library/ctypes.html).[^8][^9][^10]

Add targeted failure-path and launch-order checks when implementing that correction. Keep process-lifetime containment distinct from file/network isolation: closing a job cannot undo a host file changed while the agent was alive. Both boundaries belong in the worker environment proposed in §1.1. These are review findings only; no process-spawning reproduction or implementation change was made here.

## 6. Corpus design after access is controlled

Do not immediately rewrite commit messages into vaguer bug reports. Clear requirements are desirable, and feature implementation is a valid coding task. Obscurity is not difficulty. An issue can also contain a solution or link to one, so switching to issue text does not automatically close answer access.

Use task context that existed at the chosen cutoff and preserves the information needed to satisfy the held-out requirements. Prefer actual reports and authorized discussion over a synthetic narrative reconstructed after reading the gold patch. Validate ambiguity separately from difficulty. The current benchmark-quality literature documents both answer leakage and tests that enforce unstated details. [OpenAI's coding-evaluation audit](https://openai.com/index/separating-signal-from-noise-coding-evaluations/).[^6]

Keep three tracks:

1. **Representative evaluation:** a frozen task distribution for the selected-patch performance claim, with easy tasks retained for regression measurement.
2. **Development challenge set:** difficult or mixed-outcome tasks and natural checkpoints used to improve the system. Selection criteria are explicit; results describe that population.
3. **Mechanical fault suite:** controlled missing checks and known regressions for verifying that triggers and continuation paths work.

Selecting harder tasks using an independent development pilot is not inherently invalid. Reusing an unusually bad control realization as the comparison baseline is the problem. If an enriched population is selected, freeze the selection rule, rerun both arms freshly and report that conditional population. Use a separate representative holdout for broader claims.

A 40–60% initial success band may be convenient, but it is not an exit criterion in itself. Measure whether failures are recoverable by the proposed intervention and whether the candidate pool contains useful alternatives. A lower score caused by broken environments, unavailable requirements or forbidden-answer removal without replacement context provides no such guarantee.

Use an existing external benchmark implementation when it fits the chosen track, with pinned assets and documented access policy. The official SWE-bench tooling now includes task collection and execution interfaces; assess them before extending the custom miner further. That is an implementation option, not a claim that its default corpus solves all validity problems. [SWE-bench CLI reference](https://www.swebench.com/SWE-bench/reference/cli/).[^7]

## 7. Proposed next sequence and decision rules

| Step | Deliverable | Decision enabled |
|---|---|---|
| 1. Correct the Phase B account | Separate block events/runs, package exposure, answer retrieval and actual task outcomes | Prevent another experiment from inheriting incorrect premises |
| 2. Define the information policy | One enforced worker/evaluator boundary and a documented task-context cutoff | Establish what a baseline score measures |
| 3. Build a selector diagnostic from saved candidates | Frozen development pools and blinded selector comparisons | Determine whether choosing a better patch is a promising lever |
| 4. Capture common proposed-stop checkpoints | Original patch, eligibility and exact intervention record | Make the pure Stop question identifiable |
| 5. Run a small decision-point pilot | Repairs, damage, eligibility and uncertainty, plus a generic-compute control when warranted | Identify whether sensing, feedback or repair is the bottleneck |
| 6. Validate on a clean frozen holdout | Selected correctness and total compute under the intended policy | Support a product-level performance claim |

No paid run is prescribed merely to reach a task count. For each pilot, define a question and a decision in advance. Examples:

- If nearly all eligible checkpoints are already correct, improve error targeting before paying for more continuation.
- If eligible wrong patches rarely improve, compare a fresh worker or a more specific counterexample against generic continuation.
- If correct candidates exist but selectors miss them, prioritize candidate representation and selection.
- If clean pools contain no correct candidates, prioritize stronger generation, localization and diagnosis diversity.
- If a component's interval remains too wide to decide within its allocated budget, keep it optional and proceed with the better-supported product path. The entire outer-loop system need not wait for a definitive gate paper.

The next milestone should demonstrate a useful transition or a better selected candidate. The exact gate effect can remain an open component question while the system becomes more capable. The archive and evaluator have finally made that progression possible; their strongest use now is to explain and improve individual decisions, then test the resulting policy on genuinely held-out work.

## Sources

[^1]: Pujun Zheng and colleagues. [SWE-Bench Pro Verified: A Reliable Benchmark for Software Engineering Agents](https://arxiv.org/html/2609.08149v1). arXiv:2609.08149v1, 8 September 2026. Used for answer-access channels and the distinction between task quality and leakage.

[^2]: Predrag Klasnja, Eric B. Hekler, Saul Shiffman, Audrey Boruvka, Daniel Almirall, Ambuj Tewari and Susan A. Murphy. [Microrandomized Trials: An Experimental Design for Developing Just-in-Time Adaptive Interventions](https://dept.stat.lsa.umich.edu/~tewaria/research/klasnja15microrandomized.pdf). Health Psychology 34, Supplement, 1220–1228, 2015. Used as methodological precedent for randomization at decision points, with coding transfer explicitly proposed.

[^3]: Microsoft Experimentation Platform. [Patterns of Trustworthy Experimentation: Pre-Experiment Stage](https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-pre-experiment-stage/). 31 July 2020. Used for component hypotheses, exposure-aware sizing and counterfactual logging.

[^4]: Microsoft Experimentation Platform. [Patterns of Trustworthy Experimentation: Post-Experiment Stage](https://www.microsoft.com/en-us/research/articles/patterns-of-trustworthy-experimentation-post-experiment-stage/). Used for triggered analysis, trigger completeness and population-level interpretation. Accessed 14 September 2026.

[^5]: Joongwon Kim and colleagues. [Scaling Test-Time Compute for Agentic Coding](https://arxiv.org/html/2604.16529v1). arXiv:2604.16529v1, 2026. Used for structured trajectory representations, selection and sequential reuse; no projected ElevenPowers uplift is inferred.

[^6]: OpenAI. [Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/). 8 July 2026. Used for task underspecification, narrow tests and benchmark-validity limitations.

[^7]: SWE-bench project. [CLI reference](https://www.swebench.com/SWE-bench/reference/cli/). Accessed 14 September 2026. Used only for available task-collection/execution tooling.

[^8]: Microsoft. [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects). Updated 14 July 2025. Used for descendant inheritance and kill-on-close semantics.

[^9]: Microsoft. [AssignProcessToJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject). Used for assignment requirements and failure reporting. Accessed 14 September 2026.

[^10]: Python documentation. [ctypes — A foreign function library for Python](https://docs.python.org/3/library/ctypes.html). Used for default native function return and argument conversion, and explicit type declarations. Accessed 14 September 2026.

Local primary evidence: [chunk1.json](E:/ElevenPowers/results/chunks/chunk1.json), [chunk2.json](E:/ElevenPowers/results/chunks/chunk2.json), associated bundles and host transcripts indexed in [evidence.md](E:/ElevenPowers/docs/research/audit_2026_09_14/evidence.md); [Plan v0.7](E:/ElevenPowers/PLAN.md); [journey/25-treatment.md](E:/ElevenPowers/journey/25-treatment.md); [D92–D94](E:/ElevenPowers/journey/decisions.md:128). Source-code claims refer to the inspected working tree, whose pre-existing modifications are recorded in the evidence appendix.
