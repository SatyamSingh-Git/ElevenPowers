# The journey

A full record of how this project got from a prompt to a working thing: what was
asked, what was tried, what was wrong, what the measurements said, and what
changed as a result.

It is written so that someone who was not here can reconstruct the reasoning,
including the parts that were mistaken. Every number quoted was produced by a
command in this repository and can be reproduced.

## Read in order

| File | Covers |
|---|---|
| [00-brief.md](00-brief.md) | The original brief, verbatim and unedited — the document everything here is answering, and the one later plans are judged against |
| [01-origins.md](01-origins.md) | The original brief, the first plan written from memory, and why that was the wrong way to start |
| [02-research.md](02-research.md) | Reading fourteen systems from source: method, what each one actually does, and the findings that overturned assumptions |
| [03-architecture.md](03-architecture.md) | Two rewrites of the plan, the pivot from classifying tasks to deriving proof obligations, and what the thing actually is |
| [04-build.md](04-build.md) | Building the first working version, and the three defects that only appeared when it was used |
| [05-measurement.md](05-measurement.md) | Measuring the gate as a classifier: 75 percent false blocks, every fix, and the honest limits of the result |
| [06-intermittency.md](06-intermittency.md) | The flaky-bug gap: a false verification found by reasoning, and the arithmetic that decides how many clean runs are enough |
| [07-scope.md](07-scope.md) | A guard that was dead code, where a task's scope actually comes from, and how the replacement shipped inert too |
| [08-wiring.md](08-wiring.md) | Three defects in the layer nobody had measured, found by reading 36,000 real commands |
| [09-claims.md](09-claims.md) | What real prompts look like, and why the claim has to follow the work |
| [10-live.md](10-live.md) | 89 real agent runs: the mechanism works, the measurement does not, and what an answer costs |
| [11-usable.md](11-usable.md) | Two wrong fixes and a right one: the gate stops interrupting work that was already correct |
| [12-composition.md](12-composition.md) | Assembling the composition baseline the mission is measured against, and mismeasuring with it |
| [13-instrument.md](13-instrument.md) | Four rounds of building a ruler, the rule that decides whether a task measures anything, and the prior art that was there all along |
| [14-null.md](14-null.md) | Twelve real bugs, a fair test at last, a gate that changed nothing, and why the obvious fix is theatre |
| [15-correction.md](15-correction.md) | An external critique, an answer key that should have been read first, and six of seven failures turning out reachable |
| [16-audit.md](16-audit.md) | Sixteen reproduced defects, a grader blind to regressions, a change of objective, and two bad attempts at responding to it |
| [17-preservation.md](17-preservation.md) | Two evaluator defects closed, the hole that fixing the first one opened, and a probe that could never have passed |
| [18-evidence.md](18-evidence.md) | Repairing the foundation: all nine evidence-layer defects, the controls that stop a fix being a removal, and the defect underneath the one that was reported |
| [19-host.md](19-host.md) | The host contract read rather than assumed: a 20-second timeout that was self-inflicted, a shell the runtime never subscribed to, and adversarial verification as a standing requirement |
| [20-reconstructible.md](20-reconstructible.md) | Closing Phase A: a run that survives its workspace, a grader graded against known answers, an exit criterion that was lying, and a live sweep that failed usefully |
| [21-corpus.md](21-corpus.md) | Phase B1: fifteen instances from five repositories, difficulty as a label rather than a filter, and three repositories that contributed nothing without saying why |
| [22-instrument.md](22-instrument.md) | Phase B2 and B3: a score that refuses to run unpinned, an interval over tasks rather than runs, and a taxonomy whose every category can be opened |
| [23-spend.md](23-spend.md) | Phase B4: the four defects a unit test cannot find, a grader asked five questions on somebody else's code, and the first run allowed to cost money |
| [24-move.md](24-move.md) | A corpus of 15 that could not move becomes 49 that can, why its size had been set by a default and an unhandled encoding, and a second agent that uninstalled a package from the machine mid-measurement |
| [25-treatment.md](25-treatment.md) | Two paired chunks and 100 runs: the gate fired on four tasks of twenty-five and changed none of them, and on both tasks where the arms differed it never fired at all |
| [26-access.md](26-access.md) | A second audit: the agents fetched the upstream fix, twelve percent was the wrong denominator, and the hook that “never fired” had asked four scope questions |
| [27-checkpoint.md](27-checkpoint.md) | A passive recorder that captures the candidate at every proposed stop, in both arms — and within four runs, a gate refusing a patch that was already correct |
| [28-nothing-changed.md](28-nothing-changed.md) | Sixteen gated runs: every outcome identical to its own first proposal, four blocks across nineteen runs that changed nothing, and `pip` fetching the answer through a wall that denied `git clone` |
| [29-outside.md](29-outside.md) | Reading the field instead of buying runs: the premise confirmed by independent survey data, the mechanism aimed at freshness when the measured failure is sufficiency, two shipping projects that arrived at stale-on-edit independently, and the answer sitting unbuilt in our own §5.0 |
| [30-reaimed.md](30-reaimed.md) | Five research passes and Master Plan v0.8: 46 percent of agent validation evidence discriminates nothing, the reproduction test is worth +28pp against localisation's +8, the decisive error lands at step 7 of 27 — and both fixes were already written in our own plan, unbuilt. Plus the correction that mattered most: borrowing is the method, so every component now names its prior art, licence and limit before its design |
| [31-forty-two-percent.md](31-forty-two-percent.md) | Phase B2, the first experiment that cost nothing: 42 percent of preserved passing suite records say PASS while holding a failure count, because pytest piped to `tail` exits 0 — and an oracle gap that swings from +4.4 to +20.0 on the same fifteen tasks, on five lucky runs |
| [32-could-not-fail.md](32-could-not-fail.md) | The two-way rule stops being a habit: enforced in code for every runner, and shipped as `core/stress.py` — the runtime now runs each declared check against the pre-change tree and reports the ones that could not have failed |
| [33-which-door.md](33-which-door.md) | The boundary recipe was wrong, `--network none` would have killed the CLI's own API access — and a sharper exposure screen finds 21 of 36 runs handed the fix's own vocabulary, four of them from the machine's site-packages, a door no network policy closes |
| [34-the-ratchet.md](34-the-ratchet.md) | The best proven state kept in a private ref so a later edit cannot lose it — and a guard that closed the registry answer key, broke `pip install -e .`, and had to come back out |
| [35-computed-not-generated.md](35-computed-not-generated.md) | The reproduction obligation stops demanding an ordering and starts asking the old tree: a test red there and green now is a reproduction, whoever wrote it and whenever — and collection errors are the common case, not an edge one |
| [36-the-shelf.md](36-the-shelf.md) | The registry answer key shut: a local shelf of the build backends the corpus declares, so the index can close while an honest `pip install -e .` still works — three of four doors now closed, the fourth measured rather than assumed |
| [37-what-the-fixture-could-not-show.md](37-what-the-fixture-could-not-show.md) | `radius.py` and `atlas.py`, and five defects every one of which a fixture hid and real code exposed: subscripted bases, `Generic` as a false interface, a probe that broke its own parse, a design note counted as the architecture map, and `tests/test_mypy.yml` named as the test to run. Then the sweep's own instrument: a missing base commit blinding 37% of a paid run, a pre-flight that could not see it because it built the ledger itself, and `reproduced` turning out to be `discriminates` reported twice |
| [38-the-null.md](38-the-null.md) | The measurement, finally worth reading, came back **zero**: 0 of 14 checks non-discriminating against the literature's 46%, and B3's single case did not replicate when the other model got the same task. The frequency claim is withdrawn. And the sweep found something that outranks it — **12.5% of runs bypassed the gate entirely**, a 5,396-line patch graded resolved with `ledger.touched` empty |
| [39-the-constraint-that-cost-more-than-it-bought.md](39-the-constraint-that-cost-more-than-it-bought.md) | Pointed at somebody else's repository for the first time and three things broke in an hour: `node --test` produced no evidence at all, the blast radius had nothing to say about 1,463 TypeScript files, and the universality fix briefly let a text file fabricate a passing suite. The zero-dependency rule is kept where it matters and relaxed where it only cost coverage - tree-sitter, optional and guarded, which is what Aider, Continue and OpenCode all reached. And `Error` turned out to be `Generic` all over again, caught by counting real bases rather than by reasoning |
| [40-the-assumption-nobody-ran.md](40-the-assumption-nobody-ran.md) | Four commits that had no entry, and the pattern under all of them: seven defects in one day, every one a format written from memory and none found by thinking harder. It is API Knowledge Conflict, 20.41% of hallucinations in the largest taxonomy - and retrieval fixes 0.87 to 3.05 points of it, so the answer is execution. `core/assumptions.py` asks the ledger two questions it could always have answered: did anything you ran ever produce this pattern, and did that new test pass on the tree as it was. Then what the check cost: the state directory now ignores itself, `core/redact.py` strips credentials by prefix and never by entropy, and a pattern is only reported when its own file names a tool the task ran - three further defects found while paying, every one by running it |
| [41-the-audit-that-reproduced.md](41-the-audit-that-reproduced.md) | An external audit read the tree, shipped fourteen runnable probes, and every one reproduced here byte-for-byte before anything changed. Twelve defects, all one shape: a weaker fact standing in for the claimed one - a test that was *selected* counted as passed, a TAP report that was *read* counted as run, two true facts about different checks counted as one reproduction, and absence from a failure list counted as a pass. Plus the worst one, which was delivery: the architecture brief was suppressed by reading the file first, which is how every edit begins, so a published 47% measured a capability nobody received. Four numbers corrected in public, including one wrong figure that came from a snippet-graded source the rules already warned about |
| [decisions.md](decisions.md) | Every significant decision, its reasoning, and whether it still stands |
| [mistakes.md](mistakes.md) | Every mistake made, what caused it, and what it changed |

