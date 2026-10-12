# PatchProof OpenAPI implementation plan

> Execute inline with `superpowers:executing-plans`; one final whole-branch review.

**Goal:** bind real OpenAPI compatibility observations to exact committed inputs
and export their qualifications for any project.
**Spec:** [PatchProof OpenAPI](../../design/patchproof-openapi.md).
**Stack:** standard-library runtime, existing Git/process/storage/export helpers,
explicit optional oasdiff 1.33.0 executable. No model calls.

## Global constraints

Manifest 64 KiB / 16 declarations; blobs 2 MiB each; executable 128 MiB;
receipt state 1 MiB / 64 records; shared 0–600-second deadline, default 30.
Fixed empty checker config, validate WARN and compare ERR thresholds, external
refs false; exact engine version 1.33.0. Reporting runs no checks or installs.
Keep existing portable schema unchanged and retain incomplete evidence.

## Task 1 — declarations and retained contract observations

Files: `core/patchproof/contracts.py`, `tests/test_patchproof_contracts.py`.
Produces `declarations(root)` and bounded `load(root)`/`save(root, record)`.
Manifest is schema 1 with unique safe IDs and supported relative paths; strict
receipt schema validates types/digests/outcomes, refuses linked/corrupt state.
Write real filesystem controls first: valid/absent/unsupported/duplicate/path
escape/over-budget manifests, durable records, corrupt/linked state and eviction.
Observe missing module fail, implement, run focused controls, commit/push.

## Task 2 — pinned real producer and bounded committed execution

Files: `core/patchproof/openapi.py`, `eval/oasdiff_install.py`,
`tests/test_patchproof_openapi.py`.
Consumes existing `identity.collect`/`GitRead`, Task 1 declaration/store.
Produces `check(root, contract_id, engine, base='HEAD~1', head='HEAD', seconds=30)`.
Copy bounded regular blobs; before/after patch, declaration and executable guards;
real validation then comparison, independent outcome/execution and provenance.
Installer is explicit development/CI utility, pins official archive digests and
extracts only the named binary. Never invoked by runtime or reporting.
Observe real compatible/incompatible/invalid/external/timeout controls fail before
API; qualify output status consistency, version/config, blob modes and budgets.
Push executable/protocol and each completed runner qualification separately.

## Task 3 — fresh associations in existing PatchProof bundles

Files: `core/patchproof/contract_report.py`, `core/patchproof/report.py`,
`tests/test_patchproof_contract_report.py`.
Consumes Task 1 records/declarations and existing patch/report binding.
Produces `inspect(root, patch, deadline)` with absent/incomplete/fresh/stale/gone
states, patch-specific association and sanitized producer/input summaries.
Before/after saved-state/declaration reads, exact pair and current raw input hashes
plus current engine digest; report never runs the engine. Write stale spec/config/
engine/range, damaged/moving state, privacy and both-format controls RED→GREEN.
Run old PatchProof/portable regressions, commit/push additive integration.

## Task 4 — explicit CLI and unrelated project exercise

Files: `plugin/bin/ep_contract.py`, `eval/openapi_contracts.py`, CLI/exercise tests,
`results/patchproof-openapi/` and CI dependency/import steps.
CLI selects one declared ID and explicit engine, emits qualified JSON/Markdown;
complete pass exits 0, incompatible exits 1, incomplete/error exits 2.
No output overwrite by default. Ordinary PatchProof CLI remains read-only.
Run two unrelated real repositories through pass/fail/incomplete/absent/stale
states, independent Git/input hashes and export checks. Save no raw specifications,
outputs or engine paths in public artifacts. Push verified CLI and controls.

## Task 5 — review, documentation and integration

One fresh whole-branch review, Important/Critical findings witnessed RED→GREEN in
one repair pass; defer Minor findings explicitly. Run full regressions, named audit
probes, grader/host checks, stdlib imports and checksum-pinned four-job hosted CI.
Update README, guide, PLAN/status, contributor brief, journey 74, research/validation
and all affected architecture views. `architecture/check.py --render` and local
link validation are required. Integrate verified code onto main under standing
authorization; report CI/publication outcomes and unresolved incidents honestly.

## Review focus

1. Implicit checker configuration, environment overrides and external refs cannot
   change or extend the recorded inputs/policy.
2. Invalid specs, output limits and inconsistent exit/finding states never pass.
3. Changed executable/config/spec/refs and linked state cannot reuse a bound pass.
4. Corrupt/evicted history and unknown declarations stay visible without resetting.
5. Exported metadata does not disclose raw contents, checker paths or findings.

## Execution outcome — 2026-10-12

All five tasks delivered. One independent review found three Important, no
Critical/Minor findings. Five real regressions failed before the single repair
pass and passed after; all 37 contract controls passed. Local full regression
(2063 passed, 2 skipped in 1368.86s (0:22:48)), 107 audit probes and [four-job hosted qualification](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38214465591)
passed. Docs, five architecture views and separately identified producer
observations retain the qualifications. ImpactGraph enrichment is next;
installed-session requalification and causal benefit remain separate.
