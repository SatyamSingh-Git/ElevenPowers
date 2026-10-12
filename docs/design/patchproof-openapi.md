# PatchProof OpenAPI receipts

2026-10-12. The next authorized PatchProof extension is one real contract
adapter. It is architectural work inside the shared runtime, generalized across
projects and coding hosts. The user requested inline implementation and frequent
pushes; the existing exact patch and export interfaces remain the foundation.

Borrow **oasdiff 1.33.0** (Apache-2.0), pinned at upstream commit
`322d7ae815e5fb80f415bd4e8ef16d4b30cd8bdf`. We add bounded committed-input
execution, exact producer/configuration provenance, retained outcomes and fresh
read-only PatchProof associations. We do not implement an OpenAPI diff engine.
The real Windows producer has been run before defining the parser.

## Project contract

Projects explicitly declare applicability in `elevenpowers.contracts.json`:

```json
{"schema": 1, "contracts": [{"id": "public-api", "kind": "openapi", "path": "api/openapi.yaml"}]}
```

JSON manifest only; OpenAPI specifications may be JSON or YAML. Allow at most
16 unique declarations, IDs of 1–64 ASCII letters/digits/underscore/hyphen,
relative `.json`/`.yaml`/`.yml` paths without traversal, drive syntax or hidden
state/Git paths. Manifest reads are bounded to 64 KiB. No declared contract is
invented by discovery. Absent, unsupported or malformed declarations stay visible.

`ep_contract.py --project PATH --id ID --engine EXECUTABLE --base BASE --head HEAD`
explicitly checks one declaration. It resolves the existing committed patch,
reads regular Git blobs (at most 2 MiB each), and copies only those two blobs
and a fixed empty checker configuration into a new private temporary directory.
External/file references are disallowed; multi-file contracts are unsupported.
The shared contained runner uses argument arrays, bounded output and a shared
0–600-second deadline (default 30 seconds). It is not a security sandbox.
Operators must trust the explicitly selected executable. Reporting never selects,
installs or launches an engine. No model session is required.

## Observed checker protocol

Require exact `oasdiff version 1.33.0`. Hash the resolved executable before and
after running, bounded to 128 MiB. Strip `OASDIFF_*` environment overrides and
pass `--config` with the private `{}` file, preventing implicit project settings.
Record version, executable SHA-256, OS/platform, configuration digest, limits,
commit/tree-pair identities, declaration/manifest digest and base/head input hashes.
These observations remain unsigned; they do not authenticate the executable.

First run `validate --format json --fail-on WARN --allow-external-refs=false`
on each input. Only complete exit 0 and a well-formed finding array without
WARN/ERR qualify validation. Invalid/load-error inputs retain incomplete
compatibility execution, never a compatible result.
Strict standard-library JSON loading rejects duplicate object names, including
JSON-form documents with a YAML suffix. Actual YAML duplicate mappings are
rejected by the pinned producer. Its `upgrade --format json` output is used only
as a bounded structural probe, with external references disabled; original blobs
remain the comparison inputs. The probe conservatively rejects `$dynamicRef`,
`$recursiveRef`, `$schema`, `$id`, `$vocabulary`, `$dynamicAnchor` and
`$recursiveAnchor` anywhere, including literal/example occurrences, and structures
deeper than 128. Custom/dynamic schema semantics are currently unsupported.
Then run `breaking --format json --fail-on ERR --allow-external-refs=false`.
The observed output is an array: empty with exit 0 for no findings, and rule
records with integer `level` 1/2/3. Exit 1 must agree with ERR findings; exit 0
must have none. Preserve WARN/INFO counts and qualified rule IDs. Unknown shape,
inconsistent status, stderr, truncation, timeout or unsupported version cannot
produce a complete compatibility observation. No raw output or finding text,
endpoint locations or contract contents enter exports.

## Receipt storage and report

Retain up to 64 schema-1 records in `.elevenpowers/contracts.json`, bounded to
1 MiB, under the existing short ledger OS lock and atomic writer. Record eviction
counts. Linked/corrupt/oversized state cannot be silently reset or treated as no
checks. Private engine paths support a fresh binary hash read but are not exported.

Latest records for each declared contract show result (`pass`, `fail`, `unknown`),
execution (`complete`, `incomplete`), freshly computed input/manifest/engine
freshness and exact requested-patch association separately. A failed check may
have bound inputs. Changed specs, declarations, executable bytes, requested
ranges, missing inputs or observed state movement invalidate qualification.
Read manifest/receipt state around report collection. A declaration without a
receipt stays absent. The existing schema-1 portable report is unchanged;
PatchProof gains an additive `contracts` section and matching Markdown.
API compatibility beyond the declared OpenAPI contract stays unsupported.
Working-tree CRLF normalization can conservatively leave raw-byte association
stale; do not substitute semantic equality for recorded input identity.

## Delivery controls and remaining work

Use real pinned-engine compatible/incompatible/invalid/external-reference cases
in two unrelated disposable repositories, plus stale spec/config/engine/range,
missing/corrupt state, timeout, bounded reads, privacy and JSON/Markdown controls.
Real producer acceptance is optional locally when the engine is absent and
required in hosted CI with checksum-verified pinned binaries. No fake engine
substitutes for those controls. Retain both legitimate and adversarial outcomes.

Compatible ImpactGraph enrichment, other contract producers, custom rule policies,
multi-file contracts, explicit broader verification and GitHub presentation
remain separate extensions. Installed-host successes stay dated at their original
runtime identity; neither this adapter nor its exercises establish coding benefit.
