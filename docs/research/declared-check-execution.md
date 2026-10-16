# Declared-check execution: reuse and boundary

The starting implementation is this repository's completion-owned verification
(`core/verify.py`), process containment (`core/process.py`), project ownership and
journal (`core/jobs.py`), exact declared parsing (`core/parsers.py`) and paired
selected input execution observations (`core/inputs/execution.py`). Existing
license/provenance is recorded in [build-on](build-on.md) and the
[license register](licenses.md); this milestone adds no third-party dependency.

What is added: explicit selection of a declared property outside completion,
durable real child outcomes independent of an outer shell's status, and optional
owned configuration/producer associations carried by ordinary receipts.

The motivating producer observation is retained in
[the previous installed controls](../../results/command-input-scopes/README.md):
both agents appended a shell trailer, so exact declared failure attribution was
not established. V1 preserves that matcher and gives agents an explicit path.
It does not reinterpret arbitrary shell chains, trust text claiming an exit code,
or call the new receipt a native host observation.

Actual Python and Node commands, independent external faults, repair and
missing-input refusal exercise the API. Five synthetic outer callbacks test
integration; these establish no model adoption, installed compatibility or causal
coding-quality improvement. Cross-task benefit needs a separately controlled
end-to-end comparison.
