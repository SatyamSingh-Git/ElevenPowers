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
- Installed observation of intent, emission, owned adoption and exact follow-up
  in a real model session remains open.
