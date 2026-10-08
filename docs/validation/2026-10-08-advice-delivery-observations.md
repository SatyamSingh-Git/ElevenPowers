# Observable advice delivery — 2026-10-08

Base `d05b932`; branch `codex/advice-delivery-observations`. Build generalized
behavior on existing advice reservations, native diagnostics, transports and
fresh evidence. No new dependency, default advice activation or completion gate.
See [design](../design/advice-delivery-observations.md),
[plan](../superpowers/plans/2026-10-08-advice-delivery-observations.md),
[guide](../../the-guide/advice-delivery.md) and
[observations](../../results/advice-delivery/README.md).

Witnessed RED: fourteen emission controls before last-mile observations;
seventeen follow-up controls before the readiness view; seven preparation
controls before optional advice exercise setup; three controls before the actual
command producer. A separate capacity probe witnessed missing writer bounds
before enforcing the original 64 KiB limit and protecting the active task.

The emission/worker/hook/policy group passed 50 controls. Emission/follow-up
controls passed 37 after retention protection. Optional preparation, follow-up
and native provenance passed 37 controls. A health compatibility run passed 70
controls with one forward fixture corrected afterward: an opaque string was
not a pytest summary and correctly failed the zero-test qualification. The
fixture now supplies actual pytest summary forms. Copilot's fixture also uses
its native `sessionId` field. Neither correction weakens runtime validation.
The real producer's focused Python/JavaScript group passed three controls.

The one whole-branch review found three Important issues: recommendation hashes
could survive text truncation, optional state entered mandatory health stamps,
and the optional declaration was missing from the final acceptance contract.
Six regression controls witnessed failures before repair. Rendering now derives
complete visible command identities with its text, optional state has a separate
before/after check, and acceptance seals the declaration across its read. The
combined repair/emission/follow-up/preparation/policy/worker group passed **74**.
Review declined installed acceptance, comprehension/benefit and hostile-writer
authentication; these remain explicit limits, not approved claims.

A fresh final producer run qualified **20/20 cells** and **100 actual command
attempts**, with no model calls. The [summary](../../results/advice-delivery/summary.json)
retains runtime and producer identity. Host doctor passed all 11 checks, grader
validation distinguished all four outcomes, and new modules import with `-S`.
Architecture has **132 nodes, 306 edges and seven planes**; `--render` verified
all five tabs, planned cards, filters, keyboard, shared links and narrow layout.
All eight saved earlier candidates reproduced their independent source grades
(six checks at stage one, eight at stage two). This does not rerun installed
sessions or change the original two final correctness ties.

The producer uses real commands, but all host callbacks are deliberately
synthetic or replayed. No installed acceptance, model comprehension or causal
coding benefit is established by these controls. No old comparison archive is
changed or retroactively qualified. Final measured observations, review repairs
and integration outcomes belong to their actual command output and exact
qualified revision.

```sh
python -m pytest tests/test_advice_emission.py tests/test_advice_followup.py tests/test_advice_acceptance.py tests/test_advice_delivery_exercise.py -q
python -m eval.advice_delivery NEW_DISPOSABLE_DIRECTORY
python plugin/bin/ep_doctor.py --host
python -m eval.validate
python results/behavior-preservation/reproduce.py
python architecture/check.py --render
python -m pytest -q
```

Generic fixtures remain outside repository Git boundaries. Do not set a
checkout-local pytest basetemp. Replay and synthetic ingress controls remain
distinct from an installed model session, even when local diagnostics are
successfully written.
