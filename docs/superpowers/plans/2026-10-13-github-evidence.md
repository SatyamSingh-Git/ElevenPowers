# GitHub evidence presentation implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, with one fresh-context whole-branch review at the end.

**Goal:** Present exact-patch evidence and gaps to GitHub reviewers without implicit verification.

**Architecture:** Repair the witnessed cleanup boundary, reuse the read-only
PatchProof bundle, add context/summary/publication helpers, then a portable CLI
and composite Action. Exercise actual hosted summary and artifact producers.

**Tech Stack:** Python standard library, Git, existing evidence/export/runner,
GitHub Actions summary files and official MIT artifact uploader.

**Spec:** `docs/design/patchproof-github.md`

## Global constraints

- Same policy for every eligible Git project; no named-project commands/paths.
- Presentation runs no project command/model/install and needs no write token.
- Preserve existing bundle schema/verdicts and separate outcome/freshness/association.
- Defaults: 120 seconds, finite 0–600; event 2 MiB; JSON 8 MiB; summary 64 KiB;
  64 rows/category and 384 characters/free-text cell, explicit omissions.
- Fresh output directory outside project, fixed filenames, no overwrite/links.
- No default correctness gate, safety percentage, automatic comments or attestation.
- Frequent descriptive commit/push parts; all qualified code on main at the end.

## Review focus

1. A process's cached return code must not masquerade as actual Windows termination.
2. PR merge SHA or another repository/run must not qualify the selected subject/link.
3. Failed, absent, incomplete, stale or unavailable inputs must survive presentation.
4. Hostile Markdown/workflow strings or secret-like values must not become active output.
5. Artifact publication must not mutate the inspected project or silently overwrite files.

### Task 1: Repair witnessed Windows termination completion

Files: `core/process.py`, `tests/test_process.py`, `eval/execution_reliability.py`.
Consumes existing `run`; produces bounded kernel-handle completion in cleanup.

- [x] Add real repeated cancellation control against the original handle:
  `assert _winapi.WaitForSingleObject(child._handle, 0) == _winapi.WAIT_OBJECT_0`.
- [x] Run the control RED; preserve hosted failures and actual kernel observations.
- [x] Add `_reap(child, deadline)` with finite `child.wait` and Windows kernel wait
  using only remaining allowance; timeout remains incomplete, POSIX unchanged.
- [x] Run process/host/recovery controls GREEN; include handoff in bounded hosted
  repetitions; commit/push `Wait for actual Windows termination after cancellation`.

### Task 2: Read-only context-bound evidence presentation

Files: new `core/patchproof/github_context.py`, `core/patchproof/github.py`,
`tests/test_patchproof_github.py`. Consumes existing `report.build`; produces
`build(root, base, head, repository=..., event=None, timeout=120, impact=False)`.

- [x] Add tests using actual committed Python/Node fixtures and ledger receipts;
  preserve all property states and original bundle fields, project bytes unchanged.
- [x] Test actual PR-shaped fork/base/head context and wrong merge/repository:
  `with pytest.raises(ValueError): build(root, base, merge, repository=repo, event=pr)`.
- [x] Run RED; implement bounded context/event reads, exact subject matching and
  canonical public bundle hash with existing redaction; refuse invalid metadata.
- [x] Run complete task GREEN; commit/push `Bind GitHub evidence to exact declared subjects`.

### Task 3: Bounded literal summary and durable output

Files: new `core/patchproof/github_output.py`, `tests/test_patchproof_github_output.py`.
Consumes presentation; produces `markdown(value)` and `publish(value, destination=None, project=root)`.

- [x] Add controls for missing/failed/incomplete/stale states, credential-shaped
  values and injected Markdown; assert `'<script>' not in markdown(value)` and
  recorded omissions point to the full JSON artifact.
- [x] Add excessive-size, existing destination, link and inside-project controls:
  `with pytest.raises(ValueError): publish(value, root / 'artifact')`.
- [x] Run RED; implement fixed new external directory, bounded escaped summary,
  canonical JSON and no-overwrite outputs; no project mutation or transport call.
- [x] Run GREEN; commit/push `Export bounded literal GitHub evidence summaries`.

### Task 4: Portable CLI, composite Action and actual hosted exercise

Files: `plugin/bin/ep_github.py`, `github/patchproof/action.yml`,
`eval/github_presentation.py`, `tests/test_patchproof_github_cli.py`, workflow step/job.
Consumes Task 2/3 APIs; produces explicit Actions file writes and upload link mode.

- [x] Add failing real CLI controls, Actions environment-file simulation, exact
  repository/run URL validation, wrong identity refusal and read-only subprocess run.
- [x] Implement CLI; stdout contains controlled metadata rather than raw workflow
  strings. Validate runner file targets before writing. Default local exit means export.
- [x] Implement Action with data passed through environment/arguments, trusted
  runtime path, uploader revision and `contents:read` caller example.
- [x] Build independent actual-command exercise; inspect real `GITHUB_STEP_SUMMARY`,
  uploader URL/ID/hash and downloaded artifact. Publish needs/gaps intentionally;
  never credit upload as independent safety evidence.
- [x] Run GREEN controls and hosted producer; push coherent CLI/Action/exercise parts.

### Task 5: Review and complete delivery

- [x] One fresh whole-branch review, regrade by effect, one RED→GREEN repair pass.
- [ ] Full suite, named audits, independent grader/source reproduction, doctor,
  stdlib imports and hosted four-cell matrix plus actual presentation exercise.
- [x] Update README, PLAN/status, guides/indexes, contributor brief, validation,
  journey/index and every affected architecture view/card/meta/mirror.
- [x] Render architecture, resolve local links, preserve all failed attempts.
- [ ] Push and fast-forward main normally without rewriting qualified runtime bytes;
  verify remote identity, final Pages bytes and separately report automatic repeats.
