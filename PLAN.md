# Master Plan v0.6

2026-09-11. Amends v0.5 after an external critique corrected the diagnosis behind it.

v0.5 concluded from twelve real bugs that a runtime watching one agent cannot reach
an oracle strong enough to matter. That conclusion rested on one task read wrongly:
the agent was said to have misunderstood the issue, when in fact its answer for the
reported case was right and it simply failed to generalise to `DateTime` and to the
variadic path. The claim was made from the agent's own test without reading the
answer key, which is the error this project keeps repeating.

Auditing all seven failures, **six are recoverable from what a runtime can observe**.
Only one needs a decision a person has to make.

| What v0.5 said | Corrected |
|---|---|
| The failures require unknowable intent | Six of seven do not. They are incomplete generalisation, unprobed edge cases, and preservation properties |
| The oracle must not be the agent | Still true, but the useful form is narrower: **a passing test must never promote an interpretation into a requirement** (§5b) |
| Mutation score is the next oracle | Killed before building: the failing agents write strong tests. Replaced by three mechanisms measured separately (§6, M2.5) |
| The gate refuses the stop | Conflates ending computation with certifying completion, and produced loops where the missing ingredient was information. Five distinct outcomes instead (§5c) |
| SWT-Bench doubles precision | With about 20 percent recall. Filtering, not resolution |

---

## v0.5 preamble, retained

2026-09-10. Amends v0.4 after the first fair comparison returned a null and the
literature explained why. The change is to the thesis itself, not to a policy.

| What v0.4 assumed | What twelve real bugs showed | v0.5 |
|---|---|---|
| Computing completion from evidence is the hard part | The evidence can be written by the agent being judged, so computing over it changes nothing. Identical outcomes in both arms, 1.4x cost | The thesis gains a second clause: the oracle must not be the agent (§2) |
| Obligations differ by what they require | They differ by **whose word they take**, which v0.4 never asked | Every obligation is graded by its oracle (§5b), and two of the four in the default set turn out to be the agent's own |
| Reproduction-first is the fix for self-confirmation | Fowler measured no difference; the agent implements ahead so the test never goes red, and a reproduction encoding a misunderstanding still goes red to green | Kept as process evidence, demoted as a correctness claim (§11b) |
| M3 repository model comes next | An inert gate does not benefit from finer invalidation | M2.5 independent oracles comes first (§6) |

---

## v0.4 preamble, retained

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

> **Completion should be computed from dependency-tracked evidence, not asserted by the model — and no expectation may be treated as a requirement on the strength of the agent's own say-so.**

The second clause was bought with a null result on twelve real bugs, and refined after that result was diagnosed wrongly. v0.4's thesis is necessary and was not sufficient: a runtime can compute faultlessly over evidence the agent authored to agree with itself, and that is what this one did, twelve times out of twelve.

The refinement matters. "The oracle must not be the agent" reads as though agent-authored evidence is worthless, which is too strong and would forbid useful things. The operative rule is about **promotion**: an agent may propose an expectation, and its own passing test may not be what turns that proposal into the standard the work is judged against.

Everything is machinery in service of it, and each piece must answer two questions now: if this vanished, would a developer notice their agent got worse — and whose word does it take?

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
| 1 | Process-stage gates enforced by code | partial — Stop gate is code and ledger-driven, and discharges what it can compute; no stage rule such as "reproduce before edit" | done for now |
| 5 | Externalized task state surviving compaction and host switch | partial — the ledger survives compaction; host switch untested on one host | M5 |
| 10 | Decision-level observability | partial — blocks now record which obligation was unmet, which is how M1 was solved; still no record of why a stage ran | done for now |
| 2 | A calibrated task classifier | none | M4 |
| 4 | Repository model with test edges and a blast-radius number | none | M3 |
| 7 | Memory write gating that produces useful records | none | M6 |
| 8 | Replay-gated learning | machinery exists (`eval/replay.py`), feature does not | M6 |
| 9 | **Composition without dilution** | baseline built and censused; benefit untested for want of a discriminating suite | M2, M4 |

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
| Live blocking | 12 percent of runs, down from 75, nothing stable regressed | `python -m eval.live --arm gate --model haiku` |
| Tests | 339 | `python -m pytest tests -q` |

