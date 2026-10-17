# Fresh matched multi-stage comparison

Status: three of four scheduled conversations completed; comparison in progress.
The [ordinary Python arm](workflow-queue-py-ordinary.json) and
[assisted Python arm](workflow-queue-py-assisted.json) each retain 4/6/8/10
passing cumulative groups, no observed regression, preserved scope and qualified
session identity. Model-process times were 120.899 and 283.349 seconds,
respectively: a correctness tie, with a slower assisted arm. Owned-runner
adoption is observed in all four assisted Python turns. The
[assisted JavaScript arm](workflow-orders-js-assisted.json) also finishes at
4/6/8/10 with no observed regression, using 167.510 model-process seconds;
none of its four turns qualifies owned-runner adoption. It remains in the
comparison. The ordinary JavaScript arm is the final scheduled conversation.

[Preparation](prepared.json) freezes the current qualified producer, equal
matched public inputs, independent baselines, requests/oracle identities and
alternating order before outcomes. Each baseline passes its two established
contract groups. [Fresh rehearsal](rehearsal.json) reproduces all sixteen
reference snapshots with cumulative 4/6/8/10 passing groups and zero model calls.

Four Sonnet 5.5 medium subscription conversations share 720 seconds each across
four turns: Python queue ordinary/assisted, then JavaScript orders assisted/ordinary.
There is no API fallback, favorable retry, case replacement, hidden-grade feedback
or controller repair between requests. Preserve every scheduled incomplete arm.

The queue covers leases/retries, restart, atomic batches and migration/replay;
the order system covers holds, exact refunds, restart and atomic replay.
Cases are authored systems, not a representative upstream-project sample.
Correctness and earlier-behavior regression grades are independent of native
delivery. Missing assisted delivery does not remove a comparable adverse pair.

The [execution plan](../../docs/superpowers/plans/2026-10-17-matched-workflow-comparison.md)
reuses the existing controller and independent source reproducer.
