# Resolved Is Not Pinned: One Sentence Gets Coding Agents to Write Tests That Pin Their Changes

*Draft, 2026-11-28. Every figure below comes from a sealed, pre-registered record in this
repository; each section links the record it reports. Sections marked TODO wait for an
analysis that is still running.*

## Abstract

Coding agents are judged by whether their patches pass hidden tests. A patch can pass
and still leave the repository unable to notice if the change were undone: no test
pins it. On 40 recent fixes from 12 popular Python projects, plain Claude Code (Sonnet
5.5) resolved 91 of 120 runs, and 79% of the resolved patches were **vacuous**: undoing
the source change left every test green. We compared four setups on the same tasks,
fresh and interleaved, in 480 sealed runs with the analysis fixed in advance: nothing;
one line of project instruction ("Add a test that fails without your change."); a
skill system (superpowers 7.0.2); and a runtime verification layer (ElevenPowers).
Resolve rates did not differ. Vacuity did: 79%, **0%**, 81% and 49%. The instruction
beat the runtime check on every task where they differed (Holm-adjusted p = 0.0005),
and the skill system did nothing on these single requests. The instruction's tests are
not tuned to the agent's own code: 183 of its 186 pinning tests also pass on the
upstream maintainers' fix, which the agent never saw.

## 1. Introduction

Benchmarks for coding agents ask one question of a patch: do the hidden tests pass?
A second question matters to whoever maintains the code afterwards: **would the
repository notice if this change were undone?** If not, the fix is unprotected, and
the next edit can remove it silently.

We call a resolved patch **VACUOUS** when reverting its source change leaves the
repository's tests, including any the agent wrote, all passing. We measure it with a
revert probe (Section 3.3) and ask three questions:

- **RQ1.** How often are resolved agent patches vacuous, and what changes it?
- **RQ2.** When agents do write pinning tests, do they test the requested behaviour, or
  their own implementation?
- **RQ3.** How much of each changed line do the tests pin? (TODO, Section 4.3)

Contributions: a pre-registered four-arm comparison on independently sourced tasks;
the finding that a one-line instruction removes vacuity entirely while a skill system
and a runtime check do not; a test-transfer check showing the instruction's tests
describe behaviour; and every protocol, record and analysis script, sealed before the
runs.

## 2. Related work

- **Weak benchmark tests.** UTBoost [1] found SWE-bench patches wrongly accepted by
  insufficient tests; SWE-ABS [2] strengthens SWE-bench tests with generated mutant
  patches. These concern the *benchmark's* tests; we study the tests the *agent* leaves
  in the repository.
- **Agent-written tests.** Chen et al. [3] find that how many tests agents write barely
  changes task success. We agree on success, and show what it misses: whether the
  change is pinned.
- **Tests in agent pull requests.** Haque et al. [4] measure how often agentic pull
  requests include tests; Milanese et al. [5] compare testing in human-agent and
  human-only pull requests. Both measure presence or smells, not whether a test pins
  the change.
- **Evaluating generated tests.** SWT-bench [6] scores a generated test by whether it
  fails before the repository's fix and passes after. We borrow it for RQ2, against
  the upstream fix the agent never saw.

## 3. Method

### 3.1 Tasks

40 tasks from 12 permissive, pure-Python repositories in the top-PyPI ranking,
commits after 2026-06-01, taken by a frozen rule (seeded hash order, at most 4 per
repository). The prompt is the upstream commit message. Each task runs on its own
closed-book interpreter: the fixed release is not importable, network tools are
denied, and every tool call reaching outside the workspace is recorded. All 40 were
rehearsed on their gold patches with no model: the base fails, the gold source
resolves, the gold patch with its tests is not vacuous, and its source alone is.

### 3.2 Setups

| setup | added to the workspace before the seed commit |
|---|---|
| nothing | — |
| instruction | `CLAUDE.md`: `Add a test that fails without your change.` |
| skill system | superpowers 7.0.2 enabled in project settings |
| runtime check | ElevenPowers installed, the task's test command declared |

Identical in all four: Claude Code 2.1.319, Sonnet 5.5 at medium effort, the same
prompt with a line saying no one will answer questions, the same tools (Bash, Read,
Edit, Write, Glob, Grep, Skill), a 900 s cap, user settings and user memory excluded.
A run counts only if its own init and hook events show exactly its setup's plugins.
The instruction's delivery was checked both ways: asked to quote its instructions, an
agent with the file quoted it and one without answered `NONE`.

### 3.3 Measures

- **Resolved:** the upstream fix's hidden tests pass on the agent's patch.
- **VACUOUS** (resolved runs): apply the patch; deselect tests already failing; restore
  every changed non-test source file to the base; run the suite. Vacuous if it stays
  green. A no-op edit must keep the suite green or the run is not scored.
- **Test transfer** (RQ2): a *pinning test* passes with the agent's whole patch and not
  with its test files alone; it *transfers* if it also passes with the upstream source
  fix plus the agent's test files (after SWT-bench [6]).
- **Mutation score** (RQ3): Cosmic Ray 8.7.0 mutants on the changed lines only, at most
  8 per run, judged like the revert.

