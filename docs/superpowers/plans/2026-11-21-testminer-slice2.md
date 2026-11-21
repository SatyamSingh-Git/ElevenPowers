# TestMiner Slice 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Select functions from a sanitized record of a real run, and try a typed set of extreme values per function, with a `partly checked` verdict.

**Architecture:** `functions.py` gains the value set per function; `runner.py` runs one mutant per value and folds the outcomes into a verdict; a new `observe.py` records a run in the person's tree and turns the record into targets; `ep_testminer.py` gains `record` and `--observed`.

**Tech Stack:** Python 3.11+, coverage.py 7 (tests: 7.10.7), pytest.

**Spec:** `docs/superpowers/specs/2026-11-21-testminer-slice2-design.md` (and slice 1's, which it extends).

## Global Constraints

- Report only; the person's tree gets only `.elevenpowers/testminer.json` and `.elevenpowers/testminer-observed.json`.
- `record` stores the command's form and target and the argument count, never the arguments.
- `None` is always the first value tried.
- Outcomes follow slice 1: failure, error or timeout = detected; all passing = not detected.
- A partial set of values (budget) gives `unknown (budget)`, never a verdict.
- Defaults stay 60 s, 20 functions, 15 s per command; `Budget(deadline, limit * 9 + 3)`.
- Never run the full suite locally; targeted tests, `py -3.11` for changed tests, hosted CI after push.
- A new module goes on the architecture map in the same commit (`python architecture/check.py --render`).
- Every test is seen failing first; every new check is mutation-checked.

## Review Focus

1. A string annotation (`-> 'int'`) and `from __future__ import annotations`: both still give `int` values.
2. A recorded file deleted since recording: one issue line, no crash, no verdict.
3. A console script whose name is not importable under `-m` (e.g. `flask`'s `flask` *is*, `black` *is*; a script with a different module name is not): refused with the accepted forms.
4. Ctrl-C during `record`: the observation is still saved (simulated by the script raising `KeyboardInterrupt`); TestMiner itself does not die first.
5. A function chosen both explicitly and by a stale observation: examined normally.

---

### Task 1: The value set per function

**Files:**
- Modify: `core/testminer/functions.py`
- Test: `tests/test_testminer.py`

**Interfaces:**
- Produces: `Function.values: tuple[str, ...] = ('None',)` — Python source for each replacement, `None` first. `_values(node: ast.FunctionDef) -> tuple[str, ...]`.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize('code, values', [
    ('def f() -> bool:\n    x = 1\n    return x\n', ('None', 'True', 'False')),
    ('def f() -> int:\n    x = 1\n    return x\n', ('None', '0', '1')),
    ('def f() -> float:\n    x = 1\n    return x\n', ('None', '0.0', '1.0')),
    ('def f() -> str:\n    x = 1\n    return x\n', ('None', "''", "'A'")),
    ('def f() -> bytes:\n    x = 1\n    return x\n', ('None', "b''", "b'A'")),
    ('def f() -> list[int]:\n    x = 1\n    return x\n', ('None', '[]', '[None]')),
    ('def f() -> typing.Dict[str, int]:\n    x = 1\n    return x\n', ('None', '{}', '{None: None}')),
    ('def f() -> set:\n    x = 1\n    return x\n', ('None', 'set()', '{None}')),
    ('def f() -> tuple:\n    x = 1\n    return x\n', ('None', '()', '(None,)')),
    ('def f() -> Optional[int]:\n    x = 1\n    return x\n', ('None', '0', '1')),
    ('def f() -> int | None:\n    x = 1\n    return x\n', ('None', '0', '1')),
    ("def f() -> 'int':\n    x = 1\n    return x\n", ('None', '0', '1')),
    ('def f() -> Thing:\n    x = 1\n    return x\n', ('None',)),
    ('def f() -> None:\n    x = 1\n', ('None',)),
    ('def f():\n    x = 1\n    return x > 0\n', ('None', 'True', 'False')),
    ('def f(x):\n    if x:\n        return f"{x}"\n    return "no"\n', ('None', "''", "'A'")),
    ('def f(x):\n    if x:\n        return 1\n    return "no"\n', ('None',)),
    ('def f(x):\n    print(x)\n', ('None',)),
])
def test_values_follow_the_return_type(code, values):
    assert functions(code)[0].values == values
```

- [ ] **Step 2: Run** `python -m pytest tests/test_testminer.py -q -k values_follow` — Expected: FAIL, `Function` has no attribute `values`.
- [ ] **Step 3: Implement `_values`.** Annotation first: unwrap a string constant with `ast.parse(s, mode='eval').body`; `Optional[X]` and `X | None` unwrap to `X`; a subscript uses its value; an attribute uses its `attr`; map lowercased names (`list`/`List` …) through one table. Without an annotation: the kinds of every `return VALUE` in the function's own body (not nested defs, as `_yields` walks), one kind → its values; `Compare`/`not` → bool; `JoinedStr` → str; `List`/`Dict`/`Set`/`Tuple` displays → that type; constants by `type()`.
- [ ] **Step 4: Run** the same command — Expected: 18 passed; and `-k "functions_are or bodies_that or stub_bodies or getter"` still passes.
- [ ] **Step 5: Mutation-check** (remove the string-annotation unwrap; remove the Optional unwrap; drop the single-kind requirement) — each must fail a case. Commit `testminer: each function gets the extreme values its return type allows`.

### Task 2: One mutant per value, and `partly checked`

**Files:**
- Modify: `core/testminer/runner.py` (`_empty`, the probe loop, `give`, the `Budget`), `plugin/bin/ep_testminer.py` (text line)
- Test: `tests/test_testminer.py`

**Interfaces:**
- Consumes: `Function.values`.
- Produces: `_empty(path: Path, fn, value: str = 'None') -> None`; each result entry gains `values: [{'value': str, 'detected': bool}]` (empty list when no mutant ran); verdict `'partly checked'`.

- [ ] **Step 1: Write the failing tests**

```python
TYPED = '''\
def total(xs) -> int:
    return sum(xs) + 5
'''
TYPED_TESTS = '''\
from svc import total

def test_total():
    assert total([1]) is not None
'''

@needs_coverage
def test_a_value_only_checked_against_none_is_partly_checked(tmp_path):
    root = service(tmp_path, ...)  # svc.py = TYPED, test_svc.py = TYPED_TESTS
    result = mine(root, names=('svc.py::total',), command=pytest_command())
    item = result['functions'][0]
    assert item['verdict'] == 'partly checked'
    assert [v['value'] for v in item['values'] if not v['detected']] == ['0', '1']
    # forward control: an exact assertion detects every value
    (root / 'test_svc.py').write_text(TYPED_TESTS.replace('is not None', '== 6'))
    commit(root)
    assert mine(root, names=('svc.py::total',), command=pytest_command())['functions'][0]['verdict'] == 'checked'

@needs_coverage
def test_a_budget_between_two_values_gives_no_verdict(tmp_path, monkeypatch):
    # let the deadline pass after the first value's run
    ...
    assert item['verdict'] == 'unknown' and item['reason'] == 'budget'
```

(`service` and `pytest_command` exist; extend `service` to take the file texts if it does not already, and add a `commit` helper only if none exists.)
- CLI test: `ep_testminer.py` text output prints `svc.py:1 total: partly checked (returning 0 or 1 failed no test)`.

- [ ] **Step 2: Run** `-k "partly_checked or between_two_values"` — Expected: FAIL (verdict `checked`).
- [ ] **Step 3: Implement.** For each value, `trial` + `_empty(copy / path, fn, value)` + `execute` + `_verdict`. Fold: any value `unknown` not budget → that unknown; deadline passed before all values ran, or any value `unknown (budget)` → `unknown`, `budget`; none detected → `reached, not checked`; all → `checked`; else `partly checked`. Detected = `_verdict(...)[0] == 'checked'`. Budget attempts `limit * 9 + 3`.
- [ ] **Step 4: Run** the new tests and the whole file `python -m pytest tests/test_testminer.py -q` — Expected: all pass (existing `return None`-only fixtures keep their verdicts).
- [ ] **Step 5: Mutation-check** (fold `partly` into `checked`; drop the budget-partial rule). Commit `testminer: every extreme value runs, and mixed outcomes are partly checked`.

### Task 3: `record`

**Files:**
- Create: `core/testminer/observe.py`
- Modify: `plugin/bin/ep_testminer.py` (`record` subcommand when `sys.argv[1:2] == ['record']`), `architecture/index.html` (the testminer node names `observe.py`)
- Test: `tests/test_testminer.py`

**Interfaces:**
- Consumes: `coverage_run._words`, `coverage_run._beside`, `strength.isolation.copy_plan`'s file listing (or the same `git ls-files -z --cached --others --exclude-standard`).
- Produces: `OBSERVED = '.elevenpowers/testminer-observed.json'`; `record(root: Path, words: list[str]) -> tuple[int, dict | None]` (the command's exit status, the saved observation or None); observation `{'schema': 1, 'command': 'python -m pkg', 'arguments': 2, 'recorded': ISO-8601 UTC, 'files': {posix_path: {'sha256': str|None, 'lines': [int]}}}`.

- [ ] **Step 1: Write the failing tests**
  - `test_record_keeps_lines_and_hashes_of_tracked_files_only`: git fixture with `app.py` (calls `used()`, not `unused()`) and an untracked-but-ignored `venv/x.py` run by it; `record(root, ['python', 'app.py', '--token', 'SECRET'])` → exit 0; `files` has `app.py` only, its lines include `used`'s body and not `unused`'s, sha256 matches the file; `'SECRET' not in` the file text; `command == 'python app.py'`, `arguments == 2`; `git status --porcelain` differs from before only by `.elevenpowers/`.
  - `test_record_saves_when_the_program_is_interrupted`: `app.py` ends with `raise KeyboardInterrupt` → exit status nonzero, observation saved with lines.
  - `test_record_accepts_module_form_and_refuses_others`: `['python', '-m', 'pkg']` records; `['node', 'x.js']` and a console script with no importable module raise `ValueError` naming `python SCRIPT` and `python -m MODULE`.
  - `test_a_file_changed_during_the_run_has_no_hash`: `app.py` rewrites a tracked `other.py` that it imported → `files['other.py']['sha256'] is None`.
- [ ] **Step 2: Run** `-k record` — Expected: FAIL, no module `observe`.
- [ ] **Step 3: Implement** `record`: rcfile in a temp dir with `[run]` `data_file`, `source = ROOT`, `sigterm = true`; hash tracked `.py` files before; run `[python, '-m', 'coverage', 'run', '--rcfile', rc, *target]` with `cwd=root`, inheriting stdio, SIGINT ignored in the parent (`signal.signal(SIGINT, SIG_IGN)`, restored in `finally`); `coverage json` to the temp dir; keep files with lines that are in the tracked set and hash unchanged-after (else `sha256: None`); write `OBSERVED`. No data file → return `(status, None)`, write nothing.
- [ ] **Step 4: Run** `-k record` — Expected: pass. Add `observe.py` to the testminer node in `architecture/index.html`, bump `meta.updated`, changelog line, `python architecture/check.py --render` — Expected: OK.
- [ ] **Step 5: Mutation-check** (keep arguments; drop the tracked filter; hash only before). Commit `testminer: record a real run as line numbers and hashes`.

### Task 4: `--observed`

**Files:**
- Modify: `core/testminer/observe.py` (`observed`), `core/testminer/runner.py` (`mine(..., observed=False)`, `_selected`), `plugin/bin/ep_testminer.py` (`--observed`)
- Test: `tests/test_testminer.py`

**Interfaces:**
- Produces: `observed(root: Path) -> tuple[list[tuple[str, Function]], list[tuple[str, Function]], list[str]]` — (current functions with an observed body line, stale functions with an observed line, issues); raises `ValueError('no observation; run: ep_testminer.py record -- COMMAND')` when the file is absent. `STALE = 'changed since it was recorded; record again'`.

- [ ] **Step 1: Write the failing tests**
  - `test_observed_selects_what_ran_and_never_what_did_not`: after `record`, `mine(root, observed=True, ...)` examines `used` and not `unused`.
  - `test_an_edited_recorded_file_is_unknown_never_a_verdict`: edit `app.py` after recording → `used` is `unknown`, reason `STALE`; also named with `--function` → examined normally.
  - `test_a_deleted_recorded_file_is_one_issue`: delete it → one issue naming the path, no entry.
  - `test_observed_without_a_record_is_refused`.
- [ ] **Step 2: Run** `-k observed` — Expected: FAIL.
- [ ] **Step 3: Implement**; `mine` requires one of base/names/paths/observed; stale functions not otherwise selected get `unknown`/`STALE` and do not count toward `limit`.
- [ ] **Step 4: Run** `python -m pytest tests/test_testminer.py -q` and `py -3.11 -m pytest tests/test_testminer.py -q` — Expected: pass (coverage-needing tests skip on 3.11).
- [ ] **Step 5: Mutation-check** (treat stale as current; let stale override explicit). Commit `testminer: --observed examines what a recorded run executed`.

### Task 5: Rehearsal and records

**Files:**
- Modify: `results/testminer/rehearse.py`, `results/testminer/README.md`, `the-guide/commands.md`, `docs/status.md`, `README.md` item 3, `architecture/index.html` (card text)
- Create: `journey/105-*.md`

- [ ] **Step 1:** On one held-out project with coverage available, `record` one real entry point, then `--observed`; read five verdicts by hand, including whether `__getstate__` remains a false candidate (spec decision 2). Anonymise private names as before.
- [ ] **Step 2:** Document `record`, `--observed`, `partly checked` and the value table; journey entry with what the rehearsal showed and the qualifications.
- [ ] **Step 3:** `python architecture/check.py --render`; commit; push; read hosted CI.
