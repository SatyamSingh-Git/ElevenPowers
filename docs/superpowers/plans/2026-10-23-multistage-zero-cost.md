# Multi-stage v2, $0 phase — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build everything the multi-stage v2 comparison needs before any model call: the case format, the three oracles, the no-model rehearsal with its four variants, eight independently authored and reviewed cases, and the power simulation.

**Architecture:** Cases are directories of plain files (`eval/multistage_cases/<id>/`): a start tree, one reference diff per stage, a dependent-missed diff per cross-cutting stage, hidden group tests and a cumulative fact table. Four flat modules sit beside the existing `eval/` code: `multistage_cases.py` (load, validate, build a stage tree), `multistage_oracles.py` (behaviour groups, docs facts, rules), `multistage_rehearse.py` (reference and variants, no model) and `multistage_power.py` (simulation). Cases are written by fresh agents that are told nothing about ElevenPowers, and reviewed by others.

**Tech Stack:** Python 3.11+, stdlib, pytest 9; git for trees and patches (`eval.bundle.apply_patch`, `export_patch`); the revert probe `eval.heldout_vacuity.vacuity`; `_signed_rank` from `eval.vacuity_power`.

**Spec:** [docs/superpowers/specs/2026-10-23-multistage-field-claims-design.md](../specs/2026-10-23-multistage-field-claims-design.md)

## Global Constraints

- Nothing in this plan calls a model. The qualification, pilot and full run are separate, gated on the user's go.
- Python 3.11 is the floor (CI runs 3.11 and 3.13 on Ubuntu and Windows); run changed tests under `py -3.11` before pushing.
- Case projects use the standard library and pytest only.
- No change under `core/` or `plugin/`: ElevenPowers runs as shipped.
- Each case has six stages: at least four `cross-cutting`, at least one `self-contained`, and every stage changes at least one documented fact.
- Requests never mention docs, tests, the changelog, `CLAUDE.md` or the dependents.
- The `CLAUDE.md` rules, verbatim in every case:
  1. Keep `docs/reference.md` current whenever behaviour changes.
  2. Add a `CHANGELOG.md` entry for every change.
  3. Every bug fix carries a test.
  4. Never edit `<protected path>`.
- Behaviour groups: two base groups (`since` 0) plus two per stage; they check behaviour, never spelling.
- Write regexes and escapes with Write/Edit, never a shell heredoc.
- Commit and push to `main` after each task; read `gh run list` after pushing.

## Review Focus

1. An agent's tree carries its own `conftest.py` or `pytest.ini` that skips or rewrites tests. Expected: groups still run in the oracle's private folder, and a skip-everything conftest in the tree does not turn a failing group into a pass. Pinned in Task 2.
2. `docs/reference.md` is missing, empty or restructured into prose. Expected: every expected fact counts as stale, with no crash. Pinned in Task 2.
3. A candidate hangs, for example with an infinite loop in an imported module. Expected: the group reads `timeout`, which is not a pass, within the allowance. Pinned in Task 2.
4. CRLF line endings in the docs or the changelog. Expected: parsing gives the same facts and counts as with LF. Pinned in Task 2.
5. The `## Unreleased` section is missing or renamed. Expected: the changelog count is 0 and nothing crashes. Pinned in Task 2.

---

### Task 1: Case format, loader and stage trees

**Files:**
- Create: `eval/multistage_cases.py`, `eval/multistage_cases/conftest.py`
- Create: `tests/multistage_fixture.py`, `tests/test_multistage_cases.py`

**Interfaces:**
- Produces:
  - `STAGES = 6`, `CROSS_CUTTING = 4`, `SELF_CONTAINED = 1`
  - `FORBIDDEN = ('doc', 'docs', 'documentation', 'reference.md', 'changelog', 'test', 'tests', 'claude.md')`
  - `load(root: Path) -> dict`, which raises `ValueError` naming the first rule broken
  - `tree(case: dict, stage: int, folder: Path, variant: str = 'reference') -> Path`, where `variant` is one of `'reference' | 'dependent-missed' | 'docs-forgotten' | 'no-op'`
  - `tests/multistage_fixture.py::make_case(root: Path) -> Path`, a valid tiny six-stage case

