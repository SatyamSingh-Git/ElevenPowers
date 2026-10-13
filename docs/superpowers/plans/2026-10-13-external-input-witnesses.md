# External Input Witnesses v1 Implementation Plan

> For agentic workers: execute inline with superpowers:executing-plans, witnessed RED→GREEN controls and one fresh whole-branch review at the end.

**Goal:** Qualify receipt reuse against explicitly approved local dependency/tool bytes.

**Architecture:** Shared strict declaration/binding and bounded collection modules,
then optional execution witness association, read-only export and actual controls.

**Tech Stack:** Python standard library, existing project-owned commands, Git,
Python and Node disposable exercises. No runtime package or model installation.

**Spec:** `docs/design/external-input-witnesses.md`

## Global constraints

- Generalized for any project; no project-name, host or language-specific policy.
- Explicit private root approval; declarations cannot grant external reads.
- Schema 1 policy/approval, 64 KiB each; 32 witnesses, 32 paths each, IDs 1–64.
- Default 2,048 files / 4,096 entries / 32 MiB / 10 seconds / depth 32.
- Maximum 16,384 files / twice as many entries / 256 MiB / 60 seconds.
- Existing caller deadline, required commands, profiles and cleanup limits stay intact.
- No project commands/imports/installations/network/model in reporting or collection; bounded read-only Git metadata checks are allowed.
- Match selected bytes only; preserve incomplete observations and historical results.

## Review focus

1. Tracked or copied root bindings must not authorize private files in another project.
2. Linked/replaced paths and descriptors must not silently escape approved roots.
3. Empty or truncated collection, additions/deletions and budget exhaustion cannot qualify reuse.
4. Late policy/binding/source changes must invalidate final associations and defer commands.
5. Older records and source-only receipt states must not acquire invented external freshness.

### Task 1: Demonstrate the actual unchanged-source gap

Files: `tests/test_external_input_reuse.py`.
Consumes existing `verify`/`plan`; produces actual dependency control fixtures.

- [x] Write Python/Node fixtures with a separate dependency directory, committed
  unchanged source and stable private root approval. First check passes.
- [x] Independently change dependency value 2→9; actual direct check fails.
- [x] Assert `plan(...)["checks"][0]["action"] == "run"`; observe RED from current reuse.
- [x] Keep unchanged-input positive controls, private counters and source/HEAD checks.
- [x] Preserve the RED outcome and push the reproduced controls with scope explained.

### Task 2: Strict policy and explicit local root approval

Files: `core/inputs/definition.py`, `core/inputs/bindings.py`,
`core/inputs/__init__.py`, `tests/test_input_definitions.py`,
`plugin/bin/ep_inputs.py`, `tests/test_input_cli.py`.
Interfaces: `definition.load(root) -> dict|None`;
`bindings.load(root, definition, deadline) -> dict`;
`bindings.bind(root, name, directory, replace=False) -> None`.

- [x] Assert missing policy returns None, valid literals load, malformed/duplicate/
  traversal/drive/unknown/non-finite/oversized policy raises controlled ValueError.
- [x] Assert `bind(...)` approves only declared roots, refuses links/state/ancestors,
  refuses copied/tracked approvals and replacement without explicit flag.
- [x] Run absent-module RED, then implement strict bounded reads and atomic private
  binding save with existing `jobs.replace`; preserve other ignore rules.
- [x] Implement explicit bind/inspect CLI, bytecode suppression before imports and
  controlled scrubbed diagnostics; no inspection-side writes.
- [x] Verify actual CLI and legitimate/adversarial controls GREEN; commit/push.

### Task 3: Shared bounded external-byte collection

Files: `core/inputs/collection.py`, `tests/test_input_collection.py`.
Interface: `capture(root, deadline) -> dict` with schema/state/fingerprint,
witnesses/counts/issues/limits. Missing declaration is `not_configured`.

- [x] Assert content/name/scope edits, additions/deletions alter complete fingerprints;
  repeated unmodified captures match and project file bytes remain unchanged.
- [x] Assert linked/special/unavailable/moving inputs, limits and malformed approval
  yield incomplete with no qualifying fingerprint, including empty-tree coverage.
- [x] Observe RED; implement explicit scoped traversal, shared deduplicated reads,
  descriptor/path checks, bounded inventories and policy/binding rechecks.
- [x] Run full collector controls GREEN and standard-library import; commit/push.

### Task 4: Execution, reuse and read-only evidence views

Files: `core/patchproof/execution_state.py`, `execution_report.py`, `execution.py`,
`planning.py`, `report.py`, `github_output.py`; related existing and new tests.
Consumes `capture`; optional complete `external_inputs_fingerprint` augments
existing witness only when policy is configured. Legacy shapes remain readable.

- [x] Run Task 1 RED again; add old-record/new-policy, incomplete-approval,
  during-execution drift, binding/config movement and latest-result controls.
- [x] Add capture to execution witnesses and optional strict state shape. The
  report's independent view checks current policy before launch even with no history.
- [x] Preserve source binding while external associations explain drift/missing data.
  Complete drift allows fresh execution; incomplete capture refuses launch/reuse.
- [x] Make actual gap controls GREEN: source/HEAD/env unchanged, direct failure,
  no obsolete reuse, actual new failure; unchanged input retains one execution.
- [x] Retain every declared command and old history. Export literal bounded summaries
  without private paths/contents. Run affected controls GREEN; commit/push parts.

### Task 5: Actual disposable acceptance and qualification

Files: `eval/external_inputs.py`, `tests/test_external_inputs_exercise.py`,
`.github/workflows/tests.yml`; documentation and architecture.

- [x] Build an explicit new-directory exercise using Task 1 behavior expectations;
  controller checks current dependency correctness independently of report labels.
- [x] Rehearse Python/Node actual producers, readonly exports and private counters,
  with good/drifted/incomplete cases and saved machine-readable outcomes.
- [x] Push the actual exercise and add it plus stdlib imports to hosted qualification.
- [x] Request one fresh whole-branch review; regrade by user effect and repair
  Important/Critical findings in one witnessed RED→GREEN pass.
- [ ] Run full regressions, named audits, grader/source reproduction, doctor,
  hosted four-cell matrix, actual exercise and architecture/link checks.
- [ ] Update README/plan/status/contributor brief, guides, journey 78, validation,
  all five architecture views/Planned card/meta/generated mirror; push.
- [ ] Fast-forward main normally after gates; verify remote refs, raw runtime
  identity and served graph bytes. Archive only this plan's private workspace.