## The shape of it, in one page

**The ask.** Build an agentic software engineering system that makes existing
coding agents measurably better, without being another collection of prompts.
Research first, challenge everything, measure, discard weak ideas.

**First attempt, and its flaw.** A 522-line plan was written in about an hour
from recollection of the named projects. It was well organised and largely
unfounded: no repository had been read. Asked directly whether it was the best
possible plan, the honest answer was no, and the reasons were specific.

**Research.** Fourteen systems were cloned and read from source at recorded
commits, with three host extension surfaces documented and the 2026 literature
checked. About 3,000 lines of cited notes. Several assumptions did not survive:
the benchmark everyone quotes is saturated, published work already measures the
problem this project targets, and the mechanism the design needs is standard
industrial practice under a different name.

**The pivot.** An external critique argued the project was becoming a research
laboratory rather than a product, and proposed deriving the workflow backwards
from what would prove the work. That survived scrutiny, and for a better reason
than the one given: obligations are stable while plans are contingent. Adopting
it made the system smaller, not larger.

**What it became.** Not a framework, an agent, or a harness. The closest
analogue is `make`. Evidence is bound to the state of the files it observed, so
editing a file invalidates it the way a build system invalidates an object file.
Completion stops being something the model asserts and becomes something the
runtime computes.

**Building it.** About 1,400 lines, working end to end on a real repository on
day one rather than week four. Three defects appeared immediately, and none of
them would have been found by testing: they only showed up when the whole cycle
ran in order.

