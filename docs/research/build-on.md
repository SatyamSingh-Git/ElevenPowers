# What we build on: prior art for each v0.8 component

2026-09-15. Companion to [complementarity-matrix.md](complementarity-matrix.md),
which did this for v0.7's architecture. PLAN v0.8 named three builds and did not
say what they stand on. This does.

**The standing rule, restated because v0.8 drifted from it.** Nothing here is
built because nobody else built it. Every component below starts from the best
existing implementation, names its licence and its limit, and states the one
thing we add. **A component with no prior art listed is a component nobody
researched yet, not a component that is original.**

Licences are all permissive and compatible with Apache-2.0
([licenses.md](licenses.md)); reuse obligations and per-repo caveats are
recorded there and are not repeated here. Every reused file carries a provenance
header and an entry in `NOTICE`.

---

## C0 — The ratchet: keep the best proven state

**What the research says.** 60-69% of failures reach and edit the correct
functions and still produce a wrong patch; five documented cases produced a
patch identical to the reference mid-trajectory and then corrupted it, all five
recovered by edit-commit checkpointing. Checkpoint-and-resume measures +25.6pp
in one study, +8pp in another. The published blocker is **10-40x test
invocations**.

**What we are not writing.** A checkpoint store. Two exist and both are better
than a first attempt would be.

| Piece | From | Licence | What it gives us |
|---|---|---|---|
| 3-parent stash commits in private refs, persistent private index | **Cline** `hooks/checkpoint-hooks.ts` | Apache-2.0 | Snapshots that survive anything, without touching the user's branch, index or stash |
| **Compare-and-swap restore that refuses when HEAD moved** | **Cline** `session/checkpoint-restore.ts` | Apache-2.0 | See below — this is the important one |
| Side-gitdir snapshots with per-step patches and revert | **OpenCode** `snapshot/index.ts`, `session/revert.ts` | MIT | Per-step granularity and a revert path already shaped for an agent loop |
| Autosubmit on every failure path, recovering the diff from a dead container | **SWE-agent** `agents.py`, `tools/diff_state` | MIT | The candidate is never lost, including on crash — already a lesson this project learned the expensive way |
| Evidence bound to a working-tree hash | **gstack** `bin/gstack-evidence`, `gstack-wtree` | MIT | Prior art for our own ledger; cited, not copied |
| Resume *with learnings* rather than blind restart | AgentRewind (arXiv 2608.14380) | paper | The resume carries what the failed attempt established |

**Cline already solved the trap the 2026 literature just named.** The
recoverability paper's finding is that *"a saved state is not necessarily a
suitable place to resume"* — checkpoint-only recovery picked an ineligible
source in every eligibility challenge while restoring bytes perfectly and
satisfying final invariants 20/20. **Task success cannot detect a bad recovery
decision.** Cline's compare-and-swap restore, which refuses when HEAD has moved
underneath it, is exactly an eligibility check on the restore rather than a
check on its outcome. A paper names the gap; a shipping product had already
closed it. Take Cline's.

**What we add, and it is the only part that is ours.** *When* to snapshot.
Everyone else snapshots per step or per edit, which is why the naive version
costs 10-40x in test invocations. We snapshot **when declared checks are green
and fresh against the exact files they observed** — `core/evidence.py:87`
already computes that on every edit, and `core/verify.py` already runs declared
commands unasked. Invalidation is what turns an unaffordable intervention into
a free one. That is Test Impact Analysis pointed at checkpoint selection, and
it is the single strongest thing this architecture can do that the others
cannot.

---

## C1 — The reproduction test: derive it, do not wait for it

**What the research says.** A reproduction test is worth **+28pp** against
perfect localisation's +8pp. Deriving a contract *before* generating tests is
worth **+9.8pp bug detection (p = 0.035)** on 90 real production bug-fix pairs.
Interaction on underspecified tasks recovers up to +74% relative — but models
detect underspecification at between 89% and chance, so *knowing when to ask* is
the hard part. Naive "write the test first" prompting made regressions **worse**
(6.08% → 9.94%).

| Piece | From | Licence | What it gives us |
|---|---|---|---|
| Systematic debugging: **reproduce first**, instrument boundaries, hypotheses, condition-based waiting, 3-fix breaker | **Superpowers** `systematic-debugging/SKILL.md` | MIT | The procedure, already written and field-tested. Reproduce-before-fix is step one |
| Open-question admission rule: *the request does not say, the code cannot settle, the user would notice* | **BMAD** `bmad-project-context/references/best-practices.md` | MIT | A codifiable test for **when to ask** — the exact thing models are measured bad at |
| Bounded clarification: at most 5, one at a time, recommendation first, write-back per answer | **Spec Kit** `clarify.md` steps 3-9 | MIT | The protocol that stops clarification becoming its own ceremony |
| Typed gap grammar: missing, partial, contradicts, unrequested | **Spec Kit** `converge.md` | MIT | Vocabulary for what a derived contract is missing |
| Contract extraction before test generation | arXiv 2608.17177 | paper | The ordering that carries the measured effect — it helps at **oracle construction**, not at patch writing |
| Execution-based selection over many candidates | **Agentless** | MIT | Prior art for choosing among derived tests by running them |

