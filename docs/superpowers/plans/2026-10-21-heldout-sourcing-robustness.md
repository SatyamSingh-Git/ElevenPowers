# Held-out Sourcing Robustness and Remaining Path — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make held-out sourcing survive a long run on a small disk, regenerate the corpus by the frozen rule, then carry it through rehearsal, pilot and sweep.

**Architecture:** Amends Task 3 of `2026-10-20-heldout-vacuity.md`. The sampler journals atomically, resumes from its journal, deletes a repository's clone and environment once it can contribute no task, stops cleanly below a free-space floor, and reads history only up to a fixed end date so that a fresh clone reproduces the same candidates. Everything after sourcing reuses modules already built and tested.

**Tech Stack:** Python 3.13, git, pytest; Claude Code subscription CLI for the paid tasks only.

**Spec:** `docs/superpowers/specs/2026-10-20-heldout-vacuity-design.md`; parent plan `docs/superpowers/plans/2026-10-20-heldout-vacuity.md`.

## Why this amendment exists

On 2026-10-20 at 20:22 the sourcing run filled E: (58 repositories, ~5.4 GB of clones and venvs) and died inside its journal write. `Path.write_text` truncates before writing, so `corpus.json` was left at 0 bytes and the 13 tasks it held were lost. The traceback is retained in `E:/ep-installed/heldout/sample.log`. No outcome of any kind exists yet, so the rule amendments below are made before outcomes.

## Global Constraints

- Frozen rule values: seed `heldout-2026-10-20`, since `2026-06-01`, **until `2026-10-20T00:00:00+00:00` (new, committer date)**, want 40, cap 4, limit 400 commits per repository, repositories in `results/heldout/repos.json` order.
- Free-space floor: 2 GB on the work drive, checked before each repository.
- Mining suite timeout stays 120 s; nothing CPU-heavy runs beside sourcing (pilot, sweep, full pytest), because contention could push a repository past it and change the corpus.
- If fewer than 40 tasks validate, stop and report; the size is never lowered silently.
- Paid runs: Sonnet 5.5 at medium effort under the standing authorization; state runs, wall time and cost before launch; a launched slot is never retried.
- Escapes in Python source go through Write/Edit, never a heredoc.

## Review Focus

1. A crash during `git clone` leaves a partial directory that the next run mistakes for a clone; expect a stale partial to be discarded and cloned again (Task 1 test `test_a_partial_clone_is_discarded`).
2. Git marks object files read-only on Windows, so a plain `rmtree` of a clone raises `PermissionError`; expect pruning to remove it (Task 1 test `test_prune_removes_read_only_git_objects`).
3. Resuming with different rule values would splice two samples; expect a refusal (Task 1 test `test_resume_refuses_changed_rule_values`).
4. A pruned repository whose task was kept would orphan that task's grading; expect only non-contributing repositories removed (Task 1 test `test_prune_keeps_repositories_with_kept_tasks`).
5. The disk filling during a repository; expect the journal from the previous repository intact and the run resumable (Task 1 tests `test_a_failed_journal_write_keeps_the_previous_journal`, `test_low_disk_stops_before_the_next_repository`).

---

### Task 1: Sampler robustness

**Files:**
- Modify: `eval/mine.py` (`candidates` gains `until: str | None = None`, passed as `--until=`)
- Modify: `eval/heldout_sample.py`
- Test: `tests/test_heldout_sample.py`

**Interfaces:**
- Consumes: `eval.preservation._write(path, value)` (tmp + replace) for the journal.
- Produces:
  - `sample(repositories, candidates_for, check, *, seed, want, cap, progress=None, resume=None, room=None)`: `resume` is a prior journal dict; repositories in `resume['processed']` are skipped and its `tasks`/`rejections` preloaded. `room()` returning False raises `LowDisk` before the next repository. `progress(kept, rejections, processed)`.
  - `class LowDisk(Exception)`.
  - `clone(url: str, into: Path) -> bool`: clones into `into.with_name(into.name + '.partial')`, renames on success, discards a stale partial first.
  - `prune(work: Path, processed: list[str], kept: list[dict]) -> list[str]`: deletes `work/repos/<name>` and `work/venvs/<name>` for processed repositories that contributed no kept task; returns the names deleted. Read-only files are made writable (`shutil.rmtree(..., onexc=...)`).
  - Journal gains `until`, `processed` (repository URLs in order), `environments[url]['head']` (clone HEAD sha) and, when stopped, `stopped` (reason).
  - CLI gains `--until` (default above), `--min-free-gb 2`, and resumes automatically when `--out` holds a journal with equal rule values.