**Case directory, fixed here.** `<id>/case.json`, `start/`, `stages/<n>/reference.diff` (n = 1..6, each against the previous reference tree), `stages/<n>/dependent-missed.diff` (cross-cutting stages, against the reference tree at stage n), `oracle/groups/<group>.py` and `oracle/facts.json`.

`case.json` holds:
- `id`, `pythonpath` (for example `"src"`), `test_dir` (`"tests"`), `protected`, `docs` (`"docs/reference.md"`), `changelog` (`"CHANGELOG.md"`);
- `stages`: a list of six entries, each `{"request", "kind", "bugfix", "dependent_missed_fails"}`;
- `groups`: a list of `{"id", "since", "until"}`.

`facts.json` holds `{"0": {key: value}, ..., "6": {...}}`, each a complete cumulative map.

**What `load` rejects:**
- the wrong number of stages;
- fewer than 4 cross-cutting or fewer than 1 self-contained stages;
- a request containing a `FORBIDDEN` word as a whole word, case-insensitive;
- a missing group file;
- `since` or `until` outside 0..6, or `since > until`;
- not exactly 2 groups with `since` 0, or not exactly 2 groups introduced per stage;
- a cross-cutting stage without `dependent-missed.diff`, or with an empty `dependent_missed_fails`, or naming a group whose window does not satisfy `since < n <= until`;
- missing fact stages, or `facts[n] == facts[n-1]` for any n.

**What `tree` builds for each variant:**
- `reference`: copy `start/`, `git init` and commit, then apply the reference diffs 1..stage with `eval.bundle.apply_patch`.
- `dependent-missed`: the reference tree, then the stage's `dependent-missed.diff`.
- `docs-forgotten`: the reference tree at the stage, with the docs file taken from the stage − 1 tree.
- `no-op`: the stage − 1 reference tree.

`eval/multistage_cases/conftest.py` is `collect_ignore_glob = ["*"]`, so the repository's `python -m pytest` never collects case projects.

**The fixture `make_case`.** Under `src/pkg/` it writes:
- `core.py`, with `DEFAULT = 0` and `def scaled_v0(x): return x * DEFAULT`;
- `use.py`, with `def apply(x): return core.scaled_v0(x)`;
- `_generated.py`.

Stage n sets `DEFAULT = n` and its docs row ``| `default` | `n` |``. On stages 1 to 4 (cross-cutting), stage n also renames `scaled_v{n-1}` to `scaled_v{n}` and updates `use.py`. That stage's dependent-missed diff restores `use.py`'s old call, so the base group `use` fails. Stages 5 and 6 are self-contained: they add a function `extra_v{n}` nothing calls, and a documented fact for it. Stage 6 also removes stage 5's fact. Stage 5 is the bug-fix stage, and its reference diff adds `tests/test_extra.py`, which fails if `extra_v5` is reverted. The two groups each stage introduces are generated `def test_...` files that assert the stage's behaviour. Diffs are produced with `git diff --binary` between trees the fixture writes.

- [ ] **Step 1: Write failing tests** in `tests/test_multistage_cases.py`:
  - `test_the_fixture_case_loads`: `load(make_case(tmp_path))['id'] == 'fixture'`.
  - `test_each_rule_is_refused`, parametrized over: a request containing `"Update the docs"`; stage 2's kind set to self-contained (leaving 3 cross-cutting); a removed group file; `facts["3"] = facts["2"]`; a cross-cutting stage with no dependent-missed diff. Each must raise `ValueError`.
  - `test_trees_differ_by_variant`: at stage 2 the reference tree's `core.py` contains `DEFAULT = 2`; `no-op` contains `DEFAULT = 1`; `docs-forgotten` has `DEFAULT = 2` with the stage-1 docs row; `dependent-missed`'s `use.py` calls `scaled_v1`.
  - `test_case_projects_are_never_collected`: `python -m pytest --collect-only -q eval/multistage_cases` reports no tests, after copying the fixture's start tree into a temporary `eval/multistage_cases/_probe/`, which is removed in `finally`.
- [ ] **Step 2:** Run `python -m pytest tests/test_multistage_cases.py -q`. Expected: FAIL, because the module is missing.
- [ ] **Step 3:** Implement `eval/multistage_cases.py`, the conftest and the fixture.
- [ ] **Step 4:** Run the tests under `python` and `py -3.11`. Expected: PASS.
- [ ] **Step 5:** Mutation check: each refusal rule removed in turn must fail its parametrized case, and each variant swapped must fail the tree test. Then commit and push: `eval: multi-stage v2 case format and stage trees`.

