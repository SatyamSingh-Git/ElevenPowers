# Four arms on the held-out tasks — sweep of 2026-11-26

What makes an agent pin its change: nothing, a one-line instruction, superpowers,
or ElevenPowers? Design and analysis were fixed before any run:
[pre-registration](../../../docs/superpowers/specs/2026-11-26-heldout-four-arms-design.md),
`eval/heldout_analyse.py --four-arms`.

**Status: running.** Results go here when the sweep is complete.

## Conditions

Claude Code 2.1.319, Sonnet 5.5 at medium effort on a claude.ai Max subscription,
superpowers 7.0.2 (`superpowers@claude-plugins-official`), ElevenPowers at the
sealed runtime fingerprint. Every run's init event lists Claude Code's built-in
plugins in every arm, plus superpowers in its own arm only; the launcher keeps user
settings, user plugins and the user's own `CLAUDE.md` out.

## Before sealing (no model, then one cent per check)

- **Rehearsal, no model:** 40 of 40 tasks usable on their gold patches, identical to
  October's rehearsal on every check (canary, base fails, gold resolves, gold not
  VACUOUS, source alone VACUOUS); 2,110 s.
- **Instruction delivery** (`harness/probe.py`, $0.05): asked to quote its
  instructions, a workspace with the arm's `CLAUDE.md` quoted
  `Add a test that fails without your change.`; one without answered `NONE`.
- **Check batch** (one task, one slot per arm, $0.21, outside the study): all four
  graded on the one model. The init and hook events showed exactly each arm's
  condition: superpowers' plugin, 37 skills and its "You have superpowers" context
  only in `superpowers`; ElevenPowers' session-start context only in `assisted`.

| check slot | resolved | VACUOUS | seconds | cost |
|---|---|---|---|---|
| ordinary | yes | yes | 9 | $0.040 |
| instructed | yes | no | 14 | $0.050 |
| superpowers | yes | yes | 10 | $0.051 |
| assisted | yes | no | 35 | $0.065 |

One task, one run each: a check of the harness, not a result.

## Estimate

480 slots, two workers: about $35 and 4-5 hours, from October's rates and the
check batch.
