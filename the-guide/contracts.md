# Declared OpenAPI compatibility

PatchProof can include a real, saved OpenAPI backward-compatibility observation.
It compares two **committed standalone specification files** with explicitly
selected oasdiff 1.33.0. Any language or coding host can use this project-owned
declaration; no framework, repository name or route filename is hardcoded.

Commit `elevenpowers.contracts.json` with your specification:

```json
{"schema":1,"contracts":[{"id":"public-api","kind":"openapi","path":"api/openapi.yaml"}]}
```

The manifest is JSON; standalone OpenAPI specifications may be JSON or YAML.
External/file references and multi-file contracts are currently unsupported.
Use at most 16 unique declarations; paths must stay inside the project and have
`.json`, `.yaml` or `.yml` extensions. Malformed or unsupported declarations remain
visible rather than being silently ignored. A declaration without a receipt is
absent, not compatible.

Install the optional trusted checker explicitly. The provided development/CI
utility downloads checksum-pinned official 1.33.0 archives for Windows/Linux
x86_64 into a **new directory**:

```bash
python -m eval.oasdiff_install --directory NEW_ENGINE_DIR
```

Other platforms can install the official [oasdiff release](https://github.com/oasdiff/oasdiff/releases/tag/v1.33.0)
manually. Select the executable explicitly; runtime export never installs or
discovers an engine on your behalf. The selected program must be trusted: the
contained process runner provides lifecycle/output limits, not a security sandbox.

```bash
python plugin/bin/ep_contract.py --project PATH --id public-api --engine OASDIFF_EXECUTABLE --base BASE --head HEAD
python plugin/bin/ep_contract.py --project PATH --id public-api --engine OASDIFF_EXECUTABLE --format json --output observation.json
python plugin/bin/ep_patchproof.py --project PATH --base BASE --head HEAD --format json --output bundle.json
```

`ep_contract` explicitly runs the checker and retains an unsigned receipt in
`.elevenpowers/contracts.json`. Its exit codes are 0 for complete/no ERR breaking
findings, 1 for complete/ERR breaking findings, and 2 for incomplete execution or
publication/configuration errors. `--seconds` accepts 0–600, default 30; `--force`
permits replacing an export, otherwise output refuses overwrite atomically.
`ep_patchproof` reads saved observations, computes current freshness and associates
them with the requested patch. It executes no checker and its existing binding
gate does not become a compatibility gate.

Both inputs first pass `validate` at the WARN threshold. Only then does the
`breaking` command compare them at ERR. WARN/INFO comparison counts remain visible.
The adapter copies only committed blobs into a private directory, disables
external references, uses a fixed empty checker config and strips `OASDIFF_*`
overrides. It records the exact commit/tree pair, input SHA-256s/blob IDs,
manifest/configuration digest, producer version/binary hash, platform and limits.
No raw specs, output, endpoint findings or executable paths appear in exports.

Spec or manifest edits, changed executable bytes, another requested patch range,
missing files, corrupt state and observed concurrent changes leave association
unavailable. Freshness, result, execution and patch association are distinct:
a fresh failing result is still a failure, and a fresh result from another range
does not bind this patch. CRLF checkout normalization can conservatively leave
raw-byte freshness stale. Retained history is bounded to 64 receipts/1 MiB;
evictions are counted and damaged history is not reset silently. Manifest reads
are limited to 64 KiB, blobs to 2 MiB each, and binary hash reads to 128 MiB.

This observes specification compatibility under one checker policy. Actual route
implementations, deployment behavior, database/security compatibility and consumer
tests remain separate evidence. Producer hashes identify bytes, not authenticity
or independent attestation. No compatibility percentage or coding-benefit claim
is derived from a passing checker.

For a model-free JSON/YAML exercise in two independently created repositories:

```bash
python -m eval.openapi_contracts --output NEW_DISPOSABLE_DIR --engine OASDIFF_EXECUTABLE
```

Prefer ignored scratch or a location outside other repositories; each project
creates its own Git boundary and the utility refuses an existing output directory.
See [design](../docs/design/patchproof-openapi.md),
[validation](../docs/validation/2026-10-12-patchproof-openapi.md) and
[journey 74](../journey/74-a-contract-needs-a-producer.md).
