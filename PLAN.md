# Master Plan v0.4

2026-09-09. Supersedes v0.3, which superseded v0.2 (research-grounded but lab-shaped) and v0.1 (written from memory). The research in `docs/research/` is unchanged and still governs; v0.4 is the first plan that actually obeys it.

What changes here is direction. v0.3 reduced the project to a single mechanism and postponed everything else, including the goal the project was started for. That was the right opening move and the wrong place to spend ten phases.

---

## 0. Why v0.3 needed replacing

Each item below is a correction forced by a measurement, not a change of taste. The evidence is in `journey/` and reproducible from this repository.

| What v0.3 said | What happened | v0.4 |
|---|---|---|
| Seven core pieces, everything else postponed | Ten phases inside the 90/10. Two of the ten residual gaps built, five untouched, including composition, which is the project's stated purpose | The ten residual gaps become the backlog (§3), with a milestone owning each |
| "The system must beat the composition baseline" (research §6) | The baseline was never assembled, so the central claim is untestable | The baseline is M2, before any claim of superiority (§6) |
| Noise floor measured in week one | Skipped. Three live comparisons run first; two identical passes then scored 69 and 94 percent | The noise floor is a gate, not an intention (§7) |
| False-block rate under 5 percent | 0 percent on constructed scenarios; live, the gate blocked 7 of 8 then 12 of 16 first stops, nearly all on already-correct work | P2 is redefined against observed behaviour, and the gate gains a guidance channel (§5) |
| P8: under 10 percent tokens, under 5 seconds | The layer costs ~100 ms per call. The work it induces costs 2.5x tokens. One target cannot cover both | P8 splits into layer cost and induced cost (§8) |
| Micro tier: 10 tasks, 1 run, minutes | P1 needs ~252 agent runs per comparison to reach 0.05 at 80 percent power | Every hypothesis carries its power requirement (§7) |
| Nine core pieces, all mechanism | No config, no override, no status command, one host. Installing it yields something that interrupts and is otherwise invisible | Product surface is a first-class milestone (§5) |

---

## 1. What this is

Unchanged and still correct.

It is not a framework: it prescribes no process the user must learn. It is not an agent: it never acts. It is not a harness: it does not own the loop. It watches an agent work, decides what would constitute proof that the work is done, collects that proof from what the agent already runs, tracks which proof is still valid as the code changes, and computes a completion state the agent cannot assert.

The closest analogue is `make`. `make` does not build software; it knows what depends on what, notices when something is stale, and refuses to call a target up to date when its inputs have changed. It converts "is this built?" from an opinion into a computation.

**Working description: an incremental verification layer for coding agents, and a runtime that selects which verification is worth doing.** The second half is new in v0.4 and is where composition lives.

---

## 2. The thesis

> **Completion should be computed from dependency-tracked evidence, not asserted by the model.**

Unchanged. Everything is machinery in service of it, and each piece must answer: if this vanished, would a developer notice their agent got worse?

Ten phases add one corollary, learned the hard way:

> **A verification layer that cannot verify itself is worthless.** Three of its components shipped doing nothing, and each was found by measurement rather than review.

---

## 3. The mission, restored

The project's first goal, stated by the user before any code existed: **combine the strengths of the studied systems so that each one's weakness is covered by another's strength, then add what none of them has.**

`docs/research/complementarity-matrix.md` did that mapping across fourteen systems, sixteen weakness classes, and ten residual gaps. Those gaps are "the only places where new architecture is justified". They are the backlog. Nothing else is.

| # | Residual gap | Status | Milestone |
|---|---|---|---|
| 3 | Typed claims, risk-scaled evidence contracts, automatic capture | **built** | done |
| 6 | Tooling for intermittent and concurrency bugs | **built** — runner and derived run counts; no instrumentation helpers, no hypothesis ledger | M4 completes |
| 1 | Process-stage gates enforced by code | partial — Stop gate is code and ledger-driven; no stage rule such as "reproduce before edit" | M1 |
| 5 | Externalized task state surviving compaction and host switch | partial — the ledger survives compaction; host switch untested on one host | M5 |
| 10 | Decision-level observability | partial — blocks, scope questions, claim openings recorded; not why | M1 |
| 2 | A calibrated task classifier | none | M4 |
| 4 | Repository model with test edges and a blast-radius number | none | M3 |
| 7 | Memory write gating that produces useful records | none | M6 |
| 8 | Replay-gated learning | machinery exists (`eval/replay.py`), feature does not | M6 |
| 9 | **Composition without dilution** | **none** | M2, M4 |

