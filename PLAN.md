# Master Plan v0.7

2026-09-11. Supersedes v0.6. Written after an external audit reproduced sixteen defects in the runtime and the evaluator, and argued that the project has been optimising the wrong objective. Both halves of that are accepted. Earlier plans are in git history; `docs/research/` and `journey/` are unchanged and still govern.

**This is a larger change than any previous revision.** v0.4 restored the mission, v0.5 and v0.6 adjusted the thesis. v0.7 changes what the system is for.

---

## 0. Why v0.6 needed replacing

| What v0.6 assumed | What the audit established | v0.7 |
|---|---|---|
| The project is a verification layer that decides when work is done | Better stopping cannot explore a diagnosis the worker never considered. The brief was to make coding agents dramatically more capable | The system owns an **outer loop**: generate candidates, select among them, decide what to try next. Verification is one component (§1) |
| Architecture is justified only by gaps in the fourteen surveyed systems | That is a novelty filter. A mature, widely implemented capability can be the largest missing contributor | Work is ranked by the failure it addresses, not by whether anyone else built it (§1.2) |
| The twelve-bug null was a fair test of the gate | **The grader never ran a preservation set.** A patch that breaks existing tests scores as resolved. The gate's main mechanism is catching regressions, and the measurement was blind to them | Every reproduced defect is P0 and blocks new performance claims (§4) |
| Milestones exit in order | M2 needed a suite assigned to M5; M2.5 sat behind an unresolved M2 | Three tracks with explicit prerequisites, not a chain (§7) |
| Local absence of Docker bounds the work | An environment limitation was allowed to define the scientific scope | Provision an isolated Linux worker for external benchmarks (§7, Phase A) |

Sixteen probes reproduce against the current implementation; `docs/research/audit_2026_09_11/reproduce.py` runs them. The one that matters most was independently re-confirmed on a real mined instance: maintainer's fix applied, an unrelated existing test broken, suite red, **grader still reports resolved**.

---

## 1. What this is, restated

Not a plugin that says no. **Given a task, permitted repository context and a compute envelope, produce the strongest patch the system can find, with the evidence for it.**

The completion state is one output of that system rather than its organising purpose. Existing hosts keep the inner tool-use loop; this owns the decisions around it: restart an unproductive attempt, allocate another model, preserve alternative patches, choose a winner, continue from a better diagnosis.

**1.1 What survives from the old framing.** Automatic collection from ordinary work, automatic execution of declared checks, evidence bound to state, explicit provenance, honest unresolved outcomes, and a recorded history of failed hypotheses. These are good foundations for a search system and were always the valuable part.

**1.2 What stops governing investment.** The residual-gap census ranks by novelty. Work is now ranked by the failure it addresses: environment setup, localisation, requirement interpretation, implementation, cross-file integration, candidate selection, context loss. The matrix stays useful for choosing an implementation to borrow once a bottleneck is identified.

**1.3 Composition is a hypothesis, not a purpose.** "The stack beats its best part" is worth measuring and is not a reason the product must exist. If a small controller around one strong worker wins, that is a success.

---

## 2. The thesis, demoted and kept

> Completion should be computed from dependency-tracked evidence, not asserted by the model — and no expectation may be treated as a requirement on the strength of the agent's own say-so.

Still true, and no longer the point of the project. The audit's formulation is better:

> **The evidence layer can be valuable inside a stronger search-and-selection system without being an independent semantic oracle.**

Twelve real bugs said the gate changes nothing on its own. The most promising distinctive investment is an evidence store that makes **alternative solutions comparable and failed attempts reusable**. Today the ledger explains why one attempt stopped. Making it support choosing what to try next is the larger opportunity, and it keeps the part of the original idea worth keeping.

---

## 3. Where we actually are

**Working, and still useful.** Evidence capture from ordinary tool output; provenance and staleness; self-discharge of declared commands; profiles and config; `ep-status`; a scope guard; a repeat runner with derived run counts; a miner that builds real tasks from upstream history without Docker; a live harness driving the real CLI.

**Not trustworthy until §4 is done.** Every number this project has published rests on an evaluator that does not check preservation, an analysis that discards replicates, and an evidence layer with nine reproduced soundness defects.

**Never built.** Candidate pools, selection, diagnosis branching, localisation, run bundles, an isolated benchmark environment.

---

## 4. P0: the defects that make measurement untrustworthy

