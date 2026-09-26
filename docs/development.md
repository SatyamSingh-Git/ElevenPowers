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

