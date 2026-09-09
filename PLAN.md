# Master Plan v0.3

2026-09-09. Supersedes v0.2 (research-grounded but lab-shaped) and v0.1 (written from memory).
v0.2's research stands and is unchanged in `docs/research/`. What changes here is the product: what gets built, how small it is, how fast it runs on a real repository, and what it actually is.

---

## 0. Verdict on the critique

Accepted, with the reasoning:

| Critique | Accepted because | Change |
|---|---|---|
| This is a research lab, not a product | True. v0.2 spends three weeks on harness before any code touches a repository. Nothing in it could be dogfooded in month one | Vertical slice in seven days; harness grows beside it |
| Evaluation cost will explode | 8 arms times 48 tasks times 3 runs is 1,152 agent runs per full sweep, and v0.2 wanted several | Progressive tiers plus **offline replay**: most hypotheses are functions of traces already collected, not new runs (Section 9.3) |
| Friction is not a first-class hypothesis | Correct and dangerous. A gate with bad precision is worse than no gate | The gate is measured as a classifier: precision, recall, false-block rate. Product track in Section 9.2 |
| Novelty claims are overreaching | Correct. Searching found AgentLTL, proof-carrying certificates for LLM pipelines, and proof-of-execution attestation, none of which v0.2 knew about | Every claim rebounded to "not found among the fourteen systems surveyed and the papers read" (Section 10) |
| M3 referenced but never defined | Real inconsistency | Fixed, plus three more found (Section 11) |
| The name looks derivative | Probably true | Analysed, not changed yet (Section 12) |
| Proof-driven compilation may be the stronger architecture | This is the best idea in the critique and it survives scrutiny | Adopted as the spine, with a bounded claim and a fallback (Section 4) |

Rejected or reframed:

- **"Eval before architecture" becomes "measure before commitment, prototype before infrastructure."** Accepted as stated. But one piece of v0.2 stays: the noise floor is measured in week one, because without it every later number is unreadable. That is two hours of compute, not three weeks.
- **The Developer Friction Index as a single summed number.** Rejected. Summing questions, blocks, latency and tokens into one figure hides which one is hurting. A four-component vector plus one headline (false-block rate) is more actionable and harder to game.
- **Autonomy Rate as defined.** Reframed. "Completed without human intervention over resolvable tasks" rewards a system that plows ahead recklessly. It must be conjoined with correctness (Section 9.2).

---

## 1. What this thing is

Reasoning from first principles rather than picking a category name.

It is not a framework: it prescribes no process the user must learn. It is not an agent: it never acts. It is not a harness: it does not own the loop. It watches an agent work, decides what would constitute proof that the work is done, collects that proof automatically from what the agent already runs, tracks which proof is still valid as the code changes, and computes a completion state that the agent cannot simply assert.

The closest true analogue is not any coding-agent project. It is `make`.

`make` does not build software. It knows what depends on what, notices when something is stale, and refuses to call a target up to date when its inputs have changed. It converts "is this built?" from an opinion into a computation.

This does the same thing for correctness claims. An agent says "fixed the auth race." That is a claim. A claim has obligations. Obligations are discharged by evidence. Evidence is produced by commands the agent already runs, and it is bound to the exact repository state it observed. Edit a file, and the evidence that depended on it goes stale, exactly as an object file does. Completion is then not a sentence the agent writes. It is a computed property of the ledger.

**Working description: an incremental verification layer for coding agents. It decides when work is actually done, and keeps that decision honest as the code changes.**

The two moments that sell it, both achievable in the first week:

```
UNVERIFIED  bug_fixed(auth-race)
  met      regression test tests/auth/test_race.py added
  missing  no run showing it failed before the fix
  missing  suite tests/auth not run since the change
```

```
STALE  evidence: tests/auth passed (84 tests)
  recorded at tree e3f1a9c, you have since edited src/auth/session.py
  re-run to restore
```

