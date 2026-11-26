# Four arms on the held-out tasks: one line of instruction beat everything

What makes an agent pin its change: nothing, a one-line instruction, superpowers,
or ElevenPowers? Design and analysis were fixed before any run:
[pre-registration](../../../docs/superpowers/specs/2026-11-26-heldout-four-arms-design.md),
`eval/heldout_analyse.py --four-arms` ([output](analysis.json), [records](collected.json)).

## Result

| | ordinary | instructed | superpowers | ElevenPowers |
|---|---|---|---|---|
| graded runs | 120 | 120 | 119 | 119 |
| resolved | 91 | 90 | 89 | 90 |
| **VACUOUS among resolved** | 72 (79%) | **0 (0%)** | 72 (81%) | 44 (49%) |
| resolved patches changing a test file | 18 | 90 | 17 | 46 |
| mean model-process seconds | 22.0 | 30.8 | 23.6 | 51.5 |
| total cost | $8.70 | $10.73 | $10.32 | $10.67 |

`instructed` is a project `CLAUDE.md` holding one line: `Add a test that fails
without your change.` Every one of its 90 resolved patches changed a test file, and
in every one undoing the source change failed a test.

**Primary: five pairs, two-sided signed-rank over tasks, Holm-adjusted together.**

| pair (first - second) | tasks differing | lower VACUOUS | tied / dropped | p | Holm p |
|---|---|---|---|---|---|
| ordinary - instructed | 26 | instructed on all 26 | 6 / 8 | < 0.00001 | 0.00001 |
| ordinary - superpowers | 5 | ordinary 3, superpowers 2 | 26 / 9 | 1.0 | 1.0 |
| instructed - assisted | 18 | **instructed on all 18** | 13 / 9 | 0.00012 | 0.0005 |
| superpowers - assisted | 17 | assisted 14, superpowers 3 | 14 / 9 | 0.0019 | 0.0053 |
| ordinary - assisted | 14 | assisted 13, ordinary 1 | 17 / 9 | 0.0018 | 0.0053 |

**Secondary:** resolve did not differ in any pair (sign tests p 0.625 to 1.0; at most
3 tasks of 40 differ in any pair).

## What it means

- **One line of instruction pinned every resolved change.** It took 40% more model
  time than nothing and cost 23% more.
- **ElevenPowers did less than that line,** and significantly so: VACUOUS 49%
  against 0%, lower for the instruction on all 18 tasks that differ, at twice the
  instruction's model time. Its guide profile surfaces an untested change; it does
  not ask for the test in so many words, and half its resolved patches came without one.
- **Superpowers, on single requests like these, did nothing to vacuity:** 81%
  against 79% with nothing, 17 of 89 resolved patches with a test. Its skills loaded
  in every run; the agent mostly did not invoke them for a small fix.
- **October replicates:** ElevenPowers against nothing, 49% against 79% (October
  37% against 84%), p = 0.0053 after Holm.

By the reading fixed in advance: the instruction is significant and the runtime
check does not add to it; the opposite. What ElevenPowers measures (VACUOUS, the
revert probe) is what found this; what it does to the agent is beaten by a sentence.

## Incomplete

Two of 480 runs ended `host_failed`, both in the same minute on both workers
(`cachetools-ec0b97b8--superpowers--0` and `--assisted--0`): `API Error: Unable to
connect to API: Self-signed certificate detected`, a network fault on this machine
(the same session saw two connection resets). Not retried, under the protocol. No
run reached the network from its tools. Every resolved run's probe was scored.

## What this does and does not show

- One model (Sonnet 5.5, medium), one host, Python, 12 repositories, small fixes. The
  instruction is one wording.
- VACUOUS says the repository's tests, with the agent's, notice the change undone;
  not that the tests are good. Tests written to an instruction could pin the
  implementation rather than the behaviour; that was not measured here.
- Superpowers was measured on single requests with an unattended line. On the
  multi-stage cases it left 1 VACUOUS stage of 475, under the coarser bar and on
  different tasks; the two results do not contradict each other and are not pooled.

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
