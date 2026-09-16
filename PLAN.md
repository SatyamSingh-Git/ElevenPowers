# Master Plan v0.8

2026-09-15. Supersedes v0.7. Written after a literature sweep rather than a
paid sweep: five parallel research passes over the 2026 work on coding-agent
reliability, evaluation integrity, long-horizon failure and the market.
Earlier plans are in git history; `docs/research/` and `journey/` are unchanged
and still govern. [journey/29-outside.md](journey/29-outside.md) is the record
of what was read and what it cost to learn.

**v0.7 changed what the system is for. v0.8 changes where it acts.** The thesis
survives intact and better supported than it has ever been. What does not
survive is the *placement*: a gate that fires at Stop, asking whether evidence
exists and is current. Three independent literatures say that is the wrong
moment and the wrong question, and this project's own null result is what they
predict.

---

## 0. Why v0.7 needed replacing

v0.7's own §5.0 and §5.6 already contained the two highest-value interventions
in the 2026 literature. Neither was built. That is the finding that motivates
this revision: the plan was not wrong, it was unexecuted, and the parts left
unexecuted were the parts that mattered.

| What v0.7 assumed | What the sweep established | v0.8 |
|---|---|---|
| The gate's job is to decide, at Stop, whether evidence exists and is fresh | Freshness is not the failure. **Every model saturates the visible test suite**; the best generated suites detect 36% of mutants. Evidence that exists, passes and does not discriminate is the actual failure | Evidence must be shown to **discriminate**, not merely to be current (§5.10) |
| Intervening at the proposed stop is where a completion gate belongs | The **median decisive error lands at step 7 of 27**, the recovery window is one step, and observable signals appear about ten steps later. 82% of doomed runs keep executing | Act where the premise is formed and where a verified state exists, not at the end (§5.11) |
| A better detector produces better outcomes | *Accurate failure prediction does not imply effective failure prevention.* Harm concentrates in early blocks on runs that would have succeeded — which is this project's own 6.6x false block | Detection and intervention are separately justified. Default to recording, not refusing (§5.12) |
| `reproduced` is one obligation among several, collected as a receipt | Handing the agent a **reproduction test is worth +28pp**, against +8pp for perfect localisation and +2pp for a regression test. It is the largest single measured lever in the field | The reproduction test is an **artifact to produce first**, not a receipt to collect last (§5.13) |
| Closed-book is enforced by denying tools by name | pip has no flag that forbids VCS requirements, and a registry allowlist fails because the registry serves the fixed release | `--network none` plus a pre-staged wheelhouse (§4.1) |
| A paired sweep on mined SWE-bench-style tasks can answer P1 | The benchmark over-reports by **6.2 absolute points**; 29.6% of plausible patches diverge behaviourally from ground truth | No claim is made on a delta smaller than the benchmark's own validity noise (§6) |

Two things in v0.7 are strengthened rather than replaced. §5.1 — measure pool
coverage against selected success before building a selector — is independently
confirmed, with a threshold attached: **below about four points of oracle gap,
selectors do more harm than good.** And §5.3's reading of the context-file
study is confirmed by a second population.

---

## 1. What this is, restated

Not a plugin that says no. **Given a task, permitted repository context and a
compute envelope, produce the strongest patch the system can find, with the
evidence for it.**

v0.8 adds where the evidence layer earns that. Ordered by measured effect, the
three positions are:

**1.1 Before the fix — the reproduction test.** Holding the agent fixed and
injecting one oracle signal at a time from a 35% baseline, a reproduction test
is worth **+28pp**; execution context +15pp; perfect localisation +8pp; a
regression test +2pp. The stated cause is that a reproduction test is a
*precise description of the failure condition*, where the issue text is
ambiguous. `core/obligations.py` already names this obligation — "that test
failed before the fix" — and treats it as a receipt collected at the end. It is
the most valuable artifact in the system and it is being asked for at the
moment it is worth least.

**1.2 During the work — the ratchet.** Agents reach correct code and then
destroy it: **60-69% of failures edit the correct functions and still produce a
wrong patch**, and in five documented cases an agent produced a patch identical
to the reference solution mid-trajectory and corrupted it afterwards.
Checkpoint-and-resume measures +25.6pp in one study and +8pp in another. The
published blocker is cost — running the test subset after every edit multiplies
test invocations by 10 to 40 times. **That cost is the one this architecture
exists to avoid.** Evidence already carries a content hash of exactly the files
a command observed, and `freshness()` already recomputes on every edit. The
runtime already knows *the tree was green at this fingerprint*. It prints that
as a complaint and discards it.

**1.3 At the end — the report, not the refusal.** Nineteen gated runs, four
blocks, no outcome changed. That is what the literature predicts, and the
market says the same from the other side: **56.3% of AI review comments are
rejected**, and of the unresolved ones **55.6% are "intentional design
decision"** — the tool did not know why the project did it that way. Evidence
is not rejectable the way an opinion is. The deliverable is a statement of what
rests on what, aimed at whoever has to trust the change.

**1.4 What survives unchanged.** Automatic collection from ordinary work,
automatic execution of declared checks, evidence bound to state, explicit
provenance, honest unresolved outcomes, and a recorded history of failed
hypotheses. These were always the valuable part and every one of them is load
bearing for §1.1 to §1.3.

**1.5 Borrowing is the method, not a fallback.** *(restored 2026-09-15)*

The founding document of this project is a source-read of fourteen systems, and
[complementarity-matrix.md](docs/research/complementarity-matrix.md) exists to
map each one's weakness onto another's strength. That was always the plan. v0.7
said work is ranked by the failure it addresses rather than by whether anyone
else built it, which is correct — and v0.8's first draft then drifted into
asking what remains *unclaimed*, which is the novelty filter under a new name.

**Restated, and it governs:**

> Every component starts from the best existing implementation of it. We name
> that implementation, its licence and its limit, and then state the one thing
> we add. A component with no prior art listed is one nobody researched, not
> one that is original.

[build-on.md](docs/research/build-on.md) does this for every v0.8 component.
The short version: the checkpoint store is **Cline's**, the revert-and-recheck
loop is **SWE-agent's**, the reproduce-first procedure is **Superpowers'**, the
"when to ask" rule is **BMAD's**, the bounded clarify is **Spec Kit's**, the
repository map is **Aider's**, the `--no-verify` block is **ECC's**, and the
mutation engines already exist. Everything is MIT or Apache-2.0 and compatible
with ours ([licenses.md](docs/research/licenses.md)); every reused file carries
a provenance header and a `NOTICE` entry.

One of those borrowings is worth calling out as the pattern. The 2026
literature on checkpointing names a trap — *a saved state is not necessarily a
suitable place to resume*, and task success cannot detect a bad recovery
decision. **Cline had already shipped the answer**: a
compare-and-swap restore that refuses when HEAD moved underneath it, which is
an eligibility check on the restore rather than a check on its outcome. A paper
found the gap; a product had closed it. Reading both is how that gets noticed.

**What is left as ours, narrowly:** invalidation as an economic mechanism
rather than a correctness detail (§1.2); discrimination as a stored fact
(§5.10); and obligations that arrive at the first edit and survive compaction
(§5.14). Three things. Everything else on the roadmap has a better
implementation already written by somebody else.

**Residual-gap ranking is retired as an investment filter.** It stays useful as
what it actually is — a map of where the borrowing runs out.

---

## 2. The thesis, confirmed and re-aimed

> Completion should be computed from dependency-tracked evidence, not asserted
> by the model — and no expectation may be treated as a requirement on the
> strength of the agent's own say-so.

v0.7 demoted this. **v0.8 restores it, because it has been independently
measured.** A hand-analysis of 1,184 failed CLI coding-agent trajectories puts
**57.9% of failures in the epistemic class** — information misuse rather than
capability — and the largest single category, at **30.7%, is false premises:
acting on unverified assumptions.** Specification neglect is another 14.9%.
Competence gaps account for 32.8% and environment for 9.4%.

The same shape appears in production rather than in benchmarks. Across **20,574 real coding-agent sessions**, the reviewer-visible symptoms are developer-constraint violation **38.3%**, misread developer intent **27.0%**, **inaccurate self-reporting 22.6%**, and faulty implementation **17.8%** — the mechanical class is the smallest of the four, and "the agent said something that was not so" is its own 22.6%.

One number in it argues against the obvious response. Only **15.4%** of causes are the user's instruction being underspecified, against **36.5%** that are the agent not following an instruction it did receive. **More specification is not the lever; adherence is.** That is consistent with the context-file nulls in §5.3 and with the complete absence of controlled evidence for spec-driven frameworks (§10).

The independent-failure assumption fails the same way. Forty-eight
implementations of one specification across different agents, models and
languages, over a million randomised inputs: **429 coincident failures against
115 predicted under independence, z = 29.20.** The agents converged on the same
misreading of the spec. Voting cleans up stochastic slips and cannot touch a
shared false premise.

So the thesis is right and the field has caught up to it. What was wrong is the
implementation of one word. **"Computed" was implemented as "collected."**

> The evidence layer's job is to make a premise checkable at the moment it is
> formed, and to preserve the best state that was ever proven, rather than to
> adjudicate a stop.

Two corollaries the old framing did not contain.

**2.1 A passing check is not evidence until it is shown to discriminate.** This
is §5.0 restated as a property of the artifact rather than a habit of the
developer. The cheap general form is reversion: undo the change the record was
bound to, re-run the recorded command, and if it still passes the record proved
nothing. The cheap *specific* form is already in the codebase — **a test
observed failing before the fix and passing after is discriminating by
construction.** `reproduced` is not one obligation among several. It is the
only one that answers the oracle problem, and the field's largest measured
lever is the same artifact.

**2.2 The valuable output is provenance, not permission.** What a reviewer
needs is which claims rest on checks that ran, which rest on checks that
cannot fail, and which rest on nothing. That is a report. Refusing to stop is
a separate feature that must earn its cost separately, and has not.

---

## 3. Where we actually are