Nobody in the fourteen systems surveyed produces either message. gstack comes closest: it grades one declared command FRESH, STALE or MISSING against a working-tree hash. That is the same idea at one-command granularity, which is both encouraging and the whole opening.

---

## 2. The thesis, restated

v0.2's thesis was a list of five things: externalized state, enforced stages, typed claims, risk-scaled contracts, automatic capture. That is a system description, not a thesis, and four of the five exist in some form in the field.

v0.3's thesis is one sentence:

> **Completion should be computed from dependency-tracked evidence, not asserted by the model.**

Everything else is machinery in service of that, and each piece must justify itself against the question: if this vanished, would a developer notice their agent got worse?

| Subsystem | Vanishes, would users notice? | Verdict |
|---|---|---|
| Evidence capture from tool output | Yes. Without it the gate needs manual input and dies | **Core** |
| Content-hash provenance and staleness | Yes. This is the visible magic | **Core** |
| Claim inference | Yes, but it needs one cheap call, not a taxonomy | **Core, minimal** |
| Obligation contracts | Yes. This is what makes the gate meaningful | **Core, as data** |
| Completion gate on Stop and TaskCompleted | Yes. The product | **Core** |
| Scope guard | Yes. Agents touching unrelated files is a top complaint | **Core** |
| End report | Yes. It is the entire visible surface | **Core** |
| Repeat runner for flaky work | Yes, sharply, for anyone with a flaky suite. About 100 lines | **Core, cheap** |
| Task ledger | Only indirectly, through resumption. Keep it as a file, not a subsystem | Minimal |
| Workflow compiler with five templates | Unclear. This is where ceremony enters | **Postponed** to a two-step version |
| Repository model, PageRank map | Not at first. Needed later for finer invalidation | **Postponed** |
| Context engine with per-stage budgets | No | Postponed |
| Memory | No, and both real implementations report automatic capture failing | Postponed |
| Model routing | No, the host already does it | Dropped from Phase 1 |
| Critics and subagents | No at first; they add cost and latency | Postponed |
| Multi-host adapters | No, until one host works | Postponed to a two-day spike |

Seven core pieces. That is the 90/10.

---

## 3. The 90/10 core

Estimated sizes are what the first working version should cost, not what it will eventually be.

| Piece | What it does | Lines |
|---|---|---|
| Evidence parsers | Turn pytest, jest, vitest, tsc, build and lint output into typed records | 300 |
| Provenance and staleness | Hash the files an evidence record depended on; recompute freshness on demand | 150 |
| Claim inference | One cheap model call mapping the request to zero or more claims from a closed set | 80 |
| Obligation table | Claim type times risk tier to required evidence kinds. Data, not code | 60 |
| Gate | On Stop and TaskCompleted, compute VERIFIED, UNVERIFIED, CONTRADICTED, or STALE; block with the specific missing items | 200 |
| Scope guard | Deny edits outside the declared touch set with a one-line reason | 100 |
| Repeat runner | Run a command N times, report failure rate and classify deterministic, flaky, clean | 100 |
| Ledger and report | JSON file per task; the banner and end report | 200 |
| Claude Code adapter | Hook wiring, one MCP tool for `record_evidence` and `declare_claim` | 200 |
| Host contract | Reading real payload shapes, generated subscription, blind-spot log, `ep-doctor` | 400 |

About 1,400 lines. If the first implementation is much larger than that, something has gone wrong.

---

## 4. Proof-driven compilation: analysis, not adoption on faith

The critique proposes replacing

```
intent -> task category -> workflow template -> verification appended
```

with

```
intent -> claims -> proof obligations -> required observations -> actions -> workflow
```

I tested it rather than adopting it, and it survives, but not for the reason first given.

**Why it is better.** In the classification architecture, the load-bearing component is a classifier guessing a process, and a wrong guess produces wrong ceremony with no way to notice. In the obligation architecture, the load-bearing component is "what would convince us this is done", which is concrete, checkable, correctable by a human in one line, and directly the thing users care about.