About 2,400 lines of runtime, 1,600 of evaluation, 1,200 of tests.

**Not built**

One host. No repository model. No composition. M1 added profiles, a project config, a status command and self-discharge, so the gate is no longer the only thing a user ever sees.

**Against the field**, from the research cards: Superpowers is 195 files and 14 skills across 11+ hosts; ECC is 3,538 files, 286 skills, 68 agents, 94 commands, 16 install targets. We are roughly one to two percent of ECC by surface. We are the only one that computes completion. Both facts are true and the second does not excuse the first.

---

## 5. What the live runs changed about the design

The gate stopped 7 of 8 runs on one model and 12 of 16 on another, and on nearly all of them a plain agent had already resolved the same task. It roughly doubles turns and multiplies cost by 2.5 to buy evidence for work that was mostly already correct.

That is the design working as specified — "probably correct" is exactly what the thesis refuses — and it is also the behaviour most likely to get the tool switched off. Both readings are right, which means the design is missing a channel rather than being wrong.

**Three channels, not one.**

| Channel | When | Cost | Status |
|---|---|---|---|
| **Guide** | after the first source edit: what would prove this work | tokens only, no interruption | built; measured, no effect on blocking |
| **Compute** | at the end: run what the project declared and record the result | seconds, no tokens | built; this is what worked |
| **Report** | at the end, always | a few lines | built |
| **Gate** | at the end, when obligations are unmet | an interruption and a re-run | built |

That hypothesis was P14, and it was wrong: guidance moved blocking from 12 of 16 runs to 14, and the transcripts confirm the text reached the agent. What the decision records then showed is that in all fifteen blocked runs the agent had written a test and run it, and never run the whole suite, because that is a second invocation of the same tool.

So the gate was solving it backwards. Blocking to make an agent run a command costs another turn at 2.5x the tokens; running the command costs seconds and none. The runtime now runs the commands a project declared and computes the missing evidence itself, which took blocking from 75 percent of runs to 12.

**Profiles, taken from ECC.** `off` records only; `guide` never blocks; `strict` blocks as today. Which is default is decided by M1's measurement, not by taste. This is the method the project is supposed to use: our weakness class covered by another system's strength.

---

## 5b. Every obligation, graded by whose word it takes

The axis v0.4 never asked about. An obligation is worth checking only if the
thing that decides pass or fail is not the agent being judged.

| Obligation | Oracle | Independent? | What it is actually worth |
|---|---|---|---|
| `suite_green` | the project's existing tests | **yes** | real, but blind to the new bug by definition: if the suite covered it, it would not be a bug |
| `build_ok`, `typecheck_ok` | the compiler | **yes** | real, and narrow |
| `stable` | this runtime's repeat runner | **yes** | real, and only applies to nondeterminism |
| `test_added` | a test the agent wrote after deciding it was done | **no** | evidence that a test exists, nothing more |
| `reproduced` | a test the agent wrote, in a verified red-to-green order | **no** | process evidence: it did verify something. Not a correctness oracle |
| `runtime_ok` | the agent's reading of its own output | **no** | the weakest thing in the table |
| **mutation score over changed lines** | the code itself | **yes** | proposed. A test that survives every mutant asserts nothing about the change |

Two of the four obligations in the default `bug_fixed` set are the agent's own
word, and the two that are not are blind to the bug. That is the whole
explanation of the null, and it was visible in this table before the measurement,
had the table existed.

**Standing rule from here.** A new obligation must name its oracle, and every
expectation must record where it came from:

| Origin of an expectation | What it establishes |
|---|---|
| An explicit user example, or an approved acceptance criterion | a directly specified requirement |
| An applicable existing contract: documentation, a type signature, an adjacent test | a requirement within that contract's scope |
| The original program's behaviour | what previously happened, which grounds preservation |
| The agent's interpretation | a hypothesis, which needs scrutiny |

**A passing test must never promote an interpretation into a requirement.**
Provenance is necessary and not sufficient, since an agent can cite documentation
incorrectly; a direct example or a mechanically checkable contract deserves more
weight than an inferred reading of prose.