**Working, and more valuable than v0.7 credited.** Evidence capture from
ordinary tool output; provenance and staleness bound to a content hash of the
observed files; self-discharge of declared commands; profiles and config;
`ep-status`; a scope guard; a repeat runner with derived run counts; a miner
that builds real tasks from upstream history without Docker; a live harness
driving the real CLI; run bundles that survive their workspace; a checkpoint
recorder; an exposure screen.

Three of those turn out to be the substrate for §1.1 to §1.3 rather than
supporting cast:

- `core/evidence.py:87` already answers "was this tree green, and is it still
  the same tree" on every edit. That is a checkpoint pointer being used as a
  complaint.
- `core/verify.py` already runs declared commands without asking the agent. A
  ratchet needs exactly that and nothing more.
- `core/obligations.py:149` already names the +28pp artifact.

**Measured and honest.** The gate fires on 8% of runs; four blocks across
nineteen runs changed no outcome; cost is 1.3x vanilla; 80% of first proposals
were already correct; `eval/exposure.py` is the only part of the information
boundary that has never failed.

**Never built.** Candidate pools, selection, diagnosis branching, localisation,
an isolated benchmark environment, the reversion check, the ratchet, and
reproduction-test synthesis.

**Built and never run.** `eval/stack.py` — the composition baseline. This is the
one that should be uncomfortable: [complementarity-matrix.md](docs/research/complementarity-matrix.md)
§6 says the bar this project is judged against is **a stack of best-of-breed
pieces installed together**, not vanilla, and every comparison bought so far has
been against vanilla. The code exists. The measurement has never been taken, and
it was not in the experiment queue until 2026-09-15.

**No longer distinctive, which is not the question.** Stale-on-edit and
no-evidence-no-close now ship elsewhere, and §1.5 retired novelty as a filter.
The useful statement is about *fit*, not about who got there first:
discrimination (§2.1) and the ratchet (§1.2) are the two places where **this
design has an advantage that is structural rather than chronological.** Others
would have to pay the 10-40x test cost that invalidation already avoids here.
If somebody ships either one tomorrow, the right response is to read their
implementation, not to look for a different gap.

---

## 4. P0: the defects that make measurement untrustworthy

All reproduced by `docs/research/audit_2026_09_11/reproduce.py`. **P0 here means a prerequisite for trusting a research conclusion, not a production emergency**: the tool is usable, and its numbers are not yet evidence. None may be deferred, and no new performance claim is made until each is fixed and covered by a regression test derived from the probe that found it.

Each lives in `tests/test_audit_probes.py` as a test asserting the behaviour the system is supposed to have. **All nineteen now pass and no `xfail` marker remains in that file**, which is the state Phase A's first exit criterion asks for. The file holds more tests than there are rows below, because defects found after the audit keep their probes there too.

While any remained, the marker was `xfail(strict=True)`. The marker comes off when the fix lands, and cannot be put back quietly: a fixed defect that regresses turns the test red. **Status below is that file, not this table** — `python -m pytest tests/test_audit_probes.py -q` is the authority, and a row saying `fixed` with an `xfail` still on it is a documentation bug.

### Evaluator

| | Defect | Consequence | Status |
|---|---|---|---|
| E1 | The grader runs only `f2p`; there is no preservation set | A patch that breaks existing tests scores as resolved. **The gate's main mechanism is regression-catching and the measurement could not see it** | fixed |
| E2 | `eval/analyse.py` keeps one row per task and arm | `--runs N` is incompatible with the analysis. Replicates, uncertainty and cost vanish | fixed |
| E3 | The workspace is deleted; `Run` holds no diff, log or trajectory | Freezing twelve candidate patches is impossible because they no longer exist | fixed |
| E4 | Model alias, inherited environment, silent plugin omission, fixed arm order | An arm can be labelled present and be absent | fixed |
| E5 | Grading happens inside the candidate's mutable workspace | Separation in time is not isolation of authority | fixed |
| E6 | Task selection keyed to the gate's own detection mechanism; flip-rate bound is invalid | Selecting the benchmark around the intervention being tested. A baseline can fail deterministically while a treatment succeeds deterministically, giving zero baseline flips and complete between-arm disagreement | fixed |

### Evidence layer

| | Defect | Consequence | Status |
|---|---|---|---|
| R1 | Size and mtime, with `vcs_state` as tie-breaker | Two different contents of an already-modified file share a porcelain status; evidence survives a real change | fixed |
| R2 | `observed` is a stored list; additions escape it | A new failing test file does not stale anything. Environment and dependency changes are not fingerprinted at all | part |
| R3 | Only `STALE` is rejected | Deleting an observed file yields `GONE` and still verifies | fixed |
| R4 | Older passes satisfy; first failure excused as pre-existing | fail → pass → fail returns VERIFIED | fixed |
| R5 | Substring match plus exit code | `echo pytest` is a passing suite with zero tests | fixed |
| R6 | `_test_written_and_suite_green` searches `touched ∪ seen` | **Reading** an existing test counts as writing one. Added in M1 to cut false blocks, and cut them partly by being wrong | fixed |
| R7 | `on_prompt` reuses the task id | A new request inherits the previous task's evidence, read set and `guided` flag; concurrent writers lose updates | fixed |
| R8 | `observe_edit` returns early when a claim exists | An edit under `src/auth/` leaves risk low | fixed |
| R9 | Stability accepts any `Kind.STABILITY` record | Clean repeats of an unrelated command certify a flaky test; the cap overstates confidence | fixed |
| R10 | A suite record's result is the exit code alone, with the parsed failure count ignored | `pytest ... \| tail -80` exits with **tail's** status, so a failing suite is recorded as passing. **123 of 295 preserved passing suite records (42%) carry `failed > 0`**, the worst at `failed=87, passed=1339`; 61% of gated runs carry at least one. Found 2026-09-15 by reading saved ledgers, not by reasoning | fixed |

**Every one now has a probe**, including the eight the audit reported without executing. `reproduce.py` covered R1–R9, E1 and E2; E3–E6 and H1–H4 were source findings it never ran, so their probes were written here rather than derived — H1–H4 against the documented host contract rather than a replayed transcript, since **replay fidelity is not delivery fidelity** and that confusion is what H1 is.

### Host contract

| | Defect | Consequence | Status |
|---|---|---|---|
| H1 | `read_result` looks only under nested keys; documented failure hooks use top-level `error` | A documented failure shape yields `readable=False` and no evidence. **This narrows the 174/174 claim**: replay fidelity is not delivery fidelity | fixed |
| H2 | 20-second hook timeout against 300-second verification | A timed-out hook loses its output and makes no decision. **Long verification must run outside the short-lived callback**, with snapshot-bound job state and a controlled resume path | fixed |
| H3 | `additionalContext` on Stop continues the conversation | Report-only branches emit it | fixed |
| H4 | Bash-only subscription | PowerShell commands are invisible | fixed |

**E3–E6, closed 2026-09-12.** A run now survives its workspace: `eval/bundle.py` exports the candidate as a patch against the seeded base and keeps it with the manifest, the host's answer, the ledger, the blind-spot log and the grade with the node outcomes behind it. Grading happens from that patch in a tree the evaluator builds, so anything the workspace acquired and the patch does not carry — ignored output, an editable install, a helpfully edited runner — does not come along. The grade is a function of the base and the patch, which is what makes a second opinion possible at all.

An arm named for a plugin whose directory is unset used to run as vanilla under the plugin's name; that is now a hard error naming the variable to set, because a comparison of two identical configurations reported under two names is worse than no comparison. Arm order is shuffled per task with a recorded seed, the environment the run happened in is recorded, and the model written down is the one the host resolved rather than the alias asked for.

The flip-rate bound is withdrawn. Converting discordant pairs into paired runs by dividing by the within-arm flip rate has nothing behind it: a baseline that fails every time against a treatment that succeeds every time flips never and disagrees always, so the smaller the flip rate the more confident the wrong answer looked. Discordance must be measured with both arms running, and `runs_for` takes it as an input rather than inventing it.

**Found while closing these:** `git apply` resolves paths against the enclosing repository rather than the working directory, and skips every file while exiting zero when the two differ. A home directory under version control is enough to trigger it, so every re-grade would have silently graded the base tree.

**H1–H4, closed 2026-09-12.** Checked against the live documentation rather than against what the code assumed, which changed two of the four answers. The documented failure hook carries no result object at all — a top-level `error`, and `is_interrupt` alongside it — so a shape the host is documented to send produced no evidence and a blind-spot entry. The exit-code pattern now accepts a bare `Exit code 1`, since only the transcript form writes `Error:` first.

The 20-second hook timeout was **this project's own choice**, not a host limit: the documented default for a command hook is 600 seconds. Stop now gets 600, because it may run the project's whole suite to compute evidence rather than demand it, and every other event keeps 20 — a hook that hangs is worse than one that gives up.

`additionalContext` is not honoured on Stop, so three report-only branches were writing their reports into a field the contract discards; they use `systemMessage`. And `PowerShell` is a distinct tool name used on Windows where Git Bash is absent, so on those machines the runtime was subscribed to a shell that never ran — including the machine this is developed on.

Each was written as a failing probe first and watched fail, and each has both directions per §5.0: the reader still reports a shape it does not understand, only Stop gets the long timeout, a blocked stop still speaks on stderr, and a second shell did not turn every tool into a shell.

**R7 and R9, closed 2026-09-12.** A prompt that states its own subject starts a task, and a task starts empty — the id was reused and nothing was cleared, so a suite run for the previous bug could discharge an obligation for this one purely because the ledger sat in the same directory. `save` merges the append-only fields against whatever is on disk at the moment of writing and names its temporary file per process; atomic replacement stops a torn file and does nothing about a lost update. SQLite remains the right answer and this covers the case that happens.

Stability records are bound to a target that actually failed in the task, so three hundred clean repeats of `python -c pass` no longer certify a flaky test. `runs_needed` no longer clamps to the 300-run budget: a 0.1 percent rate needs 2,995 clean runs, and 300 leave that fault alive with about 74 percent probability. Where the budget cannot buy the confidence the check reports insufficient evidence and says what the budget does rule out. An existing test asserted the cap and encoded the defect; it now asserts the honest number.

