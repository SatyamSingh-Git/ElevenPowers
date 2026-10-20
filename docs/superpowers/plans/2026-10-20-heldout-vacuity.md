# Held-out vacuity comparison implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independently sourced, closed-book corpus of real-repository tasks and a sealed subscription runner, so ordinary vs assisted vacuity can be compared exactly as the design fixes it.

**Architecture:** Sourcing is a pure, frozen pipeline (ranking → repositories → commits → validated tasks) whose every rejection is retained. Each repository gets its own virtual environment holding its test dependencies but not the package itself, so the fix cannot be imported. The runner reuses `eval.live` materialise/grade, `eval.preservation`'s seal/never-retry pattern and `eval.subscription`'s command and auth.

**Tech Stack:** Python stdlib, git, venv/pip, pytest, Claude Code subscription CLI.

**Spec:** [Held-out vacuity by arm](../specs/2026-10-20-heldout-vacuity-design.md)

## Global Constraints

- Ranking snapshot: `top-pypi-packages-30-days.min.json`, `last_update` 2026-10-01, retained with its sha256; packages considered in rank order up to rank 400.
- Excluded libraries: click, attrs, jinja2, markupsafe, itsdangerous, and every repository named in `eval/corpus.lock` or `eval/corpus-paired.lock`.
- Permissive licences only: MIT, BSD-2/3-Clause, Apache-2.0, ISC, PSF/Python-2.0; pure Python = the latest release ships a `py3-none-any` (or `py2.py3-none-any`) wheel.
- Commit cutoff: authored on or after 2026-06-01; seed `heldout-2026-10-20`; want 40 tasks; at most 4 per repository.
- Model `claude-sonnet-5-5`, effort medium, subscription only, `ANTHROPIC_DEFAULT_HAIKU_MODEL` pinned to it; 900 seconds per run; never retry a launched slot.
- 40 tasks × 3 replicates × 2 arms = 240 runs; primary test two-sided Wilcoxon signed-rank over tasks, α 0.05 (`eval.vacuity_power._signed_rank`).
- Every sourcing and run artifact retains rejected/incomplete rows with reasons; no runtime (`core/`, `plugin/bin`) change is needed or allowed for sourcing.

## Review Focus

- Distribution name differs from import name (`python-dateutil` → `dateutil`): the closed-book canary must test the import name, read from the wheel's `top_level.txt`/RECORD, not the project name.
- Tests in `test/` rather than `tests/`, or a flat (non-`src/`) layout: discovered per repository, not assumed.
- A suite slower than the 120 s mining timeout: rejected with that reason, never silently dropped.
- A commit message that is only an issue reference or empty: retained as-is (the prompt rule is fixed), flagged in the corpus row.
- A repository whose test extras cannot be installed offline later: environment built once at sourcing time; a missing dependency at run time is a `setup` outcome, not a failure.

---

### Task 1: Repository selection under the frozen rule

**Files:**
- Create: `eval/heldout_source.py`, `tests/test_heldout_source.py`

