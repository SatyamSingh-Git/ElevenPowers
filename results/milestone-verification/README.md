# Milestone verification capability controls

Recorded 2026-10-06 on Windows 11, Python 3.13.2 and Node 22.17.1. The explicit
controller exercised three connected Python milestones and an unrelated Node
layout. It ran no coding agent or model. Expectations were fixed before the
fault, and their test-file hashes remained unchanged through repair and the
equivalent implementation.

**18 actual producer runs: 15 qualified passes and three assertion-fault
rejections.** The Python checkout and worker each rejected a later provider
expiry-boundary fault; Node rejected its separately authored entitlement fault.
No setup failure is counted as a behavioral rejection.

| Observation | Result |
|---|---|
| Move from provider to checkout to worker tasks | Earlier receipts survive independently of new task evidence |
| Edit the provider after all three checks pass | Earlier observed evidence becomes `STALE` |
| Run checkout/worker against the fault | Fresh rejection; report becomes `FAILED` |
| Repair and rerun all checks | `CURRENT` |
| Equivalent Python implementation and fresh checks | `CURRENT`; valid alternative accepted |
| Add unrelated selected source after native checks | `STALE`, exposing conservative whole-source invalidation |
| Add unrelated source after a separate explicit-input producer | `CURRENT` for the unchanged declared scope |
| Unrelated Node project: fault, then repair | `STALE` → `FAILED` → `CURRENT` |

The scoped producer is controller-owned. Its narrower observations do not
establish that native host receipts automatically gain that attribution. The
graph supplies informational consumer leads only; it does not prove absence
of impact or exclude fallback tests.

The public [versioned observations](observations.v1.json) retain every state,
original output fingerprint, frozen expectation digest and timing. The
[provenance record](provenance.v1.json) identifies the original runtime commit
and artifact digests. Public logs replace local paths; their separate digests
do not replace the originals. Raw artifacts remain in the operator's disposable
exercise directory. Historical observations are not silently regraded after
later changes.

Reproduce in a new directory using a Python environment with pytest:

```bash
python -m eval.milestones --output NEW_DISPOSABLE_DIR
```

Node controls run when Node is on PATH; otherwise the gap is explicit. The
18 local command durations ranged from 358.771 to 971.588 ms. They are descriptive
execution observations including receipt collection, not normal-session
overhead, a speed improvement or representative performance.

These authored examples prove that the new retention/status capability catches
the specified later regression and accepts the specified legitimate behavior.
They do **not** establish that ElevenPowers improves an agent's code relative
to an equally funded baseline. Automatic completion integration, native overhead,
more precise attribution, patch binding and a matched end-to-end comparison
remain open. See [usage](../../the-guide/milestones.md) and
[dated validation](../../docs/validation/2026-10-06-milestones.md).