Two of ten built. The single most novel gap is done; the one the project exists for has not been started.

---

## 4. Where we actually are

Honest, reproducible, and unflattering in the places it should be.

**Built and measured**

| Piece | Result | Command |
|---|---|---|
| Evidence capture and provenance | 174/174 failing and 5,916/5,916 passing commands read correctly, over 36,034 real commands | `python -m eval.replay --all` |
| Completion gate as a classifier | 0 percent false blocks, 0 percent misses on 46 scenarios | `python -m eval.run --all` |
| Scope guard | 0 false questions, 0 misses on 25 cases | `python -m eval.scope_run` |
| Claim inference | 21 percent over-claim, 25 percent missed work over 3,557 real turns; 31/31 labelled | `python -m eval.claims_run` |
| Host integration | six checks | `python plugin/bin/ep_doctor.py` |
| Live operation | the gate fires, refuses the stop, the agent does more work | `python -m eval.live` |
| Tests | 291 | `python -m pytest tests -q` |

About 2,400 lines of runtime, 1,600 of evaluation, 1,200 of tests.

**Not built**

One host. No configuration of any kind. No override. No status command. No repository model. No composition. The gate is the only thing a user ever sees, and it appears only to say no.

**Against the field**, from the research cards: Superpowers is 195 files and 14 skills across 11+ hosts; ECC is 3,538 files, 286 skills, 68 agents, 94 commands, 16 install targets. We are roughly one to two percent of ECC by surface. We are the only one that computes completion. Both facts are true and the second does not excuse the first.

---

## 5. What the live runs changed about the design

The gate stopped 7 of 8 runs on one model and 12 of 16 on another, and on nearly all of them a plain agent had already resolved the same task. It roughly doubles turns and multiplies cost by 2.5 to buy evidence for work that was mostly already correct.

That is the design working as specified — "probably correct" is exactly what the thesis refuses — and it is also the behaviour most likely to get the tool switched off. Both readings are right, which means the design is missing a channel rather than being wrong.

**Three channels, not one.**

| Channel | When | Cost | Status |
|---|---|---|---|
| **Guide** | after the first source edit: what would prove this work | tokens only, no interruption | to build, M1 |
| **Report** | at the end, always | a few lines | built |
| **Gate** | at the end, when obligations are unmet | an interruption and a re-run | built |

The hypothesis is that the gate fires so often because obligations are stated at prompt time and forgotten by the end. Guidance at the moment of work should convert most blocks into work the agent does unprompted. That is P14 and it is cheap to measure, because block rate is observed on every run rather than only on discordant pairs.

**Profiles, taken from ECC.** `off` records only; `guide` never blocks; `strict` blocks as today. Which is default is decided by M1's measurement, not by taste. This is the method the project is supposed to use: our weakness class covered by another system's strength.

---

## 6. Milestones

Each has an exit criterion that is a command and a number. **The plan is followed by taking the next unmet exit criterion.** No milestone starts before its predecessor exits, except where marked parallel.

### M1 — Make it usable

*Gap 1, 10. The tool currently interrupts most turns and is otherwise invisible.*

- Guidance channel: after the first source edit, inject the obligations for the open claim.
- Profiles `off` / `guide` / `strict`, and a project config naming the commands this repository uses for tests, build and typecheck.
- `ep status`: what the runtime currently believes, on demand.
- Record *why* the gate blocked, not only that it did.

**Exit:** on 24 live runs, blocks on already-correct work fall below 25 percent of runs, with resolution no worse than the same suite without guidance. `python -m eval.live --arm guide,strict`.

### M2 — The composition baseline

*Gap 9. The yardstick the mission demands, never built.*

Assemble the Section 6 recipe from the complementarity matrix: Superpowers' procedures and handoff scripts, ECC's hard blocks and batched Stop check, gstack's evidence ledger and verify-gate, Aider's repo map, Spec Kit lean commands, BMAD's blind-then-claims review. All MIT or Apache-2.0; attribution in NOTICE.

Measure the conflicts the matrix predicts: three competing routers, two Stop hooks, three reviewer mechanisms, four state directories, and the skill listing truncating under load.