The deeper reason is about invariants. **Obligations are stable; workflows are contingent.** When evidence contradicts the plan halfway through a hard bug, the obligation does not change; only the route to it does. That makes replanning natural instead of a special case, and it removes the need for "recompile triggers" as a separate mechanism, because re-planning to an unchanged goal is just planning. v0.2 needed a whole invalidation subsystem to simulate what this architecture gets for free.

It also collapses two components into one. Classification plus a template library becomes claim inference plus obligation-directed sequencing. That is fewer moving parts, which is the direction the critique asks for. The more ambitious idea is also the smaller one, which is usually a sign it is right.

**Where it genuinely fails, and what to do.**

1. *Claims still have to be inferred from intent.* This is a classifier by another name. But it is a better-conditioned one: the claim set is small and closed (currently eight), several claims can be emitted for one request where a category forces exactly one, and a wrong claim is visible to the user in one line of the banner and correctable, where a wrong category is invisible.

2. *Not all work has obligations.* "Explain this module", "what do you think of this design", exploration. Proof-first degenerates here. The right behavior is a null contract and a runtime that does nothing, which is also the right product behavior: no ceremony for work that has no completion criterion. v0.2 would have run a workflow anyway.

3. *Obligations underdetermine order.* "Applies, preserves seeded data, rolls back" does not say to write the migration first. Sequencing needs a small body of procedural knowledge: operators with preconditions and effects, the goal being the obligation set. This is classical planning, and the operator library is far smaller than a workflow-template library because operators compose. For Phase 1 this is not even needed: obligations can be discharged in any order and the gate only checks the end state. Sequencing is a Phase 2 optimization, and only if measurement demands it.

4. *Formalization is ceremony if visible.* The user must never type a claim. It is inferred, shown in one line, and overridable.

**Prior art, bounded honestly.** Searching found three relevant 2026 lines of work that v0.2 did not know about:

- **AgentLTL** (arXiv 2607.02599) specifies procedural rules in first-order linear temporal logic over agent traces, produces a deterministic judge-free compliance score, and enforces at runtime by blocking actions on prefix violations. This is runtime-enforced process compliance, and it means v0.2's "runtime-enforced process stages" was not novel. It verifies *procedure*, whether the agent called things in a legal order. It does not verify *outcome*, whether the work is done and still valid.
- **Proof-Carrying Certificates for LLM Pipelines** (arXiv 2605.16407) issues Lean 4 kernel-checked certificates over deterministic pipeline steps, binding evidence to per-call artifacts, with an explicit residue of dropped claims on abstention. Formal, heavyweight, bound to call artifacts rather than repository state.
- **Proof of Execution** (arXiv 2607.05397) enforces authorization and path compliance at runtime over a causal event stream with replay and attestation certificates. Governance framing.

And one industrial practice that matters more than any of them: **Test Impact Analysis**, deployed at Datadog, Microsoft, Google and elsewhere, builds a test-to-source dependency map (statically from imports, or dynamically from coverage) and reruns only the tests a change can affect, with a documented "fall back to full when the map is stale" safety rule. That is exactly the invalidation mathematics this design needs, already proven at scale.

So the bounded claim: **obligations derived from inferred intent, discharged by automatically captured evidence, invalidated by repository change through test-impact-style dependency tracking, gating the completion of a general coding agent, was not found among the fourteen systems surveyed or the papers read.** The nearest instances are gstack's single-command working-tree fingerprint and Test Impact Analysis applied to CI test selection rather than to agent completion. The mechanism is proven; the application is what is new. That is a lower-risk kind of novelty than inventing a mechanism.

**Decision.** Obligations become the spine. Claim inference replaces task classification. The workflow compiler is postponed entirely: in Phase 1 there is no compiler, only obligations and a gate. If measurement shows the agent flailing toward obligations it cannot sequence, a minimal operator-based planner is added then, and H19's structured-versus-natural-language question applies to operators rather than to templates.

---

## 5. Evidence as an incremental build graph

The mechanism, precisely.

An **evidence record** is:

```
kind        test | test_suite | build | typecheck | lint | runtime | benchmark | browser | scanner
identity    what exactly ran (node id, suite path, command)
result      pass | fail | error, with counts
observed    the set of file paths this result depended on
tree        content hash over that set at the moment of observation
run         pointer to the raw output on disk
at          timestamp
```

An **obligation** is a predicate over evidence records: kind, identity constraint, and required result. A **claim** holds a set of obligations, chosen by claim type and risk tier.

**Freshness** is the whole trick. A record is fresh when the hash over its `observed` set still matches the working tree. Change one of those files and the record is stale, exactly as `make` marks an object file. Three levels of dependency precision, adopted in order as they earn their place:

1. **Coarse.** `observed` is every tracked file. Any edit stales everything. Correct but pessimistic. Ten lines. This is where Phase 1 starts, and it is what gstack does.
2. **Static.** `observed` is the transitive import closure of the test file. Static Test Impact Analysis. Needs an import graph, which is the first real justification for a repository model.
3. **Dynamic.** `observed` comes from coverage data of that test run. Dynamic TIA. Most precise, needs coverage instrumentation, opt-in.

The safety rule from industrial TIA carries over unchanged: when the map is missing or stale, fall back to full. A verification layer that under-invalidates is worse than useless, so every ambiguity resolves toward "stale."

**This reframes the repository model.** In v0.2 it existed to help the agent find code, which is a crowded space where Aider and Continue already do well. Here it exists to compute what a change invalidates, which is a different and much better-defined job. It gets built only when coarse invalidation proves too pessimistic in real use, and only as far as static TIA. That is a demotion in scope and a promotion in clarity.

**The state machine.** A claim's state is computed, never set:

```
                +-- obligations unmet -----> UNVERIFIED
declared -------+-- all met, all fresh ----> VERIFIED
                +-- any evidence failing --> CONTRADICTED
                +-- all met, some stale ---> STALE
```

Two transitions matter and neither is conversational: an edit can move VERIFIED to STALE, and a failing test can move VERIFIED to CONTRADICTED. An agent cannot talk its way out of either.

**Abstention.** `cannot_complete` is a claim type with its own obligations (a stated reason, evidence that the blocker is real, what was tried). The Confident and Wrong study measured action bias as the dominant failure mode: models edit when abstaining is correct. A completion system with no way to express "this should not be done as asked" reproduces that failure by construction.

---

## 6. The eight claim types

A closed set, deliberately small. Additions require a hypothesis.

| Claim | Low-risk obligations | High-risk adds |
|---|---|---|
| `bug_fixed` | a test that fails before and passes after; related suite green | reproduction evidence; stability over N runs; independent review |
| `feature_added` | tests exercising the feature pass; build and typecheck clean | integration tests; browser evidence for UI; scope within guard |
| `refactor_safe` | relevant suite green; diff within guard | mutation score not worse; public API diff empty |
| `migration_safe` | applies and reverts on a fresh database | applies to seeded data; rollback tested; shape assertions |
| `perf_improved` | benchmark before and after | repeated runs with variance; secondary benchmark not regressed |
| `deps_updated` | suite green; lockfile consistent | audit clean; no major-version behavior change untested |
| `docs_changed` | docs build if one exists | none |
| `cannot_complete` | stated reason; what was tried | evidence the blocker is real |

Risk tier comes from three signals, none of which needs a model: paths touched against a policy list (auth, payment, migrations, secrets, infra), reversibility by change type, and the size of the change. A model call refines it only when the deterministic signals disagree.

---

## 7. Seven days to a working slice

Runs on a real repository from day three. Every day ends with something demonstrable.

**Day 1. Ledger and evidence.** Record schema, JSON ledger per task, content hashing over a file set, freshness computation. `pytest` and `jest` output parsers. Unit tests on captured fixture output. No agent involved yet.