**What we add.** The **red-before-green binding**. A derived test is not
accepted because it was generated; it is accepted because it was **observed
failing on the pre-change tree and passing after**, both bound to content
hashes. That turns the field's largest lever into a proof of discrimination at
the same time — and it is why `reproduced` at
`core/obligations.py:149` was the right obligation written at the wrong end of
the task.

**The guard against our own failure mode.** A derived test encoding the wrong
failure condition is a false premise wearing a green tick — the exact thing §2
exists to prevent, manufactured by us. BMAD's admission rule and Spec Kit's
bounded clarify are the brake: when the code cannot settle it and the user would
notice, **ask** rather than derive.

---

## §5.10 — Discrimination: does this check discriminate?

**What the research says.** **46.0% of agent validation evidence carries no
bug-discriminating information**; **77% of SWE-bench Verified instances admit a
wrong-but-passing patch**; generated suites detect 36.15% of mutants.

**We are not writing a mutation engine.** Mature ones exist — `mutmut` and
`cosmic-ray` for Python, PIT for the JVM — and the general literature on
mutation-guided test generation at industrial scale is established.

| Piece | From | Licence | What it gives us |
|---|---|---|---|
| **Revert-on-new-lint**: apply, re-check, revert if the check worsened, mapping pre-existing errors through the edit window | **SWE-agent** `tools/windowed/lib/flake8_utils.py` | MIT | The revert-and-recheck loop, already built. We point the same shape at tests instead of lint |
| Differential patch testing to expose behavioural divergence | PatchDiff (arXiv 2503.15223) | paper | The general form of "does this patch do something different" |
| Mutation operators and runners | `mutmut`, `cosmic-ray` | see their licences | The engine, if we ever need mutants beyond reversion |
| Reproducible harness with request hashes and replay | **Aider** `benchmark/benchmark.py` | Apache-2.0 | Prior art for making the measurement re-runnable |

**What we add.** **Scoped reversion.** A general mutation run is expensive
because it does not know what to re-run. We do: every record names the exact
files it observed, so reverting *those* and re-running *that* command is one
mutant, correctly targeted, at roughly the cost of the original check. This is
the same invalidation dividend as C0, which is not a coincidence — it is the
one asset this design has.

---

## What we deliberately do not build

| Concern | Use instead | Licence | Why not build |
|---|---|---|---|
| Repository map / localisation | **Aider** `repomap.py` — tree-sitter tags, symbol graph, personalised PageRank, token-budgeted render | Apache-2.0 | The best in the field by the survey's own reading, and ORACLE-SWE prices perfect localisation at **+8pp**. Not where leverage is |
| Incremental code index | **Continue** — FTS5 trigrams, collapsed-AST chunker, branch-tagged incremental index | Apache-2.0 | Years of work; IDE-bound but portable. Only if retrieval becomes the bottleneck |
| `--no-verify` and destructive-command bypass | **ECC** `block-no-verify.js`, `config-protection.js`, destructive classifier handling heredocs, subshells and `sh -c` | MIT | Small, exact, already handles the bypasses. The market research named agent hook-bypass as the strongest specific unmet need, and this is the answer already written |
| Compaction survival | **OpenCode** `session/compaction.ts` (verbatim tail, chained schema, separate pruning); **Cline** deterministic overflow recovery | MIT / Apache-2.0 | §5.14 needs obligations re-asserted after compaction, not a new compactor |
| Blind review ordering | **BMAD** `step-04-review.md` — reviewers see the diff, the author's narrative reaches one lens last | MIT | The matrix rates this **full coverage as a procedure**. Drop the finding floor, keep the ordering |
| Lower-bound baseline | **mini-SWE-agent** — 190 lines, one bash tool | MIT | Any harness must beat it to justify existing. Keep it as the control arm |
| Spec-first frameworks | *nothing* | — | No controlled evidence that any of them improves task success. Not a borrow; a recorded absence |

---

## What is genuinely ours, stated narrowly

After all of the above, three things:

1. **Invalidation as an economic mechanism, not a correctness detail.**
   Evidence bound to the exact bytes it observed makes checkpoint selection and
   scoped reversion cheap. Everyone else pays 10-40x or does not do it.
2. **Discrimination as a state.** `PASS` and `FRESH` are facts about a record;
   whether it *could have failed* is a third fact nobody stores. `reproduced` is
   the cheap proof of it.
3. **Obligations that arrive at the first edit and survive compaction.** The
   matrix's residual gap 1 — *process-stage gates enforced by code* — is still
   open, and §5.14 adds the reason nobody has closed it: soft policy decays 8.3x
   faster than hard norms under compaction.

That list is deliberately short. Everything else on the roadmap has a better
implementation already written by somebody else, under a licence that lets us
use it.

## What this changes in the plan

- Phases C0 and C1 name their prior art and their licence before their design.
- Localisation stays demoted, and when it is wanted it is Aider's, not ours.
- The composition baseline in [complementarity-matrix.md](complementarity-matrix.md) §6
  is still the bar: the system must beat a stack of best-of-breed pieces, not
  only vanilla.
- **Residual-gap framing is retired as an investment filter** (PLAN §1.5). It
  stays useful as what it is: a map of where the borrowing runs out.
