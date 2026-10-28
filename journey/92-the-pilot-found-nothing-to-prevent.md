# 92 — the pilot found nothing to prevent

Multi-stage v2's pilot ran on 2026-10-28: `access_policy` and `layered_config`,
superpowers alone against superpowers plus ElevenPowers, one six-request
conversation each, Sonnet 5.5 at medium effort. Its job was to show that
something can go wrong before the full run is paid for. Nothing real did, in
either arm.

## What the qualification found first

Three things, each by running the real host before writing the runner:

- **Superpowers could not have worked.** The subscription launcher's tool list
  has no Skill tool. Superpowers' 37 skills were listed in the init event and
  could not be invoked; only its startup text would have arrived. The runner
  now allows Skill in both arms. Agent stays denied, as in every earlier
  controller, so superpowers runs its plans inline, which it supports.
- **Every subscription run carried the operator's own `~/.claude/CLAUDE.md`.**
  `--setting-sources project,local` keeps user plugins out, but not the user's
  instructions. A one-turn probe named the file. The held-out sweep carried it
  in both arms. The launcher now excludes it, and the exclusion was watched
  flipping both ways with the project's own CLAUDE.md still arriving.
- **A resumed session reports cumulative cost.** A stage's own cost is the
  difference.

## The pilot

| | lost earlier groups | stale facts (mechanical) | cost | model time |
|---|---|---|---|---|
| superpowers, `access_policy` | 0 | 0 | $0.59 | 185 s |
| superpowers, `layered_config` | 0 | 2 | $0.96 | 332 s |
| + ElevenPowers, `access_policy` | 0 | 1 | $0.85 | 471 s |
| + ElevenPowers, `layered_config` | 0 | 2 | $1.00 | 457 s |

All 24 stages completed and qualified. Every stage of every conversation added a
changelog entry, left the protected file alone, passed its new groups, and gave
both bug fixes a test that fails without the fix. The agent found dependents by
searching for them itself, in both arms. It invoked one superpowers skill in 24
turns.

**Every stale fact is the oracle's, not the agent's.** `msg.lookup` (both arms,
stages 5 and 6): the request asked for a new error from `Config.get`,
`Config[key]` and `Config.source`. Both agents left the command line's message
as it was and documented exactly that, with a new row for the API. The frozen
fact assumed the reference's choice to change the command line too, which no
request stated and no group required. `lint.redundant-role` (ElevenPowers arm,
stage 6): the agent made the lint message list every parent and renamed the
placeholder `{parent}` to `{parents}`. Its docs describe its code; the oracle
matches the placeholder's spelling, and the request never mentions the lint.
Two independent review rounds and a no-model rehearsal did not catch either.
The rehearsal only checks that the reference passes and that broken variants
fail. It cannot see a correct alternative the oracle refuses. A real agent was
the first to try one.

## The verdict, both ways

The frozen go rule is met mechanically, with 2 stale facts in the superpowers
arm. Read honestly, it is not met: the superpowers arm made no mistake the
experiment exists to count. On these two cases and this model, the field
report's effect has nothing to show itself against. The spec's response to no
headroom is to redesign the stage rules for every case before spending more.
The oracle defects get fixed by a general rule, never by editing the two cases
the pilot saw.

ElevenPowers cost 19% more and took 1.8 times the model time here, which is
in line with the field report's "slightly slower".

*Reproduce: `python -m eval.multistage_run collect --batch <batch> --out <file>
--regrade` from the kept snapshots; records in `results/multistage/`.*