**Day 2. Adapter and capture.** Claude Code plugin: `PostToolUse` on Bash parses test, build and typecheck output into records automatically; `SessionStart` loads or creates the ledger. Prove that running the agent on a real repository produces a populated ledger with no user action. This alone is a demo.

**Day 3. Claims and the gate.** Claim inference on `UserPromptSubmit`, one cheap call, closed set, shown in one line. Obligation table as data. `Stop` hook computes state and blocks with the specific missing items, bounded to two blocks then reports UNVERIFIED. **First end-to-end run on a real repository.**

**Day 4. Staleness and the report.** Freshness recomputed at gate time; the STALE message. End report showing claims, obligations met and missing, evidence with provenance. This is the second selling moment.

**Day 5. Scope guard and repeat runner.** `PreToolUse` denies edits outside the touch set with a reason and a one-word override. Repeat runner as an MCP tool and as a stability obligation for flaky claims.

**Day 6. Dogfooding.** Use it for the day's actual work, on this repository and one other. Log every friction event by hand: unnecessary block, wrong claim, wrong obligation, annoying message, latency spike. This log is the most valuable artifact of the week.

**Day 7. Micro-eval and triage.** Ten-task micro suite that runs in under fifteen minutes: gate on versus off, submit-resolve gap and false-block rate. Fix the top three friction items. Decide what week two looks like from evidence rather than from this plan.

Deliberately absent from week one: workflow compiler, repository model, context engine, memory, routing, critics, second host, and the full harness.

---

## 8. What is postponed, and the trigger for each

| Postponed | Trigger to build it |
|---|---|
| Workflow compiler | Dogfooding shows the agent failing to sequence work toward obligations it clearly understands |
| Repository model (static TIA) | Coarse invalidation is too pessimistic: measured rate of "everything stale on a one-file edit" is annoying in practice |
| Context engine with budgets | Large-repo tasks fail on context, measured, not assumed |
| Memory | Multi-session dogfooding shows the same fact re-derived three times |
| Model routing | Cost becomes a real complaint |
| Critics | Regression rate on risky changes stays high with the gate on |
| Second host adapter | Someone asks, or Phase 1 numbers are good enough to be worth porting |
| Full 48-task harness | A decision needs a number the micro and smoke tiers cannot produce |

Each of these has a home in `docs/postponed.md` with its trigger, so postponement is a decision with a condition rather than a quiet drop.

---

## 9. Evaluation: two tracks, progressive, mostly offline

### 9.1 Benchmark track

Progressive tiers. Each must justify its cost against the decision it informs.

| Tier | Size | Cost | Cadence | Answers |
|---|---|---|---|---|
| Micro | 10 tasks, 1 run | minutes | every meaningful commit | did I break the gate |
| Smoke | 20 tasks, 1 run | about an hour | daily | did behavior shift |
| Development | 48 tasks, 3 runs | hours | weekly, or at a gate | does this change help |
| Held-out | 24 tasks, 3 runs | hours | milestone gates only | am I overfitting |
| External | SWE-bench Pro, Terminal-Bench subsets | expensive | twice in Phase 1 | does it hold outside my tasks |

The noise floor is still measured in week one, at ten tasks by ten runs on vanilla, because every later interval depends on it. That is hours of compute, not weeks of construction.

### 9.2 Product track

The track v0.2 lacked. A technically superior system that people disable has lost.

**The gate is a classifier. Measure it as one.**

| | Work actually incomplete | Work actually complete |
|---|---|---|
| Gate blocked | true block | **false block** |
| Gate passed | **miss** | true pass |

- **False-block rate** is the headline product metric. A gate with poor precision is worse than no gate, because it trains users to disable it. Target below 5 percent before any public release.
- **Miss rate** is the submit-resolve gap by another name, and it is the benchmark headline.

Four friction components, reported separately because summing them hides which one hurts:

| Component | Measure |
|---|---|
| Interruption | blocks and questions per task, each labeled necessary or not afterward |
| Latency | seconds added before the agent's first useful action, and per turn |
| Tokens | tokens added by the layer, absolute and as a share |
| Ceremony | lines of framework output the user reads per task |