**Measuring it.** The gate is a classifier, so it was measured as one. The first
honest measurement was a 75 percent false-block rate: the tool would have been
uninstalled within an hour. Nine fixes later it is zero on 46 scenarios, twelve
of which were written afterwards specifically to break it. That number is real
but narrow, and [05-measurement.md](05-measurement.md) says exactly what it does
not prove. Two later phases found out how narrow.

**The flaky-bug gap.** A seventh core piece had been listed and never built, and
its absence let one lucky run satisfy "repeated runs are stable", which is a
false verification on the exact task class the project claims as its
differentiator. Building it raised a better question than the runner itself: how
many clean runs are enough. That has an arithmetic answer, computed from the
failure rate the agent measures while reproducing the bug.

**Then a second piece turned out to be dead code.** The scope guard's allow list
was read in three places and written by nothing, so it never fired. The
interesting question was not how to enforce a scope but where one comes from,
and the answer matched the rest of the project: derive it from what the task
established rather than declaring it up front.

**Then the layer between the runtime and its host turned out to be wrong.**
Auditing after two dead pieces found three more defects in one place, the worst
of which recorded every failing command as passing, because the host sends no
exit code and signals failure by returning a different shape. Replaying 241 real
sessions showed the previous reader getting 0 of 174 failing commands right and
the new one getting all of them.