### Task 2: Oracles — behaviour groups, docs facts, rules

**Files:**
- Create: `eval/multistage_oracles.py`, `tests/test_multistage_oracles.py`

**Interfaces:**
- Consumes: `load`, `tree` and `make_case` from Task 1.
- Produces:
  - `groups(case: dict, root: Path, stage: int, tree: Path, *, python: str = sys.executable, seconds: float = 120) -> dict[str, str]`, where each value is `'passed' | 'failed' | 'timeout'` and only groups with `since <= stage <= until` are run;
  - `facts(text: str) -> dict[str, str]`;
  - `stale(case: dict, root: Path, stage: int, tree: Path) -> list[str]` (sorted keys);
  - `rules(case: dict, stage: int, before: Path, after: Path, *, python: str = sys.executable) -> dict` with keys `changelog: int`, `protected: bool`, `test_with_fix: bool | None`;
  - `regressions(case: dict, stage: int, previous: dict[str, str], current: dict[str, str]) -> list[str]`.

**`groups`:**
- Each group file is copied into a fresh private temporary folder and run there with `python -m pytest -q -p no:cacheprovider --rootdir <private> <file>`.
- `PYTHONPATH` is `<tree>/<pythonpath>`, and the working directory is the private folder.
- One subprocess per group, through `core.process.run` with `timeout=seconds`.
- A timeout gives `'timeout'`, exit 0 gives `'passed'`, anything else gives `'failed'`.

**`facts`:** parses every markdown table row whose first two cells are backticked, `` | `key` | `value` | ``, ignoring `\r`.

**`stale`:** a key in `facts[stage]` whose documented value differs or is missing, plus any key removed by the stage that is still documented. A key is removed by the stage when it is in the union of `facts[0..stage-1]` but not in `facts[stage]`.

**`rules`:**
- `changelog` is the number of `- ` bullet lines under `## Unreleased` in `after`, minus the number in `before`, with a floor of 0. A missing section counts 0.
- `protected` compares the protected file's bytes between `before` and `after`.
- `test_with_fix` is `None` unless the stage is a bug fix. For a bug fix it is `not vacuity(...)['vacuous']`, where `vacuity` is called with `base=before`, the patch `before → after` (built by committing `before` in a scratch git repo, copying `after` over it and calling `export_patch`), the stage's `pythonpath` as `PYTHONPATH` and `test_dir` from the case. A `None` verdict stays `None`.

**`regressions`:** groups that were `'passed'` in `previous` and are not `'passed'` in `current`, among groups with `since < stage <= until`.

- [ ] **Step 1: Write failing tests** in `tests/test_multistage_oracles.py`, all against `make_case`:
  - `test_reference_tree_passes_its_groups`: every value is `'passed'` at stages 0 to 6.
  - `test_a_missed_dependent_fails_an_earlier_group`: the stage-2 dependent-missed tree gives `groups(...)['use'] == 'failed'` and `regressions(...) == ['use']`.
  - `test_a_conftest_in_the_tree_does_not_pass_a_failing_group` (Review Focus 1): the dependent-missed tree plus `conftest.py`, with `def pytest_collection_modifyitems(items): items.clear()`, still gives `'failed'`.
  - `test_a_hanging_candidate_times_out` (Review Focus 3): `use.py` gets `while True: pass` at import, and with `seconds=5` the group is `'timeout'`.
  - `test_stale_facts`:
    - the reference tree gives `[]`;
    - docs-forgotten at stage 3 gives `['default']`;
    - a missing docs file gives every key at that stage (Review Focus 2);
    - a CRLF copy of the docs gives `[]` (Review Focus 4);
    - a key removed in the fixture's stage 6 that is still documented counts.
  - `test_rules`:
    - one added bullet gives `changelog == 1`;
    - a missing `## Unreleased` gives `0` (Review Focus 5);
    - an edited protected file gives `protected is False`;
    - `test_with_fix` is `None` on a non-bug-fix stage;
    - `test_with_fix` is `True` on a bug-fix stage whose diff adds a test that fails when the source change is reverted, and `False` when it adds no test.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement `eval/multistage_oracles.py`.