All reproduced by `docs/research/audit_2026_09_11/reproduce.py`. **P0 here means a prerequisite for trusting a research conclusion, not a production emergency**: the tool is usable, and its numbers are not yet evidence. None may be deferred, and no new performance claim is made until each is fixed and covered by a regression test derived from the probe that found it.

Each lives in `tests/test_audit_probes.py` as a test asserting the behaviour the system is supposed to have, marked `xfail(strict=True)` until it holds. The marker comes off when the fix lands, and cannot be put back quietly: a fixed defect that regresses turns the test red. **Status below is that file, not this table** — `python -m pytest tests/test_audit_probes.py -q` is the authority, and a row saying `fixed` with an `xfail` still on it is a documentation bug.

### Evaluator

| | Defect | Consequence | Status |
|---|---|---|---|
| E1 | The grader runs only `f2p`; there is no preservation set | A patch that breaks existing tests scores as resolved. **The gate's main mechanism is regression-catching and the measurement could not see it** | fixed |
| E2 | `eval/analyse.py` keeps one row per task and arm | `--runs N` is incompatible with the analysis. Replicates, uncertainty and cost vanish | fixed |
| E3 | The workspace is deleted; `Run` holds no diff, log or trajectory | Freezing twelve candidate patches is impossible because they no longer exist | open |
| E4 | Model alias, inherited environment, silent plugin omission, fixed arm order | An arm can be labelled present and be absent | open |
| E5 | Grading happens inside the candidate's mutable workspace | Separation in time is not isolation of authority | open |
| E6 | Task selection keyed to the gate's own detection mechanism; flip-rate bound is invalid | Selecting the benchmark around the intervention being tested. A baseline can fail deterministically while a treatment succeeds deterministically, giving zero baseline flips and complete between-arm disagreement | open |

### Evidence layer

| | Defect | Consequence | Status |
|---|---|---|---|
| R1 | Size and mtime, with `vcs_state` as tie-breaker | Two different contents of an already-modified file share a porcelain status; evidence survives a real change | fixed |
| R2 | `observed` is a stored list; additions escape it | A new failing test file does not stale anything. Environment and dependency changes are not fingerprinted at all | part |
| R3 | Only `STALE` is rejected | Deleting an observed file yields `GONE` and still verifies | open |
| R4 | Older passes satisfy; first failure excused as pre-existing | fail → pass → fail returns VERIFIED | open |
| R5 | Substring match plus exit code | `echo pytest` is a passing suite with zero tests | open |
| R6 | `_test_written_and_suite_green` searches `touched ∪ seen` | **Reading** an existing test counts as writing one. Added in M1 to cut false blocks, and cut them partly by being wrong | open |
| R7 | `on_prompt` reuses the task id | A new request inherits the previous task's evidence, read set and `guided` flag; concurrent writers lose updates | open |
| R8 | `observe_edit` returns early when a claim exists | An edit under `src/auth/` leaves risk low | open |
| R9 | Stability accepts any `Kind.STABILITY` record | Clean repeats of an unrelated command certify a flaky test; the cap overstates confidence | open |

### Host contract

| | Defect | Consequence | Status |
|---|---|---|---|
| H1 | `read_result` looks only under nested keys; documented failure hooks use top-level `error` | A documented failure shape yields `readable=False` and no evidence. **This narrows the 174/174 claim**: replay fidelity is not delivery fidelity | open |
| H2 | 20-second hook timeout against 300-second verification | A timed-out hook loses its output and makes no decision. **Long verification must run outside the short-lived callback**, with snapshot-bound job state and a controlled resume path | open |
| H3 | `additionalContext` on Stop continues the conversation | Report-only branches emit it | open |
| H4 | Bash-only subscription | PowerShell commands are invisible | open |

**R1, closed 2026-09-12.** `vcs_state` is a content fingerprint rather than a status listing: the porcelain output names which files differ from HEAD and not how, so two edits of one already-modified file shared a line and evidence recorded against the first survived the second. It now folds in `git diff HEAD` for tracked content and reads untracked files directly, because a test file written a minute ago is untracked and is exactly what changes next.