**And the switch that turns the whole runtime on was miscalibrated.** The same
corpus showed 51 percent of real turns getting obligations attached while
changing nothing, and a no-claim prompt clearing the obligations of work already
in progress, so the gate switched itself off whenever the user typed "continue".
One real prompt in five is four words or fewer, which no classifier reading the
prompt alone can handle. The claim now follows the work: the first source edit
opens one when the prompt stated none.

**Then it ran for real, and the floor turned out to be higher than the effect.**
Eighty-nine live agent runs across three task suites and two models. The gate
fires in a real session and refuses the stop, which closes three phases of "it
has never run live". But two identical plain passes scored 69 and 94 percent on
the same sixteen tasks, so a quarter of the suite answers differently run to run
and every arm comparison so far was reading noise. What survived is a friction
result: the gate stops nearly every first attempt to finish, and nearly always on
work that was already correct.

**Then the plan was rewritten to obey its own research, and the first milestone
under it worked.** v0.4 made the ten residual gaps the backlog and gave each
milestone an exit criterion that is a command and a number. M1 took four live
passes, two of which tested ideas that turned out to be wrong, and ended with the
gate blocking 12 percent of runs instead of 75 by computing the evidence itself
rather than demanding it.

**Then four rounds of building a ruler, and a withdrawal.** A suite that can
measure blocked two milestones, and every attempt to write one failed: tasks too
easy, tasks that were single-function bugs in disguise, tasks so trapped that
nothing could solve them. The rule that finally emerged is that a task measures
verification only if running the existing suite would catch the fix an agent
reaches for first. Looking up how the field does this found that rule already
named — SWE-bench's FAIL_TO_PASS and PASS_TO_PASS — and, in the same search,
published prior art on the thesis itself. The novelty claim was withdrawn and the
instrument now mines real bug fixes out of somebody else's history.

**Then the first fair test, and the gate did nothing.** Twelve bugs mined from
click's own history, validated the way SWE-bench validates, with nothing in them
written by this project. Identical outcomes in both arms on all twelve, at 1.4
times the cost. The reason is the useful part: the gate asks for a passing test
and a green suite, the agent produces both unprompted, and it writes its test
after deciding the fix is right, so the test agrees with whatever the fix does.
Self-confirming review is weakness class L in this project's own research, and it
had been built into the gate. The obvious fix — demand a test that fails first —
turns out to be published and measured: TDD inside the agent loop shows no
discernible difference, because the agent implements ahead of its own test. The
real conclusion is structural, and grading every obligation by whose word it
takes shows the whole null at a glance.

