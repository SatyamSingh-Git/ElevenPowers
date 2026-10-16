# Reliable Declared-Check Execution v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run a project's exact declared check explicitly and retain its actual qualified outcome.

**Architecture:** Reuse the owned verification primitives and existing receipts. Add a small explicit runner/API and CLI; host guidance advertises it without parsing arbitrary outer shells. Investigate the existing CI failure before runtime expansion.

**Tech Stack:** Python 3.11+, standard library runtime; actual Python/Node acceptance; existing pytest and hosted matrix.

**Spec:** `docs/design/declared-check-execution.md`

## Global Constraints

- Generalized for any project; no repository-specific runtime paths or commands.
- No new dependency or shell parser; reuse existing process/ownership/receipt APIs.
- Default allowance 120 seconds; finite positive values up to 600 seconds.
- Exit codes 0 passed, 1 failed, 2 incomplete/refused, 130 interrupted.
- Passive `off` and read-only inspection launch nothing; no new model sessions.
- Preserve all required checks, complete command scopes and conservative freshness.
- Push tested deliverables frequently; update docs/journey/all five architecture views; integrate main after qualification.

## Review Focus

- Outer successful shell trailers must not replace owned failure receipts (Task 3).
- Source/configuration/task/runtime changes during execution prevent a current pass even without external inputs (Task 2).
- Interrupted/new attempts supersede old passes with durable incomplete evidence (Task 2).
- Independent command scopes retain evidence when another input moves (Task 4).
- Same-command aliases and host callback parsing do not create a later misleading pass (Tasks 3–4).

### Task 1: Diagnose and repair advice exercise reliability

**Files:** `eval/advice_delivery.py`, `tests/test_advice_delivery_exercise.py`, targeted producer-boundary regression if justified.

**Interfaces:** Consumes `exercise(destination, hosts, languages, modes)`; preserves existing result shape, adds actionable component diagnostics where needed.

- [x] Preserve assertion diagnostics; inspect hosted evidence and run repeated actual JavaScript controls.
- [ ] Reproduce the original intermittent failure at a specific boundary and witness its regression RED. **Open incident:** the original log retained only a Boolean failure; twelve local and eighty hosted repetitions passed. There is no defensible boundary regression yet.
- [x] Record the inconclusive cause and complete diagnostic qualification, rather than inventing a fix. The cause of run 38623263659 remains unresolved.
- [x] Commit and push the inspected diagnostic change with its actual evidence.

### Task 2: Add owned declared-check execution

**Files:** Create `core/checks.py`; test `tests/test_checks.py`; reuse `core/verify.py`, `core/jobs.py`, `core/inputs/execution.py` as references.

**Interfaces:** Produces `execute(root: Path, property: str, *, seconds: float = 120) -> dict` and `available(root: Path) -> dict`; schema 1 result has `state`, `property`, redacted `command`, `exit_code`, `issues`, `receipt_count`, `attempt`. States passed/failed/incomplete.

- [x] Write actual-command tests for pass/fail/timeout/repair, unknown/off refusal, and during-command source/config/task/runtime drift; run RED (missing API).
- [x] Implement exact property resolution, ownership, provisional save, fresh source/input/guard pairs, contained execution and final save. Recheck configuration under ownership before launch; refuse nesting that would overwrite another journal.
- [x] Run `python -m pytest tests/test_checks.py -q`; require all controls GREEN, including persisted receipts and actual execution counters.
- [x] Commit and push.

### Task 3: Ship the portable CLI

**Files:** Create `plugin/bin/ep_check.py`; test `tests/test_check_cli.py`.

**Interfaces:** Consumes Task 2; accepts optional selector, `--project`, `--list`, `--seconds`, `--json`. Lists without creating state; execution exits according to spec.

- [x] Write subprocess tests for shell-masked failure, read-only listing, invalid/unknown/zero budgets, aliases, interruption, and redacted public output; run RED (CLI absent).
- [x] Implement CLI with metadata-only human/JSON output and explicit failure/incomplete exit status. Do not interpret outer command chains.
- [x] Run `python -m pytest tests/test_check_cli.py tests/test_checks.py -q`; require actual child and saved receipt assertions GREEN.
- [x] Commit and push.

### Task 4: Connect host guidance and portable acceptance

**Files:** `core/hook.py`, host guidance as appropriate, create `eval/declared_checks.py`, `tests/test_declared_check_protocol.py`, `.github/workflows/tests.yml`.

**Interfaces:** Consumes Tasks 2–3; produces `exercise(destination) -> dict` and `python -m eval.declared_checks --output NEW_DIR`; no model calls.

- [x] Write actual Python/Node scoped-input, milestones and outer-host callback controls; show pre-feature rejection/absence before implementation where the existing runner already suffices.
- [x] Add shared startup guidance using the actual runtime/script paths; keep passive and read-only semantics. Add hosted protocol execution/artifact retention.
- [x] Run protocol plus affected host/receipt tests; require owned failure survives outer callbacks, repaired checks become current, independent scopes remain current, and controls are explicitly synthetic rather than installed acceptance.
- [x] Commit and push.

### Task 5: Review, qualification and publication

**Files:** Relevant guides/README, `PLAN.md`, `docs/status.md`, dated validation, research/build-on, new journey, `architecture/index.html`, generated `architecture/graph-data.js`, protocol results.

**Interfaces:** Final public documentation describes the shipped CLI and actual qualified states; all five maps match final structure.

- [x] Refresh documentation, journey and architecture; render using `python architecture/check.py --render`.
- [x] Conduct one fresh whole-branch review; reproduce/fix Important findings RED→GREEN, retain rulings and deferred minors.
- [x] Run full suite, named audits, independent grader/reproduction, doctor, standard-library imports and final hosted matrix/artifact protocol. Local: 2,458 passed / 3 skipped; all four hosted cells passed. Read all failures; no green rerun is described as a demonstrated repair.
- [x] Push descriptive qualified parts, integrate main normally, verify remote heads and final docs/runtime/map identities, and report measured results and limitations. First main delivery: `2139b7f`; published HTML/data hashes verified after successful Pages deployment. The documentation closure preserves all qualified source inputs. Task 1 retains the explicitly open original CI cause.
