# TestMiner Slice 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** For named Python functions, report whether the project's tests
reach them and whether emptying each one fails any test that reached it.

**Architecture:** One analysis in a private copy of the project. A baseline
run of the project's own test command, under coverage.py with
`dynamic_context = test_function`, gives the tests that reached each
function. Each function reached by a test is then replaced by `return None`
in a fresh trial copy, and only the tests that reached it are run. Isolation,
budgets and output parsing come from `core/strength`.

**Tech Stack:** Python 3.11+ standard library. coverage.py 7.x is optional
and must be importable in the project's own test interpreter.

**Spec:** `docs/superpowers/specs/2026-11-13-testminer-design.md`. Its
"Decided after the builder check" section governs.

## Global Constraints

- Report only: no verdict change, nothing sent to the agent, and the
  person's tree is never written except `.elevenpowers/testminer.json`.
- Runtime stays standard library only. coverage.py is never installed.
- Verdicts are exactly `not reached`, `reached, not checked`, `checked` and
  `unknown`. Every `unknown` carries a reason.
- Defaults: `--seconds 60`, `--limit 20`, `--test-seconds 15`.
- One of `--base`, `--function` or `--path` is required.
- Python 3.11 floor. Test the new files with `py -3.11`.
- Never run the full suite locally (user rule, 2026-11-12). Run only the
  files this plan names.

## Review Focus

1. A function reached only from a fixture, `setUp` or import (context `""`)
   must be `unknown`, not `not reached`. Pinned in Task 2.
2. A pytest node id that does not resolve gives exit 4 or 5, and must not be
   read as `checked`. Pinned in Task 3.
3. A project without coverage.py in its test interpreter gives `unknown`
   everywhere, with the install line. Pinned in Task 3.
4. A one-line `def f(): return 1`, a docstring-only body, a generator, an
   `async def` and `__init__` give `unknown`, never a mutant. Pinned in Task 1.
5. Methods with the same name in two classes stay distinct (`A.size` and
   `B.size`). Pinned in Task 1.

---

### Task 1: Function spans

**Files:**
- Create: `core/testminer/__init__.py` (a one-line docstring)
- Create: `core/testminer/functions.py`
- Test: `tests/test_testminer.py`

**Interfaces:**
- Produces: `@dataclass(frozen=True) class Function: name: str; first: int;
  last: int; body: int; refused: str`. Here `name` is the qualified name
  (`Box.size`); `first`/`last` cover the whole body; `body` is the first
  replaceable line (after a docstring); `refused` is `''` or the reason it
  cannot be emptied.
- Produces: `functions(source: str) -> list[Function]`. Top-level functions
  and methods of top-level classes only, in line order.

- [ ] **Step 1: Write the failing tests**

```python
def test_functions_are_qualified_and_spans_cover_the_body():
    found = {f.name: f for f in functions(SOURCE)}
    assert set(found) == {'add', 'log', 'A.size', 'B.size', 'gen', 'run', 'Box.__init__', 'one', 'doc'}
    assert (found['add'].first, found['add'].last) == (2, 3)

def test_bodies_that_cannot_be_emptied_say_why():
    found = {f.name: f.refused for f in functions(SOURCE)}
    assert found['gen'] == 'generator' and found['run'] == 'async function'
    assert found['Box.__init__'] == '__init__' and found['one'] == 'one-line function'
    assert found['doc'] == 'no statement besides a docstring'
    assert found['add'] == ''
```

`SOURCE` is a module literal in the test file that has:
- `add`, two lines;
- `log`, with a docstring followed by statements;
- classes `A` and `B`, each with `size`;
- `gen`, which uses `yield`;
- `async def run`;
- `Box.__init__`;
- `def one(): return 1`;
- `doc`, whose body is only a docstring;
- a nested `def inner` inside `add`, which must not appear.

- [ ] **Step 2: Run it and see it fail**

Run: `.venv/Scripts/python.exe -m pytest -q tests/test_testminer.py`
Expected: an ImportError for `core.testminer.functions`.

- [ ] **Step 3: Implement `functions()` with `ast.parse`.** Iterate only
  `module.body` and top-level class bodies. A generator is a function whose
  own body contains `Yield`/`YieldFrom` outside nested functions.

- [ ] **Step 4: Run it and see it pass.** Run the same command, then
  `py -3.11 -m pytest -q tests/test_testminer.py`.

- [ ] **Step 5: Commit**: `testminer: function spans with qualified names`.

### Task 2: Reached by which tests

**Files:**
- Create: `core/testminer/coverage_run.py`
- Test: `tests/test_testminer.py`

