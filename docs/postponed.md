# Postponed, with the trigger that would build it

Postponement is a decision with a condition, not a quiet drop. Nothing here is
built until its trigger fires, and the trigger is a measurement rather than an
opinion.

| Subsystem | Trigger |
|---|---|
| Workflow compiler | Dogfooding shows the agent failing to sequence work toward obligations it clearly understands. Until then, obligations are order-free and only the end state is checked |
| Repository model (static test-impact analysis) | Measured rate of "one edit stales everything" is annoying in daily use (P4). Then narrow `observed` to the import closure of each test |
| Dynamic invalidation from coverage | Static import closure proves too coarse on a real codebase |
| Context engine with per-stage budgets | Large-repository tasks fail on context, measured rather than assumed |
| Memory across sessions | Multi-session dogfooding shows the same fact re-derived three times. Note that the two systems in the field with real memory code both report automatic capture failing to produce useful records |
| Model routing | Cost becomes a real complaint. The host already selects models per subagent |
| Critics and subagents | Regression rate on risky changes stays high with the gate on |
| Second host adapter | Someone asks, or Phase 1 numbers justify porting. Codex first: its hook engine is the closest match to Claude Code's |
| Full 48-task harness | A decision needs a number the micro and smoke tiers cannot produce |
| Browser evidence | A UI claim type is needed. gstack's Playwright daemon is MIT and liftable |

Built since this file was written: the repeat runner, whose absence let a single lucky run satisfy the stability obligation, a false verification on the one task class this project claims as its differentiator; the scope guard, whose allow list was read in three places and written by nothing; and the host integration layer, where three further defects were found by audit, the worst of which recorded every failing command as passing.

Two things are deliberately still not built, and both now have sharper triggers:

| Not built | Trigger |
|---|---|
| Reconstructing repository state from a transcript's file-history rows | Replay needs to measure freshness and staleness, which it currently cannot. Only worth it once P4 is the question being asked |
| Replaying subagent transcripts | Subagent sessions are stored separately, 1,290 of them alongside 241 main sessions. Worth adding when subagent work is gated |

---

## Added 2026-09-23, from the question "what about the edge cases?"

`PLAN.md` §5.16 proposes diff-scoped mutation as the answer to *is this changed
logic actually tested*. These three were considered alongside it and deferred,
each with the measurement that would revive it. Deferring them is a decision
about **order**, not about value: §5.16 is cheaper to falsify, and if it is
falsified the reason will most likely apply to these too.

| Not built | Trigger |
|---|---|
| **Property-based testing** (`hypothesis`) on changed functions | §5.16 ships, and its surviving mutants cluster on *input values* rather than on branches — that is the signature of a gap properties close and mutants do not. Deferred because inferring properties without a specification produces noise, and this project has paid for unmeasured noise before |
| **Differential testing, old tree against new** | A measured rate of changes whose behavioural difference no test covers. Directly answers *did you change something you did not mean to*, which mutation does not. Needs input generation, so it inherits the property-inference problem above and is ordered behind it |
| **Mutating code the change *depends on*, not only the change itself** | `core/radius.py` already computes the siblings and callers of a changed symbol. If §5.16's survivors are concentrated at the boundary between changed and unchanged code, the scope is wrong and this is the correction. Deferred because it breaks the diff bound that makes §5.16 affordable |

**What has no trigger, because nothing would satisfy it.** Deciding whether the
logic is *correct*. That needs a specification the repository does not have, and
no mechanism in this file or in `PLAN.md` produces one. It is written here so
that the absence is a recorded decision rather than an oversight — see §1.6.