**Then the diagnosis of that null did not survive review.** The claim that the
agent had misunderstood the issue was made from the agent's own test without
reading the answer key. The hidden tests show its answer for the reported case was
right; it failed by not generalising to a second type. Auditing all seven, six are
recoverable from what a runtime can observe, and one of them wants only a
comparison against the original program. The conclusion that no reachable oracle
could help was withdrawn, two citations that had been trimmed the flattering way
were corrected, and the plan gained the distinction it was missing: establish what
the expected behaviour is before judging whether the patch implements it.

**Then an audit recorded sixteen observations, naming fifteen defects, and changed the objective.** The worst
is that the grader never ran a preservation set: a patch breaking existing tests
scored as resolved, so the measurement was blind to regressions, which is the
gate's main mechanism. Beneath the defects a harder argument — better stopping
cannot explore a diagnosis the worker never considered, and ranking work by gaps
in other frameworks optimises novelty rather than performance. v0.7 gives the
system an outer loop: generate candidates, select among them, decide what to try
next, with verification as one component.

## The two things worth taking away

### A measurement is only as good as the population it runs on

The same lesson arrived four times, each time from a wider population, and each
time the previous number turned out to have been true and narrow rather than
wrong.

**Measuring at all.** The gate was elegant and, on its first honest measurement,
blocked 75 percent of completed work. Every fix that followed came from asking
why one specific case failed, not from thinking harder about the architecture.

**Holding a set back.** After tuning, the score on the original scenarios was
zero. On twelve fresh ones written afterwards to break it, the same code scored
43 percent. Without that second set the project would have believed a number
that was three-quarters overfitting.

**Using payloads somebody else wrote.** Every number up to that point came from
hook payloads written by the same person who wrote the code reading them, so
both halves shared one wrong assumption and agreed perfectly. The host sends no
exit code and signals failure by changing shape, so every failing command had
been recorded as passing. Real session transcripts settled it in one pass, and
they had been sitting on the machine the whole time.

**Using prompts somebody else wrote.** The gate scored zero false blocks on 46
scenarios while attaching obligations to 51 percent of real turns that changed
nothing. Both numbers were correct. Every scenario in that suite was a piece of
work, and real sessions are mostly conversation.

The pattern is not that the earlier measurements were sloppy. It is that a suite
you construct yourself inherits your blind spots exactly, and agrees with you
about all of them.

### Three pieces failed by doing nothing

The repeat runner was never built. The scope guard's allow list was read in three
places and written by nothing. The subscription that was meant to feed the guard
delivered a single tool. In each case the code was correct, the tests passed, and
the component was never reached.

Nothing raises no exception, prints no warning, and looks exactly like a run
where there was nothing to do. So the fixes are structural rather than careful:
the hook subscription is generated from the constants the handlers branch on,
anything unreadable is appended to a blind-spot log, and `ep-doctor` exercises
the join between the runtime and its host rather than either half alone.

## Where it stands

Every figure below comes from a command in this repository.

