# 68 — Text leaving the runtime

The previous delivery repaired command identity behind literal directory
wrappers. The next observation gap was earlier in the loop: advice state said
`delivered` when the inspection worker returned text. That happened before host
formatting and before stdout reached the caller. It could not establish that
the advice survived either step.

The new boundary observes successful output flushing. Prepared advice stays in
memory only; its hash and exact recommendation hashes can be retained after
the expected text appears in a supported context slot. Another field mentioning
advice is insufficient. Failed flushes, partial context, replay, missing sessions
and changed generations cannot establish qualified emission.

The original state bound also mattered. Extra metadata multiplied by twenty
tasks and ten attempts would exceed the reader's 64 KiB budget. Writers now
evict older task history with a counter while protecting the active allowance.
An unbounded writer would have made its own valid diagnostics unreadable.

Readiness then asks a narrower question: did a later native receipt match an
emitted recommendation in the current task/session/runtime? Its outcome can
still fail, become stale or remain incomplete. A prior baseline and a controller
rerun cannot establish this follow-up. The view stays outside completion gates.

This moves observability forward. It does not prove a model read the context,
followed it because of the advice, or produced better code. Actual local command
controls and an explicitly prepared installed exercise preserve that distinction.
The earlier correctness ties remain unchanged.

See the [guide](../the-guide/advice-delivery.md),
[measured observations](../results/advice-delivery/README.md) and
[validation](../docs/validation/2026-10-08-advice-delivery-observations.md).
