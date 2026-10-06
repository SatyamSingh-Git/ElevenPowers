# Milestone Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Preserve qualified earlier behavior evidence across tasks and expose a generalized read-only milestone view.

**Architecture:** Strict project-owned declarations select exact aggregate command receipts. Bounded history lives in the existing atomic ledger; a separate report uses existing freshness and optional ImpactGraph without altering task verdicts.

**Tech Stack:** Python 3.11+ standard library, pytest controls, existing optional ImpactGraph adapters and Node for an independent producer control.

**Spec:** [Milestone verification](../../design/milestone-verification.md).

## Global Constraints

- All runtime behavior is project-independent and host-independent.
- No mandatory dependency, model session, automatic check execution or completion blocker.
- Declaration schema 1: 128 KiB, 64 milestones, 128 inputs and 16 checks per milestone.
- History: 256 latest command identities, 4 MiB JSON; report ledger read: 8 MiB.
- Report budget: cooperative 0-120 seconds, default 30; gaps cannot pass `--check`.
- Keep task verdicts, original scopes and receipt provenance separate.
- Commit and push independently verified pieces as delivered; update architecture before finishing.

## Review Focus

- Late/concurrent old-task saves must preserve newer history without certifying a newer task.
- An older pass must not hide a later incomplete/failing attempt on the same command.
- Missing coverage, empty observations and redacted identity must never yield current evidence.
- Partial graph paths must not certify unaffected behavior or permit test exclusion.
- Report collection concurrent with a definition/state change must expose movement.

### Task 1: Strict declaration inputs

**Files:** Create `core/milestones/definition.py`, `core/milestones/__init__.py`; test `tests/test_milestone_definition.py`.

**Interfaces:** `load(root) -> dict` supplies `configured`, `fingerprint`, `milestones`, `issues`; `safe_path(root, value) -> Path` validates ordinary normalized inputs. No directory/state writes.

- [x] Write valid/absent/invalid/schema/duplicate/path/budget controls first. A representative assertion is:

```python
def test_absent_definition_is_not_configured(tmp_path):
    from core.milestones.definition import load
    assert load(tmp_path)['configured'] is False
    assert not (tmp_path / '.elevenpowers').exists()
```

- [x] Run `.venv/Scripts/python.exe -m pytest tests/test_milestone_definition.py -q`; expect missing feature RED, then implement strict bounded JSON loading/path validation and rerun to GREEN.
- [x] Draw the implemented module and refresh the Planned card/design status; commit `Read bounded project-owned milestone behavior declarations` and push the branch.

### Task 2: Atomic cross-task receipt history

**Files:** Create `core/milestones/history.py`; modify `core/ledger.py`; test `tests/test_milestone_history.py` and existing persistence controls.

**Interfaces:** `retain(root, prior, records) -> dict` returns bounded schema-1 history, filtering configured aggregate command/kind pairs. `Ledger.milestone_history` survives load/save/new tasks independently of current claims.

- [x] Write real receipt round-trip/new-task/latest incomplete/corrupt/eviction/concurrent-save controls first. Pin the cross-task invariant:

```python
def test_new_task_keeps_history_without_adopting_claim_evidence(root_with_definition, passing_record):
    from core.ledger import Ledger
    first = Ledger(root=root_with_definition, task='first')
    first.add([passing_record]); first.save()
    Ledger(root=root_with_definition, task='second').save()
    second = Ledger.load(root_with_definition)
    assert second.evidence == []
    assert second.milestone_history['receipts']
```

- [x] Run focused history tests to RED; implement retention inside the existing write lock/payload replacement with detail stripping and explicit limits, then run history and ledger/command regressions to GREEN.
- [x] Draw the history flow; commit `Retain bounded milestone receipts across task boundaries atomically` and push.

### Task 3: Qualified read-only view

**Files:** Create `core/milestones/report.py`, `plugin/bin/ep_milestones.py`; modify `core/milestones/__init__.py`, `core/export.py`; test `tests/test_milestone_report.py`.