## 5c. Five outcomes, not two

"Refuse the stop" conflates ending computation with certifying completion. When
the missing ingredient is information rather than effort, refusing produces an
expensive loop: measured live, blocking bought extra turns at 1.4 to 2.5 times
the cost and changed no outcomes.

| Situation | What the runtime does |
|---|---|
| Required evidence missing or stale | run the checks it can run itself |
| A grounded expectation is violated | return the counterexample: input, expected, observed, and where the expectation came from |
| A material expectation is ambiguous | ask one concrete question, not "verify more" |
| Budget or environment prevents verification | stop, unresolved, and say so |
| The acceptance protocol is satisfied | issue a certificate scoped to this contract, these checks, this tree |

An agent may end its turn unresolved. It may not report an unresolved result as
verified completion. The certificate means *this artifact satisfied this version
of the contract under these checks in this environment*, which is something a
runtime can actually compute, unlike unrestricted correctness.

---

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

**EXITED 2026-09-09**, after four passes of which two tested wrong ideas.
Blocks on already-correct work fell from 69 percent to 12, turns by a quarter,
cost by 15 percent, and none of the eleven tasks a plain agent always resolves
regressed. Guidance did nothing; what worked was the runtime running the
project's declared commands and computing the missing evidence rather than
blocking to demand it. Full account in `journey/11-usable.md`.

### M2 — The composition baseline

*Gap 9. The yardstick the mission demands, never built.*

Assemble the Section 6 recipe from the complementarity matrix: Superpowers' procedures and handoff scripts, ECC's hard blocks and batched Stop check, gstack's evidence ledger and verify-gate, Aider's repo map, Spec Kit lean commands, BMAD's blind-then-claims review. All MIT or Apache-2.0; attribution in NOTICE.

Measure the conflicts the matrix predicts: three competing routers, two Stop hooks, three reviewer mechanisms, four state directories, and the skill listing truncating under load.

**Exit:** a measured comparison of the stack against vanilla, against its best single part, and against us, on the discriminating suite from M5. If the stack does not beat its parts, composition dilutes, and that finding is the argument for M4.

**BUILT, NOT EXITED, 2026-09-09.** The baseline exists and rebuilds from one
command, so the central claim is testable for the first time. The conflict
census confirms the prediction and sharpens it: nine review mechanisms rather
than three, nine state directories, ~1,038 always-on tokens. Assembling it also
found a hazard the matrix does not mention: superpowers delivers its routing
through a SessionStart injection, so taking its skills without its hooks buys
their whole token cost and none of their behaviour.

The comparison was run on the wrong suite and could not have worked. The plain
arm failed exactly one of sixteen tasks, and it is the task nothing ever
resolves, so no arm had headroom to improve on. Cost is a per-run measurement
and is sound: composition costs 1.4x vanilla tokens and 1.5x wall clock, and the
stack is indistinguishable from its best single part. Benefit is unmeasured.
Full account in `journey/12-composition.md`.

**Blocked on:** a task suite that discriminates, which is now blocking M2 and M5
both, and is therefore the next thing built.

### M2.5 — Establish the contract before judging the implementation

*Twelve real bugs, no effect. Six of the seven failures were reachable, so the
question is which mechanism reaches them, not whether anything can.*

**Two questions, where v0.5 had one.**

- *Contract validity:* what supports this expected behaviour?
- *Implementation validity:* what supports the claim that this patch implements it?

An agent-authored assertion can speak to the second only once the first has
support from somewhere else. Today the runtime asks only the second, and accepts
the agent's answer to the first by default.

**Three mechanisms, measured separately, because they carry different
information.**

| | Mechanism | Costs | What the audit says it would reach |
|---|---|---|---|
| A | Independent checks derived from the issue, frozen before the patch is visible | a model call | the reported case, stated APIs |
| B | **Differential behaviour against the original program** | no model call | preservation properties: `bc32a92c`'s borrowed stream and missing flush |
| C | Probes that distinguish competing interpretations | a model call | generality and edge cases: `762c97ee`'s `DateTime`, `047adef2`'s dedupe, `f316d5cb`'s boundaries |