**Verified Autonomy Rate**, replacing the proposed Autonomy Rate:

```
tasks resolved AND verified AND completed with no human intervention
-----------------------------------------------------------------
                    all attempted tasks
```

The conjunction matters. The proposed version rewards a system that never asks and is often wrong. Alongside it, **escalation precision**: of the times the system stopped to ask, how many were cases where proceeding would have been wrong. A system that asks rarely and correctly is the goal; a system that never asks is not.

**Would-disable rate**: during dogfooding, count sessions in which a gate was overridden or switched off, with the reason. One a day means the design is wrong, not the user.

### 9.3 Offline replay: the cost killer

Most hypotheses are functions of traces already collected, not new agent runs.

Whether the gate would have blocked a run, whether claim inference picks the right claim, whether an obligation set was satisfied, whether the risk tier was right, whether the scope guard would have fired: all of these are deterministic functions over a stored trace of tool calls and outputs. Collect the traces once, then evaluate variants offline, at the cost of parsing rather than the cost of inference.

This means most iteration on the classifier, the obligation table, the parsers and the gate policy costs approximately nothing. Only changes that alter the agent's own behavior require new runs. v0.2 assumed every hypothesis needed a fresh sweep, which is what made its budget frightening. A trace corpus of a few hundred runs, collected once, supports dozens of offline experiments.

**Built, 2026-09-09, and better than assumed.** The corpus did not need collecting: Claude Code already stores a transcript of every session, including each tool result exactly as the host produced it. `python -m eval.replay --all` reads them. The first run covered 241 sessions, 3,557 turns and 36,034 commands at no inference cost.

The ground truth is the part that makes it worth more than expected. The host records whether each command failed, by returning a different shape, so the corpus grades the runtime without the author labelling anything. That removes the failure mode every earlier measurement in this project shared: scenarios written by the person whose code is being graded.

What it cannot measure is freshness. The working tree at each moment is not recoverable from a transcript, so staleness results would be meaningless and are not reported.

---

## 10. Novelty claim audit

v0.2 contained unbounded claims. Corrected:

| Was | Now |
|---|---|
| "the only system that will refuse to say done without evidence" | "none of the fourteen systems surveyed computes completion from dependency-tracked evidence; gstack grades one declared command against a working-tree hash" |
| "Tooling for intermittent bugs: no cover at all" | "no repeat runner, stress harness or instrumentation tooling was found among the fourteen surveyed" |
| "runtime-enforced process stages" as novel | withdrawn. AgentLTL enforces procedural compliance at runtime over agent traces with temporal logic |
| "typed claims are new" | bounded. Proof-carrying certificates for LLM pipelines type pipeline steps against a Lean kernel; the difference is binding to repository state rather than call artifacts |
| "evidence contracts are new" | bounded. Proof-of-execution binds contracts to a causal event stream for governance; the difference is correctness of work rather than authorization of actions |
| "staleness invalidation is new" | withdrawn as a mechanism. Test Impact Analysis is standard industrial practice; the application to agent completion is what was not found |

Standing rule: a novelty claim names the search that failed to find prior art. "Not found among the fourteen systems surveyed and the papers in `reading-list.md`" is the strongest form allowed without an exhaustive literature review.

---

## 11. Inconsistencies found and fixed

1. **M3 with no M3.** v0.2 protected a bet "through M3" while defining M0 to M2. Fixed: protection runs to the Phase 1 exit gate. And the protected bet is now the evidence core, which is also the smallest piece, so protection costs little.
2. **Two verification philosophies.** v0.2 said verification depth scales with risk, and separately compiled a fixed verify stage into every template. Resolved: obligations are the only mechanism; risk selects which obligations, and there is no separate verify stage.
3. **"No product code before the M0 gate" versus a twelve-week schedule.** The rule guaranteed nothing was usable for three weeks. Removed. Replaced by: no *new subsystem* before its trigger fires.
4. **Prediction calibration had no consumer.** v0.2 added the metric with nothing acting on it. Resolved: it is a leading indicator reported in the product track, and it becomes a control signal only if H21 shows it predicts the miss rate.