**R3–R6 and R8, closed 2026-09-12.** `GONE` now counts as not-fresh alongside `STALE`, so a claim can no longer be verified by a test result whose files were deleted. The newest record for an identity speaks for it, and a target that is red right now withholds the obligation rather than being outvoted by an older pass; the no-new-failures concession compares which tests failed rather than how many, and is refused outright where the runner reported no per-test detail, because a stable count is not evidence of preserved behaviour. A suite record that counted zero tests can no longer satisfy an obligation that a suite passes — the command being recognised, the process finishing, tests running and the required ones passing are four facts that had become one. `_test_written_and_suite_green` reads `touched` alone, which only works because `observe_edit` no longer returns before recording an edit when a claim is already open: R6 and R8 had to land together or the first would have deleted the M1 concession rather than narrowing it.

Each ships with a control asserting the rule still fires — a fail → pass history still verifies, a suite that really ran still satisfies, and an agent that did write the test still gets the concession. Without those, *fixed* and *disabled* are indistinguishable.

**R1, closed 2026-09-12 — and the reported defect was the smaller half.** The audit named the tie-breaker: `vcs_state` compared a porcelain status, which says which files differ from HEAD and not how, so two edits of one already-modified file shared a line. It now folds in `git diff HEAD` and reads untracked files directly.

That fix does not close the case the audit described, because `freshness` returns fresh on a `tree_hash` match **before** the tie-breaker is reached. The fingerprint itself was size and modification time, and a rewrite that keeps the length and lands inside the filesystem's timestamp resolution is invisible to it — measured at **220 of 300 attempts** on a two-line lock file. Evidence surviving a real edit was the common case, not a race, and the original docstring defended the trade while reasoning only about the harmless direction: falsely stale costs a re-run, falsely fresh is the failure this project exists to prevent.

`tree_hash` now hashes content, with stat as a cache key rather than the answer, and re-reads any file touched within two seconds whatever the cache holds — the window stat cannot resolve is where an agent's edits land. Measured at 6ms against 1ms for stat over 59 files; the cache is what keeps that affordable against the host's 20-second hook timeout (**H2**). The tie-breaker is now unreachable by construction and has been removed.

**R2, part closed 2026-09-12.** A record produced by scanning the tree now says so, and freshness re-derives the file set instead of consulting a stored list that cannot grow — a file that did not exist when the suite ran could never have appeared in it, so a new failing test staled nothing. Dependency manifests and lock files joined the observed set, since a dependency upgrade changes behaviour exactly as an edit does. **Still open:** a package installed without touching a manifest is invisible, and there is no fingerprint of the interpreter or the environment the command actually ran in. Marked `part` rather than `fixed` because the row claims more than the fix delivers.

**E2, closed 2026-09-12.** `load` keeps every replicate. The rates are then over runs and the paired test over tasks, because runs of one task are not independent and pairing replicate against replicate would multiply the apparent sample size while the correlation stayed — buying significance by claiming independence that was never there. At one replicate each the test is exactly McNemar again. `eval/noise.py::outcomes` refuses a file holding replicates instead of silently reading its last run, since that mode's question is what two separate passes did.

**E1, closed 2026-09-12.** `eval/mine.py` now records a pass-to-preserve set — everything green with the fix commit's tests in place both before and after the source change — and rejects a commit that yields none, because a task that cannot show a regression cannot grade a fix. `eval/live.py` grades on membership in the passing set of a whole-suite run rather than on the exit code of a handful of node ids, which also answers *were the required tests collected at all*. Before running it, the test tree is restored from the upstream repository: without that the preservation set asks the agent to mark its own work a second time, since an agent that edits an existing test until it agrees with its patch would be recorded as having preserved it. `Graded` reports `resolved`, `unfixed`, `regressed`, `timeout` or `setup` separately, because a regression and a patch that never worked were previously the same zero.

---

## 4.1 P0: the information boundary *(2026-09-14)*

A repair benchmark is a claim about what the worker could not see. This project has never stated that claim, and the first sweep to be checked against it failed: 24 of 100 runs retrieved their own answer commit from GitHub, one of them the single discordant pair the comparison rested on.

**Permitted, and written down before the next run:** the base snapshot, the task text, prepared dependencies, and model connectivity through the host or a constrained proxy.

**Excluded:** the fix commit, hidden tests, corpus metadata, other attempts, the local corpus clones, and general network access to the upstream repository.

Three properties this has to have, from what has already gone wrong here:

- **Enforced, not requested.** `PIP_REQUIRE_VIRTUALENV` and a job object bound what the agent does to the machine; neither says anything about what it can read. An environment variable is a request.
- **Declared as part of the benchmark.** Network permission is a property of the task, versioned with the corpus and covered by the graded digest, not an incidental setting of whichever machine ran it.
- **Checked after every sweep, not assumed.** The screen that found this is a read-only pass over saved transcripts against each task’s own `fix` sha. It costs nothing and should run with the taxonomy.

**Decided, 2026-09-15: the boundary is `--network none` plus a pre-staged wheelhouse.**
Network reachability is a capability, not a tool name. `pip`, `uv`, `poetry`, `npm`, `cargo`, `ssh`, `nc` and `python -c "import urllib"` all reach the same socket, and **pip has no flag that forbids VCS requirements** — `--no-index` disables the index, and a direct-URL requirement never goes through the index. No configuration closes this.

Two further traps, both confirmed and both worth recording because the obvious fix has them:

- **Do not allowlist PyPI.** The registry serves the upstream project's own post-fix releases, so `pip download <pkg>==<version-after-the-fix>` retrieves the answer from an allowed host. A registry allowlist is not a closed book. If a proxy is ever used it must front a private index serving only the pinned dependency closure, with the package under test excluded.
- **Do not rely on timestamp-based git pruning.** The upstream implementation of that idea shipped with a timezone comparison bug for roughly six months, and a sibling dataset still exposes 116 future-dated tags. Delete `.git`, re-initialise as a single commit, and restore the real history only at scoring time.

The plan of record, feasible on this machine today via Docker Desktop on WSL2: clone at the base commit, strip and stash `.git` out of band keyed by run id, resolve and build the dependency closure once while online (`pip wheel -w ./wheelhouse`), then run with `--network none`, `PIP_NO_INDEX=1` and `PIP_FIND_LINKS=/wheels`. `pip download --no-binary :all: "pkg @ git+https://..."` then has no socket to open. A task whose dependencies could not be pre-staged is a **drop, reported in a drops manifest, not a task failure in the denominator**.

**Two corrections to this recipe, 2026-09-16, found before spending.**

**`--network none` cannot work as written.** The `claude` CLI is launched by
`eval/live.py` as a child process and the agent's shell tools are *its*
children, so they share one network namespace. Cutting the network cuts the
CLI's own path to the model API and the run does not happen at all. The boundary
has to be an **egress allowlist containing the model endpoint and nothing
else** - which is also what Cursor's harness does, and what the agent's own
`gh`, `curl` and `pip download` then fail against.

**A network boundary would not have closed the biggest door anyway.** The
workspace virtualenv is built with `--system-site-packages` (§27, the fix that
finally stopped agents installing into the machine), so the *installed* copy of
the library under test is readable from inside the workspace - and it is a newer
release that **already contains the fix**. `eval/canary.py` caught four runs
reading exactly that: `cat`, `Read` and `diff -u` against
`AppData/Roaming/Python/Python313/site-packages/`. No egress policy touches it.
Closing it means pinning the workspace interpreter to the *base* version of the
package under test, or dropping `--system-site-packages` and paying back the
cost §27 avoided. Neither is built.

**Blocked on this machine, 2026-09-16.** No Docker, no WSL distribution. The
Claude Code sandbox is documented as unsupported on native Windows. So B3 needs
an install decision before it can proceed, and the honest state is that **every
score this project has published was measured with the book open**, with a floor
now measured rather than guessed (below).

**The registry is an answer key, and no allowlist closes it.** Measured 2026-09-16 by `eval/canary.py` on the post-denial sweep: the denial list works — upstream network exposure falls **14 → 0** against the pre-denial sweep, which is the canary seen to flip — and every one of the four survivors is *a released version of the package that already contains the fix*: a downloaded `attrs-24.2.0` tree, a downloaded `click-8.5.0` wheel, an installed `clickcheck/` tree, and the machine's own `site-packages`. Every published boundary design allowlists a package registry because dependencies need one, so this door is open in all of them.

`PIP_NO_INDEX=1` blocks three of the four and **was reverted the same hour**: it also breaks `pip install -e .`, because pip fetches `setuptools` into an isolated build environment, and nothing an environment can set turns that isolation off — `PIP_NO_BUILD_ISOLATION`, `PIP_BUILD_ISOLATION=false|0|no` and a `pip.ini` were each measured and each ignored, while the command-line flag works. Shipping it would have repeated `PIP_USER`, `PYTHONUSERBASE` and `PIP_REQUIRE_VIRTUALENV`, one of which was observed being switched off by an agent mid-run. **The fix is a staged wheelhouse with `PIP_FIND_LINKS`, built once while online.** Reading the machine's `site-packages` by absolute path is not preventable without containment at all; it is detectable, and the canary detects it.

**The probe must be seen to flip.** Plant a run whose true fix contains a unique nonsense token, then grep every transcript and patch for it. It must be **found with the boundary off and absent with it on**. Until both states have been observed, the boundary is untested prevention, which §5.0 says is not prevention at all.

**Measured again, 2026-09-15, and the denial does not hold.** `git clone` is refused and `pip download` fetches the same repository, because pip clones `git+` URLs internally. An agent used that route to extract its own fix commit with `git format-patch` and apply it verbatim; the run graded `resolved`. Two of sixteen runs did this. Tool denial closes the doors it names and a package manager walks through the wall, so §4.1 needs an operating-system or network boundary rather than a longer list. `eval.exposure` is what keeps this honest in the meantime, and it is
the only part of the boundary that has never failed.

