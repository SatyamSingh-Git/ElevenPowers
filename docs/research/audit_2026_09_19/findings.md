# Findings and proposed replan — 19 September 2026

Audited revision: **4e9b797fc0d53561bd326b27611f2ef2dfd2f45f**. Objective: **maximize actual agentic coding performance, accepting higher cost when it buys better results**.

This is a fresh audit of the current implementation and plan. It does not implement fixes or amend existing project documents. The companion [evidence appendix](evidence.md) contains runnable probes, their outputs, test commands and limitations.

## Assessment

The project has improved substantially at preserving work, exposing historical confounds and correcting its own claims. Those investments are useful. However, the next bottleneck is not a shortage of diagnostics. It is the missing connection between trustworthy observations and a better final candidate.

I found **12 implementation findings**, supported by **14 executable probes**, while the **177 existing tests in the focused suite passed**. Several findings violate the evidence contract itself: skipped or unexecuted tests become passing reproductions; a clarification question creates a supposedly proven checkpoint without evidence; stale discrimination decisions survive changes to the tests being evaluated.

The recommended direction is to repair those contracts, then build and measure one complete improvement path: **an early issue-grounded reproduction, a preserved incumbent, one alternative candidate, and conservative selection using permitted evidence**. Avoid requiring a larger framework of diagnostics before trying that path.

The present PLAN already acknowledges that C0 snapshots at Stop and that C1 detects reproductions retrospectively instead of supplying them before implementation. Those are not newly discovered bugs. Their significance is that the proposed mechanisms for improving generation and rescuing earlier work remain only partly implemented.

Also, the user's historical 92% baseline, 12% firing rate and no-treatment-on-discordants interpretation are no longer the project's current findings. PLAN now withdraws the repair-score interpretation because of answer exposure, distinguishes 8% of runs from 0.12 block events per run, and documents pre-Stop interventions. The next experiment must start from those corrections.

## Scope and confidence

Reviewed current runtime hooks, evidence and ledger logic, discrimination and confirmation, ratchet, assumption checking, architecture/context features, impact analysis, parser additions, redaction, evaluation pooling and design documents. Compared current plans with previous audits and checked primary research behind several new decision rules.

Validation used an isolated Python environment, temporary fixture repositories, real git/pytest where relevant, and isolated hook probes. No paid agent run was launched; no existing run was regraded. This was not the full test suite, a live host delivery test, or a stress test of process containment. Optional tree-sitter integration was not exercised.

**P1** means repair before relying on the affected evidence or behavior in the next experiment. **P2** means a concrete defect worth scheduling, with narrower impact. These are audit priorities, not claims about how often each bug occurred in archived runs.

## Implementation findings

### F1 — P1: Confirmation invents passes for tests that did not pass

Location: [core/stress.py:312](E:/ElevenPowers/core/stress.py:312).

Confirmation selects node IDs, runs them, collects failures and treats the remaining selected IDs as green. Selection is not proof of execution.

Two independent reproductions:

- With fail-fast enabled, the first selected test fails. A later test never executes, as verified by its absent execution marker, yet is emitted as PASS and accepted as the reproduction.
- A selected test explicitly skipped by pytest is emitted as PASS and accepted as the reproduction.

The first probe uses three nodes because the suite summary also inherits the last selected node's identity. That collision excludes one node as failed and obscures the problem in a two-node example. Confirmation additionally returns inferred passing records without preserving the corresponding failures.

**Change:** Obtain explicit node outcomes for runtime-owned verification. Distinguish passed, failed, skipped, deselected, not run, setup error and incomplete capture. Record both positive and negative results. Only an observed completed pass may discharge a named reproduction.

**Acceptance:** Fail-fast, skip, collection errors and partial output cannot create a named PASS. Mixed runs preserve their actual failures. An all-passing complete run still works.

### F2 — P1: A clarification question creates a proven checkpoint with no evidence

Locations: [core/ledger.py:355](E:/ElevenPowers/core/ledger.py:355), [core/hook.py:294](E:/ElevenPowers/core/hook.py:294).

The ledger returns VERIFIED to permit a question to end the turn. The Stop hook interprets that status as permission to snapshot with the note that declared checks passed.