**Exit:** a measured comparison of the stack against vanilla, against its best single part, and against us, on the discriminating suite from M5. If the stack does not beat its parts, composition dilutes, and that finding is the argument for M4.

### M3 — The repository model

*Gap 4, and the strength most worth taking from another system.*

Lift Aider's `repomap.py` (Apache-2.0): tree-sitter tags, file graph, personalized PageRank, token-budgeted render. Add what it lacks and what this project needs: **test-to-source edges and a blast-radius number.**

This is not for finding code, which is a crowded space. It is to compute what a change invalidates, turning `observed` from every source file into the import closure of each test. Coarse invalidation stales everything on one edit and has never been measured in daily use.

**Exit:** P4 and P10 measured. Static invalidation stales measurably less than coarse on real edits, with no evidence wrongly kept fresh. Test-impact analysis' safety rule holds throughout: when the map is missing or stale, fall back to full.

### M4 — Selective composition

*Gap 2, 9, and the completion of 6.*

If M2 shows that stacking dilutes — which the matrix predicts, with three routers all over-routing trivial work — then the thing worth building is a runtime that chooses which piece runs for this task. That is the calibrated classifier (gap 2) and the workflow compiler under its proper name.

Labels come from the evaluation harness, not from prose. The feature set starts from ECC's size-to-ceremony table and BMAD's route-after-investigation rule, both already specified in the matrix.

**Exit:** the selective runtime beats the M2 stack on the discriminating suite, at lower token cost than loading everything.

### M5 — Answer P1

*The thesis, properly powered.*

Requires first: a task suite where most tasks discriminate. Eleven of the current sixteen are resolved by a plain agent every time and carry no information.

**Exit:** ~252 paired runs per comparison, McNemar p reported with the ceiling stated up front. A result either way is a result; an underpowered one is not.

### M6 — Memory and learning (parallel, low priority)

*Gaps 7, 8.* Both real implementations in the field report automatic capture failing. Writes only as proposals from a retrospective, with evidence links, validated by replay before promotion. Not started until M1 to M4 exit.

---

## 7. Measurement discipline

Ten phases produced four instances of the same failure. These rules exist so there is not a fifth.

**Every metric names its population.** Three separate measurements were true about a population invented by the person being graded and false about the real one: hook payloads written by hand agreed with the code because both shared one wrong assumption; the gate scored 0 percent false blocks on a suite containing no conversations; claim inference looked fine until it met 3,557 real prompts. A number without a stated population is not reportable.

**Prefer ground truth the author did not write.** The host records whether a command failed. A hidden test decides resolution. A turn's own behaviour says whether work happened. Where such a signal exists, use it and say it is a proxy where it is one.

**The noise floor is measured before any comparison.** Two identical passes disagreed on a quarter of the suite. Skipping this cost three comparisons and about $12. `python -m eval.noise` reports the flip rate and sorts tasks by whether they discriminate at all.

**State the ceiling before the p-value.** An arm can only overturn tasks the baseline failed. A run that cannot reach significance however well it goes is a pilot, and `eval/analyse.py` says so before it says anything else.

**Hold a set back, and expect it to hurt.** The tuned score was 0 percent; the held-out score was 43. Fresh cases guard against overfitting to the cases; they do nothing about overfitting to the *kind* of case you think to write, which is why the population rule comes first.

**Silence must leave a trace.** Three components failed by doing nothing. Anything unreadable is appended to a blind-spot log, the hook subscription is generated from the constants the handlers use, and `ep-doctor` exercises the join rather than either half.

**Replay before spending.** 241 stored sessions and 36,034 commands cost nothing to grade. Live runs cost money and hours. Every hypothesis states which it needs.

---

## 8. Hypotheses