**R2, part closed 2026-09-12.** A record produced by scanning the tree now says so, and freshness re-derives the file set instead of consulting a stored list that cannot grow — a file that did not exist when the suite ran could never have appeared in it, so a new failing test staled nothing. Dependency manifests and lock files joined the observed set, since a dependency upgrade changes behaviour exactly as an edit does. **Still open:** a package installed without touching a manifest is invisible, and there is no fingerprint of the interpreter or the environment the command actually ran in. Marked `part` rather than `fixed` because the row claims more than the fix delivers.

**E2, closed 2026-09-12.** `load` keeps every replicate. The rates are then over runs and the paired test over tasks, because runs of one task are not independent and pairing replicate against replicate would multiply the apparent sample size while the correlation stayed — buying significance by claiming independence that was never there. At one replicate each the test is exactly McNemar again. `eval/noise.py::outcomes` refuses a file holding replicates instead of silently reading its last run, since that mode's question is what two separate passes did.

**E1, closed 2026-09-12.** `eval/mine.py` now records a pass-to-preserve set — everything green with the fix commit's tests in place both before and after the source change — and rejects a commit that yields none, because a task that cannot show a regression cannot grade a fix. `eval/live.py` grades on membership in the passing set of a whole-suite run rather than on the exit code of a handful of node ids, which also answers *were the required tests collected at all*. Before running it, the test tree is restored from the upstream repository: without that the preservation set asks the agent to mark its own work a second time, since an agent that edits an existing test until it agrees with its patch would be recorded as having preserved it. `Graded` reports `resolved`, `unfixed`, `regressed`, `timeout` or `setup` separately, because a regression and a patch that never worked were previously the same zero.

---

## 5. The architecture to build toward

```
task + permitted context
   → reproducible base environment
   → localise code, enumerate plausible diagnoses
   → isolated candidate attempts          ←────────────┐
   → immutable candidate snapshots                     │
   → visible checks + grounded behavioural probes      │
   → candidate comparison and selection                │
   → worth more work?  ──── new diagnosis or repair ───┘
   → selected patch + evidence report
   → independent held-out evaluator
```

The held-out evaluator's answers are unavailable to the worker, the selector and the within-task repair policy.

**5.1 Measure the generation ceiling before building a better examiner.** For a frozen pool of N candidates: *pool coverage* is the fraction of tasks where at least one candidate is correct; *selected success* is the fraction where the chosen one is correct; the difference is **selection regret**. If every candidate is wrong, no reranking helps and the investment belongs in localisation, models or diagnosis diversity. Pilot at N = 1, 4, 8.

**5.2 Branch at diagnosis, not only at patch generation.** Workers given the same interpretation reproduce the same mistake. Branch where the interpretation is chosen. Share verified repository facts; keep speculative diagnoses separate until comparison. Measure diversity by failure overlap and solutions found, not by role names.

A **missing-code search** after a candidate edit — sibling implementations of the changed interface, callers with other argument types, exception paths, resource-ownership transitions, parsers that must agree — targets exactly the failure that beat `click-762c97ee`, which fixed `Choice` and never generalised to `DateTime`.

**5.3 Context is a constructed working set.** The old plan excluded finding code because the field is crowded. That optimises novelty rather than task success, and the restriction is removed. Compact worker state carries contract, diagnosis, located symbols, observed failures, rejected approaches, active candidate, open questions and evidence references, with code and logs retrievable. Summaries must distinguish observation from hypothesis so a guess is not promoted during compaction. No giant always-loaded overview: the revised AGENTS.md study finds context files generally do not improve success while increasing cost.

**5.4 Select on summaries, then inspect primary evidence.** There is direct support for trying this: structured rollout summaries with tournament voting and parallel-distill-refine are reported to move SWE-Bench Verified from 70.9 to 77.6 percent and Terminal-Bench v2.0 from 46.9 to 59.1. That used substantial extra inference on specific older model and harness combinations, so it justifies the experiment and not an expected uplift. Bounded candidate summaries with diagnosis, snapshot, changes, compatibility assumptions, checks actually run, and provenance of every expectation. Randomise presentation order and measure rejection of correct candidates, not judge agreement.

**5.5 Generated checks are uncertain until grounded.** Freezing a wrong assertion before seeing a patch does not make it right. Distinguish mandatory checks backed by authorised requirements from speculative ones. Adding checks raises the chance a correct candidate is falsely rejected, so measure **correct-candidate survival through each filter** and keep rejected candidates. A speculative disagreement should start an investigation or lower a score, not eliminate every candidate that disagrees.