**Measured far higher, 2026-09-16, by a sharper screen.** `eval/canary.py` looks
for the answer's *vocabulary* rather than its sha: identifiers the upstream fix
**defines** which appear nowhere in the base tree, counted only when a tool
result hands one to the run **before the run ever uses it**. On chunk1 it finds
**21 of 36 watchable runs** against `eval.exposure`'s 2 on the same bundles, and
it names the door: **14 upstream network** (`gh api`, `gh pr diff`, `WebFetch`,
`curl`), **4 the machine's own site-packages**, 3 local. Five runs reached the
same vocabulary unaided, which is the control that says the screen can still
tell convergence from retrieval. The figure sits beside Cursor's independently
audited 63 percent.

**Measured, 2026-09-14.** The channel was the network alone: of a hundred runs, zero reached the local clones and zero reached evaluator assets. With `WebFetch`, `WebSearch` and the Bash network commands denied, ten open-book successes were rerun closed-book and **nine resolved** — so exposure was convenience rather than necessity, and most of the 92 percent survives the book closing. The tenth reached GitHub through a **sub-agent**, which `--disallowed-tools` does not cover; `Agent` and `Task` are denied now. Ten tasks selected for having succeeded is not a corpus-wide rate, and the corpus-wide closed-book rate is still unmeasured.

The existing runs are retained under their real conditions. Dropping the 42 flagged runs and recomputing would select on a behaviour that may itself depend on difficulty and treatment, which is the E6 mistake in a new place.

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

**5.0 Verification is adversarial, not observational.** *(standing requirement, 2026-09-12)*

The runtime watches commands the agent chose to run and reads their output. That is passive, and passive observation cannot tell a test that discriminates from one that agrees with whatever it is handed — which is the oracle problem restated as an implementation fact. **Every check the system performs is run in both directions:**

| | |
|---|---|
| **forward** | the thing does what it should — the legitimate case is accepted, the rule still fires |
| **adversarial** | the thing refuses what it should — the system actively tries to break, defeat or dishonestly satisfy its own check |

Concretely, the system must **do the breaking itself** rather than wait to observe it: revert the candidate's source change and confirm the new test goes red; mutate the patch and confirm something notices; empty or weaken a test and confirm the check stops being satisfied; run the preserved set against the pre-patch tree to establish which failures are the agent's. A check that survives none of these is not evidence, and a check that survives all of them by refusing everything is not evidence either.

**Both directions, then conclude from the four states** — `VERIFIED`, `UNVERIFIED`, `STALE`, `CONTRADICTED` — not from a pass/fail bit. The four already distinguish *no evidence* from *evidence that no longer applies* from *evidence pointing the other way*, and an adversarial pass that produces a bare boolean throws that away.

This is why it is a requirement rather than a testing habit: a check that refuses everything passes every adversarial test, and a check that accepts everything passes every forward test. Either alone is indistinguishable from the feature being deleted, and this project has already come within one control of proving it — fixing **R6** without a forward control would have looked exactly like reverting the M1 work that cut live blocking from 75 percent of runs to 12.

It applies to this project's own development with the same force: every narrowing fix ships a control asserting the rule still fires, and every behavioural fix is checked against a worktree at the previous commit, where it must fail.

**Enforced in code as of 2026-09-15, because remembering it failed.** R10 was fixed in `_pytest` and the same defect sat untouched in six sibling parsers for the rest of that hour — the fix looked complete because one direction of one runner went green. `tests/test_audit_probes.py::test_every_runner_is_read_both_ways` now asserts both directions for every runner `parse` dispatches to, in a single test so neither direction can ship alone, and `test_the_both_ways_table_covers_every_runner_parse_dispatches_to` counts the dispatch sites in the source and **fails if a runner is added without both**. That guard was itself watched firing and clearing.

