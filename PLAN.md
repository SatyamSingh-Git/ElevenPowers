# ElevenPowers: Master Plan

Version 0.2, 2026-09-09. Supersedes v0.1, which was written from recollection before any research.
Status: planning. No product code exists. Every claim about another system now traces to a source-read card in `docs/research/cards/` at a recorded commit; every claim about a host traces to `docs/research/hosts/`; every claim about the literature traces to `docs/research/reading-list.md`.

---

## 0. What changed from v0.1, and why it matters

v0.1 was an execution plan built on priors. Fourteen systems were then cloned and read from source, ten hosts and papers were checked, and the priors were tested. This section lists only the changes that alter what gets built.

| v0.1 said | Evidence found | v0.2 does |
|---|---|---|
| SWE-bench Verified is the bug-fix suite | Frontier models cluster at 95 to 97 percent across four leaderboards; secondary reporting says a February 2026 audit found widespread flawed tests and gold-patch memorization | Drop it as a discriminating suite. Use SWE-bench Pro public set, SWE-rebench v2, Terminal-Bench 2.0 |
| "False success" is the key metric | The Confident and Wrong study quantifies it: one model submitted on 100 percent of runs and resolved 44 percent; silent semantic failures were 68 to 80 percent of failures; pre-edit prompts did not fix it | Rename to the **submit-resolve gap**, adopt its definition, and add abstention tasks where the correct answer is "not as specified" |
| Instruction files are the wrong mechanism (asserted) | The AGENTS.md study measured it: context files raised cost over 20 percent on average; model-written ones lowered success about 3 percent; developer-written ones raised it about 4 percent | Keep the gates-over-text thesis, cite the study, and add a "no instruction file" arm to every experiment |
| Adapters are a milestone at week 19 | Codex, Gemini CLI, Cline CLI and Continue CLI all ship Claude-Code-shaped hooks; Codex's engine struct is literally named after them | Portability is a week of work per host, not a phase. Move the second host to M2 as a two-day spike |
| Provider independence needs six adapters | Only OpenCode lacks a completion-blocking hook | Adapter contract is three capabilities; OpenCode gets the documented degraded path |
| Repository knowledge graph, tiered | Only Aider and Continue have any repository model; Aider's is Apache-2.0 and self-contained; Continue's index is Apache-2.0 | Do not build tier 1. Wrap Aider's `repomap.py` and measure. Build only the edges it lacks |
| Evidence ledger is a new idea | gstack already binds test evidence to a working-tree content hash and grades FRESH, STALE, MISSING; OpenHands has an evidence-demanding judge; BMAD audits a test per I/O matrix row | Cite all three as prior art. The new part is typed claims, risk-scaled contracts, and automatic capture |
| Compaction-safe task state is a new idea | Superpowers keeps a plan-scoped ledger for exactly this reason; OpenHands condenses via tombstones with legal cut points; Cline keys checkpoints to survive compaction | Cite as prior art. The new part is that the runtime writes it, not the model |
| Six milestones over 26 weeks | The single-engineer estimate was fantasy past week ten; the harness alone is three weeks | Two phases. Phase 1 is 12 weeks and is a shippable product. Phase 2 is scoped after Phase 1 numbers exist |
| Every component is deletable at its gate | A plan whose every component can be deleted converges on the safest, least ambitious thing | One **protected bet** gets a full trial through M3 regardless of intermediate results. Everything else stays deletable |
| Learning arrives at week 15 as proposals | The harness produces labeled outcomes from day one; gstack's specialist gating is the only working outcome-to-policy loop in the field and it is narrow | Move learning to M1 as a data problem: train the profiler on harness outcomes |
| Ten memory classes reduced to one schema | Both systems with real memory code report automatic capture does not produce useful records (gstack: 43 of 44 learnings were manual; ECC's v1 learning hook is a no-op) | Keep the schema. Assume automatic capture fails until proven; the default is user-confirmed writes |

Two facts reframe the whole project:

1. **mini-SWE-agent reports over 74 percent on SWE-bench Verified with a 190-line loop and one bash tool**, and its authors now recommend it over their own full harness. Any complexity this project adds must beat that baseline on a suite that still discriminates. This is the humility constraint.
2. **Nine of the ten systems studied enforce their process with text the model can ignore, and three admit it in their own repositories.** That is the opening.

---

## 1. Executive summary

**What this is.** A runtime that sits between a developer's request and an existing coding agent and moves four things out of the model's context window into deterministic code: task state, process control, budgets, and proof of completion. The model does judgment. The runtime does bookkeeping, gating, and evidence.

**The one-sentence reason to exist.** It is the only system that refuses to say "done" without evidence sized to the risk, and that decides the engineering process per task instead of making the developer choose it.

**The protected bet.** Externalized task state plus typed evidence contracts, enforced by host hooks. This is the thesis. It gets a full trial through M3 even if intermediate results are mixed, because every partial version of it in the field (gstack's evidence ledger, Superpowers' ledger, OpenHands' goal judge) shows a piece working while none has the whole.

**How the strengths get combined.** The user's stated first goal is to combine the strengths of the studied systems so each one's weakness is covered by another's strength. `docs/research/complementarity-matrix.md` does that mapping in full: 16 weakness classes, each mapped to a covering strength with its mechanism, cost, and coverage rating. Ten residual gaps survive that mapping. Those ten, and only those, justify new architecture. The composition itself becomes a measured baseline (Section 5), so "combine the best pieces" is tested rather than assumed.

**How success is measured.** A harness built before the architecture, running six arms on tasks from suites that still discriminate, reporting per category with confidence intervals, and gated on a held-out set. Headline metric is the submit-resolve gap.

**First three weeks.** Harness, 48-task development set, and baselines. No product code until baselines exist with intervals.

**Primary risk.** Building infrastructure instead of learning. Mitigation: a ten-task smoke tier under an hour, and a first vertical slice at week six that is useful on its own.

---

## 2. Grounding: what the field actually looks like

Full detail in `docs/research/competitor-map.md` and the fourteen cards. The findings that shape this plan:

**Enforcement.** Superpowers, ECC, Spec Kit, gstack, and BMAD are process frameworks whose gates are prose. Superpowers' own `CLAUDE.md` says agents ignore its guidelines. Spec Kit's "mandatory hooks" are executed by the model parsing a YAML block and emitting an `EXECUTE_COMMAND:` line, while its `HookExecutor` never executes anything. BMAD's "NEVER load multiple step files" is unchecked. The exceptions are ECC's PreToolUse blocks, gstack's freeze and careful hooks plus its verify-gate, OpenCode's permission engine, and Cline's plan-mode command guard, and every one of those gates a *tool call*, never a *process stage*.

**Verification.** Done means the model stopped calling tools in OpenCode, Cline, and Continue. Aider runs tests only if configured. SWE-agent's deliverable is a patch regardless of test results. Spec Kit gates `implement` on a checklist the same agent generated and ticked in the same turn. The only content-bound evidence anywhere is gstack's, which hashes the working tree and grades test evidence FRESH, STALE, or MISSING.

**Repository understanding.** Eight of ten systems have none beyond grep and read. Aider has a symbol graph with personalized PageRank and a budgeted render. Continue has a content-addressed incremental index with a collapsed-AST chunker. Neither has test-to-source edges, ownership, or a blast-radius number.

**Cost of ceremony.** Measured from the cards: ECC loads 21 to 23k tokens on every turn before any MCP schemas, of which about 13k is descriptions for 286 skills including energy procurement and customs compliance. gstack pays 12 to 28k per skill invocation with a 6.5k preamble repeated in every tier-2 skill. Spec Kit's standard sequence on a one-line CSS change is 15 to 20k prompt tokens and 5 to 8 new files; its own lean preset does the same artifact contract in about 5 percent of the text. Superpowers loads about 16k of process text before any project content on a feature. BMAD reads 6 to 9k before code and its blind reviewer has a mandatory finding floor, so a one-line diff is guaranteed a finding to refute.

**Triage.** Three systems have size-to-ceremony logic (ECC's classifier, BMAD's route-after-investigation, Superpowers' three-path brainstorm). All three are prose. None is calibrated against outcomes.

**Memory.** gstack and BMAD have real memory code with decay, trust gates, injection filters, and provenance. gstack's own source comments say 43 of 44 learnings came from explicit user commands rather than automatic capture. ECC's continuous-learning v1 is a no-op that logs to stderr.

**Multi-agent.** gstack's `/ship` re-runs the review army that `/review` just ran, because "never skip a verification step". BMAD ships three near-identical copies of its build and review pipeline and they have already drifted. gstack's adaptive gating, which skips a reviewer with zero findings in ten dispatches, is the only mechanism in the field that reduces agent overhead based on evidence.

**Intermittent bugs.** No system has a repeat runner, a stress harness, or instrumentation tooling. Every card's hard-task trace ends with the analysis left to the model. OpenHands is worse than neutral here: its stuck detector halts the run after three or four identical action and observation pairs, which is exactly what deliberately re-running a flaky test looks like.

**Hosts.** Claude Code, Codex, and Gemini CLI all support injecting text at a turn boundary, intercepting and blocking a tool call, and blocking completion. Cline and Continue copy the Claude Code hook schema verbatim. Claude Code additionally offers `PostToolBatch` (blocks the loop before the next model call) and `TaskCompleted` (blocks marking a task done), neither of which v0.1 knew about. Only OpenCode lacks a completion block.

---

## 3. Operating principles

1. **Beat mini-SWE-agent or delete the component.** A 190-line loop is the floor. Complexity earns its place against that, not against a strawman.
2. **Eval before architecture.** No component without a metric it should move and a baseline for that metric.
3. **Deterministic where possible, model where necessary.** If it can be code, it is code. Scope guards, budget limits, evidence parsing, secret scanning, destructive-command detection: never prompts.
4. **Outside the context window by default.** Profile, workflow, evidence, hypotheses, budgets and memory live in a ledger. The model gets a stage brief.
5. **Typed claims, contracted evidence.** Completion is a proof obligation. UNVERIFIED is a first-class outcome and so is abstention.
6. **Retrieval over injection, with a budget per stage.**
7. **One agent until proven otherwise.** A second agent is for independence of evidence, not for parallelism.
8. **Trust is a property of the source.** System policy over user, over project config, over repository content, over tool output, over web content. Instructions found in lower-trust content are data.
9. **Interoperate rather than replace.** Where Aider, gstack, or Superpowers already do it well, wrap it and attribute it.
10. **Remember little; verify what is remembered.** Default to user-confirmed memory writes until automatic capture proves itself, because in the field it has not.
11. **Delete freely, except the protected bet.** One thesis gets a full trial. Everything else goes at its gate with an ADR recording the numbers.
12. **Attribution is kept.** `docs/research/licenses.md` records every obligation. AutoCodeRover is ideas-only under its source-available license.

---

## 4. The ten residual gaps

From `complementarity-matrix.md` Section 5. These survived the mapping of every studied strength onto every studied weakness. Architecture that does not address one of these is not built.

| # | Gap | Nearest existing cover | What is actually missing |
|---|---|---|---|
| G1 | Process-stage gates enforced by code | gstack verify-gate (one command at Stop); ECC batched Stop check; Claude Code `Stop`, `PostToolBatch`, `TaskCompleted` | Every gate in the field is tool-level. Nothing enforces "reproduce before edit" or "this claim needs this evidence" |
| G2 | A calibrated task classifier | ECC's table, BMAD's route rule, Superpowers' triage, all prose | No classifier is trained or validated against outcomes |
| G3 | Typed claims with risk-scaled contracts and automatic evidence capture | gstack's fingerprinted ledger; BMAD's matrix audit; OpenHands' goal judge | No claim types, no contract that scales with risk, no parsing of tool output into evidence, no abstention |
| G4 | Repository model with test and dependency edges and a blast-radius number | Aider's PageRank map; Continue's incremental index | No test-to-source edges, no ownership, no computed blast radius, no validation against observed regressions |
| G5 | Externalized task state the runtime maintains | Superpowers' ledger (model-maintained); OpenHands tombstones; Cline run-count checkpoints | Every version is either model-maintained or conversation-scoped |
| G6 | Tooling for intermittent and concurrency bugs | Nothing | No repeat runner, no variance reporting, no instrumentation helpers, no hypothesis ledger. OpenHands actively penalizes repeat runs |
| G7 | Memory writes that produce useful records | gstack decay and trust gate; BMAD provenance SHA | Both report automatic capture does not fire. No validation of a memory against later outcomes |
| G8 | Replay-gated learning | gstack specialist stats (narrow); Superpowers' skill-testing method | No general path from outcome to policy change with a regression check |
| G9 | Composition without dilution | Nothing | No system measures what happens when frameworks stack. Skill listings are budget-truncated and lost after compaction |
| G10 | Decision-level observability | Cost accounting everywhere | Nothing records why a stage ran, why a critic spawned, or why a gate blocked |

---

## 5. The composition baseline

The user's first goal is combining strengths. The honest test of that goal is to build the combination and measure it. This is an arm in the harness from week three, not a thought experiment.

**Arm C (composition).** Best-of-breed pieces installed together on Claude Code, all MIT or Apache-2.0, attribution in NOTICE:

| Concern | Piece | Source | Form |
|---|---|---|---|
| Debugging procedure | systematic-debugging, condition-based-waiting, verification-before-completion | Superpowers | skills, as-is |
| Subagent handoff | task-brief, review-package, sdd-workspace | Superpowers | scripts |
| Hard blocks | block-no-verify, config-protection, destructive classifier | ECC | PreToolUse hooks only |
| Stop-time checks | edit accumulator plus batched typecheck | ECC | Stop hook |
| Evidence | gstack-evidence, gstack-wtree, verify-gate | gstack | bin scripts plus Stop hook |
| Browser evidence | Playwright daemon and `$B` CLI | gstack | standalone binary |
| Repository map | `repomap.py` and tag queries | Aider | one MCP tool, budgeted |
| Large-feature artifacts | lean preset plus feature pointer | Spec Kit | commands |
| Review procedure | blind-then-claims, verification-gap lens, verdict-then-route | BMAD | one critic subagent, no finding floor |
| Checkpoints, model per role | worktree subagents, `model` frontmatter | Claude Code | host features |

Known conflicts this arm must resolve, all observed in the cards: three competing "when in doubt, invoke the skill" routing instructions; two Stop hooks and three reviewer mechanisms firing on one change; the Claude Code skill listing budget (1 percent of context, truncated by usage frequency, not reloaded after compaction) silently dropping skills as the stack grows; Superpowers' TDD absolutism and ECC's mandatory coverage both firing on a CSS edit; four state directories.

**Why this arm matters.** If Arm C beats every individual framework, composition is the product and the runtime's job is to make composition selective and conflict-free. If Arm C is worse than its best part, dilution is real, measured, and becomes the strongest argument for the runtime. Either result is worth the two weeks. This directly tests G9.

---

## 6. Evaluation harness

Built weeks 0 to 3, before architecture. This section is the most load-bearing in the plan.

### 6.1 Statistics first

v0.1 wrote decision rules that its sample size could not support. v0.2 fixes the order:

1. Measure the noise floor: vanilla Claude Code, ten smoke tasks, ten runs each, same model and settings. Report per-task variance.
2. Compute the minimum detectable effect for the intended design (paired per-task, three runs, bootstrap intervals). Publish it in `eval/MDE.md`.
3. Size the suite to the effects the plan claims. The submit-resolve gap target is a halving, which is a large effect and detectable with fewer tasks than a five-point success difference. Where an effect is too small to detect at feasible cost, say so and do not write a decision rule that pretends otherwise.
4. Only then write the hypothesis decision rules.

Comparisons are paired per task, bootstrap 95 percent intervals on the per-task difference, McNemar for pass/fail. Reported per category, never as a single mean, because the project's whole claim is that process should differ by task.

### 6.2 Task suite

Eight categories, six tasks each, for a 48-task development set. Cut from v0.1's sixteen categories because sixteen at three tasks each cannot support a per-category claim. A held-out set of 24 is frozen at M1 and evaluated only at gates by a script that withholds traces until the gate decision is recorded.

| Category | Source | Hidden check | Risk |
|---|---|---|---|
| Trivial change | Seed repos, Aider polyglot | Tests plus touch set | low |
| Normal feature | Seed repos | Tests | medium |
| Ambiguous feature | Seed repos, two valid readings | Tests for both, question rubric | medium |
| Bug fix | SWE-bench Pro public subset | Fail-to-pass and pass-to-pass | medium |
| Hard debugging (including flaky) | Seed repos with real concurrency bugs; SWE-bench Pro hardest | Fail-to-pass, repeat-run stability | high |
| Refactor | Seed repos | Full suite, public API diff empty, mutation score | medium |
| Risky change (migration, auth, payments) | Seed repos | Apply and revert, seeded data, security scan | critical |
| Large or unfamiliar repository | SWE-rebench v2, Terminal-Bench 2.0 | Task-provided | medium |

Added and new in v0.2: **abstention tasks**. In each of the ambiguous and risky categories, two tasks are specified so that the correct behavior is to stop and ask or to report that the request as stated is unsafe or impossible. Scoring an agent that confidently proceeds as a failure is the only way to measure the action bias the Confident and Wrong study identified.

Three seed repositories, not four: a TypeScript web application with PostgreSQL, a Python service with a queue, and a small monorepo. Each ships hidden tests, a Playwright suite where there is a UI, an expected touch set, and a reference solution the validator confirms flips the hidden checks.

### 6.3 Arms

| Arm | Command |
|---|---|
| V vanilla | `claude --bare -p` with model pinned |
| S Superpowers | plus `--plugin-dir` |
| E ECC | plus `--plugin-dir` |
| K Spec Kit lean | plus rendered commands, lean preset |
| A Aider | `aider --message`, same model family |
| M mini-SWE-agent | its own runner, bug-fix and large-repo categories only |
| C composition | Section 5 |
| X ElevenPowers | from M1 |

`--bare` is mandatory for every Claude Code arm. Without it, a `-p` run executes the task repository's own hooks and MCP servers with no trust prompt, and evaluation repositories are untrusted content. `--strict-mcp-config`, `--max-budget-usd`, and `--max-turns` bound each run. `system/init` events are checked so a run whose framework failed to load is discarded rather than scored.

### 6.4 Metrics

| Metric | Definition |
|---|---|
| Resolved | Hidden checks pass in a clean environment, no edits to hidden checks |
| **Submit-resolve gap** | Runs asserting completion where Resolved is false, over runs asserting completion. Headline metric |
| Abstention accuracy | On abstention tasks: correctly stopped versus confidently proceeded |
| Regressions | Previously passing tests now failing |
| Scope discipline | Files outside the expected touch set; diff size versus reference |
| Evidence coverage | Completion claims carrying an evidence record of the required kind |
| **Prediction calibration** | New in v0.2. Before each verification command, the agent states the expected outcome; Brier score of prediction against result |
| Interventions | Questions asked, each labeled necessary or not against the task's ambiguity label |
| Cost | Tokens in, out, cached; dollars; wall time; model calls; failed tool calls; identical retries |
| Context share | Per turn, input split into instructions, repository content, tool output, history |
| Localization accuracy | Predicted touched set versus reference solution files, precision and recall |
| Quality | Lint and type deltas, complexity delta, mutation score of added tests, plus a rubric judge calibrated against 40 human-labeled diffs before it is trusted |

Prediction calibration is new because it is cheap, it is a leading indicator of the submit-resolve gap, and no studied system measures it. An agent that predicts "this test will pass" and is wrong half the time is detectable long before its final claim is checked.

### 6.5 Implementation

Python 3.12 with `uv`. One Docker container per run, pinned images, resource limits, timeouts. Trace capture via Claude Code OpenTelemetry (`claude_code.api_request`, `tool_result`, `tool_decision`, with `OTEL_LOG_RAW_API_BODIES=file:` for the context-share metric) plus hook-based capture; other arms' logs normalized into one schema. SQLite for runs, Parquet for analysis. Hard per-run cost cap. Task authoring template plus a validator that confirms hidden checks fail before the reference solution and pass after.

Tiers: smoke (10 tasks, 1 run, under an hour, runs before any merge), standard (48 tasks, 3 runs, weekly), full (all arms, all tasks, 3 runs, gates only).

---

## 7. Architecture

Mapped onto the six harness responsibilities from the survey in the reading list (Observation, Context, Control, Action, State, Verification) so that this system can be compared to others on the same axes. Each component carries the gap it addresses and the hypothesis that justifies it.

```
request
   |
   v
[Intake]---------------> profile: scope, ambiguity, risk, knowledge gap,
   |   (Control, G2)              verification surface, parallelism
   v
[Compiler]-------------> workflow IR: stages with preconditions,
   |   (Control, G1)              exit evidence, guards, budgets, triggers
   v
[Runtime]<--> [Ledger]   (State, G5)  profile, IR, hypotheses, evidence,
   |            budget, checkpoints, decisions
   |
   +--> [Context engine] (Context)  stage brief under a token budget
   |         ^
   |         +-- [Repo model] (Observation, G4) Aider map + edges
   |
   +--> [Host adapter] (Action)  hooks: inject, intercept, block
   |         |
   |         v
   |    coding agent (Claude Code first)
   |
   +--> [Evidence engine] (Verification, G3)  typed claims, contracts,
             |                                 parsers, UNVERIFIED
             v
        [Retrospective] --> proposals --> replay --> promote or reject (G8)
```

### 7.1 Intake and profile (G2)

Six dimensions, each tied to a downstream decision. Seeded from ECC's classifier features (files touched, new dependency, ambiguity) and BMAD's route rule (intent gaps, irreversibles, footprint), then made data-driven: the harness labels every task with its true category, risk, and outcome, so the profiler is trained and validated rather than prompted.

| Dimension | Signal | Decides |
|---|---|---|
| Scope | request features plus repo-model touched-set estimate plus one cheap model call | planning depth, budget |
| Ambiguity | unresolved choices the code cannot settle and the user would notice (BMAD's admission rule) | whether to surface a contract first; research stage |
| Risk | blast radius from repo model, reversibility by change type, domain sensitivity from path and term policy | verification depth, critic, checkpoints, permissions |
| Knowledge gap | memory hits, repo-model coverage, unknown libraries | research stage, model class |
| Verification surface | tests exist, build exists, browser reachable, runtime reproducible | contract composition |
| Parallelism | independent subgraphs in touched set | worktree split |

Each carries a confidence. Low confidence triggers a cheap probe (run the suite once, grep, read one file) rather than a guess. Hard budget on a trivial task: under 5k tokens and ten seconds, or the design is wrong (H16).

### 7.2 Compiler and IR (G1)

A directed graph of stages instantiated from templates that declare preconditions, produced artifacts, required exit evidence, guards, budgets, and invalidation triggers. Borrows the shape of hierarchical task network methods. The IR is data, inspectable and diffable, written to the ledger and shown at start.

```yaml
task: t-2026-09-09-001
profile: {scope: medium, ambiguity: low, risk: {blast: 0.42, reversible: true, domains: [auth]},
          knowledge_gap: low, verification_surface: [tests, runtime], parallelism: none}
budget: {tokens: 400000, usd: 6.00, wall_minutes: 40}
stages:
  - id: reproduce
    template: debug.reproduce
    exit: {evidence: [runtime.failing_repro], repeat: {runs: 20, min_failures: 3}}
    on_exit_fail: {recompile: true, hint: not-reproducible}
  - id: hypothesize
    needs: [reproduce]
    exit: {artifact: hypotheses, min: 2, each_with: [prediction, discriminating_test]}
  - id: isolate
    needs: [hypothesize]
    exit: {evidence: [runtime.root_cause_demonstrated]}
    output_schema: {file, symbol, line_range, intended_behavior}   # AutoCodeRover's grounded contract
  - id: fix
    needs: [isolate]
    guard: {allow: ["src/auth/**", "tests/auth/**"], deny: ["migrations/**", "**/*.lock"]}
    exit: {evidence: [test.regression_added, diff.within_guard]}
  - id: verify
    needs: [fix]
    contract: [test.regression_passes, test.suite:tests/auth, static.typecheck,
               runtime.repro_stable:{runs: 50, max_failures: 0}]
    critic: {when: "risk.blast > 0.3", role: concurrency reviewer, fresh_context: true,
             ordering: blind_then_claims}   # BMAD
invalidate_when: [evidence CONTRADICTED, edit outside guard, ambiguity increases, budget +20%]
```

Passes: template selection, elision (drop stages whose preconditions already hold), verification insertion from risk, guard synthesis from the touched set, parallel split, budget allocation. Five templates at M1: trivial-change, small-feature, bugfix, risky-change, research-needed. Template count is a tracked metric; each new one must win a hypothesis.

**The natural-language alternative.** The Natural-Language Agent Harnesses paper reports comparable performance with much shorter policy documents when the harness is an editable natural-language document interpreted by a runtime. H19 tests structured IR against that on the same runtime. This is a real fork in the design and it is measured, not assumed.

### 7.3 Runtime and ledger (G5)

The ledger is a directory or SQLite database per task holding profile, IR, current stage, hypotheses, evidence, budget consumption, checkpoints, and decisions. The runtime, entirely through hooks:

- `UserPromptSubmit`: intake, compile, inject the stage brief as `additionalContext`
- `PreToolUse`: scope guard, destructive-command guard, secret guard, budget check, deny with a one-line reason
- `PostToolUse`: parse test, build and lint output into evidence records; truncate floods to a file pointer
- `PostToolBatch`: budget enforcement and forced replan point (new in v0.2; not known in v0.1)
- `TaskCompleted`: block marking a task done without its evidence (new in v0.2)
- `Stop`: contract check; block with the specific missing items; after a bounded count, return UNVERIFIED rather than looping
- `SubagentStart` and `SubagentStop`: inject the critic role spec; merge its findings under a JSON contract
- `PreCompact` and `SessionStart(compact)`: persist and re-inject the brief

Hook output must use `additionalContext` JSON or exit 2. Plain stdout on exit 0 goes to the debug log and never reaches the model, a fact recorded in the host card that would otherwise have cost days.

Loop detection fingerprints actions, **with an exemption for stages that declare repeated execution**, because OpenHands' stuck detector demonstrates the failure mode: three identical test runs is a loop during implementation and a measurement during flaky-bug reproduction.

### 7.4 Repository model (G4)

Do not build what exists. Wrap Aider's `repomap.py` (Apache-2.0, self-contained, needs `grep_ast`, `networkx`, `diskcache`) as a retrieval tool with attribution, and fix its two documented weaknesses: the unfiltered word-bag identifier hints, and the memo staleness in non-auto refresh modes. Then add, and measure separately, only the edges it lacks:

- test-to-source mapping by import, naming convention, and coverage data when available
- import and dependency edges, git churn, ownership
- a blast-radius scalar, validated against observed regressions across all harness runs (H13, AUC at least 0.7 or the scalar is dropped and risk falls back to policy rules)

Continue's incremental tag and cacheKey framework is the reference design for keeping this fresh across branches if the naive cache proves inadequate.

### 7.5 Evidence engine (G3)

Claim types with contracts that scale by risk tier:

| Claim | Low risk | High risk adds |
|---|---|---|
| bug_fixed | regression test added and passing; related suite passes | reproduction shown failing first; repeat-run stability; critic review |
| feature_implemented | feature tests pass; build and typecheck clean | integration tests; browser evidence for UI; scope within guard |
| refactor_preserving | relevant suite passes; diff within guard | mutation score not worse; public API diff empty |
| migration_safe | applies and reverts on a fresh database | seeded database; rollback tested; data-shape assertions |
| performance_improved | before and after benchmark | repeated runs with variance; secondary benchmark no regression |
| cannot_complete | reason plus what was tried | evidence that the blocker is real |

`cannot_complete` is a first-class claim type. The Confident and Wrong study's central finding is action bias: models edit when abstaining is correct. A system that cannot express "this should not be done as asked" will produce the same failure.

Evidence records carry kind, identity, before and after state, and the run that produced them. Status is VERIFIED, UNVERIFIED, or CONTRADICTED. Confidence is computed from contract coverage, never self-reported; the model's own confidence is recorded separately and scored for calibration.

Capture is by parsing, not by asking: pytest, jest, vitest, go test, cargo test, builds, type checkers, linters, and gstack's working-tree fingerprint so that "tests passed" binds to the bytes on disk.

### 7.6 Intermittency toolkit (G6)

The one gap with no prior art at all, and therefore the clearest differentiator.

- **Repeat runner**: run a command N times, report failure rate with a confidence interval, classify deterministic, flaky, or clean. Wired into the compiler as `repeat: {runs, min_failures}` in a stage's exit condition.
- **Stability contract**: `runtime.repro_stable: {runs: 50, max_failures: 0}` as a discharge condition, so "fixed" for a race means measured stability, not one green run.
- **Instrumentation helpers**: timestamped boundary logging that the runtime can insert and remove around a suspected region, from Superpowers' instrument-then-trace procedure.
- **Hypothesis ledger**: each hypothesis carries a prediction and a discriminating test; a hypothesis whose prediction fails is marked dead and cannot be revisited without new evidence.
- **Loop-detection exemption** for declared repeat stages.

### 7.7 Memory (G7) and learning (G8)

One record schema (kind, scope, statement, source with evidence links, trust, confidence, verification state, supersession, decay, conflicts). Two kinds: facts and procedures. Given that both real implementations in the field report automatic capture failing, the default is: writes are proposals surfaced to the user at task end, and only user-confirmed records enter the store. Automatic promotion is enabled only if H6 shows it beats confirmed-only writes.

Learning is a data problem, not an instruction problem, and it starts at M1 because the harness produces labels from day one:

1. Profiler trained on harness outcomes (task features to true category, risk, and outcome).
2. Template and routing policy changes proposed by the retrospective, then **replayed** on the relevant task subset before promotion. gstack's specialist gating is the working precedent: skip a reviewer with zero findings in ten dispatches.
3. Rule count is a metric that is allowed to decrease.

### 7.8 Security

Trust levels on every context item and tool result. Injection screening on tool output and retrieved content, with flagged content wrapped as quoted data rather than dropped. Destructive-command guard per risk tier. Secret scanning on context packs, diffs and logs. Permission budget compiled from the profile. MCP tool descriptions treated as untrusted.

Reusable pieces exist and are better than anything written from scratch: OpenCode's tree-sitter bash parsing with arity-based patterns, ECC's destructive classifier including heredoc and subshell handling, Continue's `terminal-security` package, gstack's fail-closed hook polarity with a trap backstop, OpenHands' shell-AST policy rails.

### 7.9 Observability (G10)

Start banner: profile with confidences, compiled workflow, context pack summary as counts, budget, cost estimate. One line per stage boundary. End report: evidence ledger, actual versus estimated cost, what was learned, what was proposed for memory. Every decision (stage selected, stage elided, critic spawned, gate blocked, recompile) stores a reason retrievable by an `explain` command. OpenTelemetry export.

### 7.10 Adapters

Three capabilities: inject at a turn boundary, intercept a tool call, block completion. Present natively on Claude Code, Codex CLI, Gemini CLI, and the Cline and Continue CLIs. Degraded path for OpenCode: guards at commit time via a pre-commit check, and the evidence gate as a final tool named in the rules file. The eval reports the host's capability tier next to its numbers.

---

## 8. Hypotheses

Each has an experiment, a metric, a decision rule written before runs, and a stated consequence. Protocols in `experiments/`.

| ID | Hypothesis | Decision rule | If false |
|---|---|---|---|
| H1 | Profile-driven workflow matches fixed process on success and cuts tokens at least 30 percent on trivial and small tasks | Success intervals overlap or better; tokens down 30 percent | Compiler collapses to two templates or is removed |
| H2 | Evidence-gated completion halves the submit-resolve gap versus vanilla | At least 50 percent relative reduction, interval excluding zero | Redesign; if still nothing, evidence engine becomes reporting only |
| H2b | Evidence gating also improves abstention accuracy | Abstention accuracy up, interval excluding zero | Abstention handled by prompt only |
| H3 | Procedures retrieved lazily match loaded skills on success with fewer instruction tokens | No success loss; instruction tokens down 40 percent | Retrieval kept for memory only |
| H4 | Repo-model additions beyond Aider's map give diminishing returns | Keep an edge type only if it improves resolved or regressions with interval excluding zero | Drop the additions; wrap Aider's map alone |
| H5 | A fresh-context critic with blind-then-claims ordering improves regressions on high-risk tasks and only adds cost on trivial ones | Regression reduction on risky, interval excluding zero; no gain on trivial | Critics compiled only where shown, else removed |
| H6 | Confirmed-write memory beats both no memory and automatic capture on multi-session sequences | Best on later-task resolved and cost; zero poisoning incidents | Memory reduced to user-authored facts |
| H7 | Model escalation cuts cost at least 25 percent on low-complexity tasks with no success loss | Cost down 25 percent, success intervals overlap | Routing removed |
| H8 | Instruction adherence falls as instruction length rises | Monotone decline with intervals | The gates-over-text argument weakens; record it |
| H9 | Stage-level context budgets improve success on large repositories | Resolved up, interval excluding zero | Budgets become hints |
| H10 | Recompile triggers improve hard-debugging success versus static plans | Resolved up; strategy loops down | IR becomes static |
| H11 | Evidence-derived confidence is better calibrated than self-report and can drive escalation | Lower Brier; escalation arm resolved up | Confidence reported, not used for control |
| H12 | Deterministic scope guards beat prompt instructions at reducing unrelated changes | Guard arm lowest out-of-scope, no success loss | Guard becomes a warning |
| H13 | Computed blast radius predicts observed regressions | AUC at least 0.7 | Drop the scalar; risk from policy rules |
| H14 | Replay-gated learning improves over sessions without regressions | Monotone or flat, no round worse than baseline | Learning reduced to memory proposals |
| H15 | Hypothesis-driven debugging beats a generic fix template on hard debugging | Resolved up, interval excluding zero | Template dropped |
| H16 | Intake on trivial tasks stays under 5k tokens and ten seconds without losing profile accuracy | All three thresholds met | Short requests bypass intake with a heuristic profile |
| H17 | Ledger re-injection survives compaction better than host-native context | Post-compaction errors down, resolved up | Kept as a resume aid only |
| H18 | Bounded candidate search in the fix stage improves bug-fix success at acceptable cost | Resolved up, cost within 2x | Search removed |
| **H19** | A structured IR beats a natural-language harness policy on adherence and tokens | Adherence up or tokens down at equal success | Adopt the natural-language form; the compiler becomes a document generator |
| **H20** | The composition arm beats its best individual part | Resolved up or submit-resolve gap down versus best single framework | Composition dilutes; that result is the case for a selective runtime |
| **H21** | Prediction-before-action calibration predicts the submit-resolve gap | Correlation strong enough to act as a leading indicator | Metric kept for reporting only |
| **H22** | Repeat-run stability contracts reduce false "fixed" claims on flaky bugs | Submit-resolve gap on the flaky subset halved | Toolkit reduced to the repeat runner as a plain tool |

---

## 9. Roadmap

Two phases. Phase 2 is scoped only after Phase 1 numbers exist, because v0.1's twenty-six-week schedule was not credible past week ten.

### Phase 1: prove the thesis (weeks 0 to 12)

**M0, weeks 0 to 3. Harness and baselines.**
Noise floor and MDE published. Three seed repositories with hidden tests and reference solutions. 48-task development set including abstention tasks. Arms V, S, E, K, A, M running headless with trace capture. Composition arm C assembled. Research map, complementarity matrix, failure taxonomy with counts from trace mining.
Gate: baselines for at least five arms with intervals; MDE published; failure taxonomy labeled from real traces; ADR on the paradigm choice.

**M1, weeks 4 to 7. Vertical slice.**
Ledger and IR schemas with validators. Claude Code hook adapter. Evidence parsers for pytest, jest, vitest plus the Stop and TaskCompleted contract checks. Intake with five templates. Aider map wrapped as a tool. Scope guard from the touched set. Loop detection with repeat exemption. Start banner and end report. Profiler v1 trained on M0 labels.
Hypotheses: H1, H2, H2b, H12, H16, H20, H21.
Gate: submit-resolve gap at least halved versus vanilla; tokens on trivial and small tasks down at least 30 percent versus Superpowers; success not worse than either; intake overhead within budget. If H1 fails but H2 holds, the product pivots to an evidence gate that composes with other frameworks, which is still a product.

**M2, weeks 8 to 12. Evidence depth, intermittency, portability spike.**
Risk-scaled contracts. Verification runners: browser, migration simulation, mutation testing. Intermittency toolkit in full. Ephemeral critic with blind-then-claims ordering. Recompile triggers. Context packs with budgets. Security suite v1 and the injection screen. Second host adapter as a two-day spike (Codex first: its hook engine is the closest match).
Hypotheses: H3, H5, H9, H10, H11, H13, H15, H17, H22.
Held-out set frozen at the start of M2.
Gate: regressions down on risky categories; flaky-subset submit-resolve gap halved; critic spawn rate near zero on trivial tasks; gate override rate below the agreed threshold; the dev set runs on two hosts with comparable numbers.

**Phase 1 exit.** Held-out evaluation. The 50-percent removal review: every component listed with its winning hypothesis; components without one are deleted in that milestone. Public release of what survives.

### Phase 2: scoped after Phase 1 (weeks 13 onward)

Candidates in priority order, each contingent on Phase 1 evidence: memory and replay-gated learning (H6, H14); model routing and escalation (H7); repository model edges beyond Aider's map (H4); bounded candidate search (H18); the natural-language harness fork (H19); additional adapters. Scope is set by which Phase 1 gates passed and by how much time M0 to M2 actually consumed.

---

## 10. Attacking this plan

### 10.1 Pre-mortem

| Failure | Likelihood | Mitigation |
|---|---|---|
| The suite cannot detect the effects claimed, so gates are inconclusive | High | MDE published before the suite is sized; effects too small to detect are declared undetectable rather than tested |
| Harness construction eats the schedule | High | Three-week box, smoke tier in week one, benchmark reuse (SWE-bench Pro images, Terminal-Bench), three seed repos not four |
| Intake overhead makes daily use worse | High | H16 is an M1 gate; short requests bypass intake |
| Single engineer, twelve weeks, still too much | High | M1 alone (evidence gate plus scope guard) is a usable product; Phase 2 is deliberately unscoped |
| Cost blows up across eight arms | Medium | Tiered runs, per-run caps, full runs only at gates, cheap model for harness-internal calls |
| The compiler grows a template per week | Medium | Template count tracked; each must win a hypothesis; elision measured |
| Gates annoy users and get disabled | Medium | Gates scale with risk; one-command override with recorded reason; override rate is itself a gate metric |
| Host APIs shift | Medium | Adapter is three capabilities; compatibility test in the smoke tier; two hosts by M2 |
| Overfitting to the dev set | Medium | Held-out frozen at M2, traces withheld until the gate decision is recorded |
| The protected bet is protected past the point of evidence | Medium | It is protected through M3 only, and its protection is recorded so it can be argued about |
| Composition arm is too fiddly to assemble | Medium | It is time-boxed to two weeks; if it cannot be assembled cleanly, that difficulty is itself the finding for G9 |

### 10.2 Critiques and answers

- *"Your profiler is a prompt in disguise."* It is trained and validated against harness labels (H16, G2). Dimensions that cannot be labeled reliably are dropped.
- *"mini-SWE-agent gets 74 percent with 190 lines. Why build any of this?"* Because that number is on a saturated benchmark with documented test flaws, and because it says nothing about the submit-resolve gap, regressions, scope discipline, or risky-change safety. If the harness shows mini matching us on the discriminating suites too, the plan says to delete accordingly.
- *"Aider already has the repo map; Continue already has the index."* Correct, and this plan wraps rather than rebuilds. The measured question is only whether the edges they lack are worth adding (H4).
- *"gstack already has an evidence ledger."* Correct, and it is cited as prior art. The new parts are typed claims, contracts scaled by risk, automatic parsing, and abstention.
- *"Another layer between me and my agent."* Zero configuration by default; intake budgeted; trivial tasks bypass; two visible artifacts. H16 is the gate on this claim.
- *"Hooks are an attack surface."* The runtime reads repository content as data only; its config lives outside the repository; the security suite attacks the runtime's own parsers.
- *"Every framework you studied ended up bloated. Why not you?"* Three defenses, all measurable: the token ratchet in CI (gstack's idea), the template count metric, and the removal review with hypothesis IDs at every gate.

### 10.3 The 50-percent removal test

Applied at M1 and at Phase 1 exit. Current belief about the minimum that keeps most of the value: intake, a two-template compiler, the evidence gate, the scope guard, the end report. Everything else must present a winning hypothesis ID at the review or be deleted.

---

## 11. Mechanics

**Layout.** `docs/research/` (cards, hosts, matrix, map, licenses, reading list, failure taxonomy), `docs/adr/`, `docs/design/`, `eval/` (harness, tasks, seeds, results, MDE), `experiments/` (register plus one directory per hypothesis), `core/` (intake, repo_model, compiler, runtime, context, evidence, memory, security, observe), `adapters/`, `procedures/`, `NOTICE`, `LICENSE`.

**Technology.** Python 3.12 with `uv` for core, harness and adapters: the evaluation ecosystem is Python, tree-sitter bindings are mature, Aider's map is Python, and the MCP SDK is available. A TypeScript shim is acceptable where a host plugin demands it. tree-sitter, SQLite, Parquet, Docker, Playwright, OpenTelemetry.

**Working agreements.** No product code before the M0 gate. Every experiment's protocol committed before its first run. Every subsystem directory carries a `WHY.md` naming its hypothesis and the number it moved. Dev set versioned; held-out never edited after freezing. Smoke tier before any merge.

**License and attribution.** Apache-2.0 proposed (ADR-005). `NOTICE` lists every reused file with origin, commit, and license; every reused file carries a provenance header. AutoCodeRover is ideas-only. Anthropic guidance bundled inside Superpowers is not redistributed. BMAD trademarks are not used.

---

## 12. Decisions owed

| Question | Needed by | Default if unanswered |
|---|---|---|
| Monthly evaluation budget | week 1 | Smoke daily, standard weekly, full at gates |
| Public from day one or at Phase 1 exit | week 2 | Private until M1 numbers exist |
| Model pinned for the first evaluation series | week 1 | Most capable generally available model the host supports, pinned by ID |
| Human labeling capacity for the failure taxonomy and quality rubric | week 2 | The engineer labels; a model proposes |
| Whether to include Terminal-Bench (adds environment setup cost) | week 2 | Include; it is the only discriminating environment-heavy suite found |
| Second host: Codex or Gemini | week 8 | Codex, closest hook engine |

---

## Appendix A: evidence trail

| Document | Contents |
|---|---|
| `docs/research/cards/*.md` | Fourteen source-read cards: superpowers, ecc, spec-kit, gstack, bmad, aider, opencode, cline, continue, swe-agent (with mini), openhands, agentless-autocoderover |
| `docs/research/hosts/*.md` | claude-code, codex-cli, gemini-cli: extension surfaces, hook tables, headless flags, telemetry |
| `docs/research/competitor-map.md` | One table over twelve axes, structured on the six harness responsibilities |
| `docs/research/complementarity-matrix.md` | Strength inventory by mechanism type, sixteen weakness classes, the cross-map, ten residual gaps, the composition recipe with its conflicts |
| `docs/research/licenses.md` | Per-system obligations and caveats |
| `docs/research/reading-list.md` | Benchmarks, the submit-resolve gap study, harness-design literature, the instruction-file study, with what each changes here |

## Appendix B: glossary

- **Submit-resolve gap**: fraction of completion claims that do not survive hidden checks. Headline metric, definition from the Confident and Wrong study.
- **Task profile**: six dimensions with confidences that determine the compiled process.
- **Workflow IR**: the compiled stage graph, data not prose.
- **Task ledger**: external task state the runtime maintains.
- **Evidence contract**: the evidence kinds a claim type requires at a risk tier.
- **Claim**: a typed completion statement evaluated VERIFIED, UNVERIFIED, or CONTRADICTED. Includes `cannot_complete`.
- **Blast radius**: computed scalar for how much a change can affect, validated against observed regressions.
- **Stability contract**: an exit condition requiring N runs with at most K failures.
- **Protected bet**: the one component guaranteed a full trial through M3.
- **Composition baseline**: Arm C, best-of-breed pieces stacked and measured.