### 3.4 Protocol and analysis

480 slots (40 tasks × 4 setups × 3 replicates), sealed with the corpus, harness and
runtime fingerprints before the first run, never retried. Arm order rotates with task
and replicate. Primary analysis: five pairs, two-sided Wilcoxon signed-rank over tasks
of the per-task vacuous fraction among resolved runs, Holm-adjusted together. The
design, the analysis code and the sealed protocol were pushed before the first run.

## 4. Results

### 4.1 RQ1: vacuity by setup

478 of 480 runs were graded (two failed on a transient TLS error on the host, one
in each of two setups).

| | nothing | instruction | skill system | runtime check |
|---|---|---|---|---|
| resolved | 91 / 120 | 90 / 120 | 89 / 119 | 90 / 119 |
| **vacuous among resolved** | 72 (79%) | **0 (0%)** | 72 (81%) | 44 (49%) |
| resolved patches changing a test file | 18 | 90 | 17 | 46 |
| mean model seconds | 22.0 | 30.8 | 23.6 | 51.5 |

| pair | tasks differing | direction | Holm p |
|---|---|---|---|
| nothing vs instruction | 26 | instruction lower on all 26 | 0.00001 |
| nothing vs skill system | 5 | 3 vs 2 | 1.0 |
| instruction vs runtime check | 18 | instruction lower on all 18 | 0.0005 |
| skill system vs runtime check | 17 | runtime check lower on 14 | 0.0053 |
| nothing vs runtime check | 14 | runtime check lower on 13 | 0.0053 |

Resolve rates differed in no pair (sign tests, p ≥ 0.625). An earlier, separately
sealed sweep of the same tasks (October 2026, 240 runs, without the unattended line or
Skill tool) found 84% against 37% for nothing against the runtime check; the effect
replicates. The mechanism is the test file: of 107 vacuous patches in that sweep,
106 contained none.

### 4.2 RQ2: do the tests pin behaviour?

| | nothing | instruction | skill system | runtime check |
|---|---|---|---|---|
| runs with a pinning test | 12 | 87 | 13 | 43 |
| all pinning tests transfer | 12 | 86 | 13 | 43 |
| pinning tests transferring | 29 / 29 | 183 / 186 | 30 / 30 | 69 / 69 |

The one instruction run that does not transfer asserts an ordering the request left
open ("transfer transport ownership before processing") that upstream chose
differently. Five runs of one task could not be measured: the agents' patches and the
upstream fix both edit the same non-test data file.

### 4.3 RQ3: mutation score on the changed lines

TODO: `eval/heldout_mutation.py` on the 360 resolved runs, running.

## 5. Discussion

- **The cheapest intervention wins.** One sentence in `CLAUDE.md` took vacuity from 79%
  to 0%, at 40% more model time and no change in resolve rate, and its tests describe
  behaviour the maintainers' fix shares.
- **A skill system that is loaded is not a skill system that is used.** Superpowers'
  skills loaded in every run; on small single requests the agent mostly did not invoke
  them, and vacuity matched having nothing.
- **A runtime check surfaces less than it measures.** ElevenPowers' guide profile reports
  an untested change but does not ask for the test in so many words; half its resolved
  patches came without one, at twice the instruction's model time. Its value here was
  the measurement: the revert probe is what found all of the above.

## 6. Threats to validity

- One model (Sonnet 5.5), one host (Claude Code), Python, 12 repositories, small fixes
  (the upstream fixes change a median 10.5 source lines, 1 to 143). One wording of the
  instruction.
- VACUOUS and transfer say the tests notice the change and agree with upstream; they do
  not grade test quality beyond that. Equivalent mutants make mutation scores lower bounds.
- The four setups were run by the project that builds one of them. The protocol, the
  analysis and the sealed records were committed before each run, and every run's
  record is kept.
- The fix is in a new source file in one task (7 runs); the revert probe restores only
  changed existing files.

## 7. Availability

Design: `docs/superpowers/specs/2026-11-26-heldout-four-arms-design.md`. Protocol, records,
analysis: `results/heldout/sweep-2026-11-26-four/`. Code: `eval/heldout_run.py`,
`eval/heldout_analyse.py`, `eval/heldout_transfer.py`, `eval/heldout_mutation.py`.

## References

1. UTBoost: Rigorous Evaluation of Coding Agents on SWE-Bench. arXiv:2506.09289.
2. SWE-ABS. arXiv:2603.00520.
3. Chen et al. Rethinking the Value of Agent-Generated Tests for LLM-Based Software
   Engineering Agents. arXiv:2602.07900.
4. Haque, Ingale, Csallner. Test inclusion in agentic pull requests. MSR '26. arXiv:2601.03556.
5. Milanese et al. Testing in human-agent pull requests. arXiv:2601.21194.
6. Mündler, Müller, He, Vechev. SWT-Bench: Testing and Validating Real-World Bug-Fixes with
   Code Agents. NeurIPS 2024. arXiv:2406.12952.

*Reference details beyond titles and identifiers were read from abstracts and search
summaries, not the full papers; check each before submission.*