The probe starts with an UNVERIFIED claim and zero evidence. Ending with “Which behavior do you want?” creates a ratchet snapshot.

**Change:** Separate the permission to end a turn from candidate verification. Waiting for clarification, reporting a limitation and submitting a verified candidate are different decisions. Snapshot eligibility must depend on concrete qualifying evidence, not the status used to allow a response.

**Acceptance:** A question can return normally without creating or replacing a good checkpoint. A qualifying check result can create one independently of the phrasing of the final message.

### F3 — P1: Discrimination caches omit mutable inputs

Location: [core/stress.py:147](E:/ElevenPowers/core/stress.py:147), with confirmation at [line 312](E:/ElevenPowers/core/stress.py:312).

A discrimination result is cached by check kind within a task. Although the base commit stays fixed, the tests and fixtures carried onto that base do not.

The probe first caches a non-discriminating test. It then changes the implementation and the test. A fresh control execution on the old tree fails, but the cached result remains non-discriminating.

Confirmation has a related static defect: the existence of a prior CONFIRMED decision suppresses another attempt, and the decision is recorded before validating a usable command result. A failed invocation can therefore consume the attempt.

**Change:** Key discrimination by the base, carried test/fixture content, command and selection, plus the relevant environment. Key forward confirmation by the candidate and those same inputs. Store failed attempts separately from valid observations. Invalidate only what changed, but include every actual dependency.

**Acceptance:** Editing a carried test invalidates its discrimination result; unchanged inputs reuse it. An invocation error does not permanently prevent a valid retry.

### F4 — P1: Unrelated checks can be joined into a reproduction

Location: [core/ledger.py:499](E:/ElevenPowers/core/ledger.py:499).

The suite reproduction fallback accepts any discriminating check together with a fresh passing suite. The synthetic probe supplies discriminating typecheck evidence and a passing test suite. The ledger says the declared check failed on the base and passes now, although those observations describe different checks.

Matching only the word “tests” would still be insufficient if the selections or configurations differ.

**Change:** Join base and candidate observations on an explicit check identity: runner, arguments, test selection, carried test/fixture manifest and environment. Keep unrelated base failures and infrastructure errors separate from a behavioral reproduction.

**Acceptance:** Different check kinds or selections cannot discharge one another. A matching base failure and candidate pass can.

### F5 — P1: Reading a TAP file counts as running a passing suite

Location: [core/parsers.py:219](E:/ElevenPowers/core/parsers.py:219).

Parsing the command “cat fixture.tap” with a valid TAP version header, one passing result and a plan produces a passing suite with ran_tests true. A text file was read; no test ran.

This is a remaining route through the execution-provenance problem already raised in an earlier audit, rather than a claim that the whole category is new. The newer TAP handling still permits the explicit-header path.

**Change:** Separate recognition of a report format from attribution to an execution. Runtime-owned runner output can establish mechanical execution facts; an imported report needs its own provenance and weaker status. Do not solve this with an expanding list of forbidden shell words.

**Acceptance:** Reading or printing a report does not satisfy “the tests ran.” Legitimate TAP runner executions remain supported.

### F6 — P2: Reading a file suppresses the architecture context intended for its first edit

Location: [core/hook.py:150](E:/ElevenPowers/core/hook.py:150).

The pre-edit neighborhood brief is gated on the file being absent from ledger.seen. A normal Read records the file as seen first.

The same fixture emits the architecture note when edited directly and emits nothing after Read → Edit. The ordinary workflow suppresses the feature.

**Change:** Track context delivery separately from file observation, or deliver useful context at the read boundary. Record whether the message was actually delivered.

**Acceptance:** Read → Edit gets the intended context once; repeated edits do not spam it. This also needs a host-level delivery check before claiming an agent saw it.

### F7 — P2: Output capture is incomplete, while absence is interpreted as behavioral evidence

Locations: [core/hook.py:198](E:/ElevenPowers/core/hook.py:198), [core/ledger.py:334](E:/ElevenPowers/core/ledger.py:334), [core/assumptions.py:261](E:/ElevenPowers/core/assumptions.py:261).

Two related probes:

- An ordinary producer command prints a sample, but creates no parser-recognized evidence and writes no file. The hook returns before saving its output. The assumption checker therefore misses observations it was designed to compare.
- A touched test file absent from failed_before is reported as vacuous. Absence from the failure list does not establish a pass on the old tree: the test might have been excluded, skipped or never reached.

The first is a capture defect; the second is an invalid inference from incomplete capture.

**Change:** Capture eligible readable command output independently of semantic evidence extraction. Preserve truncation, eviction and completeness metadata. The current bounded sample store cannot justify claims about everything a task ran. Vacuity requires an observed old-tree pass, not the absence of an old-tree failure.

**Acceptance:** Unrecognized producer output is available within the documented retention policy. Unknown outcomes remain unknown. Fail-fast and skipped tests are never called vacuous solely because they lack a failure record.

### F8 — P1: The offered restore command does not restore the checkpoint tree

Location: [core/ratchet.py:118](E:/ElevenPowers/core/ratchet.py:118).

The printed git restore command restores tracked paths but leaves later untracked files. In a real temporary repository, a newly added failing test survives the recommended command; ratchet.differs remains true afterward.

**Change:** Prefer opening the checkpoint in an isolated worktree for comparison and promotion. If an in-place restore is supported, it needs an explicit manifest, ownership checks for additions, and a current HEAD/worktree precondition at execution time. A guard checked when printing instructions is not a guard on the later operation.

Do not add an unconditional clean command: that could erase unrelated user work.

**Acceptance:** The recovery path produces the checkpoint tree or explicitly reports remaining differences, while preserving unrelated work.

### F9 — P2: The off profile still dispatches new verification work

Location: [core/hook.py:294](E:/ElevenPowers/core/hook.py:294) and the preceding discrimination/confirmation calls.

The off-profile return occurs after new verification and snapshot logic. An isolated probe with the old-tree executor stubbed records a dispatch under the off profile. This proves dispatch, not a complete downstream process run in that probe.

**Change:** Make profile behavior explicit across separate capabilities: record, emit context, execute checks, snapshot and block. Enforce those capabilities before the action. Passive observation should not silently trigger execution.

**Acceptance:** Off performs only its documented actions, including when fresh suite evidence and a declared command are present.

### F10 — P2: An unchanged tracked file is treated as wholly changed

Location: [core/radius.py:113](E:/ElevenPowers/core/radius.py:113).

An empty diff plus an existing file is treated as an untracked new file. The probe supplies an unchanged tracked file: git diff is empty, but changed_lines returns its first line as changed.

This makes reverted edits look like active changes and increases context noise. A git error also needs its own state rather than an empty-diff interpretation.

**Change:** Distinguish tracked-and-unchanged, untracked, deleted and failed-to-inspect. For deleted or renamed symbols, consider the before-tree structure as well as the current one.

**Acceptance:** Unchanged tracked files have no changed lines; new files have their actual lines; inspection failures are reported as unknown.

### F11 — P2: Redaction covers one stored copy but misses evidence details

Locations: [core/ledger.py:334](E:/ElevenPowers/core/ledger.py:334), [core/parsers.py](E:/ElevenPowers/core/parsers.py), [core/evidence.py](E:/ElevenPowers/core/evidence.py).

The probe uses a synthetic credential-shaped string in pytest output. The output sample is redacted, but the duplicate stored in Evidence.detail remains in serialized evidence.

**Change:** Apply a consistent persistence-boundary policy to all stored output-bearing fields, not just the sample buffer. Keep explicit redaction metadata so semantic comparison does not mistake removed content for an observed value.

**Acceptance:** The synthetic value is absent from every persisted representation. This is a concrete missed copy, not a claim that regex redaction can guarantee removal of every possible secret.

### F12 — P2: The ALL POOLED summary silently loses earlier attempts

Location: [eval/pool.py:104](E:/ElevenPowers/eval/pool.py:104).

The pooled path builds a dictionary keyed by task, overwriting attempts from an earlier sweep when the same task occurs again.

The synthetic example has one successful and one unsuccessful attempt in different sweeps. ALL POOLED reports one attempt and zero coverage. The actual union has two attempts, full task coverage and a 50% random-pick success rate.

