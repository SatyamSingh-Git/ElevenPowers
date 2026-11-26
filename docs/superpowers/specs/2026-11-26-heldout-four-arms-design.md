# What makes an agent pin its change: four arms on the held-out tasks

2026-11-26. Pre-registration, written and pushed before any run of this study.
Follows the held-out sweep of 2026-10-22
([results](../../../results/heldout/sweep-2026-10-22/README.md)): VACUOUS among
resolved patches 84% with plain Claude Code against 37% with ElevenPowers
(p = 0.00016), resolve unchanged, the difference being whether a test was written.
User: "go on run it", for the comparison against a one-line instruction and against
superpowers; standing authorization for Sonnet 5.5 at medium on the subscription.

## Question

October compared nothing with ElevenPowers. A reader's first question is whether
simply telling the agent to write a test does the same, and superpowers alone left
1 VACUOUS stage of 475 on the multi-stage cases (different tasks). So, on the same
40 held-out tasks: does an agent pin its change with **nothing**, with **one line
of instruction**, with **a skill system** (superpowers), or with **a runtime check**
(ElevenPowers)?

## Arms

All four are run fresh and interleaved, so model or host drift since October falls
on every arm alike. October's two arms are not reused as comparators; the fresh
`ordinary` and `assisted` arms are also a replication of October.

| arm | what differs in the workspace before the seed commit |
|---|---|
| `ordinary` | nothing |
| `instructed` | `CLAUDE.md` containing exactly: `Add a test that fails without your change.` |
| `superpowers` | `.claude/settings.json` enabling `superpowers@claude-plugins-official` (as `eval/multistage_run.py` does) |
| `assisted` | ElevenPowers installed, the task's test command declared (as October) |

Identical in every arm: the prompt is the upstream commit message followed by the
multi-stage runner's unattended line ("I won't be around to answer questions while
you work on this, so make any decisions yourself and finish the request in this
turn."), because a print-mode turn that stops to ask produces no patch; the tool
list is `Bash,Read,Edit,Write,Glob,Grep,Skill` (superpowers works through Skill;
the other arms have no skills to call); Sonnet 5.5 at medium effort, 900 s cap,
closed book with the October denial list, the subscription launcher that keeps
user settings, user plugins and the user's own `CLAUDE.md` out.

Two differences from October, both applied to all four arms: the unattended line
and the Skill tool.

## Runs

40 tasks (`results/heldout/corpus.json`, unchanged) × 4 arms × 3 replicates = 480
slots, sealed before the first run and never retried. Slots are ordered replicate by
replicate (all tasks' replicate 0 before any replicate 1), and within a task the arm
order rotates with the task index and replicate, so a sweep stopped early leaves
whole replicates of every arm. Two workers take alternate slots.

A slot qualifies only if its run completed on the one model and, from the run's own
init and hook events: superpowers is loaded exactly in `superpowers`, ElevenPowers'
session-start context appears exactly in `assisted`. The init event lists no memory
files, so `CLAUDE.md` delivery in `instructed` is checked once, in the harness check
below, and stated as a condition.

**Harness check, before sealing.** The 40 tasks rehearsed on their gold patches with
no model (40/40 required, as October). Then one sealed four-slot check batch on one
task, one slot per arm, kept and reported but outside the study; plus a one-turn
probe in an `instructed` workspace asking what the project instructions say.

## Estimates

From October ($0.065 a plain run, $0.094 an assisted one, about 30 s and 100 s of wall
time) and the multi-stage superpowers runs: about $45-55 in all, and 6-7 hours with
two workers. Sized replicate by replicate so a stop at any point leaves whole
replicates.

## Analysis (fixed now; `eval/heldout_analyse.py`)

Per task and arm, the VACUOUS fraction among resolved graded runs. For each pair,
the two-sided Wilcoxon signed-rank test over tasks of the difference; tasks where
either arm of the pair resolved nothing are dropped and counted, ties counted.
Replicates are aggregated per task, never treated as tasks.

**Primary: five pairs, Holm-adjusted together at α = 0.05.**

1. `ordinary` - `instructed`: does one line of instruction reduce VACUOUS?
2. `ordinary` - `superpowers`: does a skill system?
3. `instructed` - `assisted`: does the runtime check add anything beyond the line?
4. `superpowers` - `assisted`: does it add anything beyond superpowers?
5. `ordinary` - `assisted`: October's comparison, replicated.

**Secondary**, reported beside and never in place of the primary: resolve per pair
(sign test over tasks); per arm, the share of resolved patches that add a test file,
mean seconds and total cost; October's two arms beside the fresh ones, descriptive.

**What would change the reading.** If (1) is significant and (3) is not, the effect
is the instruction and ElevenPowers' contribution is the measurement, not the
agent's behaviour. If (3) is significant, the runtime adds something an instruction
does not. Either way it is reported as it falls.

## Bounds stated now

One model, one host, Python, 12 repositories, small fixes. VACUOUS is this project's
measure of whether the repository's tests pin the change, not correctness. The
instruction is one wording; a different wording could do better or worse.