| | Result | Reproduce with |
|---|---|---|
| Gate, as a classifier | 0 percent false blocks, 0 percent misses on 46 scenarios | `python -m eval.run --all` |
| Scope guard | 0 false questions, 0 misses on 25 cases | `python -m eval.scope_run` |
| Claim inference, real turns | 21 percent over-claim, 25 percent missed work over 3,557 turns | `python -m eval.claims_run` |
| Claim inference, labelled | 31 of 31 | `python -m eval.claims_run --cases` |
| Reading tool results, real commands | 174 of 174 failures, 5,916 of 5,916 successes over 36,034 commands | `python -m eval.replay --all` |
| Host integration | eleven checks, five of them driving the launcher as a process | `python plugin/bin/ep_doctor.py --host` |
| Live blocking, P2 | 12 percent of runs, down from 75 | `python -m eval.live --arm gate --model haiku` |
| The grader, graded | four patches with known answers, four correct | `python -m eval.validate` |
| The corpus, graded | 11 of 15 against the corpus as it was mined: four click tasks pinned a node id holding an installed version string a stray editable install had invented. Mining now drops such a node and records it, and the lock rebuilds 15 of 15 identical on every other field | `python -m eval.validate --corpus eval/corpus.lock` |
| Corpus, pinned | 15 instances from 5 repositories, rebuilt identically from a 3.8KB lock | `python -m eval.corpus --rebuild eval/corpus.lock --repos DIR` |
| Corpus, widened | 451 candidates reachable against about 130 before, 94 instances mined, 49 pinned on band | `python -m eval.corpus --select mined.json --bands substantial,one-liner` |
| The 49, rebuilt | 49 of 49 from a 12KB lock, identical on every field that decides a score | `python -m eval.corpus --rebuild eval/corpus-paired.lock --repos DIR` |
| Real mined instances | validated from upstream history, no Docker, with a preservation set | `python -m eval.mine --repo DIR --out mined.json` |
| Audit defects closed | all 20, R2 narrowed rather than closed; every one has a probe | `python -m pytest tests/test_audit_probes.py -q` |
| Baseline, pinned and paid for | 90 runs, $67.42: 68.9% and 73.3% over two passes, overlapping intervals | `python -m eval.baseline --show results/b4-passA-regraded.json` |
| Every grade recomputed from its bundle | pass A 0 of 45 changed; pass B 9 of 45, all of them an agent's editable install breaking a later task | `python -m eval.baseline --regrade results/b4-passB.json results/bundles-B` |
| Failure taxonomy, in the wild | three categories seen on real runs: resolved, no-patch, localised. `regressed` still never seen outside a test | `python -m eval.failures results/bundles-B` |
| Two paired chunks | 100 runs, $101.76: vanilla 46/50, gate 49/50, 22 of 25 tasks solved in all four attempts — **with upstream answer access, see below** | `python -m eval.baseline --show results/chunks/chunk2.json` |
| Answer exposure in that sweep | **24 of 100 runs name their own task's fix commit sha**, returned by the GitHub API as a tool result | `python -m eval.exposure results/chunks/bundles-chunk1 --corpus CORPUS` |
| The denial list works | Upstream network exposure **14 → 0** between the pre-denial and post-denial sweeps, same screen — the canary seen to flip | `python -m eval.canary --corpus E:/ep-corpus/prevalence.json results/prevalence/bundles` |
| The registry, closed | `pip download click` blocked while `pip install -e .` still works offline — and with no shelf staged the index is left alone rather than breaking every install | `python -m pytest tests/test_wheelhouse.py -q` |
| A reproduction, computed | A test red on the base commit and green now discharges `reproduced` whatever order the agent worked in — no model call | `python -m pytest tests/test_stress.py -q` |
| The best state is kept | Green at a stop → a private ref; the report offers it back if the tree moves off it | `python -m pytest tests/test_ratchet.py -q` |
| Which door the answer came through | **21 of 36 watchable runs** handed the fix's own invented identifiers — 14 upstream network, **4 the machine's own site-packages** | `python -m eval.canary --corpus E:/ep-corpus/paired.json results/chunks/bundles-chunk1` |
| A check that could not have failed | The runtime says so, in the report, without refusing the stop | `python -m pytest tests/test_stress.py -q` |
| A suite that failed, recorded as passing | **123 of 295 (42%)** preserved passing suite records carry `failed > 0`; 61% of gated runs carry one. Fixed, probed, controlled | `python -m eval.discriminate --bundles results --verbose` |
| The oracle gap does not settle | +2.0 to +20.0 across comparable pools, from 1-5 disagreeing tasks each | `python -m eval.pool --from-bundles results/chunks results/bundles-A results/bundles-B` |
| Evidence that cannot fail | **46% of agent validation evidence carries no bug-discriminating information**, measured elsewhere on 3,730 validation events. Ours has never been measured — Phase B2.1, $0 | `python -m eval.discriminate --bundles results/` *(not built)* |
| The gate's blocks, graded at the block | **4 blocks across 19 runs, none changed an outcome.** One blocked a correct patch, one a broken one, one a regression it then failed to catch | `python -m eval.checkpoint --grade results/prevalence/bundles --corpus results/prevalence/tasks.json` |
| First proposals already correct | 12 of 15 (80%), so the case the gate exists for barely occurs on this corpus | `python -m eval.checkpoint --grade results/prevalence/bundles --corpus results/prevalence/tasks.json` |
| A false block, graded at the block | the gate refused a candidate that was already `resolved`, twice, and the run took 43 more turns and 6.6x the cost to reach another correct patch | `python -m eval.checkpoint --grade results/checkpoint/bundles --corpus results/checkpoint/tasks.json` |
| What exposure was worth | 10 open-book successes rerun closed-book: **9 resolved**. The tenth reached GitHub through a sub-agent, which the denial did not cover | `python -m eval.exposure results/closedbook/bundles --corpus results/closedbook/tasks.json` |
| Where the treatment applied | Stop blocks in 4 of 50 gated runs (8%), 6 events. Pre-Stop interventions are **not** counted by that field: one gated run has 4 scope questions and 0 blocks | `python -m eval.failures results/chunks/bundles-chunk2` |
| Live agent runs, P1 | unanswered: two identical passes scored 69 and 94 percent, and later 68.9 and 53.3 | `python -m eval.noise a.json b.json` |
| Tests | 513 | `python -m pytest tests -q` |
| P1, twelve real bugs | no effect: identical outcomes both arms, 1.4x cost — **graded before the preservation set existed, and the candidates were deleted, so it cannot be re-graded** | `python -m eval.live --suite mined --arm vanilla,gate` |