**Interfaces:**
- Produces: `select(ranking: dict, metadata: Callable[[str], dict | None], *, limit: int, exclude: set[str]) -> list[dict]` — rows in rank order `{project, rank, repo, verdict: 'accepted'|'rejected', reason}`; `repo` is `https://github.com/<owner>/<name>` or `''`.
- CLI: `python -m eval.heldout_source --ranking FILE --limit 400 --out repos.json` (fetches `https://pypi.org/pypi/<project>/json`, records each response's sha256).

- [ ] **Step 1: Failing tests** with fixture metadata: an MIT pure-Python GitHub package is accepted; rejected with distinct reasons: no GitHub source URL, compiled-only wheels, GPL licence, excluded name (`click`), metadata unavailable; output preserves rank order and stops at `limit`.
- [ ] **Step 2: Run** `python -m pytest tests/test_heldout_source.py -q` — FAIL (module missing).
- [ ] **Step 3: Implement** `select`; GitHub URL from `project_urls` values (`Source`, `Repository`, `Code`, `Homepage` order) normalised to owner/name; licence from `license_expression`, then `license`, then classifiers.
- [ ] **Step 4: Run** tests — PASS; mutation-check each rejection rule.
- [ ] **Step 5: Run the real producer** against the retained ranking snapshot; retain `results/heldout/repos.json`; commit and push.

### Task 2: Per-repository closed-book environment

**Files:**
- Create: `eval/heldout_env.py`, `tests/test_heldout_env.py`

**Interfaces:**
- Produces: `build(repo: Path, venv: Path) -> dict` → `{state: 'ready'|'rejected', reason, python, import_names: list[str], test_dir, source_dir, pythonpath}`; installs `.[test]`, `.[tests]` or `.[dev]` (first that resolves), then uninstalls the distribution itself; `canary(python: str, import_names, cwd: Path) -> bool` is True only when none of the import names imports from a neutral directory.

- [ ] **Step 1: Failing tests** on a disposable local package (flat and `src/` layouts, a `test/` directory, import name ≠ distribution name): ready environment, canary True after uninstall and False if the package is left installed (adversarial), and the right `pythonpath` (`src` or `.`).
- [ ] **Step 2–4:** red, implement, green; mutation-check the uninstall and canary.
- [ ] **Step 5:** commit and push.

### Task 3: Commit sampling, validation and corpus freeze

**Files:**
- Create: `eval/heldout_sample.py`, `tests/test_heldout_sample.py`
- Modify: `eval/mine.py` (`candidates` gains `since: str | None = None`; `validate`/`run_tests` gain `python: str = sys.executable` — defaults keep existing callers unchanged)

**Interfaces:**
- Consumes: Task 1 rows, Task 2 `build`/`canary`, `eval.mine.candidates/validate`.
- Produces: `order(items: list[tuple[str, str]], seed: str) -> list[tuple[str, str]]` (sha256(seed‖repo‖sha) ascending); `sample(..., want=40, cap=4)` → `results/heldout/corpus.json` (`Instance` rows plus `python`, `import_names`, `pythonpath`) and `results/heldout/rejections.json`.

- [ ] **Step 1: Failing tests:** ordering is a pure function of seed and ids; the cap stops a fifth task from one repository; an existing caller of `candidates`/`validate` without the new arguments behaves as before (forward) and `since` excludes an older commit (adversarial).
- [ ] **Step 2–4:** red, implement, green; mutation-check order, cap and `since`.
- [ ] **Step 5: Real sourcing run** (network, no model): blobless clones into `E:/ep-installed/heldout/repos/`, environments, validation in hash order until 40 or the accepted repositories are exhausted. Retain corpus, rejections and clone heads; commit and push. If fewer than 40 validate, stop and report — the size is not lowered silently.

### Task 4: Rehearsal on gold patches

**Files:**
- Create: `eval/heldout_rehearse.py`, `tests/test_heldout_rehearse.py`

**Interfaces:**
- Produces: `rehearse(task: dict, work: Path) -> dict` → `{base_fails, gold_resolves, gold_vacuous, canary, seconds}` using `eval.live` grading and the B7/B9 vacuity probe.

- [ ] **Step 1: Failing tests** on a disposable task: gold resolves and is not vacuous; a gold patch stripped of its tests is vacuous; a canary failure marks the task unusable.
- [ ] **Step 2–4:** red, implement, green.
- [ ] **Step 5:** rehearse all 40; a task whose gold is vacuous or whose canary fails is reported, not quietly replaced; commit and push.

### Task 5: Sealed subscription runner for mined tasks

**Files:**
- Create: `eval/heldout_run.py`, `tests/test_heldout_run.py`

**Interfaces:**
- Produces: `prepare(batch: Path, corpus: Path, *, replicates=3, seconds=900) -> dict` (protocol + seal; slots `task:arm:replicate`, arms interleaved per task, order alternating by replicate); `execute(batch: Path, slot: str, executable: str) -> dict` (materialise without `.git`, assisted = `core.hosts.setup.install` + declared tests command, ordinary = none, closed-book tool denial, run, grade, vacuity probe, record; refuses an existing result).

- [ ] **Step 1: Failing tests** with a fake host (as `tests/test_workflow_controller.py` does): the seal refuses a changed corpus/runtime; an existing slot is never relaunched; assisted gets hooks and ordinary none; the canary is re-checked before launch; a fake host that reaches for `git log`/network is recorded, not credited.
- [ ] **Step 2–4:** red, implement, green; mutation-check seal, never-retry and arm wiring.
- [ ] **Step 5:** commit and push.

### Task 6: Analysis fixed before outcomes

**Files:**
- Create: `eval/heldout_analyse.py`, `tests/test_heldout_analyse.py`

**Interfaces:**
- Produces: `analyse(records: list[dict]) -> dict` — primary signed-rank over per-task (ordinary − assisted) vacuous fractions among resolved runs, dropped/tied counts, secondary sign test on resolve, regressions, seconds, cost, adoption.

- [ ] **Step 1: Failing tests:** synthetic records reproduce a hand-computed statistic; replicates are aggregated per task (adversarial: duplicating a task's runs does not change n); an arm with no resolved run drops the task and counts it.
- [ ] **Step 2–5:** red, implement, green, commit and push **before** any paid run.

### Task 7 (paid gate): Pilot

- [ ] Restate the cost estimate from Task 5's fake-host timings; with standing authorization, run 4 tasks × 2 arms × 1 replicate; retain all; measure cost/run, resolve rate, engagement and harness health. Not analysed for the estimand.

### Task 8 (paid gate): Sweep

- [ ] From the pilot, restate runs, wall time and cost to the user before launch; freeze and push the schedule; run all 240; analyse exactly as Task 6; publish ties and nulls as such.
