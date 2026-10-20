# Declared-check completion closure

The completion report now lists every configured exact declaration as
`CURRENT`, `FAILED`, `STALE`, `ABSENT` or `INCOMPLETE` beside the unchanged task
verdict. Declared-check feedback is observed in three separate stages: intent,
a flushed native emission, and a later exact receipt. Owned runs are visible to
that last stage: `ep_check.py` prints the attempt digest already bound to its
receipts, and host callbacks link only receipts carrying a printed attempt, in
an `owned_links` history kept apart from native receipt history.

No model was run. This establishes what the runtime records and reports on
actual local checks driven through the real launchers. It does not establish
that a model reads or follows the feedback, installed adoption, or any coding
benefit.

## Qualification

- [No-model exercise](no-model.json): `python -m eval.declared_closure`, actual
  pytest and `node --test` projects under all five host adapters, replay and
  synthetic native ingress, with a `tool_use_id` on every tool callback:
  **20/20 cases qualified**, 202.75 seconds of case time, 0 model calls, at
  runtime fingerprint `c0f9f81a…` (commit `3f3e2e7`). Every case records
  declared states `ABSENT → ABSENT → CURRENT → STALE → FAILED → INCOMPLETE`
  across: start, generic filtered pass, owned pass, failing edit, owned failure,
  owned interruption. Native ingress records `emitted` and follow-ups
  `current / failed / incomplete`; replay records `intent` and no follow-ups.
- [Superseded first run](no-model-77e56e0-superseded.json) at `77e56e0` also
  reported 20/20, but its payloads carried no `tool_use_id`. Real adapter
  payloads do, and with one the intent note was silently skipped on four hosts.
  It is retained, not counted.
- Controls: `tests/test_feedback_delivery.py` (32), `tests/test_declared_completion.py` (4),
  `tests/test_declared_closure_exercise.py` (9). Commit `d2a3c2b`'s message says
  twenty-nine delivery controls, counted before later variants were added.
  All 18 observer-guard mutations, 5 of 6 owned-link mutations and 8 of 9
  review-fix mutations were killed. The survivors are an equivalent replay
  mutation (replay callbacks never persist links) and a deliberately weak
  `str(None)` mutation of the CLI fix, whose real defect the existing
  `test_cli_refuses_invalid_request` witnessed failing and then passing.
- Affected hook, host, advice, milestone, declared-check, CLI, batch, report and
  adoption groups: 610 passed in 579.54 seconds on the repaired runtime.

## Found while building

- The intent parser crashed the completion report on a non-object note.
- Owned-runner receipts were never linked, so the follow-up stage was blind to
  the exact path the feedback recommends. Found by running the real launcher,
  not by the unit controls.
- The annex printed `INCOMPLETEtests` (a ten-character state in a ten-wide column).
- A privacy assertion could not fail: feedback text contains newlines, which the
  stored JSON escapes, so a substring test on the raw file was vacuous.

## Found by review after the first push

- `ep_check.py` crashed with exit 1 (failed) on refused/unrun checks.
- Adapter callbacks with a `tool_use_id` skipped the intent note.
- Credential-bearing declared commands never matched their scrubbed receipts
  (pre-existing in `check_feedback`, copied into the two new read models).
- Owned links first shared native receipt history, so one passing owned run
  satisfied both `pass` and `incomplete` installed-acceptance outcomes.

## Installed observation (2026-10-20)

One frozen Sonnet 5.5 medium conversation on the authored four-stage JavaScript
case, assisted arm only, at most 720 model-process seconds. Preparation and
outcome definitions were pushed before each launch.

- [Attempt 1](installed-attempt-1.json) — **not counted**. Turn 1 ended
  `model_unqualified`: the host sent one small auxiliary call (1,152 input / 14
  output tokens) to Haiku 4.5 beside Sonnet 5.5, and the exact-model rule stopped
  the run. A real probe reproduced it on a single Bash call and showed that
  `ANTHROPIC_DEFAULT_HAIKU_MODEL` set to the protocol model removes it; launches
  now set that. The rule itself is unchanged.
- [Attempt 2](installed-attempt-2.json) — **run incomplete**, 410.343 model-process
  seconds, Sonnet 5.5 only:

| Turn | State | Grade | Declared `tests` | Feedback | Follow-up | Owned runner |
|---|---|---|---|---|---|---|
| 1 | completed | 4 | CURRENT | none (no gap) | — | no |
| 2 | completed | 6 | CURRENT | emitted | current | yes |
| 3 | timeout at its 309.7 s share | 8 | CURRENT | none | — | yes, piped after `node --test` |
| 4 | not launched | — | — | — | — | — |

In turn 2 a compound command ran the configured `node --test` reporter, the hook
emitted the declared-check feedback, and the agent's next call was
`ep_check.py --all`; the exact receipt is CURRENT and its native follow-up is
`current`. By the frozen definitions, feedback was emitted and the owned path was
taken after it. That is one temporal sequence in one conversation: startup
guidance also names the runner, and the earlier run on this case (0/4 owned turns)
was a different runtime and a single sample. No adoption rate, causal effect or
coding benefit is claimed, and four-stage completion is not established.

## Limits

- Native-control is synthetic launcher ingress, not an installed agent session.
- The generic command is reported to the launcher with a `| tail -15` filter it
  did not run; its output is the unfiltered actual output.
- The generic-verification predicate is unchanged. A runner it does not
  recognise, such as a bespoke TAP script, still produces no feedback.
- Deferred minors: a command merely naming `ep_check.py` can echo attempt ids to
  relink owned receipts (limited to `owned_links`, guarded by receipt age); a
  stale or failed zero-test receipt reads `INCOMPLETE` because the zero-test
  rule is checked first.
- A filtered `python -m unittest` run yields no generic record (the standard
  `Ran N tests … OK` summary is not read), so declared-check feedback cannot
  fire on that common runner; the Python case was therefore not scheduled.
- Installed observation has one incomplete conversation; a completed run and a
  second case remain open.
