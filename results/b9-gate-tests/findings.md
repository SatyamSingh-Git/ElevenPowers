# B9: do agents working under the gate write tests that pin their change?

**Run 2026-09-24, $0, no agent.** Every resolved patch from the paired `chunks`
sweep — 49 gate-arm, 46 vanilla-arm, 25 tasks, `claude-sonnet-5`, one sweep —
put through the B7 mutation probe.

## Why this sweep, and why this question

`results/chunks` is the one place both arms ran the same tasks with the same
model in the same sweep, so a difference between them is the arm and not a
model or a date. Pooling gate bundles from B4 with vanilla bundles from
elsewhere would have measured the sweep.

The central claim — *the gate improves the work* — has been measured on resolve
rate and never moved (PLAN §10). This measures it on something else: whether the
tests an agent leaves behind pin the change it made.

## Method

Each resolved patch is applied at its base commit, and mutants are confined to
the source lines that patch changed. Same probe, operators, three traps and
survive control as B7 (`results/b7-mutants/`). One control changes meaning: for
an *agent's* patch, reverting the change and seeing it survive is not a harness
fault — the harness is validated on the same task — it is the finding. The tests
in the tree cannot tell the fix from its absence. That is **VACUOUS** in
`core/stress.py`'s sense, and it is recorded as such.

Metrics were fixed in `analyse.py` before any result was read. The primary
comparison is the per-task survival fraction, gate against vanilla. Vacuity and
test files written are reported beside it.

## Result

| | mutants survived | VACUOUS patches | test files per patch |
|---|---|---|---|
| **gate** | 50 / 265 (19%) | **4 / 49 (8%)** | 1.43 |
| **vanilla** | 58 / 251 (23%) | **10 / 46 (22%)** | 1.24 |

**Primary, and it is a null.** Per task, gate survival is higher on 3, lower on
3, tied on 17: exact sign test **p = 1.000**. Among patches that have tests,
the gate's tests pin the change no better and no worse than vanilla's.

**Secondary, and it points one way.** Per task, the gate has fewer vacuous
patches on **5**, more on **0**, tied on **19**: **p = 0.062**. Suggestive, not
significant.

**What a vacuous patch is, measured rather than assumed.** All 14 changed only
files that existed at the base commit — so the revert really removed the fix,
and the known artefact (a fix living in a newly created file, which the revert
leaves in place) does not apply to any of them. And **all 14 contain zero test
files.** The agent wrote no test, and the repository's existing suite cannot see
the difference between the fix and no fix.

**0** mutants were counted as killed by a suite timing out, although the machine
was heavily loaded throughout.

## What this changes

**The gate's measurable effect on tests is whether a test exists at all, not how
good it is.** Its first obligation is *a test covering the change passes*. That
plausibly moves an agent from writing no test to writing one — the vacuous case
— and does nothing for how much of the change that test pins. Both halves of that
are consistent with this data; neither is established by it.

**And it reopens a withdrawn claim.** PLAN §10 qualified *"agents routinely
finish on evidence that could not have failed"* because B3 and B4 found only **1
vacuous in 22** against the literature's 46% (and 23.8% of rollouts closing on a
wholly non-discriminating evidence base). Both B3 and B4 were **gate-arm runs
only** — 16 and 16, no vanilla arm — which B4's own findings say. So the rate was
only ever measured *with the mechanism that prevents it switched on*. Here, the
vanilla arm alone is **10 of 46, 22%**, close to that 23.8%.

The two measurements differ in corpus, model and method — B3/B4 ran the declared
command through `stress.py` inside the run; this reverts the patch and runs the
whole suite afterwards — so this does not restore the claim. It removes the
reason it was withdrawn, and says what measurement would settle it: vacuity by
arm, in one sweep, by one method.

## What it does not say

- **Not significant**, on either metric.
- **Sonnet 5 only**, on one corpus of 25 well-maintained Python tasks.
- **Resolved patches only.** An unresolved patch with vacuous tests is a
  different and possibly commoner case.
- **Eight sampled mutants per patch**, as in B7.
- **Nothing about why.** The gate could reduce vacuity through its obligation
  text, its reports or its blocks; the data cannot tell them apart.

Reproduce: `chunks_probe.py` and `analyse.py`, the exact code that ran. Their
paths point at the session's scratch directory and need adjusting; the data is in
`patches.json`.
