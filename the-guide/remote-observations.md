# Remote observations

[Local input witnesses](external-inputs.md) cover bytes on this machine.
Checks can also depend on things that live elsewhere:
- a schema another team serves
- a package registry's metadata
- a configuration file in another repository

Remote observations record what such a resource returned, and when. They are
recorded only when you explicitly ask, and only for URLs you have approved.

Nothing here makes a remote "fresh". An observation has an age. Two equal
observations cannot rule out a change that was reverted between them.

## Declare the resources

The project owns `elevenpowers.remotes.json` and normally commits it:

```json
{"schema": 1,
 "remotes": [{"id": "orders-schema", "url": "https://example.com/orders/openapi.json"}],
 "limits": {"bytes": 8388608, "seconds": 15}}
```

The rules are:

- **Count:** up to 16 remotes, each with a unique `id` label.
- **Scheme:** URLs must be `https`. Plain `http` is accepted only for loopback hosts.
- **Credentials:** a URL with user info, a fragment, whitespace, non-ASCII text or a credential the runtime would redact is refused.
- **Limits:** `bytes` can be raised to 64 MiB, and `seconds` must be above 0 and at most 60.

A declaration never grants network access. Changing a declared URL in the
committed file does not carry the earlier approval over to the new URL.

## Approve each URL locally

```sh
python ElevenPowers/plugin/bin/ep_inputs.py approve-remote --project PROJECT --name orders-schema
```

Approval records the exact URL currently declared for that label in
`.elevenpowers/remote-approvals.json`. That file is private and bound to the
project. Approval is refused when:
- the approval file is tracked by Git
- the approval file was copied from another project

If the declared URL later changes, the remote shows `url-changed` and is not
fetched until you approve it again.

## Observe explicitly

```sh
python ElevenPowers/plugin/bin/ep_inputs.py observe --project PROJECT
python ElevenPowers/plugin/bin/ep_inputs.py observe --project PROJECT --name orders-schema --check
```

Each approved remote gets one `GET` request, sent with
`Accept-Encoding: identity`. A complete observation records:
- the SHA-256 of the response body
- the byte count
- the status, `ETag`, `Last-Modified`, `Content-Type` and `Cache-Control`
- whether a proxy applied

Each of the following is recorded as `incomplete`, with no digest:

- a redirect, whose target was never approved and is not requested
- a non-2xx status
- a declared or actual size over the limit
- a body that ends before its declared length
- a content-encoded body
- a timeout or connection failure

Unapproved remotes are reported as `refused`, and no request is made for them.

Each remote keeps its latest 64 observations in
`.elevenpowers/remote-observations.json`.

`--check` exits 1 unless every selected remote was observed completely.

## Read status offline

```sh
python ElevenPowers/plugin/bin/ep_inputs.py remotes --project PROJECT
```

Status reads only local state. A remote's state is one of these:

| State | Meaning |
|---|---|
| `not-approved` | The remote is declared but has no approval. |
| `url-changed` | The approval is for a different URL than the one now declared. |
| `never-observed` | The remote is approved but has never been fetched. |
| `incomplete` | The latest observation did not complete. |
| `observed` | The latest complete observation matches the previous one. |
| `changed` | The latest complete observation differs from the previous one. |

Status also reports `age_seconds` since the latest complete observation.

## In PatchProof bundles

`ep_patchproof.py` bundles now include a `remote_observations` section, built
from recorded history only. It never contacts the network.

Each receipt is associated with each declared remote by the complete
observations just before and just after the receipt's timestamp. The
association is one of these:

- `unchanged-around-run`
- `changed-around-run`
- `observed-before-run-only`
- `observed-after-run-only`
- `unobserved`

`since_run` then compares the latest observation with the one used for that
association.

The remote state files take part in the bundle's state guard. An observation
recorded while a bundle is being built therefore unbinds that bundle.

This association is about timing only. It does not show that the check read
the resource.

## Limits

- **Unsigned.** Observations are explicit, local and unsigned.
- **Caches.** CDN and proxy caches can serve bytes older than the origin. `Cache-Control` is recorded, not measured.
- **What is digested.** Only identity-encoded body bytes are digested. Headers, authentication and server-side state are not.
- **Clock.** Association compares timestamps from the same local clock.
- **Not yet used in decisions.** Remote observations do not yet feed execution, reuse or completion decisions. That is a separate adapter.
