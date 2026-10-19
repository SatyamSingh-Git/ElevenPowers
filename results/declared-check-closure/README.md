# Declared-check completion closure

The completion report now lists every configured exact declaration as
`CURRENT`, `FAILED`, `STALE`, `ABSENT` or `INCOMPLETE` beside the unchanged task
verdict. Declared-check feedback is observed in three separate stages: intent,
a flushed native emission, and a later exact native receipt. Owned runs are now
visible to that last stage: `ep_check.py` prints the attempt digest already bound
to its receipts, and host callbacks link only receipts carrying a printed attempt.

No model was run. This establishes what the runtime records and reports on
actual local checks driven through the real launchers. It does not establish
that a model reads or follows the feedback, installed adoption, or any coding
benefit.

## Qualification

- [No-model exercise](no-model.json): `python -m eval.declared_closure`, actual
  pytest and `node --test` projects under all five host adapters, replay and
  synthetic native ingress: **20/20 cases qualified**, 203.62 seconds of case
  time, 0 model calls, at runtime fingerprint `011e093b…` (commit `77e56e0`).
  Every case records declared states
  `ABSENT → ABSENT → CURRENT → STALE → FAILED → INCOMPLETE` across: start,
  generic filtered pass, owned pass, failing edit, owned failure, owned
  interruption. Native ingress records `emitted` and follow-ups
  `current / failed / incomplete`; replay records `intent` and no follow-ups.
- Controls: `tests/test_feedback_delivery.py` (30; commit `d2a3c2b`'s message
  says twenty-nine, counted before the JSON owned-output variant was added),
  `tests/test_declared_completion.py` (2), `tests/test_declared_closure_exercise.py` (9).
  Every guard in the delivery observer and owned-run link was mutation-checked;
  all 18 observer mutations and 5 of 6 owned-link mutations were killed. The
  survivor (fabricating an observation under replay) is equivalent: replay
  callbacks never persist links.
- Affected hook, host, advice, milestone, declared-check, report and adoption
  groups: 549 passed in 667.69 seconds on the final runtime.

## Found while building

- The intent parser crashed the completion report on a non-object note.
- Owned-runner receipts were never native-linked, so the follow-up stage was
  blind to the exact path the feedback recommends. Found by running the real
  launcher, not by the unit controls.
- The annex printed `INCOMPLETEtests` (a ten-character state in a ten-wide column).
- A privacy assertion could not fail: feedback text contains newlines, which the
  stored JSON escapes, so a substring test on the raw file was vacuous.

## Limits

- Native-control is synthetic launcher ingress, not an installed agent session.
- The generic command is reported to the launcher with a `| tail -15` filter it
  did not run; its output is the unfiltered actual output.
- The generic-verification predicate is unchanged. A runner it does not
  recognise, such as a bespoke TAP script, still produces no feedback.
- Installed observation of intent, emission, owned adoption and exact follow-up
  in a real model session remains open.
