# Remote observations: 2026-10-31

This delivery is [remote observations v1](../design/remote-observations.md). It adds:
- `core/inputs/remote.py`
- three `ep_inputs.py` subcommands: `approve-remote`, `observe` and `remotes`
- an additive, offline `remote_observations` section in PatchProof bundles, with the remote state files joining the bundle's state guard
- `tests/test_remote_observations.py`

Separately, `68e65fe` fixes an upstream ignore-marker defect that this work
found. The delivery contains no execution or reuse integration, no model run
and no benefit claim.

Environment: Windows 11, project `.venv` Python, Git 2.49.0.windows.1, base
upstream `908e5d8`.

## Producers run before parsing

Real `urllib` requests were made with redirects disabled and no other
configuration:

| Request | Observation | Consequence |
|---|---|---|
| `raw.githubusercontent.com/.../README.md` | 200, 68,616 bytes. `ETag` is a content hash, `Cache-Control: max-age=300`, no `Content-Encoding`. A second fetch gave the same SHA-256. | Identity is the SHA-256 of the body. Cache headers are recorded as a limit, since they mean an observation can lag the origin. |
| `github.com/.../raw/main/README.md` | `HTTPError(302)` with a `Location` header | A redirect is `incomplete` and its target is never requested. |
| `pypi.org/pypi/markupsafe/json` | 200, 1,019,822 bytes, opaque `ETag`, `max-age=900` | Validators are metadata only, never identity. |
| A missing raw path | `HTTPError(404)`, which is a subclass of `URLError` | HTTP errors are handled before generic URL errors. |

The real module then ran against a scratch project:
- An approved URL was observed completely.
- An approved redirecting URL was recorded as `incomplete (302)`.
- An unapproved URL was `refused`, with no request made.
- A repeat observation gave `changed: false`.

## Controls

`tests/test_remote_observations.py` has 32 tests. A loopback server counts
every request, so each "no request" claim is measured rather than assumed.

- **URL rules.** These are accepted: `https`, loopback `http` (IPv4, IPv6 and `localhost`). These are refused: non-loopback `http`, `ftp`, `file`, scheme-relative URLs, user info, fragments, whitespace, embedded `ghp_` tokens, non-ASCII hosts, and URLs longer than 2,048 characters.
- **Strict schema.** Each of these is refused: an unknown schema, an empty list, extra fields, duplicate IDs, and out-of-range limits.
- **Approval.** Without approval there are no requests. With approval there is exactly one request. After the declared URL changes, the result is `refused` with "differs", the new URL is never requested, and status shows `url-changed`. An undeclared label cannot be approved.
- **Private state.** A Git-tracked approval is refused as `tracked`. An approval copied from another project is refused with "another project". Neither makes a request.
- **Identity.** The digest equals the SHA-256 of the served bytes, and the ETag and Cache-Control headers are recorded. A repeat gives `observed` with `changed: false`. A changed body served with the same stale ETag gives `changed`.
- **Failures are incomplete.** Each of these is `incomplete` with no digest, and status reports `incomplete`:
  - a redirect, whose target receives zero requests
  - 404
  - a declared size over the limit
  - a body without a length that exceeds the limit
  - a body shorter than its declared length
  - a gzip-encoded body
  - a server delay longer than the timeout
- **History.** With a per-remote bound of 3, five observations of one remote keep 3, and the other remote keeps its own row.
- **Ignore marker.** After approval, observation and a later ledger save, the only untracked file is the declaration.
- **Offline reads.** `status` and a full PatchProof `build` succeed while `remote._fetch` and `OpenerDirector.open` raise, and the server's request count is unchanged.
- **Bracketing.** These cases each give their own association: unchanged around the run, changed around the run, unchanged as of the latest observation, changed since the run, observed before the run only, observed after the run only, unobserved, and an unknown remote.
- **Bundle.** A bound bundle associates its receipt `unchanged-around-run` and renders a `## Remote observations` section. An observation recorded mid-collection unbinds the bundle with "changed during".
- **CLI.** `observe` exits 0. `observe --check` exits 1 when one remote fails, and 0 when filtered to the healthy remote with `--name`. `remotes` omits internal rows.

## Seen to flip

Each guard was removed in turn, the matching probe was rerun, and the file was
restored byte-for-byte. Every probe failed:

| Guard removed | Probe |
|---|---|
| approval check | approval |
| redirect refusal | redirect |
| declared-size check | `route1` |
| streaming byte limit | `route2` |
| declared-length match | `route3` |
| content-encoding refusal | gzip |
| loopback-only http | URL refusal |
| credential URL refusal | URL refusal |
| untracked-approval check | tracked approval |
| bracket digest comparison | bracketing |
| `*` in a new ignore marker | ignore marker |
| history in the bundle `_guard` | bundle |

The upstream bind fix was flipped the same way: its new regression failed
before `68e65fe` and passed after. Input suites:
`test_input_definitions`, `test_input_cli`, `test_external_input_review`,
`test_input_collection`, `test_input_receipts` and the new file gave **100
passed, 4 skipped**.

## Other checks

The render check ran with the system Python, because `.venv` is first on PATH
and has no Playwright:

```bash
.venv/Scripts/python.exe -m pytest tests/test_remote_observations.py tests/test_patchproof_report.py tests/test_patchproof_cli.py -q
C:/Users/jay20/AppData/Local/Programs/Python/Python312/python.exe architecture/check.py --render
```

The full upstream suite, run with `.venv` on the final code, gave **2912 passed,
60 skipped, 0 failed** (3,981 s). The documentation-reading tests were rerun
after the final documentation edits: 78 passed, 1 skipped.

The render check printed `OK`, with 176 nodes, 438 edges and all five tabs
working. The existing bundle tests passed unchanged (21 passed) with the
additive section.

## Limits

- **Unsigned.** Observations are explicit, local and unsigned. Caches can lag the origin.
- **Equal digests.** Equal digests cannot exclude a change that reverted between them.
- **Timing only.** Association is timing on one local clock. It does not show that a check read the resource.
- **No decisions yet.** Remote observations do not affect execution, reuse, completion, binding or any verdict.
- **Network failures are not separated.** Real network outages and DNS failures are reported as `remote unavailable: <type>` without further classification.