- [ ] **Step 1: Failing tests** in `tests/test_heldout_sample.py`:
  - `test_until_excludes_a_later_commit`: a temporary repository with commits dated (via `GIT_COMMITTER_DATE`) 2026-07-01 and 2026-10-21; `candidates(..., since='2026-06-01', until='2026-10-20T00:00:00+00:00')` holds only the first, and without `until` holds both.
  - `test_resume_skips_processed_repositories_and_keeps_their_tasks`: resume with `processed=['a']`, one kept task from `a`; `candidates_for` is never called for `a` and the returned tasks include it.
  - `test_resume_refuses_changed_rule_values`: a journal with seed `x` resumed with seed `y` raises `ValueError`.
  - `test_a_failed_journal_write_keeps_the_previous_journal`: write a journal, then write a value `_write` cannot serialise (`float('nan')`); the file still parses to the first value.
  - `test_low_disk_stops_before_the_next_repository`: `room` false on the second repository raises `LowDisk`; `progress` saw the first repository in `processed`, and `candidates_for` was never called for the second.
  - `test_prune_keeps_repositories_with_kept_tasks`: `repos/a`, `repos/b`, `repos/c`, processed `[a, b]`, kept task from `a`: returns `['b']`; `a` and unprocessed `c` remain.
  - `test_prune_removes_read_only_git_objects`: a read-only file inside `repos/b` is removed.
  - `test_a_partial_clone_is_discarded`: a local source repository cloned by path; a pre-existing `name.partial` with junk does not block, and `into` ends up a valid clone.
- [ ] **Step 2:** Run `python -m pytest tests/test_heldout_sample.py -q -p no:cacheprovider`; expect the new tests to fail for missing names.
- [ ] **Step 3:** Implement the interfaces above; `main` checks `shutil.disk_usage(args.work).free` against the floor in `room`, prunes inside the journal callback, catches `LowDisk` to write `stopped` and exit 1.
- [ ] **Step 4:** Green; mutation-check `until`, resume skipping, rule-value refusal, atomic write, the floor, prune's kept-task guard and the read-only handler. Existing tests in the file stay green (callers without the new arguments unchanged).
- [ ] **Step 5:** Commit and push.

### Task 2: Regenerate the corpus (network, no model)

- [ ] **Step 1:** Record in the progress ledger, before launch, the amendment (`until`, prune, resume) and that the lost 13-task journal is not recoverable.
- [ ] **Step 2:** Launch in the background, nothing heavy alongside:
  `python -m eval.heldout_sample --repos results/heldout/repos.json --work E:/ep-installed/heldout --out E:/ep-installed/heldout/corpus.json`
  Existing clones are reused; the `--until` bound makes them and fresh clones yield the same candidates.
- [ ] **Step 3:** On exit: if `stopped`, free space and relaunch the same command (it resumes). If it ends below 40 tasks, stop and report counts, per-repository yield and rejection reasons.
- [ ] **Step 4:** Copy `corpus.json` to `results/heldout/corpus.json` and its rejections to `results/heldout/rejections.json`; summarise tasks per repository and rejection reasons, including the three frame limits already seen (build-generated modules, suites reading their own installed metadata, test dependencies outside the install plan). Commit and push.

### Task 3: Rehearse all tasks (no model)

- [ ] **Step 1:** `python -m eval.heldout_rehearse --corpus results/heldout/corpus.json --work E:/ep-installed/heldout/rehearse --out results/heldout/rehearsal.json`
- [ ] **Step 2:** Every unusable task is reported by name and reason, never replaced. If fewer than 40 are usable, stop and report before any paid step.
- [ ] **Step 3:** Delete the rehearsal work folders; commit `rehearsal.json` and push.

### Task 4: Record and verify (no model)

- [ ] **Step 1:** Journey entry: the vacuity text-stdin defect caught before any paid run, the one-directional environment check, the disk-full journal loss and its repairs, the frame limits.
- [ ] **Step 2:** `docs/status.md` entry; architecture node description and changelog updated; `python architecture/check.py --render` passes.
- [ ] **Step 3:** Full suite `python -m pytest -q` (default temp dir, sourcing finished); report the real counts. Commit and push.

### Task 5: Pilot (paid gate)

- [ ] **Step 1:** Qualify without spending: `claude --version` accepts `claude-sonnet-5-5`; `subscription.auth` true; no API-key environment.
- [ ] **Step 2:** State to the user: 8 runs (first 4 corpus tasks × 2 arms × 1 replicate), cap 900 s each, ≤2 h wall time, the per-run cost estimate from earlier Sonnet runs, then launch under the standing authorization.
- [ ] **Step 3:** `python -m eval.heldout_run prepare --batch E:/ep-installed/heldout-pilot --corpus results/heldout/corpus.json --replicates 1` with the first 4 tasks only (a pilot corpus file listing them, kept with the batch); `execute` each slot in protocol order; `collect`.
- [ ] **Step 4:** Report cost per run, resolve rate, engagement of the assisted arm, every non-`graded` state and every breach. Not analysed for the estimand. Commit the pilot summary.

### Task 6: Sweep (paid gate, separate approval of size)

- [ ] **Step 1:** Size against remaining weekly capacity using the pilot's measured cost and time; state runs (240), wall time and cost; push the frozen schedule (`protocol.json` and seal) before the first launch.
- [ ] **Step 2:** Execute every slot once, in order; never retry; `collect`; `python -m eval.heldout_analyse` on the collected list; publish with its qualifications.