The existing warning against quoting the pooled figure limits its intended use, but does not make a misleading diagnostic safe for reconciliation.

**Change:** Concatenate attempts within explicitly compatible conditions, or refuse to pool incompatible ones. Preserve sweep and effective configuration identity. A directory name alone is not sufficient experimental provenance.

**Acceptance:** Repeated tasks retain every eligible attempt, and the aggregate reconciles with its constituents.

## Changes needed in reasoning and experimental design

### R1 — Remove the universal four-point selector cutoff

[eval/pool.py:66](E:/ElevenPowers/eval/pool.py:66) defines HARM_LINE = 4.0; PLAN uses a gap under four points as a reason to cancel selection work.

The cited fixed-pool study reports particular selectors harming performance when recoverable gains were small. It does not establish a universal threshold for coding tasks, other selectors or conservative fallback policies. Its GPQA case with a roughly three-point recoverable gap is a result for that setup. [Primary study](https://arxiv.org/html/2607.17531v1).

A selector's expected gain is the probability mass it rescues minus the probability mass it damages. A two-point opportunity with negligible harm can still be valuable, especially under this user's objective. A large opportunity can still be wasted by a poor selector.

**Replan:** Estimate attainable gain, selection regret, harm to the incumbent and uncertainty on local candidate pools. Use the same allowed compute to compare ordinary independent attempts, generation changes and selection. Deprioritize an expensive weak selector on evidence; do not reject the entire mechanism at a literature-derived constant.

Also, different generated patches receiving different verdicts are not evidence of flaky tests. To estimate test flakiness, rerun the same patch in the same grading conditions.

### R2 — Correct the B6 design before reviving it

[results/b6-paired/design.md](E:/ElevenPowers/results/b6-paired/design.md) is marked aborted, with zero runs; do not simply resume it.

Its mandatory-replication and “31 discordants” reasoning is stronger than the statistics justify. One randomized attempt per arm per task can estimate an average treatment effect. Stochasticity increases uncertainty; it does not make the design meaningless. Replication is useful when estimating within-task variability or candidate pools, but competes with covering more independent tasks.

Thirty-one disagreements came from power assumptions for one alternative, not a universal significance requirement. At a fixed analysis, six independent discordant task pairs all favoring one arm give a two-sided exact p = 0.03125. This does not justify collecting data until a convenient p-value appears.

PLAN's corrections already acknowledge this point, but the newer B6 document reintroduces the stronger claim.

**Replan:** State the estimand first. Simulate power across plausible exposure, harm, rescue and task-correlation values. Choose replication for the question being asked. Analyze repeated observations at the task level or with a method accounting for task clustering; do not treat them as independent tasks.

### R3 — Fix the pooled B4 upper bound and qualify its population

[results/b4-discriminate/findings.md:24](E:/ElevenPowers/results/b4-discriminate/findings.md:24) reports an upper bound of roughly 13% for 1 event in 22 observations.

Under an independent identical-binomial model, the exact one-sided 95% upper bound is approximately **19.8%**, and the upper endpoint of the two-sided 95% interval is approximately **22.8%**. The rule of three is a zero-event approximation; it cannot justify 13% for one event.

Pooling repeated tasks across different model configurations also violates a simple identical independent trial interpretation. These calculations correct the arithmetic, not the pooling assumptions.

**Replan:** Report raw counts by configuration, distinguish per-run from per-task estimands, and use task-aware uncertainty for pooled conclusions. Retain the current warning about broadly failing base trees making vacuity difficult to observe.

### R4 — Benchmark validity bias is not a universal minimum detectable effect

PLAN treats published absolute benchmark inflation as a floor below which no treatment delta can be claimed. This mixes absolute label bias, differential bias between arms and sampling uncertainty.

The cited empirical study establishes that benchmark-plausible patches can be incorrect and reports aggregate score inflation. It does not establish a universal six-point noise floor for paired comparisons. Version 2 reports 6.4 points; if retaining a different version's number, pin that version explicitly. [Primary study](https://arxiv.org/html/2503.15223v2).

Equal bias could partly cancel between arms; differential bias could reverse even a large apparent improvement.

**Replan:** Report benchmark-pass effects as such. Audit discordant candidates using permitted developer checks and blind review where feasible, and report sensitivity to uncertain grades. Do not turn a population-specific validity estimate into either permission to trust large deltas or a prohibition on measuring small ones.

### R5 — Reproduction synthesis remains a promising hypothesis, with missing controls

ORACLE-SWE is evidence that supplying useful reproduction information can improve a repair process. It is not a universal effect size for this hook. Its generated-test setup includes a stronger first-stage agent and a staged 50/70-step allocation against a 120-step baseline, while separate oracle conditions use hidden benchmark information deliberately. These conditions must not be conflated. [Primary study](https://arxiv.org/html/2604.07789v1).

**Replan:** Keep hidden tests and gold patches entirely outside workers. Compare an early issue-grounded reproduction against a strong worker receiving equivalent total compute, and against ordinary extra attempts. Measure whether the early artifact is correct, delivered, used and beneficial.

A patch-blind worker provides procedural separation, not guaranteed semantic independence: it may share the same misconception. Passing a stronger wrong test is still wrong. An additive suggestion can also harm by anchoring the worker, even if it never blocks.

### R6 — Test delivery locally instead of adopting a blanket push/pull rule

The intervention-paradox paper supports caution: a critic can predict failure accurately yet make the acting agent worse. Its evaluations are on non-coding environments and effects vary across models. It does not prove that every timely factual coding note should be query-only. [Primary study](https://arxiv.org/html/2602.03338v1).

**Replan:** Compare a small amount of timely, factual context against pull-only access. Measure delivery and use, not merely whether a query exists. F6 shows why this distinction matters. Avoid flooding the prompt with every diagnostic.

## Recommended architecture: one reliable observation model, one improvement path

### 1. Separate executions, observations, candidates and decisions

The current bugs often arise when one representation is asked to mean several things.

An execution record should identify the command, working directory, input snapshot, test/fixture manifest, relevant environment and tool versions, start/end status, exit reason, selection, observed outcomes and capture completeness. Redaction and truncation are part of that record.

An observation says what that execution established, at a stated granularity. A candidate identifies an immutable patch against a recorded base. A decision says whether to wait, run another check, repair, explore another interpretation, select or submit.

Do not encode all four in a broad VERIFIED status. Mechanical evidence may establish that checks passed for a candidate; it does not establish that the checks represent the intended behavior.

Start with one structured adapter for runtime-owned pytest execution. Reuse existing runner report formats where possible. Do not build a universal telemetry platform before validating this design.

### 2. Preserve useful candidates when evidence arrives

C0 currently snapshots at Stop, as the plan openly states. That cannot rescue a good intermediate tree that was broken before Stop.

Snapshot a candidate when qualifying check evidence becomes available, bound to the exact tree. This does not require running the suite after every edit. Keep a good incumbent and a limited number of materially different alternatives. Reuse existing execution results; rerun only invalidated checks.

Recovery should open or compare that candidate safely, then validate promotion. F2 and F8 must be repaired before trusting this path.

### 3. Build an early reproduction and two-candidate experiment

A narrow complete implementation is more informative than many disconnected feature flags:

1. Freeze the task's permitted context and environment.
2. Before patching, produce an issue-grounded failure contract: a runnable reproduction when justified, with the source for the expected behavior and any unresolved premise.
3. Give that artifact to the coding worker and preserve its candidate.
4. Spend additional compute on one genuinely different candidate or a counterexample-driven repair.
5. Run the same permitted checks against both; keep a defensible incumbent when selection evidence is inconclusive.
6. Grade the selected final patch offline, with the worker unable to access grading secrets.

The comparison must include a strong baseline using the same aggregate compute, including all reproduction generation, retries, judging and verification. If ordinary extra attempts outperform the scaffold, use them. The goal is performance, not architectural novelty.

### 4. Search for disagreements that reveal missing requirements

A useful extension is to compare plausible candidates that pass the same checks and search for an input on which their behavior differs.

That disagreement identifies a question worth investigating. It does not identify the correct answer. Resolve the expected behavior through the issue, existing contracts, examples or a targeted user clarification when available. Do not treat majority voting or similarity to a candidate as ground truth.

Likewise, record only the few diagnosis premises that could change the implementation: actual producer shape, ordering, alias resolution or a compatibility requirement. Attach an observation or mark them unresolved. This is a focused tool for finding a mistaken premise, not another generic checklist.

### 5. Keep heuristic context honest

Architecture and impact features are useful when they provide accurate, concise context. Name matching, inferred imports and current-tree analysis cannot establish exhaustive semantic reachability or test coverage.

Fix delivery first. Then add explicit uncertainty, content-based caching and before/after analysis where necessary. Validate optional grammar coverage before making cross-language claims. Optimize context volume against measured usefulness, not the number of edges extracted.

### 6. Finish the worker/judge boundary before another efficacy claim

The current project already documents registry and local installed-package exposure. This audit did not discover those again or run a new containment attack.

Tool denial lists and package-manager environment variables are not an operating-system or network boundary for an arbitrary shell. Historical observations of reduced detected exposure do not prove all alternate paths closed.

For closed-book evaluation, isolate worker filesystem and egress, prepare pinned dependencies, and keep grading assets outside worker reach. Preserve the effective task, instruction revision, environment, candidate patches and intervention history. Keep grader versions and regrade history rather than overwriting the only verdict.

Production agents can have authorized documentation access; that is a different declared access policy. Store versioned project configuration separately from private task state so useful project settings can be reproduced without committing runtime artifacts.

## A practical sequence from here

| Stage | Work | Exit condition |
|---|---|---|
| 1. Restore evidence integrity | F1–F5 and F7; review historical results that used affected paths | Selected, executed and passed are distinct; cached and joined observations match their inputs |
| 2. Make recovery and delivery reliable | F2, F6, F8–F11 | Good candidates survive; restore is faithful; context reaches the worker; profiles behave as declared |
| 3. Repair experiment inputs | F12, R1–R4, worker/judge boundary and effective configuration provenance | Reconciled candidate pools, declared access conditions and a predeclared estimand |
| 4. Run one complete local pilot | Early reproduction → candidate → alternative → conservative selection | A measurable path from delivered information to a changed final candidate |
| 5. Compare end-to-end | Strong compute-matched baseline, independent held-out tasks, task-aware analysis | Report improvement and harm with uncertainty, including negative or inconclusive results |

Stages are dependencies, not a request for a broad rewrite. The highest-priority subset is the evidence contract used by the selected pilot. Avoid spending another cycle perfecting features that the pilot will not exercise.

Maintain two evaluation populations:

- A development set enriched for the mechanism's opportunity, selected using independent historical runs or baseline-only screening. It answers whether the mechanism can help when applicable.
- A frozen held-out deployment-like set. It estimates overall benefit and cost. Do not report the enriched set's uplift as the deployment effect.

Randomize after any eligibility decision used for a conditional causal experiment. Conditioning afterward on whether the treatment fired can introduce selection bias.

Track four separate rates: the relevant condition exists; the runtime detects it; the worker receives and uses the intervention; the selected patch improves. A rare block is only one possible exposure metric. An early reproduction, candidate switch or architecture note can be an intervention without a Stop refusal.

Predeclare the primary endpoint, analysis unit, budget and stopping rule. Use shadow exposure measurement to inform power assumptions, with task clustering and harm included. Do not launch a fixed expensive sweep just because the task count looks respectable.

## What I would change in the plan immediately

1. Replace universal research-derived cutoffs with local hypotheses and decision criteria.
2. Put execution completeness and check identity ahead of additional evidence features.
3. Promote the first working generation-and-selection path above further report-only expansion.
4. Make the strongest compute-matched baseline the competitor, not just a weak single attempt.
5. Require intervention delivery and candidate lineage in efficacy reports.
6. Retain the historical corrections, and reconcile newer design documents with them.
7. Keep “done” as a policy decision with explicit remaining uncertainty; reserve mechanical claims for the evidence actually observed.

No new improvement percentage is established by this audit. Its result is a set of reproduced defects, corrected experimental assumptions and a concrete route to measuring whether the next system produces better code.