**Interfaces:**
- Consumes: `Function` (Task 1).
- Produces: `wrap(command: str, rcfile: Path) -> list[str]`. The configured
  command becomes an argv list: `['python', '-m', 'coverage', 'run',
  '--rcfile', str(rcfile), '-m', RUNNER, *options]`. It raises `ValueError`
  naming `--command` unless the command is `pytest …`, `python -m pytest …`
  or `python -m unittest …`, and on `-n` or `-p xdist`.
- Produces: `reached(report: dict, path: str, fn: Function) ->
  tuple[set[str], bool]`. It returns the test contexts on lines
  `fn.first..fn.last`, and whether any of those lines ran only under `""`.
- Produces: `RCFILE = '[run]\ndynamic_context = test_function\n'`. The
  caller appends `data_file` and `source`.

- [ ] **Step 1: Write the failing tests**

```python
def test_wrap_keeps_options_and_refuses_other_runners():
    assert wrap('python -m pytest -q tests', Path('rc'))[-4:] == ['-m', 'pytest', '-q', 'tests']
    assert wrap('pytest -x', Path('rc'))[-3:] == ['-m', 'pytest', '-x']
    assert wrap('python -m unittest discover', Path('rc'))[-3:] == ['-m', 'unittest', 'discover']
    for bad in ('tox -e py', 'npm test', 'python -m pytest -n auto', 'pytest -p xdist'):
        with pytest.raises(ValueError, match='--command'):
            wrap(bad, Path('rc'))

def test_reached_reads_contexts_and_flags_fixture_only_lines():
    report = {'files': {'svc.py': {'contexts': {'2': ['tests.test_svc.T.test_add'], '6': [''], '7': ['']}}}}
    add = Function('add', 2, 2, 2, ''); log = Function('log', 6, 7, 6, '')
    assert reached(report, 'svc.py', add) == ({'tests.test_svc.T.test_add'}, False)
    assert reached(report, 'svc.py', log) == (set(), True)
```

The report shape above is the real one, from coverage.py 7.10.7 run on
2026-11-13 (`files[path]['contexts']` maps line strings to context lists).

- [ ] **Step 2: Run it and see it fail.**
- [ ] **Step 3: Implement both functions.** Use `shlex.split`, the
  platform's own `posix` setting, and the same `.exe` handling as
  `core/test_command.reduce`.
- [ ] **Step 4: Run it and see it pass**, on 3.13 and 3.11.
- [ ] **Step 5: Commit**: `testminer: wrap the test command in coverage and read which tests reached a function`.

### Task 3: The analysis and the CLI

**Files:**
- Create: `core/testminer/runner.py`
- Create: `plugin/bin/ep_testminer.py`
- Test: `tests/test_testminer.py` (fixture service, end to end)

**Interfaces:**
- Consumes: Tasks 1 and 2. Also `core.strength`:
  - `isolation.snapshot(root, Settings(), deadline)` and
    `isolation.trial(snapshot, Settings(), deadline)`;
  - `execution.execute(argv, root, Budget(deadline, maximum), seconds,
    shell=False, original=root)`;
  - `baseline.outcomes(command, execution, root)`, which returns
    `(passed, failed, errors)`;
  - `strength.settings.Settings`;
  - `strength.scope.select(root, sha, deadline)` for `--base`.
- Produces: `mine(root: Path, *, base: str = '', names: tuple = (), paths:
  tuple = (), command: str = '', seconds: float = 60, limit: int = 20,
  test_seconds: float = 15) -> dict`. It returns `{'schema': 1, 'command':
  str, 'issues': [str], 'functions': [{'path', 'name', 'line', 'verdict',
  'reason', 'tests'}]}` and saves it to `.elevenpowers/testminer.json`.
- Produces: CLI `ep_testminer.py --project PATH (--base SHA | --function
  FILE::NAME | --path FILE)... [--command CMD] [--seconds] [--limit]
  [--test-seconds] [--json]`. Exit 0 when it ran, 2 on refused input.

Rules, from the spec:
- **No function selected:** a `ValueError` naming the three flags.
- **Coverage missing:** run `python -c "import coverage; print(coverage.version_info[0])"`
  in the copy. Anything other than `7` or higher makes every function
  `unknown`, with "coverage.py 7 is not importable in the test environment;
  install it there: python -m pip install coverage".