**Interfaces:** `build(root, *, seconds=30, changed=None, impact=False) -> dict`, `markdown(value) -> str`; additive portable report section for configured projects only.

- [x] Write current/fail/stale/incomplete/absent and scope mismatch controls first, using a real parser receipt. Preserve the key stale invariant:

```python
def test_later_input_edit_requires_reverification(project_with_saved_receipt):
    from core.milestones import build
    root = project_with_saved_receipt
    assert build(root)['milestones'][0]['state'] == 'CURRENT'
    (root / 'provider.py').write_text('value = 2\n')
    assert build(root)['milestones'][0]['state'] == 'STALE'
```

- [x] Run report/CLI tests to RED; implement shared freshness, safe bounded ledger reads, explicit scope/declaration/metadata checks, definition/state movement checks, JSON/Markdown and read-only CLI/export integration.
- [x] Run report/history/portable-report controls to GREEN; draw report/export flow; commit `Explain current, failed and stale milestone evidence without running checks` and push.

### Task 4: Explained impact advice and independent staged exercise

**Files:** Modify `core/milestones/report.py`, `plugin/bin/ep_milestones.py`; create `core/milestones/impact.py`, `eval/milestones.py`; test `tests/test_milestone_impact.py`, `tests/test_milestone_exercise.py`.

**Interfaces:** Optional `impact=True` with explicit `changed` or ledger touched paths, informational explained leads. `python -m eval.milestones --output NEW_DIR` explicitly creates disposable exercises and publishes capability observations; it starts no model.

- [x] Freeze consumer/provider/worker expectations, a seeded later fault, repair/equivalent and unrelated controls before feature adaptation. Test the actual independent expectations:

```python
def test_staged_exercise_rejects_fault_and_accepts_repair(tmp_path):
    from eval.milestones import exercise
    result = exercise(tmp_path / 'exercise')
    assert result['fault']['exit_code'] != 0
    assert result['repair']['exit_code'] == 0
    assert result['new_task_kept_evidence']
```

- [x] Observe RED; implement optional fresh graph/path-to-milestone advice with limits and actual Python/Node producer controls. Keep graph advice distinct from check status and retained fallbacks.
- [x] Run focused graph/exercise controls and execute the local exercise, retaining every state and elapsed observation. Commit `Explain cross-component rechecks with independent milestone controls` and push.

### Task 5: Review, delivery evidence and integration

**Files:** Update `README.md`, `PLAN.md`, `docs/status.md`, `the-guide/commands.md`, `the-guide/configuration.md`, `the-guide/milestones.md`, `whats-offered/roadmap.md`, architecture views/mirror/README, design status, journey/index and dated validation/index; include the new stdlib imports in `.github/workflows/tests.yml`.

- [x] Dispatch one fresh whole-branch reviewer with the spec, plan, review focus, actual test/control artifacts and progress rulings. Re-grade findings by effect; Important/Critical findings get one RED-to-GREEN fix pass; deferred minors are recorded.
- [x] Run `.venv/Scripts/python.exe -m pytest -q`, host doctor, independent grader, stdlib imports and `architecture/check.py --render`. Record actual counts and platform qualifications in dated validation.
- [x] Publish real exercise evidence and limitations; check affected local links. No coding-benefit or host-acceptance claim from capability controls.
- [x] Prepare and publish the documented final candidate with descriptive messages. Integration uses the exact-head hosted Linux/Windows gate below.

**Integration rule:** obtain hosted success for the exact candidate head, then
fast-forward main under standing authorization. Actual remote completion is
recorded by the [branch's Actions runs](https://github.com/SatyamSingh-Git/ElevenPowers/actions/workflows/tests.yml?query=branch%3Acodex%2Fmilestone-verification),
main's commit history and the execution ledger; a prepared candidate is not a
claim that the hosted gate has already passed.
