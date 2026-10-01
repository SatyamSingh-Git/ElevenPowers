# Local development and verification

Use Python 3.11 or newer and Git. Run these commands from the repository root.
The runtime uses the standard library; pytest is a development dependency.
Local checks and CI install the same pinned pytest version.

## Windows PowerShell

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"
python -m pytest -q
python -m eval.validate
python plugin/bin/ep_doctor.py --host
```

Putting the virtual environment first on PATH also makes subprocesses that invoke
`python` use it. Activation is not required, so PowerShell execution policy does
not need changing. In a new terminal, set PATH again before running checks.

## Linux and macOS

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
export PATH="$PWD/.venv/bin:$PATH"
python -m pytest -q
python -m eval.validate
python plugin/bin/ep_doctor.py --host
```

Generalized onboarding/activation/edit acceptance can be checked with
`python -m pytest tests/test_onboarding.py tests/test_native_edits.py tests/test_project_readiness.py -q`.
These cover four unrelated manifest types, no-Git/dirty files, interrupted and
missing events, bounded state and concurrent launcher isolation. Doctor replay
is explicitly marked and cannot establish project activation.

Tests create temporary Git repositories. Git must have a user name and email
configured, as it does in CI. No paid agent runs are part of these commands.

If a restricted account cannot access a previous user's pytest temporary or cache
directory, select fresh directories inside the ignored virtual environment:

```sh
python -m pytest -q --basetemp=.venv/pytest-temp -o cache_dir=.venv/pytest-cache
```

Use `--basetemp` only for disposable test files: pytest clears that directory on
each run. Missing pytest or tests that cannot collect indicate an environment
failure, not a successful validation. Fix setup before interpreting grader results.

## Recompute saved experiment metrics

These commands read committed JSON records, need no corpus checkout or model
credentials, and make no paid agent calls:

```sh
python results/b8-feedback/analyse.py b8
python results/b9-gate-tests/analyse.py b9
python results/b9-gate-tests/analyse.py raters
```

The default input directory is resolved relative to the script, independently of
the current working directory. Use `--results-root /path/to/results` for another
copy of the saved records. Missing or invalid inputs return a nonzero exit status.
For B8, a clean checkout uses `results/b8-feedback/analysis-records.json`, a 36-record projection containing only the metrics and controls used by analysis. Raw local run records take precedence when present. Clean-input tests exclude those ignored runs, and both paths were checked to produce identical output.

These commands recompute metrics, not the original experiments: the historical
probe/driver scripts still require their corpus, repositories and execution setup.

## Focused delivery checks

For repository selection and automatic setup, run the tests covering the changed behavior before the broader integration check:

```sh
python -m pytest tests/test_repository_scan.py tests/test_declared_commands.py tests/test_automatic_commands.py tests/test_automatic_startup.py tests/test_wiring.py -q
```

Use the full regression suite at the integration boundary or when a change affects shared behavior. Repeat broader checks when a failure or additional change warrants it. Documentation-only updates need link, content and relevant architecture checks; they do not require an unrelated full runtime sweep.

Architecture rendering needs development-only Playwright and its browser:

```sh
python -m pip install playwright
python -m playwright install chromium --only-shell
python architecture/check.py --render
```

Confirm the output says all four tabs draw; a skipped render is not a rendered check. These tools are not runtime dependencies. Use [the validation index](validation/README.md) for dated outcomes and [current status](status.md) for remaining integration work.

## Durable runner checks

```sh
python -m pytest tests/test_jobs.py tests/test_process.py tests/test_verification_runner.py tests/test_shared_budget.py tests/test_verification_progress.py tests/test_runner_launcher.py -q
```

These include real command descendants and a shipped-launcher process killed between checks, followed by recovery that reuses the first completed result. Windows containment is exercised locally; the existing CI matrix also targets Ubuntu and Python 3.11/3.13. A configured CI matrix is not evidence that a particular remote run passed—check the run result separately.

The runtime remains standard-library-only. The process runner adapts the repository's existing `eval/live.py` Windows Job approach and uses POSIX process groups elsewhere. It adds bounded disk-spooled diagnostics and cleanup on normal completion as well as interruption. See [durable-runner validation](validation/2026-09-29-durable-runner.md) for executed checks and platform limits.

## Native host adapters

`core/hosts/` normalizes native events, collects shared-engine responses, generates wiring and provides setup/package/doctor helpers. Native payload examples in tests are schema fixtures, not live captures. Run the `tests/test_host_*.py` tests with Claude hook regressions after changing shared transport.

All four new platforms use the same scan, command discovery, ledger and runner.
Completed tool identities are committed atomically with ledger observations;
failed persistence remains retryable. Continuation hashes live separately in
`.elevenpowers/hosts.json`. Both histories are bounded. Windows project commands
encode the full PowerShell invocation; Copilot uses direct argument arrays.
Exercise actual launcher paths with shell characters, not only project cwd.

For release readiness, retain the host version and a real native event capture.
Contract fixtures cannot replace it. See [the delivery record](validation/2026-09-29-platforms.md)
for the independent review, corrections and remaining Linux diagnostic question.
