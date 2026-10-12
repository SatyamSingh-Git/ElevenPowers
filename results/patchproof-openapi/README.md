# Declared OpenAPI capability controls

2026-10-12. [Observations](observations.json) retain real pinned oasdiff 1.33.0
execution in independently created JSON/Python and YAML/JavaScript repositories.
Both distinguish current, failed, incomplete, stale and absent contract states.
The public record preserves actual exits, producer/configuration hashes and
independent Git/input comparisons, with its producing commit/runtime identity.
It includes no specifications, raw outputs, endpoint findings or engine paths.

This establishes the local producer/receipt/export mechanism under the fixed
policy. It establishes no installed-host acceptance, attestation, deployed API
correctness or coding benefit. No model call was made. Later review repairs,
if any, require a new separately identified observation rather than rewriting
this initial producer record.

Reproduce explicitly into a new disposable directory, preferably ignored or
outside other repositories, with the checksum-pinned optional executable:

```bash
python -m eval.openapi_contracts --output NEW_DIR --engine OASDIFF_EXECUTABLE
```

Each child initializes its own Git boundary. IDs and timings can differ; expected
semantic states and actual exits `0`, `1`, no completed exit remain comparable.
Full local observations remain in the requested directory. See
[guide](../../the-guide/contracts.md),
[validation](../../docs/validation/2026-10-12-patchproof-openapi.md) and
[producer provenance](../../docs/research/oasdiff.md).
