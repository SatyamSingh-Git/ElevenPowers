# oasdiff producer provenance

2026-10-12. Borrow oasdiff 1.33.0, Apache-2.0, pinned upstream commit
`322d7ae815e5fb80f415bd4e8ef16d4b30cd8bdf`.
Sources: [official release](https://github.com/oasdiff/oasdiff/releases/tag/v1.33.0),
[license](https://github.com/oasdiff/oasdiff/blob/v1.33.0/LICENSE),
[breaking command](https://github.com/oasdiff/oasdiff/blob/v1.33.0/docs/BREAKING-CHANGES.md).
The producer, flags and outputs below were also executed directly on the official
checksum-verified Windows x86_64 binary before writing the adapter parser.

Official release API archive digests used by the explicit installer:

- Windows amd64: `22f98c7247075f8a446e783595802d6d38637de1760df264f3d4b3309f766c5b`.
- Linux amd64: `43a4e328e2d13ba1552d760aa68d2485c75c5621f309f6ff64ae895188345247`.

Actual version output: `oasdiff version 1.33.0`.
`breaking --format json --fail-on ERR` emitted `[]`/exit 0 for a description-only
change, and `api-path-removed-without-deprecation`, level 3/exit 1 for endpoint
removal. A malformed document could produce the same removal finding, motivating
the separate `validate --fail-on WARN` phase. Real validation found missing info
and paths with level 3/exit 1. `--allow-external-refs=false` refused an HTTPS
reference with load-error exit 102. Actual command help confirms implicit config
lookup and `OASDIFF_CONFIG`; the adapter strips overrides and passes its own `{}`.

The adapter requires exact version 1.33.0 and consistent typed JSON array/exit
semantics. Only stable rule IDs/counts are retained, never raw messages or endpoint
locations. Private raw producer observations are retained for diagnosis; public
project observations contain semantic states and hashes. Other engine versions,
custom policies, split specifications and broader API guarantees need new controls.

The independent branch review exposed two producer limits. Duplicate JSON names
were accepted and the later `paths` value hid an earlier one; duplicate YAML
mappings were rejected. An external OpenAPI 3.1 `$dynamicRef` passed validation
and comparison without observing the referenced schema. This demonstrated missing
semantic input coverage, not a network request. Actual `upgrade --format json`
preserved that keyword, allowing a producer-backed structural guard for both
formats without writing a YAML parser. Canonicalization is only that guard;
comparison still receives the original committed bytes.

The adapter now rejects duplicate-key JSON and conservative dynamic/recursive/
custom-dialect keys, including literal occurrences. The recorded configuration
identifies this strengthened policy; earlier known profiles remain retained but
stale. This does not certify the upstream engine across all JSON Schema features.
