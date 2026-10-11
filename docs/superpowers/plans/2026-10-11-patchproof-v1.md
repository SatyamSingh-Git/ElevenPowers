# PatchProof v1 implementation plan

Spec: [exact patch and receipt design](../../design/patchproof-v1.md).
Execution: inline, authorized by the user's instruction to start real work.
Branch: `codex/patchproof-v1`; start `01e8eea`.

## Global constraints

Generalized shared runtime, standard library only, read-only collection and no
model/project command runs during reporting. Preserve schema-1 portable reports.
Use bounded Git argument arrays and native binary output, existing redaction and
atomic publication. Keep results/execution/freshness/association distinct.
Push meaningful completed pieces with descriptive messages. Update plan, status,
guides, journey and all architecture views at delivery. Installed success remains
dated evidence; new runtime acceptance, advice consumption and coding benefit are
separate exits. Preserve the unresolved Linux cleanup observation.

## Task 1: Preserve binary command output

Files: `core/process.py`, `tests/test_process.py`.
Produces: additive `run(..., text=False)` preserving bytes, same bounds/cleanup.
Consumer: Task 2's raw Git metadata collection.
Write a regression using a real subprocess producing NUL, CRLF and non-UTF-8
bytes; run it and observe the missing keyword/behavior fail. Implement binary
capture without changing default text decoding or output-limit behavior.
Run `python -m pytest tests/test_process.py -q`.
Expected: new binary control and existing lifecycle/limits all pass.
Commit/push: `Preserve bounded binary output for exact Git metadata`.

## Task 2: Collect exact committed patch identities

Files: `core/patchproof/__init__.py`, `core/patchproof/identity.py`,
`tests/test_patchproof_identity.py`.
Produces: `collect(root, base, head, seconds=30)` dictionary with full IDs,
changed modes/blobs/paths, completeness and checkout qualifications.
Consumer: Task 3.
Write disposable real-Git controls before implementation: ordinary/empty ranges,
bad refs, clean/dirty index/worktree/untracked, root mismatch, rename/delete/binary,
read-only side effects and disabled configured helper commands, linked worktree,
symlink/submodule and exhausted budgets. Observe the unavailable API fail.
Implement bounded Git collection and versioned commit/tree-pair digests.
Run `python -m pytest tests/test_patchproof_identity.py tests/test_process.py -q`.
Expected: all controls pass; gaps never become empty successful descriptions.
Commit/push: `Bind patch descriptions to exact Git commit and tree pairs`.

## Task 3: Bind existing receipts conservatively

Files: `core/patchproof/report.py`, `tests/test_patchproof_report.py`.
Produces: `build(root, base='HEAD~1', head='HEAD', timeout=120)` bundle.
Consumer: Task 4 CLI/Markdown.
Write current/fail/incomplete/absent/zero-input/unrelated/stale declaration
controls; include dirty and alternate checkout, changed config/ledger/source
during collection, excluded patch paths and empty claims. Observe missing API
fail, then implement existing report wrapping and before/after guards. Never
upgrade source scopes or infer execution at commit from byte freshness.
Run `python -m pytest tests/test_patchproof_report.py tests/test_portable_report.py -q`.
Expected: only qualified input associations bind, existing schema unchanged.
Commit/push: `Export qualified patch associations without upgrading receipts`.

## Task 4: Ship explicit CLI and matching Markdown

Files: `plugin/bin/ep_patchproof.py`, report Markdown, CLI regression controls.
Produces: standalone JSON/Markdown export with atomic output and binding gate.
Write real CLI export/no-overwrite/force/privacy/error controls first, observe
missing CLI fail. Reuse existing export writer and text escaping.
Run the Task 3 regression command plus CLI tests.
Expected: Markdown/JSON show the same identity/gaps; no project commands run.
Commit/push: `Add standalone PatchProof evidence bundle exports`.

## Task 5: Qualify on unrelated projects and review

Files: model-free acceptance runner and results, dated validation.
Run real Python and Node pass/fail/interruption and export from committed ranges
with independently checked Git IDs; preserve machine-readable observations.
Run focused controls, stdlib imports, then one fresh whole-branch reviewer.
Reproduce Important/Critical findings RED→GREEN in one fix pass. Run full pytest,
audit probes, grader controls and host doctor. Compare every expected result with
actual output. No installed session or coding-benefit claim from these exercises.
Commit/push: descriptive qualification/fix messages based on actual changes.

## Task 6: Document delivered contracts and integrate

Files: `README.md`, `PLAN.md`, `docs/status.md`, `the-guide/`, `journey/`,
contributor brief, `architecture/` and CI stdlib imports.
Update concise features, commands/setup, limitations and contributor next tasks;
draw delivered modules and links in every affected architecture view and move
PatchProof v1 out of proposal status while leaving contract adapters open.
Run `python architecture/check.py --render` and validate local document links.
Expected: all five views render and no broken links.
Push final feature commit, dispatch hosted CI; integrate verified code onto main
under standing authorization, and record final CI/deployment results honestly.

## Review Focus

- Git config/environment helpers and filters cannot execute repository commands.
- Raw NUL paths and mode changes, especially linked inputs and submodules.
- Before/after scans cannot reuse stale caches or mix changing ledger snapshots.
- Receipt selection and missing declared checks cannot imply unrelated patch proof.
- Redacted exports remain exact in identity but honest about unsigned provenance.

## Execution outcome — 2026-10-11

All six tasks delivered. One whole-branch review produced three Important
findings; real producer controls witnessed and repaired each in one pass.
CI then exposed a separate advice test-oracle defect, reproduced with a
held OS lock and fixed without changing the advice runtime. Local full
regressions (2025 passed, 2 skipped in 1696.06s (0:28:16)), named audit probes and [four-job hosted CI](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38150648555)
passed. The runtime fingerprint and original installed-session successes
remain separate dated records; installed requalification, contract/graph
extensions and coding benefit remain open.