- [ ] **Step 4:** Run the tests under 3.13 and 3.11. Expected: PASS.
- [ ] **Step 5:** Mutation check: run groups inside the tree instead of the private folder (the conftest test must fail), drop the removed-key clause, count all bullets instead of the Unreleased section, treat a timeout as a pass, and drop the `since < stage` filter. Each must fail a test. Then commit and push: `eval: multi-stage v2 oracles for behaviour, docs facts and rules`.

### Task 3: Rehearsal with four variants

**Files:**
- Create: `eval/multistage_rehearse.py`, `tests/test_multistage_rehearse.py`

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces:
  - `rehearse(root: Path, work: Path) -> dict`, returning `{'id', 'usable': bool, 'stages': [{'stage', 'checks': {name: bool}, 'detail': {...}}]}`;
  - the CLI `python -m eval.multistage_rehearse --cases eval/multistage_cases [--case <id>] --out <json>`.

**Checks for stage n (1..6), all of which must hold for `usable`:**
- `reference_groups`: every active group passes.
- `reference_docs`: `stale == []`.
- `reference_rules`: `changelog >= 1`, `protected`, and `test_with_fix is True` when the stage is a bug fix.
- `dependent_missed` (cross-cutting stages): the set of failing groups with `since < n` equals `dependent_missed_fails`.
- `docs_forgotten`: `stale` equals the keys whose values differ between `facts[n-1]` and `facts[n]`, plus the keys removed at n.
- `no_op`: every group with `since == n` fails.

Stage 0 checks that the start tree passes the base groups and has no stale facts.

- [ ] **Step 1: Write failing tests:**
  - `test_the_fixture_rehearses_usable`.
  - `test_a_broken_case_is_unusable`, parametrized: a reference stage that leaves the docs row unchanged makes `reference_docs` false; a dependent-missed diff that changes nothing makes `dependent_missed` false; a stage whose new groups also pass on the previous tree makes `no_op` false.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement the module and the CLI. The CLI writes the JSON with `eval.preservation._write` and exits 1 if any case is unusable.
- [ ] **Step 4:** Run under 3.13 and 3.11. Expected: PASS.
- [ ] **Step 5:** Mutation check each of the six checks: forcing it to `True` must fail the matching parametrized case. Then commit and push: `eval: multi-stage v2 rehearsal, reference and three broken variants`.

### Task 4: Power simulation

**Files:**
- Create: `eval/multistage_power.py`, `tests/test_multistage_power.py`

**Interfaces:**
- Produces:
  - `exact_signed_rank(differences: list[float]) -> float`: two-sided, exact over all sign flips, average ranks for ties, zeros dropped;
  - `power(*, cases: int, replicates: int, rate: float, ratio: float, heterogeneity: float, simulations: int, seed: int, alpha: float = 0.025) -> dict`, returning `{'rejection_rate', 'cases', 'replicates', 'conversations'}`;
  - the CLI, which prints a grid as JSON.

**Model.**
- Each case draws `log(rate_c) ~ N(log(rate), heterogeneity)`.
- Each arm-A conversation's count is `Poisson(rate_c)`, and arm B's is `Poisson(rate_c * ratio)`. Use Knuth's sampler.
- A case's difference is mean(A) − mean(B) over replicates.
- Reject when `exact_signed_rank <= alpha`. 0.025 is Holm's first step for two co-primary outcomes, so this is conservative for either one.

**Grid defaults:** cases 8 and 12; replicates 2 and 3; rate 0.1, 0.25, 0.5 and 1.0; ratio 1.0, 0.5 and 0.3; heterogeneity 0.5 and 1.0; 2,000 simulations.

- [ ] **Step 1: Write failing tests:**
  - `exact_signed_rank([1, 2, 3, 4, 5, 6, 7, 8]) == 2 / 256`, `exact_signed_rank([]) == 1.0` and `exact_signed_rank([1, -1]) == 1.0`.
  - A null check: `power(cases=8, replicates=3, rate=0.5, ratio=1.0, heterogeneity=0.5, simulations=400, seed=1)['rejection_rate'] <= 0.05`.
  - A strong-effect check: `rate=2.0, ratio=0.1` gives a rejection rate `>= 0.8`.
  - Invalid arguments (`cases=0`, `ratio=0`, `rate=-1`) raise `ValueError`.