---

## 12. The name

The critique is likely right. "ElevenPowers" reads as a numbered variant of Superpowers, which frames the project as a bigger skill library. That is precisely what it is not.

The concept is: claims, obligations, evidence bound to state, staleness, computed completion. Naming directions that follow from that, offered without recommendation and without further time spent:

- **Warrant.** In the Toulmin model of argument, the warrant is what licenses a claim from its grounds. Exactly the relationship being modelled.
- **Ledger, Attest, Certify.** Accurate, crowded.
- **Freshline, Staleguard.** Emphasize the invalidation mechanism, which is the visible magic.
- **Assay.** A test that determines whether something is what it claims to be.

Decision deferred until Phase 1 numbers exist. The directory stays `ElevenPowers` until then; renaming a repository with no users is free later and a distraction now.

---

## 13. Remaining hypotheses

Reduced from twenty-two. Each names its tier and whether it needs new runs or replays existing traces.

| ID | Hypothesis | Tier | New runs? |
|---|---|---|---|
| P1 | Evidence gating halves the submit-resolve gap versus vanilla | micro then dev | yes |
| P2 | False-block rate stays under 5 percent | dogfood then dev | replay |

**P2, first result (2026-09-09).** Measured on 42 labelled scenarios via
`python -m eval.run --all`. First run: 75 percent false blocks, which would have
made the tool unusable. After nine fixes: 0 percent false blocks and 0 percent
misses on both the tuning set and a held-out set written afterwards to break it.
The held-out set scored 43 percent before its two real bugs were fixed, so the
tuned number alone was three-quarters overfitting. Full account in
`journey/05-measurement.md`, including what the result does not establish: 42
constructed scenarios written by one person are not real agent behaviour, and no
agent has yet been run through this at scale.

| P3 | Claim inference picks the right claim at least 90 percent of the time | replay against labeled traces | replay |

**P3, first result (2026-09-09).** Measured on 3,557 turns from 241 real
sessions via `python -m eval.claims_run`, with ground truth taken from what each
turn actually did rather than from labels. First run: 51 percent of turns that
changed nothing had obligations attached, because any sentence longer than two
words claimed a feature. The 0 percent false-block rate on 46 scenarios was not
wrong, it was measured on a population containing no conversations, and real
sessions are mostly conversation.

The same measurement found the gate switching itself off: a prompt with no claim
in it cleared the claims of work already in progress, so typing "continue" ended
the task's obligations. One real prompt in five is four words or fewer, so no
classifier reading the prompt alone can do this job.

The claim now follows the work. A prompt that states no subject leaves an open
claim alone; the first source edit opens one when the prompt stated none; an
explicit question or read request is never overridden by an edit. Over-claiming
fell to 21 percent and missed work to 25 percent, 11 percent on turns whose
change the runtime can see. Full account in `journey/09-claims.md`, including
what the proxy cannot separate.
| P4 | Coarse invalidation is not too pessimistic to live with | dogfood | replay |
| P5 | Gating improves abstention accuracy on tasks where the right answer is to stop | dev | yes |
| P6 | Stability obligations halve false "fixed" claims on flaky bugs | micro, flaky subset | yes |

**P6, mechanism built (2026-09-09).** The `stable` obligation previously accepted
any runtime record, so one execution of a reproduction script that happened not
to fail satisfied it. That was a false verification on the differentiating task
class. It now requires evidence from a repeat runner, and the required run count
is computed from the failure rate the agent measured rather than chosen: with a
fault still present at rate p, n clean runs occur with probability (1-p)^n, so
95 percent confidence needs n >= log(0.05)/log(1-p). Verified end to end against
a real one-in-six failure. The hypothesis itself still needs agent runs.
| P7 | Deterministic scope guards beat prompt instructions at reducing unrelated edits | dev, three arms | yes |