- **Baseline:** the run must be complete and exit 0, and `outcomes` must
  show `passed > 0` with no failures. Otherwise every function is `unknown`
  with the reason (`isolation_error` keeps the guard's text). If the baseline
  recorded no non-empty context at all, every function is `unknown`.
- **Per function:**
  - a refused body gives `unknown` with `fn.refused`;
  - no tests, and no `""`-only lines, gives `not reached`;
  - no tests, but `""`-only lines, gives `unknown`, "reached outside any test
    (fixture, setUp or import)";
  - otherwise a mutant: in a fresh trial copy, lines `fn.body..fn.last`
    become one `return None` at the body's indentation. Then the runner is
    run on the reaching tests:
    - unittest: the dotted names as given;
    - pytest: `FILE::Class::name`, when the dotted module resolves to
      exactly one `.py` file;
    - otherwise: the whole wrapped command, without coverage.
- **Mutant outcome:**
  - exit 0 with `passed > 0` gives `reached, not checked`, with `tests`
    listing them;
  - `timed_out`, or `failed > 0`, or `errors` gives `checked`;
  - anything else, including pytest exit 4/5, gives `unknown`, "the selected
    tests did not run".
- **Over `limit`,** or once the budget is spent: `unknown`, "budget".

- [ ] **Step 1: Write the failing end-to-end tests.** They use a fixture
  service (a `tmp_path` Git repository: `svc.py` and `tests/test_svc.py`,
  run under the `.venv` interpreter, which has coverage 7.10.7).

```python
def test_fixture_service_gets_each_verdict():   # card acceptance 1
    result = mine(root, paths=('svc.py',), command=f'"{sys.executable}" -m pytest -q')
    verdicts = {f['name']: f['verdict'] for f in result['functions']}
    assert verdicts == {'add': 'checked', 'log': 'reached, not checked', 'never': 'not reached',
                        'setup_only': 'unknown', 'one': 'unknown'}
    assert (root / 'svc.py').read_text() == ORIGINAL

def test_verdicts_flip_both_ways():
    # Add an assertion on log: `reached, not checked` becomes `checked`.
    # Delete test_add: `checked` becomes `not reached`.
    ...

def test_red_baseline_missing_coverage_and_no_selection_are_unknown_or_refused():   # card acceptance 2
    # A failing test: every verdict is unknown, naming the baseline.
    # command=f'"{PYTHON_WITHOUT_COVERAGE}" -m pytest' (py -3.11, checked to lack coverage
    #   at test time, skipped otherwise): every verdict is unknown, naming the install line.
    # mine(root) with nothing selected raises ValueError naming --base, --function and --path.

def test_unmapped_pytest_selection_is_not_read_as_checked(monkeypatch):
    # Force the node-id mapping to a node that does not exist. Exit 4/5 must
    # give `unknown`, "the selected tests did not run".

def test_cli_prints_verdicts_and_json(tmp_path): ...
```

  `svc.py` has:
  - `add`: asserted by a test;
  - `log`: called by a test that makes no assertion;
  - `never`;
  - `setup_only`: called only from a pytest fixture;
  - `def one(): return 1`.

- [ ] **Step 2: Run it and see it fail.**
- [ ] **Step 3: Implement `mine()` and the CLI.** Write the rcfile and the
  data file in a temporary folder outside the copy. Use `source = <copy>`,
  then `python -m coverage json --rcfile RC --show-contexts -o OUT`.
- [ ] **Step 4: Run it and see it pass**, on 3.13 and on 3.11.
- [ ] **Step 5: Mutation check.** Drop each verdict rule in turn, the `""`
  rule, the exit-4/5 rule, the coverage-missing rule and the
  restore-the-original check. Every mutant must be killed.
- [ ] **Step 6: Commit and push**: `testminer: first slice - reached, checked, or unknown, per function`.

### Task 4: Real projects, docs, map

**Files:**
- Create: `results/testminer/rehearse.py`, `results/testminer/README.md`
- Modify:
  - `the-guide/commands.md` (an `ep_testminer` section);
  - `README.md` (one line under what it can do);
  - `docs/status.md`;
  - `journey/104-…md` and `journey/README.md`;
  - `architecture/index.html`: a `testminer` node; the card's status
    becomes "First slice built"; `meta.updated` and `changelog`;
  - `docs/superpowers/specs/2026-11-13-testminer-design.md` (record what
    the real runs showed).

- [ ] **Step 1:** Run `mine` with `--path` on one source file from each of
  two held-out projects, in their venvs. Use cachetools (`src/cachetools/keys.py`)
  and more-itertools (`more_itertools/recipes.py`), with `--limit 10`. Check
  three verdicts by hand per project, by reading the tests. Record every
  `unknown` and its reason.
- [ ] **Step 2:** Write the docs and the map, then run
  `python architecture/check.py --render`. Edit the map only through the
  Edit tool.
- [ ] **Step 3:** Commit, push, and watch hosted CI.
