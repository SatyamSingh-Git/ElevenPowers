# Declared-check completion closure

The [spec](../superpowers/specs/2026-10-18-declared-check-closure-design.md)
states the intent: a task can be `VERIFIED` while a configured exact check is
absent, stale, incomplete or failing, and generated feedback is not evidence that
any host delivered it. This document records how the runtime meets that intent.

## Completion annex

`core/declared_completion.py` is a pure read model. For every configured
supported declaration it selects the newest receipt whose declaration, kind and
command identity match exactly, then classifies it:

| State | Meaning |
|---|---|
| `INCOMPLETE` | the latest exact attempt did not complete, or a suite counted no tests |
| `STALE` | source, owned-execution configuration, selected input or scoped coverage no longer qualifies |
| `FAILED` | a fresh completed exact receipt reports failure |
| `CURRENT` | a fresh completed exact receipt passes |
| `ABSENT` | no exact receipt exists |

Changing the declared command itself makes earlier receipts non-exact, so the
row reads `ABSENT`, not `STALE`. Commands are compared after the same credential
scrubbing receipts receive, as `verify.py` already does.

`end_report` appends these rows after the verdict line. `ledger.status()` is not
consulted or changed, and nothing is executed or written.

## Delivery observation

`core/feedback_delivery.py` follows the shape of the existing milestone-advice
observer (`core/milestones/delivery.py`): an in-memory candidate per launcher,
recorded only after the response is flushed.

1. `check_feedback` reserves its reminder as before, then records a bounded
   **intent** note (task/declaration/text hashes, at most sixteen per task).
2. Inside a host callback, `prepare` holds the raw text in memory together with
   the host, installation generation, hashed session and event.
3. `transport.emit` (direct Claude path) and `ep_host.py` (adapter path) call
   `emitted` after printing. An **emission** note is written only when the
   complete text appears in a supported context field and the installation
   generation is unchanged and not removed, reconfigured or in error.
4. `inspect` joins later native receipt links read-only. A follow-up counts only
   when the link is from the same hashed session, after the emission, and the
   exact receipt itself is newer than the emission.

Raw feedback, commands, output, prompts and session ids never reach the ledger.
Malformed notes are ignored rather than breaking the report.

## Owned runs become observable

The feedback recommends `ep_check.py`, but the owned runner writes its receipt in
its own process, and host callbacks deliberately never parse owned output. So no
native link was ever recorded for the recommended path. The runner now prints
the random `attempt` digest already bound to its receipts. For an owned envelope,
the host callback links only ledger receipts carrying a printed attempt. Output
text still creates no evidence; an echoed attempt can only point at a receipt
that already exists, and the receipt-age rule keeps an old one from counting as
a follow-up.

These links are kept in a separate `owned_links` history in
`.elevenpowers/integrations.json`, not in the native `receipt_links`. Owned
execution is not a native command observation: health's command-capture stage,
installed acceptance outcomes, paired-evaluation receipt counts and the
milestone-advice observer read only native links and are unchanged. Only the
feedback follow-up join reads both. A first version shared the native history;
review showed one passing owned run then satisfied both the `pass` and
`incomplete` acceptance outcomes, through its provisional receipt.

The feedback intent note is written with the receipt-delivery marker cleared,
as `check_feedback` already does for its reservation. Adapter callbacks that
carry a `tool_use_id` had otherwise skipped the save silently.

## Limits

- Synthetic launcher ingress is not an installed agent session.
- A later receipt is temporal correlation, never model comprehension.
- The generic-verification predicate is unchanged: an unknown runner (for
  example a bespoke TAP script) still produces no feedback.