- [ ] **Step 2:** Run. Expected: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Run under 3.13 and 3.11. Expected: PASS. Then run the CLI and save `results/multistage/power.json`.
- [ ] **Step 5:** Mutation check: one-sided p, ties not averaged, B drawn at the same rate as A. Then commit and push: `eval: multi-stage v2 power simulation`.

### Task 5: Independent case authoring

**Files:**
- Create: `eval/multistage_cases/AUTHORING.md`, and `eval/multistage_cases/<id>/` for eight ids.

**Interfaces:**
- Consumes: the case format and `python -m eval.multistage_rehearse --case <id>`.

**The brief, `AUTHORING.md`.** It contains:
- the case format from Task 1;
- the case rules from the spec's §Cases, with the `CLAUDE.md` rules verbatim;
- the forbidden request words;
- the instruction that cross-cutting stages change a shared helper, data format, default or signature that existing code depends on, without naming the dependents;
- that self-contained stages have no dependents;
- that groups check behaviour, never spelling;
- that projects are 600–1,500 lines across several modules, standard library only;
- that the work is done when the case rehearses usable.

It says nothing about ElevenPowers, its features or the arms. Authors may read only `AUTHORING.md`, `eval/multistage_cases.py`, `eval/multistage_oracles.py` and `eval/multistage_rehearse.py`.

**Domains, so the cases vary.** Two of them persist a data format.
1. `stockroom`: an inventory CLI with a JSON store (persisted).
2. `throttle`: a rate-limiting library.
3. `marklite`: a markdown-subset renderer.
4. `cronish`: a schedule-expression parser and planner.
5. `layered-config`: a config loader with file, env and default layers.
6. `tabulate-report`: CSV-to-report aggregation.
7. `tinyroute`: a URL router with path parameters.
8. `ledgerbook`: a double-entry ledger with a persisted journal (persisted).

- [ ] **Step 1:** Write `AUTHORING.md`.
- [ ] **Step 2:** Dispatch eight fresh agents in parallel, one per id, each given only the brief and its domain. Each returns when `python -m eval.multistage_rehearse --cases eval/multistage_cases --case <id> --out <scratch>` exits 0.
- [ ] **Step 3:** Run the rehearsal over all eight. Expected: every case usable, and `python -m pytest -q` still collects nothing under `eval/multistage_cases`.
- [ ] **Step 4:** Commit and push: `eval: eight authored multi-stage v2 cases`.

### Task 6: Independent review, then freeze

**Files:**
- Create: `results/multistage/review.json`, `results/multistage/rehearsal.json`, `results/multistage/manifest.json`, `results/multistage/README.md`.
- Modify: `PLAN.md`, `docs/status.md`, `journey/` (a new entry), `architecture/index.html` and `graph-data.js`.

**Interfaces:**
- Consumes: Tasks 1–5.

**The review.** Two fresh reviewers, each taking four cases. They check:
- that no request names a dependent or mentions docs, tests or the changelog;
- that each cross-cutting stage really has a dependent and each self-contained one has none;
- that groups test behaviour, not spelling;
- that the facts match what the reference docs state.

Findings go to `review.json`. Each finding is fixed by the case's author agent or by me, then re-rehearsed. A finding not fixed is recorded with its reason.

**The freeze.**
- `manifest.json` records the sha256 of every file in every case directory, the four module hashes, the analysis choice and the pilot cases.
- The pilot cases are the two ids with the smallest `sha256("multistage-v2-pilot\0" + id)`.
- The freeze is pushed before any paid step.

- [ ] **Step 1:** Dispatch the two reviewers, collect `review.json`, apply fixes and re-run the rehearsal until all eight cases are usable.
- [ ] **Step 2:** Write the manifest and the README. The README states that the cases, the variants, the power grid and the pilot choice are fixed, and that no model has run.
- [ ] **Step 3:** Run the full suite `python -m pytest -q` (no repo-local basetemp) and `python architecture/check.py --render`, and update PLAN, status and journey. Expected: green, and OK.
- [ ] **Step 4:** Commit, push, and read `gh run list` for the push.

**Stop here.** The one-cent qualification, the pilot and the full run each wait for the user's go.
