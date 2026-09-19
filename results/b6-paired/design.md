# B6: the paired run, and what it can honestly answer

**Written before spending, and not yet run.** 2026-09-17.

> **Status: planned, NOT run.** It was launched on 2026-09-17 and stopped
> within minutes with 0 runs finished and no bundles written - the weekly
> capacity left was about 1%, against the four hours and ~$150 this design
> needs. The design is kept because the reasoning below is what makes the
> experiment worth running, not because it was run.

**If capacity is short, do not run a cheaper version of this.** One replicate
per arm halves the cost and produces a disagreement rate that cannot be
separated from agent noise - which is the exact error PLAN 10 already
withdrew a figure for. A smaller honest experiment here is fewer *tasks* at
two replicates, never fewer replicates across all tasks.

> **Qualified 2026-09-19, by an external audit, and the objection is fair.**
> Two claims above are stronger than the statistics support. One randomised
> attempt per arm per task *can* estimate an average treatment effect —
> stochasticity widens the interval, it does not make the design meaningless.
> Replication buys within-task variance and candidate pools, and it **competes
> with covering more independent tasks**; which to spend on depends on the
> estimand, which should be stated first. And the "31 discordants" figure came
> from power assumptions for one specific alternative, not from a universal
> significance requirement: at a fixed analysis, six independent discordant
> pairs all favouring one arm give a two-sided exact p = 0.03125. That is not a
> licence to collect until a p-value appears — the analysis has to be fixed in
> advance — but it does mean 16 tasks are not automatically useless.
>
> What to do instead of resuming as written: state the estimand, simulate power
> across plausible exposure, harm, rescue and task-correlation values, choose
> replication for the question being asked, and analyse repeated observations at
> the task level rather than as independent tasks.

## What it is not for

It is **not** for answering "does the gate improve outcomes" *at the power
originally assumed*. The **31 pairs on which the arms disagree** (PLAN §10) is
the number for one specific alternative, and 16 tasks cannot produce them.
Any resolve-rate difference this run reports will have an interval spanning zero
and must be read as such.

## What it is for

PLAN §10 withdrew "about 252 agent runs per comparison" and said exactly what
was missing:

> *"Converting that to runs needs a measured rate of disagreement, which no run
> here has produced."*

This run produces it. And it produces the thing that made the withdrawn figure
wrong in the first place — the distinction between **flipping** and
**disagreeing**:

- **Within-arm flip rate.** The same task, the same arm, run twice. Any
  difference is the agent's own stochasticity. This is the noise floor.
- **Between-arm disagreement rate.** The same task, vanilla against gate. This
  is signal *plus* that noise.

Neither number exists today. Without the first, the second cannot be
interpreted, which is precisely the error §10 records.

## Design

| | |
|---|---|
| tasks | 16, corpus `e2d721482fbdd2a5` — the same as B3, B4 and B5 |
| arms | `vanilla`, `gate` |
| replicates | **2 per arm per task** |
| runs | **64** |
| model | `claude-opus-5`, effort high, $15/run cap |
| sharding | 4 shards of 4 tasks, round-robin, verified non-contaminating in B4 |

The second replicate is the whole point. One replicate per arm gives a
disagreement rate that cannot be separated from noise, which is a number that
looks like an answer and is not one.

## Degrades gracefully

Each shard journals per run, so stopping early loses nothing already finished,
and the round-robin split means a partial run is still a spread across all five
repositories rather than all of one.

## What will still be missing afterwards

- Any causal claim about the gate. 16 pairs, whatever they show.
- Anything about tasks unlike these: well-specified commits from mature,
  well-maintained Python libraries.
- A clean read on runs where the base tree is broadly red, which B4 measured at
  6 of 14.