Build the **candidate-by-probe outcome matrix**: inputs down one axis, candidates across the other. Where plausible candidates disagree, retrieve the contract or nearby code that explains why. The matrix chooses the next investigation. Voting across candidates is not an authority on intended behaviour.

**5.6 Keep an incumbent, allow nonmonotonic search.** A long attempt ends at its latest patch, not its best. Candidates are immutable; a failed repair must not destroy an earlier one. After integration, snapshot again and rerun checks: evidence from two passing branches does not transfer to their merge.

**5.7 Route for complementary capability.** The question is not which model is cheaper but whether different configurations solve different tasks. Measure overlap between strong pinned configurations before assuming scaffolding helps. Model-mixing experiments show complementary benefit in some combinations and none in others, and multi-agent benefit depends strongly on task structure, so a committee is not assumed to help every sequential task.

**5.8 Learn from decisions, not from successful transcripts.** Per-task working memory and attempt histories first. Replay validates parsers and retrieval; it cannot establish the causal benefit of an action never executed. Prompt and procedure optimisation from execution feedback is worth testing once that data exists, at Phase E, keeping training, development selection and final evaluation separate.

---

## 6. Measurement discipline

Retained from v0.4–v0.6: every metric names its population; prefer ground truth the author did not write; measure the noise floor before comparing; state the achievable ceiling before the p-value; hold a set back; silence must leave a trace; know whether a metric is per-run or per-discordant-pair; audit whether each failure was reachable from permitted context; quote a result with the number that qualifies it.

Added by this audit:

- **Report pool coverage, selected success and selection regret together.** A single resolved-rate hides whether the problem is generation or selection.
- **Track correct-candidate survival through every filter.** A gate that raises precision by discarding correct work is not an improvement.
- **Separate pilots from confirmatory comparisons.** Small mechanistic pilots discover whether an intervention does anything; a preregistered comparison supports a performance claim. Report effect sizes and intervals rather than applying a universal significance gate to every iteration.
- **Do not rebuild the main test set until the preferred mechanism wins.** Keep a versioned portfolio: an external benchmark track, a frozen private development corpus, and a final holdout untouched by tuning. Publish task accounting and exclusion reasons for each.
- **Version the external benchmark itself.** A July 2026 vendor audit reports substantial task and test defects in SWE-bench Pro public and withdraws an earlier recommendation, which contradicts this project's own reading list where that set was made the primary external source. Pin a release, inspect it, record why. A benchmark's defects are a reason to version it, not a licence to discard inconvenient results.
- **Account for all compute**: inference, judge calls, external test time, infrastructure.
- **Recompute the required n per comparison.** The 252-run figure alternated between agent runs and paired runs and is not a constant.
- **Keep easy tasks in the held-out set.** They cannot show an improvement and they are the only way to catch a regression. The instinct to drop no-headroom tasks optimises for detecting gains and blinds the measurement to harm.
- **One failure is not proof a task is impossible.** Nor are a few identical failures, which may share one cause.
- **A false block must be graded at the block.** "The other arm solved this task" is a different statement. To measure a block on already-correct work, freeze the patch at the moment of the block and grade it independently; the P2 figure of 12 percent used the weaker proxy and is qualified accordingly.
- **Measure effective loaded instructions, not installed components.** Counting skills or plugins describes an install; only what actually reaches the model describes a treatment.

---

## 7. Execution: five phases, three tracks

**How this plan is followed.** Take the next unmet exit criterion. Within a
phase, take the cheapest experiment that could falsify the thing being claimed.
That rule is carried forward from v0.4, where it kept three failed attempts at
M1 pointed at the same target instead of drifting to something more interesting
after the first one did not work.

**The smallest useful slice, always.** v0.3 replaced a three-week harness with a
seven-day vertical slice and that was the correction that made the project real.
v0.7 is a larger design than v0.2, which was rejected for being a laboratory, and
the difference has to be enforced rather than asserted: **every phase ships
something runnable before it ships something complete.** Phase A's first slice is
the sixteen audit probes promoted from a script to `tests/test_audit_probes.py`,
which takes an afternoon and makes every later repair verifiable.

**The shipped tool keeps working meanwhile.** The plugin installs, captures
evidence, discharges declared commands and reports. Phase A changes what its
numbers are worth, not whether it runs. `README.md` says plainly that published
figures are provisional until §4 is closed.