**And it is a product feature, not only a development habit** *(standing requirement, 2026-09-15, at the user's direction)*. The runtime must run its own checks both ways: forward, that the evidence passes on the tree as it stands; adversarially, that it would *not* have passed without the change. A check that cannot fail is not evidence (§5.10), and the tool is the thing that should be saying so — not a person remembering to ask. This is what `UNDISCRIMINATING` is for, and it is now the next build rather than a phase C aspiration.

**5.1 Measure the generation ceiling before building a better examiner.** For a frozen pool of N candidates: *pool coverage* is the fraction of tasks where at least one candidate is correct; *selected success* is the fraction where the chosen one is correct; the difference is **selection regret**. If every candidate is wrong, no reranking helps and the investment belongs in localisation, models or diagnosis diversity. Pilot at N = 1, 4, 8.

**5.2 Branch at diagnosis, not only at patch generation.** Workers given the same interpretation reproduce the same mistake. Branch where the interpretation is chosen. Share verified repository facts; keep speculative diagnoses separate until comparison. Measure diversity by failure overlap and solutions found, not by role names.

A **missing-code search** after a candidate edit — sibling implementations of the changed interface, callers with other argument types, exception paths, resource-ownership transitions, parsers that must agree — targets exactly the failure that beat `click-762c97ee`, which fixed `Choice` and never generalised to `DateTime`.

**5.3 Context is a constructed working set.** The old plan excluded finding code because the field is crowded. That optimises novelty rather than task success, and the restriction is removed. Compact worker state carries contract, diagnosis, located symbols, observed failures, rejected approaches, active candidate, open questions and evidence references, with code and logs retrievable. Summaries must distinguish observation from hypothesis so a guess is not promoted during compaction. No giant always-loaded overview: the revised AGENTS.md study finds context files generally do not improve success while increasing cost.

**5.4 Select on summaries, then inspect primary evidence.** There is direct support for trying this: structured rollout summaries with tournament voting and parallel-distill-refine are reported to move SWE-Bench Verified from 70.9 to 77.6 percent and Terminal-Bench v2.0 from 46.9 to 59.1. That used substantial extra inference on specific older model and harness combinations, so it justifies the experiment and not an expected uplift. Bounded candidate summaries with diagnosis, snapshot, changes, compatibility assumptions, checks actually run, and provenance of every expectation. Randomise presentation order and measure rejection of correct candidates, not judge agreement.

**5.5 Generated checks are uncertain until grounded.** Freezing a wrong assertion before seeing a patch does not make it right. Distinguish mandatory checks backed by authorised requirements from speculative ones. Adding checks raises the chance a correct candidate is falsely rejected, so measure **correct-candidate survival through each filter** and keep rejected candidates. A speculative disagreement should start an investigation or lower a score, not eliminate every candidate that disagrees.

Build the **candidate-by-probe outcome matrix**: inputs down one axis, candidates across the other. Where plausible candidates disagree, retrieve the contract or nearby code that explains why. The matrix chooses the next investigation. Voting across candidates is not an authority on intended behaviour.

**5.6 Keep an incumbent, allow nonmonotonic search.** A long attempt ends at its latest patch, not its best. Candidates are immutable; a failed repair must not destroy an earlier one. After integration, snapshot again and rerun checks: evidence from two passing branches does not transfer to their merge.

**5.9 An experiment is sized on how often the intervention engages.** *(2026-09-14, paid for)* The gate blocks on about twelve percent of runs. At two replicates that gives a task roughly one chance in five of seeing a block at all, so thirteen tasks offer two or three pairs the mechanism could have caused against the thirty-one needed. A hundred paired runs returned two discordant pairs and the gate had fired on neither. The engagement rate was measured in Phase A and had been in §3's exits table ever since; the chunk was sized on what the budget could buy instead. Before any comparison: multiply the engagement rate by the replicates, and if the product cannot reach the required pairs, the experiment does not exist yet. This is D57 one step earlier — that one says sample size comes from measured discordance rather than the flip rate, and this one says the discordance a treatment can even produce is bounded by how often it applies.

**5.7 Route for complementary capability.** The question is not which model is cheaper but whether different configurations solve different tasks. Measure overlap between strong pinned configurations before assuming scaffolding helps. Model-mixing experiments show complementary benefit in some combinations and none in others, and multi-agent benefit depends strongly on task structure, so a committee is not assumed to help every sequential task.

**5.8 Learn from decisions, not from successful transcripts.** Per-task working memory and attempt histories first. Replay validates parsers and retrieval; it cannot establish the causal benefit of an action never executed. Prompt and procedure optimisation from execution feedback is worth testing once that data exists, at Phase E, keeping training, development selection and final evaluation separate.

**5.10 A check is not evidence until it is shown to discriminate.** *(standing requirement, 2026-09-15)*

`PASS` and `FRESH` are two facts about a record. Neither is the one that matters. Across model families **every model can saturate the visible test suite on every task**, and the gap between the visible suite and held-out compositional tests **grows about 27 percentage points for every tenfold increase in lines of code** — under 10K LOC the worst case was 21pp, over 25K LOC it reached 100pp. Independently, the best models generating test suites achieve **10.2% verification and 36.15% mutant detection**. Tests that exist, are current and pass are the normal case; tests that would have noticed are not.

**It has been measured, and the figure is 46 percent.** Across 3,730 validation events in 643 rollouts over 110 tasks (SWE-bench Verified and SWE-rebench), **46.0% of positive validation evidence carries no bug-discriminating information**, and **23.8% of rollouts close with an entirely non-discriminating evidence base**. A further 26.9% of bug-detecting tests fail on the developer's own correct fix — discriminating, but for the candidate rather than the bug. Independently, **77% of SWE-bench Verified instances admit at least one semantically incorrect patch that passes every existing test**, and augmenting those suites costs the top ten agents 4.2 to 9.0 points.

So P22 is no longer this project's discovery to make. What Phase B2.1 buys is the figure **for our own ledger**, which is the only way to know whether the mechanism this project ships is in the 46% or outside it — and it remains the cheapest measurement available.

**And the obvious repair does not work.** The same study fed the discrimination contrast back to the agent and reported it as a negative result against a prespecified threshold: evidence-inadequate closures fell 7.8 points and discriminating evidence rose 7.4, **both below the 10-point smallest effect size of interest declared in advance**. Detecting vacuity is established. Fixing it by telling the agent is not. §5.12 applies to this mechanism as much as to the gate, and the honest first use of the discrimination signal is to *report* it.

**Built 2026-09-16: `core/stress.py`.** The runtime runs every declared check against a detached `git worktree` at the commit the task began from. A check that already passed there is reported — in the end report, as `could not fail` — without altering the verdict, per §5.12. Only declared commands are run (the `core/verify.py` rule), the working tree is never touched, the base is captured at task open so a mid-task commit cannot move it, and *unknown* is a distinct third answer rather than a guess. Tested both ways against a real repository, including the control that a genuinely discriminating check must **not** be reported as weak. [journey/32](journey/32-could-not-fail.md).

What it does **not** cover: commands the agent chose rather than the project declared. That is most of the evidence in a real session, and closing it means deciding when re-running somebody else's shell line somewhere new is safe.

Two mechanisms, cheapest first:

- **Reversion.** Undo the change the record was bound to, re-run the recorded command. Still passing means the record proved nothing about the change. One mutant, guaranteed meaningful, and the ground truth is free.
- **Reproduction.** A record seen `FAIL` on the pre-change tree and `PASS` after is discriminating without any extra run at all. This is `reproduced`, already implemented, and §5.13 is about producing it rather than waiting for it.

This is P0 for any future claim about the gate. A verdict that cannot distinguish a discriminating check from a vacuous one is not measuring completion.

**5.11 Intervene where the error is, not where the symptom is.** *(2026-09-15)*

Across 1,184 failed CLI coding-agent trajectories the **median decisive error is at step 7 of a median 27**, the **median recovery window is one step**, and **observable failure signals appear about ten steps later** — an observability lag in which a run is already doomed and still looks healthy. **82% of failed runs keep executing after recovery becomes impossible**, and the best real-time prefix monitor reached 28.8% recall.

A Stop gate sits at the far end of that lag by construction. It is the correct place to *report* and the worst place to *repair*. This, not corpus difficulty alone, is why four blocks changed four outcomes by zero.

The same finding gives the cheapest real win available: if most of a doomed run is spent after the point of no return, then detecting lock-in is worth money even when it repairs nothing, because it stops paying for turns that cannot succeed.

**5.12 Detection and intervention are separately justified.** *(standing requirement, 2026-09-15)*

*Accurate failure prediction does not imply effective failure prevention.* Measured harm from intervening concentrates in early interruptions of runs the agent would have completed correctly — a rollback at step 0 pushing an agent off a correct answer and into a strategy change. This project produced exactly that result before reading it: a block on an already-correct patch costing 43 extra turns and 6.6x the money.

So a mechanism must clear two bars, and clearing the first has never implied the second:

| | |
|---|---|
| **it detects** | the signal is real and separates the cases it claims to separate |
| **it improves** | acting on the signal produces a better outcome than not acting, at matched compute |

The default posture that follows is **record, surface, and preserve — do not refuse.** Blocking is a profile, not the architecture. It ships with a measured and published false-block rate or it does not ship; the comparable prior generation of tools died of 8-30% signal relevance and abandonment inside two weeks, and 56.3% of current AI review comments are rejected outright.

**5.13 The reproduction test is the product's highest-value artifact.** *(2026-09-15)*

Ranked by measured effect on resolve rate from a 35% baseline, holding the agent fixed: reproduction test **+28pp**, execution context +15pp, API usage +9pp, perfect localisation +8pp, regression test +2pp. The reason given is that a reproduction test is a precise statement of the failure condition where issue text is ambiguous — which is the same failure class as §2's 30.7% false premises and the shared-misreading result.

Three consequences:

- **Localisation is not the bottleneck it was assumed to be.** Perfect localisation is worth 8pp. That reorders §5.2 and the localisation work in Phase D below reproduction-test synthesis.
- **Execution during repair is not the lever either.** Across 7,745 traces the resolve-rate gap between prohibiting and permitting execution during repair was **1.25pp and not significant**. It is not about running tests. It is about having the right test.
- **Our obligation is the artifact.** Demanding `reproduced` at Stop asks for the +28pp signal at the moment it is worth least. Offering to *derive* it at the first edit is the same mechanism pointed the right way, and it is the one intervention that is additive rather than restrictive — which is what §5.12 says to prefer.

**5.14 Compaction is lossy in a direction that targets this project.** *(2026-09-15)*

Across 1,323 episodes and seven models, constraint violation rises from **0% in full context to 78% after four compaction rounds**, mediated by whether the constraint text survived the summary: violation 1% when it survived against 43% when it was dropped. **Soft or organisational policy decays about 8.3 times more than hard safety norms.** An obligation list is soft organisational policy.

Two directives. Re-assert obligations after every compaction rather than trusting them to persist — the runtime already subscribes to `compact`. And treat any claim inherited from a summary as unverified provenance rather than as established, since summarisation measurably strips hedges and broadens claims.

**5.15 Combine first, invent last.** *(standing requirement, 2026-09-15)*

A design is not finished until it names what it borrows. Before any component is
built:

1. Search the fourteen cards and the reading list for the nearest existing
   implementation. `docs/research/` is a source-read at pinned commits; it is
   faster to read than to rediscover.
2. Record the licence and the reuse obligation from [licenses.md](docs/research/licenses.md),
   and the limit the card found — every strength in the matrix ships with the
   place it stops.
3. State the **one thing** being added. If that sentence cannot be written, the
   component is a reimplementation and should be replaced by the borrow.
4. Prefer a **code** strength over a **protocol** strength over a **prose** one,
   per the matrix's §1 taxonomy: nine of ten surveyed systems enforce process
   through text the model may ignore, and §5.14 measures how fast that text
   evaporates under compaction.

The composition baseline in [complementarity-matrix.md](docs/research/complementarity-matrix.md)
§6 remains the bar this project is judged against: **beating vanilla is not the
test; beating a stack of best-of-breed pieces is.** That comparison has still
never been run, and it is cheaper than it was, because the boundary (§4.1) and
the free measurements (Phase B2) come first anyway.

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
- **Recompute the required n per comparison.** The 252-run figure alternated between agent runs and paired runs, and was derived by dividing discordant pairs by the within-arm flip rate — which does not bound them, since a deterministic baseline against a deterministic treatment flips never and disagrees always. **Withdrawn.** What holds is 31 discordant pairs; converting to runs needs a disagreement rate measured with both arms running (`eval.noise.runs_for`).
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
the audit's probes promoted from a script to `tests/test_audit_probes.py`,
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
| B2 | **$0** — saved bundles only | discrimination rate, oracle gap, checkpoint density |
| B3 | under $5 — the boundary | canary found with it off, absent with it on |
| A | under $5 — almost all repair, tests and fixtures | probes green, instrument validated |
| B | $20–40 — a pinned baseline over several repositories | a reproducible score with an interval |
| C | $40–80 — pools at N = 1, 4, 8 over the development corpus | coverage, selected success and regret reported |
| D | $80+, decided by C's curve | a preregistered held-out comparison |
| E | not budgeted until D returns something | — |

If a phase exceeds its envelope without reaching its stop condition, that is a
result about the design, not a reason to spend more.

Tracks run in parallel where prerequisites allow: **evaluation infrastructure**, **candidate generation**, **candidate assessment**. Oracle diagnostics can proceed on frozen candidates while the harness is being made reproducible.

**Where to start, unambiguously.** Phases A and B are closed; B′ and C are
decisions rather than work. The live order is:

| | | Costs | Blocks |
|---|---|---|---|
| **1** | **B2** — the three free measurements against saved bundles | **$0** | nothing; start here |
| 2 | **B3** — the boundary, with a canary seen to flip | <$5 | every paid run after it |
| 3 | **C0** — the ratchet | build | its own contribution experiment |
| 4 | **C1** — derive the reproduction test | build | — |
| 5 | Composition baseline (`eval/stack.py`, never run) | paid | any claim that this system is worth installing |

B2 needs two modules that **do not exist yet** — `eval/discriminate.py` and a
`--from-bundles` mode for `eval/pool.py`. Writing them is the work; running them
is free. That is the whole reason B2 is first.

### Phase A — Make conclusions reconstructible *(blocking)*

Fix E1–E6, R1–R9, H1–H4, each with a regression test derived from the audit's probe. Add run bundles: task manifest, base identity, candidate diff and snapshot, host events, prompts and model configuration, trajectory, test node outcomes, limits, result. Grade in an evaluator-owned workspace from an exported patch. Keep raw host-event fixtures separate from transcript fixtures. Provision an isolated Linux worker.

**Exit, as commands:**

- `python -m pytest tests/test_audit_probes.py -q` → **zero xfailed**; every reproduced defect keeps the test that found it, now passing — **met**, 52 passed (48 at Phase A's close; later defects add their probes to the same file)
- `python -m eval.validate` → gold patch resolves; a known regression fails; a wrong patch fails; a setup failure is reported as setup failure, not as an unresolved task — **met**, four of four
- `python -m eval.live --runs 2 && python -m eval.analyse` → two rows retained per task and arm, not one — **met 2026-09-12**: `runs 2, tasks 1` on four real agent runs of `last_page` at $0.36
- `python plugin/bin/ep_doctor.py --host` → success, failure and stop paths observed against a pinned host — **met**, and note that this criterion passed for weeks by discarding the flag

**Phase A is closed, 2026-09-12.** All nineteen defects closed — eighteen fixed, R2 narrowed and marked as such — 436 tests with no xfails at that date, and all four exits passing as commands. Total live spend: $0.72 against a $5 envelope.

The first live sweep after the repairs failed all four runs, and failed *usefully*: the exported candidate was mostly compiled bytecode because the seeded workspace had no ignore rules, `git apply` rejected it, and the harness recorded `setup` rather than counting four failures against the agent. The bundles made it diagnosable from a workspace that no longer existed. Both of those are the point of the phase, demonstrated by accident on the first outing. Inspecting the surviving bundle then caught two more: the manifest recorded the model *alias* while its docstring claimed it recorded what the host resolved, and seeded tasks recorded a verdict with no node outcomes behind it.

### Phase B — Establish the strongest useful baseline

A current strong native host configuration against a minimal worker harness, pinned models and environments, several repositories and difficulty categories. Both a matched-compute comparison and a maximum-budget curve; cost is secondary here, so the curve is the product direction and the matched comparison explains where gains came from.

Measure what actually reaches the model rather than what is installed.

**Exit, as commands:** `python -m eval.baseline --pinned` reports a score with an interval that a rerun reproduces, and `python -m eval.failures` prints a taxonomy where every category cites saved trajectories. Enough repeats to separate setup problems from coding failures.

**Phase B is closed, 2026-09-14.** Both exits pass. 199 paid runs, $175.69: ninety one arm against a pinned corpus and model, a hundred with both arms, the rest dry checks. All of it preserved and re-gradable.

What it established, none of which existed before: Stop blocks land on **8 percent** of gated runs (6 events across 4 of 50); a plain `claude-sonnet-5` at high effort resolves **92 percent** of the selected corpus **with upstream answer access**; discordance runs at 2 tasks in 25.

A second external review, [audit_2026_09_14](docs/research/audit_2026_09_14/findings.md), then established the thing that reframes all of it: **24 of the 100 runs name their own task’s fix commit sha**, returned from the GitHub API as a tool result, and a broader screen finds returned diff hunks in 42. The sweep was never closed-book. Verified here against the archive before being accepted.

What it did not establish is P1, and it could not have. The arithmetic was available beforehand and was not done: a treatment engaging on 12 percent of runs, at two replicates, gives a task about one chance in five of seeing it at all, so thirteen tasks offer two or three pairs the mechanism could have caused against thirty-one needed. **§5.9 is the correction** — size on the engagement rate, not the task count. And **§5.1 is the same principle inverted**: it says that when every candidate is wrong no reranking helps, and the investment belongs upstream. When every candidate is *right* no gate helps either, and the investment belongs in the benchmark.

The binding problem is **not** the ceiling, and the earlier reading of it here was treatment of a symptom. Making prompts vaguer does not close a channel that returns the patch on request. **§4.1 is the prerequisite**: an information boundary, defined and enforced, before difficulty is recalibrated or another comparison is bought.

Phase C does not wait on a definitive P1 result. Selection and repair development proceed against saved candidates while P1 becomes a bounded component experiment at a declared decision point.

### Phase B′ — P1 becomes a bounded component experiment *(2026-09-14, decided)*

P1 is no longer a prerequisite for anything else. It had become one by habit: every phase waited on a result the experiment could not produce, and the waiting cost two audits to notice.

**What replaces the arm comparison.** A vanilla-versus-package sweep asks whether the whole product helps on a whole workload, which is the expensive question and the one least able to explain a weak answer. The bounded version asks a narrower thing at a place the system already reaches: **the first proposed stop.**

Save the candidate and its evidence at that point. Randomise between submitting it and continuing with specific evidence. Compare that against equally funded generic continuation — the same extra turns, without the gate's feedback. Three things then come apart that the paired sweep could not separate:

- whether the gate **finds** a real defect in the proposed patch
- whether its feedback **repairs** the defect
- whether the same repair comes from **extra compute alone**

The last is the null this project has never controlled for. A gated arm that runs forty turns against a plain arm that runs thirty is not a test of the gate.

**Why this is cheaper and says more.** The unit is a decision, not a task, and decisions are what the treatment acts on: 6 Stop blocks in 50 runs means a task-level sweep buys mostly nothing, while a checkpoint design spends only where the intervention applies. Exposure still has to be closed for any repair claim (§4.1), but a within-candidate comparison is less damaged by it than an absolute score, since both branches start from the same retrieved state.

### Phase B2 — Three measurements that cost nothing *(2026-09-15, next)*

Every paid experiment this project has run was an attempt to *detect an effect*. These three measure a *property*, and the data was bought already: `results/` holds candidate patches, bases, grades and evidence for over a hundred runs, preserved since Phase A made runs survive their workspaces. Local compute and wall-clock only.

**B2.1 — What fraction of our passing evidence discriminates?** *(built on SWE-agent's revert-on-new-lint loop, MIT — the same apply/re-check/revert shape pointed at tests instead of lint; mutation engines exist and we are not writing one)* For every record graded `PASS`, revert the change it was bound to and re-run the recorded command. Still passing means vacuous. This is §5.10's reversion mutant against runs already paid for, and it is the first number this project would have on whether its own central mechanism measures anything. Forward and adversarial: a record known discriminating (a `reproduced` pair) must be seen to survive, and a record known vacuous (a check bound to an untouched file) must be seen to fail.

**B2.2 — What is our oracle gap?** Across the saved chunks, four attempts exist per task. Report pool coverage, selected success and selection regret together (§5.1). **If the gap is under about four points, no selector will help and most measured selectors actively harm** — that single number can cancel Phase C, which is why it comes before it.

**B2.3 — Did a better state exist mid-run than the one submitted?** The checkpoint recorder holds candidates at every proposed stop. Grade each against final. Entry 28 answered this for first-versus-final at Stop granularity and found no difference; §1.2 predicts the effect lives at *edit* granularity, which the saved bundles cannot answer. So this measurement's honest outcome may be "the existing data cannot see it", and that is a result about instrumentation, recorded as such rather than as a null.

**Exit, as commands:** `python -m eval.discriminate --bundles results --verbose` and `python -m eval.pool --from-bundles results/chunks results/bundles-A results/bundles-B`. **Envelope: $0.** Stop condition: all three numbers exist, or a stated reason the saved data cannot produce one.

**Run 2026-09-15. Both modules exist; outputs preserved in `results/b2/`.** [journey/31](journey/31-forty-two-percent.md) is the account.

- **B2.1 found a prior defect and stopped there, correctly.** Before the reversion question could be asked, R10: **42% of preserved passing suite records say PASS while holding a non-zero failure count**, because the verdict came from a pipeline's exit status. Fixed, with a probe watched flipping and a control against the lazy fix. **The §5.10 question itself remains open** — it needs execution against the base tree, and the repositories are cached at their base commits.
- **B2.2 does not settle Phase C, and that is the answer.** The oracle gap measures +2.0, +4.0, +4.4 and +20.0 across comparable pools, straddling the four-point line. The gap is produced *entirely* by the one-to-five tasks per pool whose attempts disagree; on the same fifteen tasks, two passes of one sweep gave +4.4 and +20.0, a difference of **five single lucky runs**. It is a measurement of per-run flakiness at a sample size where that is noise, not a property of the pool. **Phase C is neither cancelled nor justified.**
- **The two halves turn out to be one question.** On this corpus "select the best candidate" largely means "notice the one run in three that worked", which running the tests already does. The selection problem worth solving is choosing between candidates that *all* pass the visible tests — which is §5.10's discrimination problem under another name.
- **B2.3 is not answerable from this data**, as the phase anticipated: the checkpoint recorder captures proposed *stops*, and §1.2 predicts the effect lives at *edit* granularity. Recorded as a result about instrumentation rather than a null.

### Phase B3 — The boundary, built and seen to flip *(prerequisite for any paid run)*

§4.1's `--network none` plus wheelhouse, on Docker Desktop over WSL2. Not started before B2 because B2 needs no agent runs at all. **Not skippable before any new paid comparison**, because every score this project has published was measured with the book open.

**Exit, as commands:** the canary probe is **found with the boundary off and absent with it on**, both observed; a task whose dependencies cannot be pre-staged appears in a drops manifest and not in the denominator; `python -m eval.exposure` on a boundary-on sweep returns a floor of zero. **Envelope: under $5.**

### Phase C0 — Build the ratchet *(shipped 2026-09-16)*

**Built on:** Cline's 3-parent stash commits in private refs and its compare-and-swap restore (Apache-2.0), OpenCode's side-gitdir per-step snapshots (MIT), SWE-agent's autosubmit-on-every-failure-path (MIT). See [build-on.md](docs/research/build-on.md) for what each gives and what its limit is. **We are not writing a checkpoint store.**

The runtime already computes, on every edit, whether a given set of files still hashes to the tree a passing record observed. Keep the answer instead of printing it. Our contribution is exactly one thing: **when to snapshot** — on green-and-fresh rather than per edit, which is what turns 10-40x test invocations into roughly the cost of the check that was already running.

- On `PostToolUse`, when declared checks are green and fresh, snapshot the working tree against that fingerprint. The plugin already subscribes to `Bash|Edit|Write` and `core/verify.py` already runs declared commands unasked.
- At Stop, if the current state is not verified and a snapshot is, **say so and offer the snapshot**. Under §5.12 this is surfacing, not refusing.
- The cost that makes this impractical elsewhere — 10 to 40 times the test invocations — is avoided by invalidation: re-run what the change actually touched, which is the whole point of binding evidence to observed files.

**The known trap, recorded before building it.** A restore that produces green tests is not evidence the restore was correct: one study found checkpoint-only recovery selecting an *ineligible* source in every eligibility challenge while restoring bytes exactly and satisfying final invariants 20 times out of 20. **Task success cannot detect a bad recovery decision.** So the snapshot carries its provenance — which checks were green, over which files, at which point — and the eligibility of a restore is asserted separately from its outcome. A probe that only checks the tests pass afterwards would be green for the wrong reason, which is the failure mode this project's own memory note names.

**Exit, as a command:** `python -m pytest tests/test_ratchet.py -q`. **Met 2026-09-16**, seven tests against a real repository: a proven state is offered back after the tree moves off it; nothing is offered when nothing was proven, when the tree has not moved, or when HEAD has. The working tree, index, branches, tags and stash are asserted untouched. [journey/34](journey/34-the-ratchet.md).

**What it does not do:** restore. It names the state and prints the command, per §5.12. And it snapshots at a *stop*, not at every edit — the literature's effect is measured at edit granularity, so the cheaper placement is a deliberate under-reach that the contribution experiment will have to account for.

### Phase C1 — Derive the reproduction test, do not wait for it

**Built on:** Superpowers' systematic-debugging procedure, which already opens with reproduce-first (MIT); BMAD's open-question admission rule — *the request does not say, the code cannot settle, the user would notice* — as the test for **when to ask**, which is the thing models are measured worst at (MIT); Spec Kit's bounded clarify, at most five, one at a time, recommendation first (MIT); and the contract-before-tests ordering that carries the +9.8pp result.

§5.13's +28pp lever. At the first edit, if the task describes a failure and no `reproduced` record exists, the runtime proposes a failing test for the described condition and records whether it was seen red on the pre-change tree. That record is discriminating by construction (§2.1), which means C1 and §5.10 are the same build seen from two ends.

This is the one intervention that is **additive rather than restrictive**, so §5.12's harm argument does not apply to it — it adds an artifact rather than removing a turn.

**Three measured warnings, recorded before building it.** This is the intervention most likely to backfire in a way that looks like success, so the failure modes go in the plan rather than in the retrospective.

- **Naive "write the test first" prompting made things worse.** One study measured test-level regression rising from 6.08% to **9.94%** under TDD prompting alone, against 1.82% when the same system derived impact analysis first. Instructing the agent to do this is not the same as deriving the artifact for it.
- **A derived test that encodes the wrong failure condition is a false premise wearing a green tick** — the exact failure in §2, manufactured by us. Note that 26.9% of bug-detecting tests in the wild fail on the developer's own correct fix.
- **The evidence that an intermediate spec helps is at oracle construction, not at patch writing.** The cleanest positive result available — extracting pre/post-condition contracts before generating tests, on 90 real production bug-fix pairs across four languages — is **+9.8pp bug detection (p = 0.035)**. That is the shape to copy: derive the contract, then the test, and do not touch the patch.

**Exit:** correct-candidate survival is measured through the new check, because §5.5 says adding checks raises the chance a correct candidate is falsely rejected and this one is no exception. Forward and adversarial: the derived test must be seen **red on the pre-change tree** — a derived test that was never observed failing is not a reproduction, it is a guess with a filename.

### Phase C — Separate generation from selection *(started early, 2026-09-14)*

Selection development does not wait on P1 or on a clean benchmark. Across the two chunks, the two vanilla attempts already contain a graded success on 24 of 25 tasks and all four attempts contain one on 25 of 25. That is **oracle coverage, not achieved performance**, and it is exposure-contaminated — but it is a ready development set for the question "does the system choose the better candidate", which does not need a closed benchmark to be worth working on. Performance claims wait for a clean holdout.

This also makes the candidate the product's central object rather than a by-product: every proposed patch, its evidence and its ancestry preserved, the strongest incumbent kept while repairs are explored, and a session's final patch not automatically outranking a better earlier one.



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

Reordered by measured effect size, with the free ones first.

| Experiment | Comparison | Decision it answers | Cost |
|---|---|---|---|
| **Discrimination rate** | recorded pass vs the same command on the reverted tree | does our own evidence measure anything? | **$0** |
| **Oracle gap** | pool coverage vs selected success on saved attempts | is a selector worth building, or under the 4pp harm line? | **$0** |
| **Checkpoint density** | best intermediate candidate vs submitted | is there a better state to ratchet back to? | **$0** |
| Boundary canary | nonsense token in the fix, boundary off vs on | is the book actually closed? | <$5 |
| **Composition baseline** | vanilla vs a best-of-breed stack vs this system | **the bar this project is actually judged against** — `eval/stack.py` exists and has never been run | scoped after B3 |
| Ratchet contribution | ratchet on vs off, matched compute | does preserving the best proven state change outcomes? | scoped after B2.3 |
| Reproduction synthesis | derived reproduction test vs none, matched compute | does the +28pp lever transfer to our setting? | scoped after C1 |
| Instrument validation | gold patch, known regression, wrong patch, setup failure | can the evaluator tell these apart? | done |
| Candidate scaling | N = 1 / 4 / 8, selected vs pool coverage | is more generation buying alternatives? | gated on oracle gap |
| Selection ablation | patch text vs summaries plus evidence | does representation improve the choice? | gated on oracle gap |
| Diagnosis diversity | retries vs different grounded diagnoses | do workers escape shared mistakes? | Phase D |
| Localisation expansion | normal context vs targeted caller/sibling search | are failures caused by missing code? | **demoted** — worth 8pp against reproduction's 28pp |
| Repair vs restart | continue transcript vs fresh worker with prior facts | does reuse preserve learning without fixation? | Phase D |
| Check survival | required checks vs added generated checks | do new checks remove wrong candidates without removing right ones? | ships with C1 |
| Complementarity | repeated strongest worker vs heterogeneous pool | does configuration diversity add solutions? | Phase D |
| Gate contribution | capture-only, auto-check, blocking | what does blocking add once search exists? | **last**, per §5.12 |

**Dropped from the queue.** Role-decomposed multi-agent pipelines: a single agent executing the same workflow sequentially matched or beat the multi-agent system across seven benchmarks at roughly a tenth of the cost, and the multi-agent failure analysis attributes failure to the coordination layer itself. Cross-session memory: the best-controlled study finds no contrast surviving multiple-comparison correction, and every positive result carries a context-budget or leakage confound. Both were already deferred in §11; they are now deferred *with evidence*.

The 1.4x gate result stands for its narrow configuration. It is not an argument against spending compute through a mechanism that demonstrably creates or selects more correct patches.

---

## 9. Hypotheses

| ID | Hypothesis | Status |
|---|---|---|
| P1 | Evidence gating halves the submit-resolve gap | **no effect measured** on twelve mined bugs, on a grader now known not to check preservation. Re-run after Phase A |
| P2 | The gate does not block already-correct work | **falsified at the block, 2026-09-15**: one of four observed blocks refused a patch that was already correct, at 43 extra turns and 6.6x cost. Four events is a small sample and the direction is measured, not inferred |
| P3 | Claim inference engages when there is work | 21 percent over-claim, 25 percent missed, over 3,557 real turns |
| P13 | The runtime reads what the host sends | **qualified by H1**: replay fidelity is not delivery fidelity |
| P17a/b/c | Frozen issue-derived checks / differential comparison / interpretation probes discriminate | not started; Phase C |
| P19 | Pool coverage exceeds selected success by a margin worth attacking | **measured 2026-09-15, and it does not settle.** +2.0 to +20.0 across comparable pools; the gap comes entirely from the 1-5 tasks per pool whose attempts disagree, so at this corpus size it measures flakiness rather than a property of the pool |
| P20 | Diagnosis branching finds solutions repeated attempts do not | new; Phase D |
| P21 | Localisation expansion resolves tasks that fail from missing code | new; Phase D |
| P22 | A meaningful fraction of our recorded passing evidence is vacuous — it passes on the reverted tree | **still open, and now askable.** B2.1 found a prior defect first (R10) and fixed it; the reversion measurement needs execution against the cached base trees. Established elsewhere at 46% of validation events |
| P23 | A reproduction record (seen red before, green after) discriminates where an ordinary pass does not | new; falsifiable on saved bundles alongside P22 |
| P24 | A verified intermediate state exists that is better than the submitted one, often enough to pay for keeping it | new; Phase B2.3 at Stop granularity, C0 at edit granularity |
| P25 | Deriving a reproduction test early raises resolve rate in this setting | new; the field's +28pp lever, Phase C1 |
| P26 | Detecting lock-in saves compute even when it repairs nothing | new, and cheap: 82% of doomed runs continue past the point of no return |
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
- **"About 252 agent runs per comparison."** Withdrawn 2026-09-12. It divided the required discordant pairs by the within-arm *flip* rate, and flipping is not disagreement: a baseline that fails every time against a treatment that succeeds every time flips never and disagrees always. What the arithmetic supports is **31 pairs on which the arms disagree**; converting that to runs needs a measured rate of disagreement, which no run here has produced.
- **"An external audit found sixteen defects."** Withdrawn 2026-09-13. The audit's own appendix says "sixteen observations, not sixteen statistically independent findings ... several exercise the same underlying design defect". It named **fifteen** (E1–E6, R1–R9). H1–H4 were found here afterwards, so §4 holds nineteen: eighteen fixed, R2 narrowed.
- **"The preservation set caught its first real regression in the wild."** Withdrawn 2026-09-13. Both `regressed` runs in the B4 sweep were an `attrs` version string that a *different* agent's editable install had overwritten. The category has still never been seen outside a test.
- **"Two tasks were solved 3/3 in one pass and 0/3 in the next."** Withdrawn 2026-09-13. Twelve jinja2 runs collected zero nodes because that same install broke `import attrs`, which `trio` needs. Re-graded from their bundles, both tasks are 3/3 and 3/3.
- **"Replicates inside one sitting are more correlated with each other than two sittings are."** Withdrawn 2026-09-13. It was inferred entirely from the reversal above, which did not happen. Five of fifteen tasks split over six replicates, and the two passes agree to within 4.4 points.
- **"Pass B of the B4 sweep resolved 53.3%."** Corrected to **73.3%** after re-grading every bundle. Pass A re-graded to the same score it was given, on all forty-five runs, which is the control that says the re-grade is deterministic.
- **"Substantial tasks resolve at 27 to 40 percent."** Qualified 2026-09-14. Measured before the prompts were framed as requests. With the same tasks asking for something, a plain agent resolves 88 percent of them, so a large part of what was read as difficulty was prompts that did not ask. The band selection was made on that measurement and is declared in the lock; what it bought is smaller than it looked.
- **"Writing the specification up front is how you stop an agent building the wrong thing."** No support as of 2026-09-15, for any of the frameworks in `docs/research/cards/`. A vision paper surveying the area states plainly that no peer-reviewed study has defined, delimited or measured them; the one "study" of Spec Kit is an uncontrolled 14-person before/after with self-reported outcomes; the comparison tables circulating with per-framework completion percentages are vendor marketing with no published protocol. **This is an absence of evidence, not evidence of absence** — but it is the same absence this project criticised the fourteen for, and it applies to the front of the pipeline as much as the back.
- **"`cannot_complete` is free."** Qualified 2026-09-15. On 200 human-verified already-fixed tasks, agents make undesirable changes in **35 to 65%** of cases, so the feature addresses something real. But an abstain-or-fix instruction raised correct abstention from ~60% to ~80% **while collapsing repair of partially-broken code from 27.3% to 6%**. Caution has a measured price, and a first-class refusal outcome has to be evaluated on both populations — the already-done and the half-done — or it will look like an improvement on one of them.
- **"A passing suite record means the suite passed."** False of the implementation until 2026-09-15, and the most consequential single line in the evidence layer: the result was taken from the exit code while the parsed failure count sat unused two lines above. An agent piping `pytest` to `tail` — which 288 of 295 preserved records did, sensibly, to save context — hands the runtime `tail`'s exit status. **42% of preserved passing suite records were wrong**, and **61% of gated runs carried at least one.** Fixed, probed, controlled. What it does *not* establish: that the defect caused any run to fail. Affected runs ran a median of five suite records against two, so exposure is confounded with difficulty and the arrow may point the other way.
- **"Fresh, passing evidence establishes that an obligation is met."** Qualified 2026-09-15, and this is the load-bearing qualification of the whole design. Freshness and passing are two facts about a record and neither is the one that matters. Measured elsewhere: every model saturates the visible test suite, the visible-to-held-out gap grows about 27 points per tenfold increase in code size, and the best generated suites detect 36.15% of mutants. A record is evidence once it has been shown to discriminate (§5.10) and not before. **This project has never measured the vacuous fraction of its own evidence**; Phase B2.1 does it for $0.
- **"Localisation is a principal bottleneck."** Withdrawn as a ranking 2026-09-15. Holding the agent fixed and injecting oracle signals one at a time, perfect edit location is worth +8pp against a reproduction test's +28pp. Localisation is worth doing and is not where the leverage is, so it moves below reproduction synthesis in §8.
- **"Letting the agent execute freely during repair is what grounds the work."** Qualified 2026-09-15. Across 7,745 traces the resolve-rate difference between prohibiting and permitting execution during repair was **1.25pp and not statistically significant**, while prohibition saved substantial tokens and wall-clock. Execution matters intensely on a few problems and not at all on most. What grounds the work is possessing the right test, not the freedom to run tests.
- **"A gate that detects a real defect will improve the outcome."** Withdrawn 2026-09-15. Detection and prevention are separate properties; measured harm from intervening concentrates in early interruptions of runs that would have succeeded. This project produced that result before reading it and did not recognise it as the general case (§5.12).
- **"Our benchmark can resolve differences of a few points."** Withdrawn 2026-09-15. Differential testing of plausible SWE-bench Verified patches finds **29.6% behaviourally divergent from ground truth**, **7.8% counted correct while failing the developer suite**, and reported resolution rates **inflated by 6.2 absolute points**. No claim is made here on a delta smaller than the instrument's own validity error.
- **"None of the surveyed systems computes completion from evidence."** True of those fourteen at their pinned commits on 2026-09-09; **no longer a description of the field.** At least two shipping projects independently arrived at no-evidence-no-close with stale-on-edit invalidation. What this design still has a structural advantage in is discrimination and the ratchet — not the ledger, and not because nobody else thought of it.
- **"Denying the answer tools makes a run closed-book."** Withdrawn 2026-09-15. `git clone` was denied and the transcript shows the refusal; the agent then ran `pip download --no-binary :all: "click @ git+https://github.com/pallets/click.git@main"`, because **pip clones git URLs internally**, extracted the exact fix commit with `git format-patch`, and applied it. That run graded `resolved` and repaired nothing. Denying commands by name cannot bound a network boundary — block the package manager too and `python -c "import urllib"` remains. Only an operating-system or network boundary closes this, and it is not built.
- **"The gate improves the patch."** No support as of 2026-09-15, and this is the central claim. Graded **at the moment of the block** across nineteen gated runs, the mechanism fired four times and changed no outcome: it refused a patch that was already correct (43 extra turns, 6.6x cost), one that stayed `unfixed`, one that stayed `regressed` — the single regression it met went past it — and a fourth that stayed `resolved`. Cost is measured at 1.3x vanilla over fifty runs against fifty; benefit is unmeasured after $195. Four events is too few to conclude the gate never helps, and the asymmetry is still not neutral: a tool earns its cost with positive evidence. **The case it exists for barely occurs here** — 80 percent of first proposals are already correct — so the next test needs tasks where the agent is wrong and says otherwise.
- **"A plain agent resolves 92 percent of the selected corpus."** Withdrawn 2026-09-14 as a repair score. Twenty-four of the hundred runs name their own task’s fix commit sha in full, returned from the GitHub API as a tool result; a broader screen found returned diff hunks in forty-two. The sweep had no closed-book condition, so it measures applying a described upstream change **with access to that change**. The runs are kept under their actual access conditions rather than filtered, because retrieval may itself depend on difficulty and treatment.
- **"The gate fires on twelve percent of runs."** Corrected 2026-09-14. Six Stop-block events across **four of fifty gated runs**: 8 percent of runs, 0.12 events per run. `blocks_recorded` counts events, and D94’s sizing arithmetic was built on the mixture.
- **"On the discordant tasks the arms differed by a hook that never fired."** Withdrawn 2026-09-14. The gated `click-bec59289` run records zero Stop blocks and **four scope questions**. The package intervenes before Stop and that field counts none of it, so the arms were not identical and the comparison cannot separate chance, pre-Stop intervention and unequal retrieval.
- **"Thirty-one discordant pairs are needed."** Qualified 2026-09-14. That is a power calculation for one alternative — a 75 percent win rate among disagreements — not a universal minimum. Six discordant pairs all favouring one arm give a two-sided exact p of 0.031. The observed comparison is p = 0.5: weak evidence, not the absence of a measurement.
- **"A paired comparison at this corpus size can answer P1."** Withdrawn 2026-09-14. Thirteen tasks at two replicates cannot produce thirty-one discordant pairs when the treatment engages on twelve percent of runs; it offers two or three. The figure was in §3's own exits table before the chunk was designed.
- **"The corpus was rebuilt so that most of it discriminates."** Qualified 2026-09-14. Across a hundred paired runs, twenty-three of twenty-five tasks were resolved twice by both arms. A plain agent resolves 92 percent of the selected corpus, so the benchmark is not hard enough to measure a treatment on, and more of it is not the fix.

---

## 11. Retain, defer, stop

**Retain:** automatic collection from ordinary work; automatic execution of declared checks; provenance of expectations; five honest outcomes rather than block-or-pass; independent oracle diagnostics; the recorded history of failed hypotheses. Every one of these is substrate for §1.1 to §1.3 rather than a legacy of the gate framing.

**Promote to the centre:** discrimination (§5.10), the ratchet (§1.2), reproduction-test derivation (§5.13), and the report as the deliverable (§1.3).

**Defer, now with evidence rather than on judgement:** a second host adapter; a large always-on framework stack; a custom tree-search framework; elaborate risk routing. **Cross-session memory** — the best-controlled study shows no contrast surviving correction, and every positive result carries a leakage or context-budget confound. **Role-decomposed multi-agent pipelines** — matched by a single agent running the same workflow at roughly a tenth the cost. **Always-on context files** — two independent populations, null on correctness, over 20% additional cost; keep only short imperative rules, never repository overviews.

Correct invalidation is *not* deferred — it is P0, and §1.2 makes it the enabling mechanism rather than a correctness detail.

**Stop:** ranking work by novelty; treating the stop gate as the organising purpose; publishing a number without the qualification that bounds it; **enforcing a boundary by naming commands**; and **claiming an improvement smaller than the benchmark's own validity error.**

---

## 12. What would falsify this direction

Carried forward: pool coverage barely exceeding selected success; candidate scaling flattening immediately; every oracle diagnostic accepting candidate and maintainer fix equally; the strong baseline already at the corpus ceiling.

Added by v0.8, and each is answerable cheaply:

- **Almost none of our recorded evidence is vacuous.** If the reversion check finds that passing records overwhelmingly fail on the reverted tree, then §5.10 describes somebody else's problem, the discrimination work is unnecessary here, and the null result needs a different explanation than the one in §0. **This is the single most falsifying measurement available and it costs $0.**
- **No better intermediate state ever exists.** If runs never pass through a verified state superior to the one submitted, the ratchet has nothing to hold and §1.2 is wrong for this workload whatever it measured elsewhere.
- **The oracle gap is under four points.** Then selection is not the bottleneck, Phase C is cancelled rather than merely deprioritised, and the investment belongs entirely in generation and reproduction synthesis.
- **Derived reproduction tests are wrong often enough to cost more than they buy.** The +28pp figure is an *oracle* signal. A derived test that encodes the wrong failure condition is a false premise with a green tick on it — the exact failure this project exists to prevent, manufactured by this project. §5.5's correct-candidate survival is the check, and it must be measured before C1 ships, not after.
- **A best-of-breed stack already does this.** The comparison that matters is
  not against vanilla, which every measurement so far has used, but against
  Superpowers + ECC's hard blocks + gstack's evidence ledger + Aider's map
  installed together. If that stack matches this system, the honest outcome is
  to contribute the discrimination check upstream rather than ship a fourth
  framework. `eval/stack.py` exists; it has never been run.
- **Surfacing changes nothing either.** If a report that names which claims rest on nothing is ignored as reliably as the block was, then the evidence layer is not a product on its own, and the honest outcome is a library the search system in §5 consumes internally.

---

## Appendix: evidence trail

`docs/research/` holds the source study of fourteen systems at recorded commits, the host cards, the complementarity matrix, the licence register, the reading list (refreshed 2026-09-11 with eight sources from the audit, each carrying the limit on what may be inferred from it, and one explicit contradiction of an earlier entry), the oracle-problem card, `audit_2026_09_11/` with its reproduction script and evidence appendix, `audit_2026_09_14/` with its evidence file, and **`audit_2026_09_15/`** — the literature audit behind v0.8, whose `sources.md` credits every paper, article and documentation page that changed a decision, graded by how strongly each was verified. `build-on.md` names the prior art, licence and limit for every component now being built. `journey/` holds fifteen phases of what was tried, what was wrong, and what the measurements said. Every number in this plan is reproducible from a command in this repository, and the ones that are not yet trustworthy are marked as such in §4 and §10.