B is the cheapest and needs no intent at all: a bug fix owes *change the defective
behaviour* and *preserve the rest*, and the original program is the oracle for the
second. The current gate checks only the first.

C produces probes that are **questions with executable inputs**, not tests. Where
the permitted context cannot settle a disagreement the runtime asks one concrete
question — for this input the plausible outputs are A and B, which is intended —
which is far cheaper for a maintainer than reviewing a patch. Two models agreeing
is evidence about their agreement, not about intent; disagreement allocates
attention rather than deciding anything.

**The diagnostic comes before the verifier.** Freeze the twelve candidate patches.
Generate checks from the original code and permitted context only, with the
candidate, the maintainer's fix and the hidden tests withheld. Then run the frozen
checks against all three:

| Observation | Reading |
|---|---|
| rejects the candidate, accepts the maintainer's fix | useful discrimination |
| rejects both | a wrong oracle, an unsupported requirement, or broken infrastructure |
| accepts both | no discrimination between these two |
| rejects a known-good candidate | a false rejection to investigate |

Checks that turn out inconvenient after the gold result is known are **counted,
not discarded**.

**Measured, at minimum:** incorrect patches certified; correct patches rejected;
tasks resolved; unresolved plus clarification burden; and cost per correctly
resolved task. A repair experiment comes only after discrimination is shown, with
a baseline spending the same budget on ordinary extra attempts — otherwise a gain
cannot be told apart from more compute.

**Exit:** each of A, B and C reported separately on the twelve, then the surviving
design assessed on tasks that were never used to develop it. Also audited: for
each failure, whether the hidden expectation was recoverable from the agent's
permitted context at all, since missing information and unused information need
different remedies.

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

**Its prerequisite is the critical path.** A suite that can measure blocks M2's
exit as well as this one, and four rounds of calibration produced a design rule
that turns out to be the field's, arrived at the slow way.

**The rule.** A task measures verification only if **running the existing suite
would catch the fix an agent reaches for first**. Where it would not, no amount
of evidence-gathering helps and the task measures raw capability instead: every
task whose naive fix left the visible suite green was failed identically by a
weak and a strong model, and every task whose naive fix turned it red was failed
by the weak model and resolved by the strong one.

This is SWE-bench's structure under different names. Their FAIL_TO_PASS is the
hidden test; their PASS_TO_PASS is the visible suite that must stay green, which
is exactly what a naive fix has to break. Their validation repeats each instance
to exclude flaky ones, which is the calibration built here. The vocabulary is
adopted rather than reinvented from here on.

**Chasing a 30 to 70 percent band was the wrong target.** These outcomes are not
coin flips: for a given model a trap is either seen or it is not, consistently.
Only the ceiling band is useless. A task the baseline never resolves is prime
headroom provided some arm can overturn it, and one run says whether it can.

**Two instruments, because one is not enough.**

| | For | Cost |
|---|---|---|
| The hand-written suite | fast iteration, per-run metrics such as block rate and cost | ~$2 a pass |
| **Mined real bugs** (`eval/mine.py`) | any milestone claim | CPU time only; no Docker, no install |

The second exists because the population problem has bitten this project three
times: hook payloads, gate scenarios and claim prompts were each written by the
person whose code they graded, and each agreed with it. Tasks written here have
now failed the same way twice more. Real commits carry their own F2P and P2P
sets, so the failure mode is removed rather than guarded against.

The SWE-bench harness needs Docker, which is not available here, but the harness
is not the valuable part. The construction is, and it needs only a repository
with history, a commit touching source and tests together, and a test runner.
`click` supplies 3,362 commits, no dependencies, and 1,982 tests in 6.9 seconds.

**Expect small effects.** The published comparator amplifies visible-pass into
hidden-fail on 1.72 percent of cells for naive retry against 0.11 percent gated,
and needed 9,240 cells for a confidence interval excluding zero. That
corroborates the 252-runs-per-comparison estimate and argues for engineering the
task suite to raise the base rate rather than hoping for a large effect.

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

**Know which kind of metric you have.** A per-run measurement such as block rate, cost or turns gives one observation per run, and sixteen runs can show a large effect. A per-discordant-pair measurement such as resolution only learns from tasks where two arms disagree, and disagreement is bounded by how often the baseline fails. M1 succeeded on the first kind and M2 was mismeasured on the second, one milestone apart.

