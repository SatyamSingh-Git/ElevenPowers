# Remote observations v1

Status: implemented 2026-10-31 on branch `remote-observations`. See
[validation](../validation/2026-10-31-remote-observations.md) and
[usage](../../the-guide/remote-observations.md).

## Intent

PatchProof and the input witnesses can vouch only for local bytes, and they
state that missing witnesses never infer remote freshness. Checks still depend
on remote resources:
- a schema served by another service
- registry metadata
- a configuration file in another repository

Remote observations give such a resource a recorded identity at a recorded
time. A report can then say whether it changed around a check's run and since
that run, without the report itself contacting anything.

## Borrowed, and what is added

- **Python's standard-library `urllib` (PSF licence).** It provides the HTTP
  client, timeouts and status handling. Redirects are refused with a handler
  that returns no follow-up request.
- **RFC 9110 validators.** `ETag` and `Last-Modified` are recorded as metadata.
  They are not used as identity, because real servers serve weak, opaque or
  stale validators: PyPI's is opaque, and a test serves a stale one.
- **Repository components.**
  - `core/inputs/bindings.py`: project identity, the Git-untracked approval check and the atomic writer
  - `core/inputs/definition.py`: the safe bounded reader and the strict JSON decoder
  - `core/jobs.ledger_write`: locking
  - `core/redact.scrub`: credential detection
  - the PatchProof `_guard` state comparison

What this adds: approval-gated, explicitly triggered observation of remote bytes,
stored as bounded local history and associated with receipts by time
bracketing, so that every read path stays offline.

## Decisions

- **Separate declaration file (`elevenpowers.remotes.json`).** The strict
  local-witness schema and its consumers are unchanged. Old runtimes ignore the
  new file, and they never fetch it.
- **Approval binds the exact URL.** A tracked declaration cannot grant network
  access, and an edited URL needs new approval. Tracked or copied approval
  files are refused, as for local roots.
- **Explicit observation only.** No status, inspection, report, bundle,
  execution or reuse path performs a request.
- **Identity is the SHA-256 of the identity-encoded body.**
  `Accept-Encoding: identity` is sent. An encoded, redirected, oversized,
  truncated, timed-out or non-2xx response is `incomplete`, never a digest.
- **History.** At most 64 observations are kept per remote, and the oldest are
  evicted first.
- **Association by bracketing.** Each receipt is placed between the complete
  observations just before and just after its timestamp. It is never reported
  as fresh.
- **New state markers ignore everything.** A newly created
  `.elevenpowers/.gitignore` starts with `*`. Building this showed that
  upstream `ep_inputs bind` created a marker without it, which left a later
  `ledger.json` committable. That bug was fixed separately in `68e65fe`.

## Non-goals

These are left to later adapters:
- remote state in execution, reuse or completion decisions
- authenticated or signed attestation
- conditional requests
- per-command remote selection
- live PR/fork transport

Proxy and CDN behaviour are recorded, not controlled.