**Compute envelopes, because this direction is not cheap.** Measured rates: a
mined bug costs about $0.25 on the small model and roughly twice that on the
larger one; a synthetic task about $0.06. No experiment starts without a stated
envelope and a stop condition.

| Phase | Envelope | Stop condition |
|---|---|---|
| A | under $5 — almost all repair, tests and fixtures | probes green, instrument validated |
| B | $20–40 — a pinned baseline over several repositories | a reproducible score with an interval |
| C | $40–80 — pools at N = 1, 4, 8 over the development corpus | coverage, selected success and regret reported |
| D | $80+, decided by C's curve | a preregistered held-out comparison |
| E | not budgeted until D returns something | — |

If a phase exceeds its envelope without reaching its stop condition, that is a
result about the design, not a reason to spend more.

Tracks run in parallel where prerequisites allow: **evaluation infrastructure**, **candidate generation**, **candidate assessment**. Oracle diagnostics can proceed on frozen candidates while the harness is being made reproducible.

### Phase A — Make conclusions reconstructible *(blocking)*

Fix E1–E6, R1–R9, H1–H4, each with a regression test derived from the audit's probe. Add run bundles: task manifest, base identity, candidate diff and snapshot, host events, prompts and model configuration, trajectory, test node outcomes, limits, result. Grade in an evaluator-owned workspace from an exported patch. Keep raw host-event fixtures separate from transcript fixtures. Provision an isolated Linux worker.

**Exit, as commands:**

- `python -m pytest tests/test_audit_probes.py -q` → **zero xfailed**; every reproduced defect keeps the test that found it, now passing
- `python -m eval.validate` → gold patch resolves; a known regression fails; a wrong patch fails; a setup failure is reported as setup failure, not as an unresolved task
- `python -m eval.live --runs 2 && python -m eval.analyse` → two rows retained per task and arm, not one
- `python plugin/bin/ep_doctor.py --host` → success, failure and stop paths observed against a pinned host

### Phase B — Establish the strongest useful baseline

A current strong native host configuration against a minimal worker harness, pinned models and environments, several repositories and difficulty categories. Both a matched-compute comparison and a maximum-budget curve; cost is secondary here, so the curve is the product direction and the matched comparison explains where gains came from.

Measure what actually reaches the model rather than what is installed.

**Exit, as commands:** `python -m eval.baseline --pinned` reports a score with an interval that a rerun reproduces, and `python -m eval.failures` prints a taxonomy where every category cites saved trajectories. Enough repeats to separate setup problems from coding failures.

### Phase C — Separate generation from selection

Candidate pools at several budgets, graded offline. Evaluate selectors without exposing hidden outcomes: patch text, structured summaries plus evidence, and the existing gate. Run the A/B/C oracle diagnostics — frozen issue-derived checks, differential comparison against the original program, interpretation probes — independently on frozen candidates.

**Exit, as a command:** `python -m eval.pool --n 1,4,8` reports pool coverage, selected success, selection regret, correct-candidate survival, regression rate and total compute together, on development and on untouched tasks.

### Phase D — Spend compute where it creates new solutions

Diagnosis branching, missing-code search, complementary worker configurations, fresh-context repair from evidence-linked summaries. Each compared against ordinary extra independent attempts at matched budget.

**Exit:** a selected-patch gain survives a preregistered held-out comparison and is not explained by scoring defects or excluded tasks.

### Phase E — Learn the allocation policy

Routing, prompts and reusable procedures on training and development tasks. Cross-project memory only if evidence-backed and separately evaluated.

**Exit:** improvement transfers to unseen tasks or repositories. Replay-only improvements do not count.

---

## 8. The experiment queue

| Experiment | Comparison | Decision it answers |
|---|---|---|
| Instrument validation | gold patch, known regression, wrong patch, setup failure | can the evaluator tell these apart? |
| Strong baseline | native host vs minimal harness, pinned | are we starting from a competitive worker? |
| Candidate scaling | N = 1 / 4 / 8, selected vs pool coverage | is more generation buying alternatives? |
| Selection ablation | patch text vs summaries plus evidence | does representation improve the choice? |
| Diagnosis diversity | retries vs different grounded diagnoses | do workers escape shared mistakes? |
| Localisation expansion | normal context vs targeted caller/sibling search | are failures caused by missing code? |
| Repair vs restart | continue transcript vs fresh worker with prior facts | does reuse preserve learning without fixation? |
| Check survival | required checks vs added generated checks | do new checks remove wrong candidates without removing right ones? |
| Complementarity | repeated strongest worker vs heterogeneous pool | does configuration diversity add solutions? |
| Gate contribution | same pipeline: capture-only, auto-check, blocking | what does blocking add once search exists? |