About 3,150 lines of runtime, 5,050 of evaluation, 2,550 of tests.

**What none of it establishes.** P1, the hypothesis the whole thesis rests on,
is still unanswered, and the run-to-run noise floor is larger than the effect.

Earlier versions of this page said answering it needs about 252 agent runs per
comparison. **That number is withdrawn.** It came from dividing the required
discordant pairs by the within-arm flip rate, and flipping is not disagreement:
a baseline that fails every time against a treatment that succeeds every time
flips never and disagrees always. What the arithmetic actually supports is **31
pairs on which the two arms disagree**. Turning that into a number of runs needs
a measured rate of disagreement, which no run here has produced — if the arms
differed on one task in four it would be 124 paired runs, and that *if* is doing
all the work.

**The gate has not been shown to help, and it costs more.** Across nineteen
gated runs the mechanism fired four times and changed no outcome; one of those
blocks refused a patch that was already correct and cost 43 extra turns, and one
met a regression and let it through. The cost side is well measured at 1.3x
vanilla over fifty runs against fifty. The benefit side is unmeasured after $195
of looking, and that asymmetry is not neutral. The honest qualifier is that the
case the gate exists for — an agent wrong and saying otherwise — barely occurs
here, since 80 percent of first proposals are already correct.

**The 92 percent is not a repair score.** Twenty-four of the hundred runs name
their own task's fix commit in full, fetched from GitHub as a tool result; a
broader screen finds returned diff hunks in forty-two. The sweep had no
closed-book condition, so it measures applying a described upstream change with
access to that change. The corpus being easy is a symptom and possibly not the
disease: vaguer prompts do not close a channel that returns the patch on request.

What is needed first is an information boundary — a worker that sees the base
snapshot, the task text and its dependencies, and cannot see the fix, the hidden
tests, the corpus metadata, other attempts or the upstream repository.

The gate's Stop blocks land on **8 percent of gated runs** (6 events across 4 of
50), and that field does not count the package's pre-Stop interventions at all:
one gated run carries four scope questions and zero blocks. Sizing an experiment
needs a declared intervention boundary before it needs a task count.
Replay still cannot measure staleness at all, because the working tree at each
moment is not recoverable from a transcript.