**Audit whether the answer was reachable.** For every failure, ask whether the
hidden expectation could have been recovered from the context the agent was
allowed. Missing information and unused information need different remedies, and
conflating them produced a withdrawn conclusion: seven failures were called
unknowable intent when six were incomplete generalisation, unprobed edges, or
preservation properties sitting in the repository.

**Quote a result with the number that qualifies it.** SWT-Bench's precision gain
came with about 20 percent recall, and this plan quoted the first without the
second. A citation trimmed in the direction that flatters the design is worse
than no citation.

**Replay before spending.** 241 stored sessions and 36,034 commands cost nothing to grade. Live runs cost money and hours. Every hypothesis states which it needs.

---

## 8. Hypotheses

| ID | Hypothesis | Needs | Status |
|---|---|---|---|
| P1 | Evidence gating halves the submit-resolve gap | ~252 paired runs | **first fair answer: no effect.** 12 mined bugs, identical outcomes in both arms, 0 discordant pairs, 1.4x cost. The obligation set is inert because the agent already does what it asks |
| P2 | The gate does not block work that is already correct | live, ~24 runs | **holds**: 69 percent of runs to 12 percent, after M1 |
| P3 | Claim inference engages when and only when there is work | replay | 21 percent over-claim, 25 percent missed, on 3,557 real turns |
| P4 | Coarse invalidation is not too pessimistic to live with | dogfood | unmeasured (M3) |
| P5 | Gating improves abstention accuracy | live | unmeasured |
| P6 | Stability obligations halve false "fixed" claims on flaky bugs | live, flaky subset | mechanism built, hypothesis unmeasured |
| P7 | Deterministic scope guards beat prompt instructions | live, three arms | mechanism built, 0/0 on 25 cases, hypothesis unmeasured |
| P8a | The layer's own cost is under 5 percent | replay | ~100 ms per call; holds |
| P8b | The work the gate induces is worth its cost | live | 2.5x tokens, 1.5-1.9x turns; worth is undecided (M1, M5) |
| P9 | Obligation-directed work beats template-directed work | live | not started (M4) |
| P10 | Static test-impact invalidation beats coarse | replay | not started (M3) |
| P11 | **Composition of best-of-breed pieces beats its best single part** | live | **half-answered**: costs 1.4x vanilla with no measurable benefit, but the test had no headroom |
| P16 | The layer reduces visible-pass/hidden-fail amplification | live, powered | published comparator: 1.72 percent for naive retry, 0.11 percent gated, over 9,240 cells (arXiv 2607.14890) |
| P17a | Frozen issue-derived checks discriminate the candidate from the maintainer's fix | diagnostic, 12 frozen patches | no runs needed beyond generation |
| P17b | **Differential comparison against the original program** discriminates | diagnostic, no model call | the cheapest, and the audit says it reaches `bc32a92c` |
| P17c | Interpretation probes discriminate | diagnostic, one model call | the audit says it reaches `762c97ee`, `047adef2`, `f316d5cb` |
| P18 | Counterexample-driven repair beats spending the same budget on more attempts | live, after discrimination | the baseline that keeps a gain from being just more compute |
| P12 | Prediction calibration predicts the miss rate | replay | not started |
| P13 | The runtime reads what the host actually sends | replay | **answered**: 174/174 and 5,916/5,916 |
| P14 | Guidance at the moment of work converts blocks into unprompted verification | live, ~24 runs | **rejected**: 12 of 16 blocked became 14; the text reached the agent |
| P15 | The runtime computing the evidence beats blocking to demand it | live, ~24 runs | **holds**: blocking 75 to 12 percent of runs, nothing stable regressed |

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
| Guidance channel | 20 | built; no measurable effect on blocking |
| Config and profiles | 82 | built |
| Self-discharge | 71 | built; the fix that made the gate usable |
| Status command | 66 | built |
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

