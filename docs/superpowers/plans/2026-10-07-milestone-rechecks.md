# Explained Milestone Rechecks Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline, with one fresh whole-branch review at the end. Steps use checkbox syntax for tracking.

**Goal:** Explain and prioritize exact earlier checks without discarding fallback verification.

**Architecture:** Reuse the existing milestone report and ImpactGraph bridge. A pure command grouper preserves all evidence states; an explicit controller grades authored projects and real test outcomes independently.

**Tech Stack:** Python standard library runtime, existing graph adapters, pytest and optional Node for evaluation.

**Spec:** [Explained milestone rechecks](../../design/milestone-rechecks.md).

## Global Constraints

- Generalized for any project and shared by all hosts; no project path/command special cases.
- Inspection launches no project checks/model/installer/host and writes no state.
- 1,024 exact check identities, 64 milestone references per identity, 16 reasons per row, 256 input observations/leads; omissions explicit.
- No receipt-scope narrowing, safe exclusions, new blockers or automatic graph hooks.
- Existing cooperative 0–120 second report budget and explicit atomic exports.
- Push verified pieces incrementally with descriptive messages; update architecture and render before finishing.

## Review Focus

- Shared commands with conflicting milestone states retain all qualifications and require refresh.
- Missing graph observations/budgets leave every check as fallback; direct matches survive graph expiry.
- Source movement between evidence/graph scans cannot produce a complete advisory.
- Dynamic/subprocess and configuration dependencies are graded without treating fallback absence as unaffected.
- Equivalent changes and unrelated edits expose false leads and conservative invalidation rather than being relabelled improvements.

### Task 1: Command-level recommendations

**Files:** Create `core/milestones/rechecks.py`, `tests/test_milestone_rechecks.py`; modify `core/milestones/impact.py`, `report.py`.

**Interfaces:** `rechecks.plan(milestones, advice, *, complete) -> dict`; consumes qualified report rows and bounded explained leads; returns schema/state/commands/issues/safe_to_exclude/timing.

- [x] Write tests grouping shared commands and preserving mixed CURRENT/STALE states; direct/dependency/fallback priority; graph gaps and source mismatch; no extra execution or state writes.
- [x] Observe failures: `.venv/Scripts/python.exe -m pytest tests/test_milestone_rechecks.py -q`.
- [x] Implement pure grouping, bounded reasons and read-only report/Markdown integration. Preserve existing CLI exit codes and optional behavior.
- [x] Run new tests plus existing milestone/report/impact controls; expect all pass. Commit/push `Explain exact milestone rechecks while retaining fallback verification`.

### Task 2: Independent relevance and cost exercise

**Files:** Create `eval/milestone_rechecks.py`, `eval/milestone_recheck_cases.json`, `tests/test_milestone_recheck_exercise.py`.

**Interfaces:** `exercise(destination) -> dict`; explicit new disposable directory; frozen corpus sources, labels and fault/control assertions; ordinary `python -m eval.milestone_rechecks --output NEW_DIR` CLI.

- [x] Freeze case identities/labels before changes. Test required/direct/negative/fallback grading and prevent missing/setup checks counting as detection; verify overwrite refusal.
- [x] Observe failures before implementation.
- [x] Reuse existing real pytest/Node receipt producer; run positive, faulty and repaired/equivalent controls; collect all labels, actual outcomes, output/source digests and read timings.
- [x] Run exercise tests and actual explicit exercise; inspect every result including misses. Commit/push `Measure milestone recommendation relevance with frozen behavioral controls`.

### Task 3: Publish qualified delivery

**Files:** Update PLAN/status/README feature section, guides, journey, validation, architecture and public results.

- [x] Publish sanitized original observations and digests; distinguish capability, limited labelled relevance and no agent benefit.
- [x] Render `python architecture/check.py --render`; verify docs links and runtime stdlib imports.
- [x] Fresh whole-branch reviewer; one reproduced fix pass for relationship attribution, incomplete-attempt persistence and multirow Markdown; 16 corrected controls pass and original grades remain unchanged.
- [x] Publish the code, six result families, guides, findings, status and all affected architecture views incrementally with descriptive messages; retain all open exits.

**Main integration rule:** Run final affected regression and the hosted full suite
on this exact branch head. Fast-forward authorized main only after all four
Windows/Linux Python 3.11/3.13 jobs pass. Hosted execution and main history carry
that integration evidence separately from implementation checkboxes.