| ID | Hypothesis | Needs | Status |
|---|---|---|---|
| P1 | Evidence gating halves the submit-resolve gap | ~252 paired runs | **unanswered**; noise floor exceeds the effect (M5) |
| P2 | The gate does not block work that is already correct | live, ~24 runs | **failing**: 7/8 then 12/16 first stops blocked, nearly all already correct (M1) |
| P3 | Claim inference engages when and only when there is work | replay | 21 percent over-claim, 25 percent missed, on 3,557 real turns |
| P4 | Coarse invalidation is not too pessimistic to live with | dogfood | unmeasured (M3) |
| P5 | Gating improves abstention accuracy | live | unmeasured |
| P6 | Stability obligations halve false "fixed" claims on flaky bugs | live, flaky subset | mechanism built, hypothesis unmeasured |
| P7 | Deterministic scope guards beat prompt instructions | live, three arms | mechanism built, 0/0 on 25 cases, hypothesis unmeasured |
| P8a | The layer's own cost is under 5 percent | replay | ~100 ms per call; holds |
| P8b | The work the gate induces is worth its cost | live | 2.5x tokens, 1.5-1.9x turns; worth is undecided (M1, M5) |
| P9 | Obligation-directed work beats template-directed work | live | not started (M4) |
| P10 | Static test-impact invalidation beats coarse | replay | not started (M3) |
| P11 | **Composition of best-of-breed pieces beats its best single part** | live | **not started (M2)** — the mission's own test |
| P12 | Prediction calibration predicts the miss rate | replay | not started |
| P13 | The runtime reads what the host actually sends | replay | **answered**: 174/174 and 5,916/5,916 |
| P14 | Guidance at the moment of work converts blocks into unprompted verification | live, ~24 runs | new (M1) |

---

## 9. The core, and what it still lacks

| Piece | Lines | State |
|---|---|---|
| Evidence parsers | 373 | built, 17 percent of real commands produce evidence |
| Provenance and staleness | 171 | built, coarse only |
| Claim inference | 90 | built, measured on real prompts |
| Obligation table | 259 | built |
| Gate | 343 | built, over-fires |
| Scope guard | 153 | built |
| Repeat runner | 120 | built |
| Report | 147 | built, end-of-turn only |
| Host contract | 393 | built after three defects |
| **Guidance channel** | — | **M1** |
| **Config and profiles** | — | **M1** |
| **Repository model** | — | **M3** |
| **Selection runtime** | — | **M4** |

---

## 10. Postponed, with triggers

| Postponed | Trigger |
|---|---|
| Context engine with budgets | Large-repository tasks fail on context, measured |
| Model routing | Cost becomes a real complaint; hosts already route |
| Critics and subagents | Regression rate on risky changes stays high with the gate on |
| Second host adapter | M1 exits, or someone asks. Codex first: closest hook engine |
| Browser evidence | A UI claim type is needed. gstack's Playwright daemon is MIT and liftable |
| Reconstructing repository state from transcript file-history rows | Replay needs to measure freshness, which it currently cannot |
| Subagent transcript replay | Subagent work is gated. 1,290 such transcripts already exist |

---

## 11. Novelty claims

Standing rule unchanged: a novelty claim names the search that failed to find prior art.

- **Bounded and standing:** obligations derived from inferred intent, discharged by automatically captured evidence, invalidated by repository change, gating completion of a general coding agent, was not found among the fourteen systems surveyed. Nearest instances are gstack's single-command working-tree fingerprint and Test Impact Analysis applied to test selection.
- **Withdrawn:** runtime-enforced process stages (AgentLTL), typed claims as such (proof-carrying certificates for LLM pipelines), staleness invalidation as a mechanism (Test Impact Analysis is standard industrial practice).
- **Untested:** that composition of these systems beats its best part. This is P11 and the project's own reason to exist. Claiming it before M2 would be the same error as every number that was true about an invented population.

---

## 12. What would falsify the project

- **P11 fails and M4 does not recover it.** If the stack does not beat its parts and selection does not beat the stack, composition was not the opportunity.
- **P1 fails when properly powered.** The thesis is wrong and no amount of the rest saves it.
- **P2 cannot be fixed.** If guidance does not cut blocking, the gate is a tax on correct work and belongs behind `strict` rather than on by default.

If P1 holds and P2 is fixed, the product exists. If P1 holds and P2 does not, the idea is right and the policy is wrong, which is tuning. The order in §6 puts the cheap, falsifying measurements first for that reason.

---

## Appendix: evidence trail

`docs/research/` holds the source study unchanged: fourteen source-read cards at recorded commits, three host cards, the competitor map, the complementarity matrix with its sixteen weakness classes and ten residual gaps, the licence register, and the annotated reading list. `journey/` holds ten phases of what was tried, what was wrong, and what the measurements said. Every number in this plan is reproducible from a command in this repository.