- **Withdrawn, 2026-09-10.** "Obligations derived from inferred intent, discharged by evidence bound to repository state, invalidated by change, gating completion" is prior art. Proof-or-Stop (arXiv 2607.14890) publishes the same spine — claim, evidence, gate, transition — binds evidence to a `materialHash` over the tracked source tree, and rejects it "the instant the source tree changes". It also names the failure this project was built around, an unattended agent retrying until a visible check turns green. Found while researching how to build a task suite, which is how prior art is usually found. Card in `docs/research/cards/proof-or-stop.md`.
- **What survives, stated narrowly:** evidence captured by parsing tool output the agent already produced, requiring no cooperation from the agent and no process from the user; claims inferred from ordinary intent rather than declared; and invalidation at test-impact granularity rather than whole-tree, which is planned in M3 and therefore a claim about the future, not the present.
- **Withdrawn:** runtime-enforced process stages (AgentLTL), typed claims as such (proof-carrying certificates for LLM pipelines), staleness invalidation as a mechanism (Test Impact Analysis is standard industrial practice).
- **Untested:** that composition of these systems beats its best part. This is P11 and the project's own reason to exist. Claiming it before M2 would be the same error as every number that was true about an invented population.

---

## 11b. The oracle problem, and what it costs this design

The first fair comparison returned a null: twelve mined bugs, identical outcomes
in both arms, 1.4x the cost. The cause is not a tuning error.

`test_added` accepts a passing test the agent wrote after deciding its fix was
correct, so the test asserts whatever the fix does. `suite_green` is an
independent oracle but does not cover the bug, which is why the bug existed. So
every obligation the gate checks is either satisfied by what the agent does
anyway, or blind to the thing that is wrong.

The field has measured this. Agent-written test volume does not change outcomes
(arXiv 2602.07900). LLM assertions encode actual rather than expected behaviour
(arXiv 2606.18168, 86,156 test patches), with no semantic remedy proposed. And
TDD inside the agent loop showed no discernible difference in outcome quality in
Fowler's experiment, with the agent implementing ahead of its own test so that it
never went red.

**Reproduction-first was the obvious fix and it is not sufficient.** Verifying a
red-to-green transition does catch implement-ahead, which instructing TDD does
not. It leaves the oracle in the agent's hands: a reproduction test encoding a
misunderstanding fails, then passes against a fix that implements the same
misunderstanding.

**The design consequence.** An obligation is only worth checking if its oracle is
not the agent. Of the sources available to a runtime watching one agent, mutation
score over the changed lines is the cheapest: mutate what changed, run the tests
the agent wrote, and see whether they notice. A test that survives every mutant
asserts nothing about the change. This is P17, and it is measurable on the same
twelve bugs. Card: `docs/research/cards/agent-authored-oracles.md`.

---

## 12. What would falsify the project

- **P11 fails and M4 does not recover it.** If the stack does not beat its parts and selection does not beat the stack, composition was not the opportunity.
- **P1 already failed once, on the obligation set of the day.** Twelve mined bugs, zero discordant pairs. That falsifies the v0.4 obligation set rather than the thesis, and the distinction is only honest if the replacement is measured on the same tasks rather than argued for.
- **All three mechanisms fail to discriminate.** If frozen issue-derived checks, differential comparison against the original program, and interpretation probes all accept the candidate and the maintainer's fix equally, then a layer watching one agent cannot tell good work from bad, and the product is a reporting tool rather than a gate.

  v0.5 asserted that outcome from a single misread task. It is still possible and it is no longer the expectation: six of the seven failures were recoverable, which is an argument that the mechanisms have something to find. The honest version is that **the diagnostic decides this, not the prose**.
- **P2 cannot be fixed.** If guidance does not cut blocking, the gate is a tax on correct work and belongs behind `strict` rather than on by default.

If P1 holds and P2 is fixed, the product exists. If P1 holds and P2 does not, the idea is right and the policy is wrong, which is tuning. The order in §6 puts the cheap, falsifying measurements first for that reason.

---

## Appendix: evidence trail

`docs/research/` holds the source study unchanged: fourteen source-read cards at recorded commits, three host cards, the competitor map, the complementarity matrix with its sixteen weakness classes and ten residual gaps, the licence register, and the annotated reading list. `journey/` holds ten phases of what was tried, what was wrong, and what the measurements said. Every number in this plan is reproducible from a command in this repository.