The 1.4× gate result stands for its narrow configuration. It is not an argument against spending more compute through a mechanism that demonstrably creates or selects more correct patches.

---

## 9. Hypotheses

| ID | Hypothesis | Status |
|---|---|---|
| P1 | Evidence gating halves the submit-resolve gap | **no effect measured** on twelve mined bugs, on a grader now known not to check preservation. Re-run after Phase A |
| P2 | The gate does not block already-correct work | holds at 12 percent of runs, on the same qualified grader |
| P3 | Claim inference engages when there is work | 21 percent over-claim, 25 percent missed, over 3,557 real turns |
| P13 | The runtime reads what the host sends | **qualified by H1**: replay fidelity is not delivery fidelity |
| P17a/b/c | Frozen issue-derived checks / differential comparison / interpretation probes discriminate | not started; Phase C |
| P19 | Pool coverage exceeds selected success by a margin worth attacking | **new, and the most informative thing to measure first**; Phase C |
| P20 | Diagnosis branching finds solutions repeated attempts do not | new; Phase D |
| P21 | Localisation expansion resolves tasks that fail from missing code | new; Phase D |
| P4–P12, P14–P16, P18 | carried forward unchanged | see v0.6 in git history |

---

## 10. Claims withdrawn or qualified

- **"Evidence is bound to exact file contents."** False of the implementation: size and mtime with a `vcs_state` tie-breaker.
- **"The instrument is honest."** Parser fidelity, host delivery, freshness, evaluator validity and statistical analysis are five separate things; none proves the others.
- **"174 of 174 failures read correctly."** True of replay. H1 shows a documented live failure shape produces no evidence at all.
- **"The first failing observation was pre-existing."** Not a baseline unless measured before the change.
- **"No more failures means no new failures."** Failure identity and execution conditions matter; equal counts can hide different failures.
- **"Real commits remove the population problem."** They improve authenticity. Sampling bias, underspecification and grader defects remain.
- **"A useful task requires the naive fix to break the visible suite."** That defines a diagnostic subset for one mechanism, not coding correctness, and selecting the benchmark that way favours the intervention.
- **"If the evidence layer cannot decide done, the project has failed."** Withdrawn. It can be valuable inside a search system without being a semantic oracle.

---

## 11. Retain, defer, stop

**Retain:** automatic collection from ordinary work; automatic execution of declared checks; provenance of expectations; five honest outcomes rather than block-or-pass; independent oracle diagnostics; the recorded history of failed hypotheses.

**Defer:** a second host adapter, a large always-on framework stack, cross-project memory, a custom tree-search framework, elaborate risk routing, precise static test-impact optimisation. Correct invalidation is *not* deferred — it is P0.

**Stop:** ranking work by novelty; treating the stop gate as the organising purpose; publishing a number without the qualification that bounds it.

---

## 12. What would falsify this direction

- **Pool coverage barely exceeds selected success.** Then selection is not the bottleneck and the search framing buys little.
- **Candidate scaling flattens immediately.** More attempts produce the same wrong answer, and the investment belongs in generation quality or localisation.
- **Every oracle diagnostic accepts candidate and maintainer fix equally.** Then the assessment track cannot discriminate, and the honest product is capture and reporting.
- **The strong baseline is already at the ceiling of the chosen corpus.** Then the corpus is exhausted, not the idea, and the portfolio needs harder tracks.

---

## Appendix: evidence trail

`docs/research/` holds the source study of fourteen systems at recorded commits, the host cards, the complementarity matrix, the licence register, the reading list (refreshed 2026-09-11 with eight sources from the audit, each carrying the limit on what may be inferred from it, and one explicit contradiction of an earlier entry), the oracle-problem card, and `audit_2026_09_11/` with its reproduction script and evidence appendix. `journey/` holds fifteen phases of what was tried, what was wrong, and what the measurements said. Every number in this plan is reproducible from a command in this repository, and the ones that are not yet trustworthy are marked as such in §4 and §10.