**P7, mechanism built (2026-09-09).** The guard was previously inert: its allow
list was read in three places and written by nothing. Scope is now derived
rather than declared, from the files the task has read, the files it has edited,
and the areas the request names, because nobody knows which files a change will
touch before making it. It asks rather than denies. Measured on 25 labelled
cases, weighted toward legitimate edits that look unrelated: 0 false questions,
0 misses. The hypothesis itself still needs agent runs.
| P8 | The layer adds under 10 percent tokens and under 5 seconds per task | micro | replay |
| P13 | The runtime reads what the host actually sends | replay | replay |

**P13, first result (2026-09-09), and it failed.** The hypothesis was added
after two core pieces turned out to be dead code, on the theory that a third
might be. Three defects were found, all in the layer between the runtime and its
host, none reachable by any test of the runtime alone.

The subscription delivered `Bash` alone to `PostToolUse`, so the scope guard was
inert one commit after it shipped. Failing tool calls raise `PostToolUseFailure`,
which nothing listened to. And the result reader looked for an exit code the host
does not send while treating the string form, which is exactly the failure case,
as success. Every command was recorded as passing, which makes `CONTRADICTED`
unreachable and lets a red suite discharge "the suite passes".

Measured on 36,034 real commands: the previous reader agreed with the host on 0
of 174 gradeable failures. The current one agrees on 174 of 174 and on 5,916 of
5,916 successes. Reported as two rates because the corpus is 97 percent
successes, where a reader that says "passed" to everything scores 97 percent.

The general fixes matter more than the three specific ones: the subscription is
generated from the constants the handlers branch on with a test asserting no
drift, anything unreadable is appended to a blind-spot log, and `ep-doctor`
exercises the join rather than either half. Full account in
`journey/08-wiring.md`.
| P9 | Obligation-directed work beats template-directed work on hard tasks | dev | yes, Phase 2 |
| P10 | Static TIA invalidation measurably beats coarse invalidation | replay | replay |
| P11 | Composition of best-of-breed pieces beats its best single part | dev | yes, Phase 2 |
| P12 | Prediction calibration predicts the miss rate | replay | replay |

Seven of twelve need no new agent runs. That is the offline-replay dividend.

---

## 14. Why this might be a genuine step beyond the systems surveyed

Stated as falsifiable propositions rather than as marketing.

1. **Completion becomes computable.** In all fourteen systems surveyed, done is either "the model stopped calling tools" or "the model said so", with gstack's single-command fingerprint the sole partial exception. Computing it from evidence with provenance is a different kind of object.
2. **Invalidation is the missing half.** Every verification effort in the field is a point-in-time check. None tracks that a check was invalidated by later edits. Agents edit constantly after testing, so this is not an edge case; it is the normal path to a false claim.
3. **The mechanism is proven, only the application is new.** Test Impact Analysis is deployed at scale in industry. Borrowing it lowers risk instead of raising it.
4. **Obligations are a better invariant than plans.** They survive replanning, they are correctable by a human in one line, and they make "why are you doing this" answerable at any moment.
5. **It composes instead of competing.** It does not replace Superpowers, Spec Kit or Aider. It sits underneath them and tells the truth about whether their work landed. That is a much easier thing to adopt than a framework demanding to own the process.
6. **The floor is honest.** mini-SWE-agent reaches over 74 percent with 190 lines. This design does not try to beat it at writing code. It tries to know when the code is right, which is a different axis and the one where the field is weakest.

If P1 and P2 both hold, the product exists. If P1 holds and P2 fails, the idea is right and the policy is wrong, which is tuning. If P1 fails, the thesis is wrong and no amount of the rest will save it, which is why it is the first thing measured.

---

## Appendix: evidence trail

`docs/research/` holds the v0.2 research unchanged: fourteen source-read cards, three host cards, the competitor map, the complementarity matrix with its sixteen weakness classes and ten residual gaps, the license register, and the annotated reading list. This plan cites but does not repeat it.
