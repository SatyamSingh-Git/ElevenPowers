# Local development and verification

Use Python 3.11 or newer and Git. Run these commands from the repository root.
The runtime uses the standard library; pytest is a development dependency.
Local checks and CI install the same pinned pytest version.

Optional mutation acceptance also needs `requirements-strength.txt`, Node 22 and
`@stryker-mutator/instrumenter@9.5.1` under `.venv/strength-js`. CI installs them
in all four Windows/Linux, Python 3.11/3.13 cells. Local equivalents:

```sh
python -m pip install -r requirements-strength.txt
npm install --prefix .venv/strength-js --ignore-scripts --no-audit --no-fund @stryker-mutator/instrumenter@9.5.1
python -m pytest tests/test_strength.py -q
python -S -c "import core.strength.runner; import core.export"
```

The optional producer controls use actual Python/Node/TypeScript tests, weak and
strong boundary assertions, fresh trials, editable-path redirection, malformed
settings, source changes, deadlines, state validation and superseded writers.
Without engines, real-engine cases skip; base imports remain stdlib-only.
Runtime does not install dependencies or run paid model evaluations.

## Generalized project-health acceptance

```sh
python -m pytest -q tests/test_project_health.py tests/test_health_boundaries.py tests/test_health_environment.py tests/test_health_report.py tests/test_health_review.py tests/test_health_cli.py tests/test_native_acceptance.py tests/test_health_host_contracts.py
python -S -c "import core.health; import core.hosts.acceptance; import core.strength.runner; import core.export"
python architecture/check.py --render
```

The focused group covers fresh/stale/gone or incomplete inputs, all declared
aggregate outcomes, malformed/moving state, current task/session/generation,
unresolved callback errors, retention/privacy and read-only behavior. Python
unittest and Node TAP producers genuinely fail, pass and time out through all
five launchers. Node 22 is used by CI. These are launcher contract controls, not
installed agent-session captures. No model call is included.

Prepare a new disposable installed-host exercise with
`ep_doctor.py --prepare-acceptance NEW_DIR --platform HOST --language python
--host-version INSTALLED_VERSION`, follow `EXERCISE.md`, then inspect with
`--acceptance DIR --platform HOST --json`. Keep the generated contract unchanged
and use one task/session. Explicit operator versions are not attestation.
Normal `ep_ready` is read-only; `--check` opts into a nonzero result for an
unobserved/incomplete pipeline. Paid evaluation still requires cost approval.
See [dated results and qualifications](validation/2026-10-01-project-health.md).

## Versioned native validation and subscription controls

```sh
python -m pytest tests/test_native_validation.py tests/test_acceptance_provenance.py tests/test_host_probes.py tests/test_validation_capture.py tests/test_validation_matrix.py tests/test_validation_cli.py tests/test_performance.py tests/test_challenge.py tests/test_paired.py tests/test_pilot_archive.py tests/test_subscription.py -q
python -S -c "import core.hosts.validation; import core.hosts.performance; import eval.paired"
```

These controls use real version-producing children, bounded source identities,
read-only project samples, normal candidate package imports, forged grade attempts,
typed behavior and private archive metadata. They launch no model. The existing
four-cell CI also checks these new imports with site packages disabled.

Installed acceptance and the explicit subscription pilot consume host capacity
only when the operator runs them. Keep preparation, callback delivery and coding
outcomes separate. The original October 2 pilot remains inconclusive, with its
original protocol preserved. Use `eval.paired --inspect ... --protocol ...` for
read-only aggregate reproduction; start a new directory for a new comparison.
See [observations](validation/2026-10-02-native-validation.md) and
[commands](../the-guide/commands.md).

## Milestone verification controls

```bash
python -m pytest tests/test_milestone_definition.py tests/test_milestone_history.py tests/test_milestone_report.py tests/test_milestone_impact.py tests/test_milestone_exercise.py -q
python -S -c "import core.milestones; import eval.milestones; import core.export"
python -m eval.milestones --output NEW_DISPOSABLE_DIR
```

The exercise explicitly writes a new disposable project and runs actual pytest
and optional Node checks. It starts no model. Frozen assertions, later faults,
repairs, equivalent implementations, scope controls, corrupt history recovery
and stale writer replay qualify capability only. See
[milestone validation](validation/2026-10-06-milestones.md).

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

Portable report controls run with
`python -m pytest tests/test_portable_report.py tests/test_repository_scan.py -q`.
They cover explicit-path and source freshness, same-size timestamp-preserving
edits, nested snapshot isolation, literal Markdown, evidence caveats, timestamp
ordering, shared budgets and unchanged ambient verification journals. Export a
real local acceptance report with `plugin/bin/ep_report.py --project PATH`;
report generation does not rerun that project's commands.

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

### Recheck evaluation controls

`python -m eval.milestone_rechecks --output NEW_DISPOSABLE_DIR` runs frozen
authored Python/Node boundary, equivalent and unrelated controls, grading known
required/negative milestone labels separately from fallback retention. Keep
assertions and labels fixed before interpreting the result; do not tune adapters
to held-out outcomes. No model is launched. See
[results](../results/milestone-rechecks/README.md).

The controller checkpoints incomplete case/overall state atomically after reads
and each requested/completed attempt. Pending identities remain when interrupted.
Shared commands are graded using milestone-specific witness reasons; a command
priority alone never credits a relationship. Saved original grades remain fixed.


The optional edit adviser reuses the standard-library ImpactGraph/report, repository process cleanup and atomic state writer. `core/milestones/advice.py` validates limits/renders context; `automatic.py` reserves before launch; `advice_worker.py` inspects read-only. `eval/milestone_large.py` seals upstream snapshots; `eval/advice_callbacks.py` intentionally writes disposable config/state and measures replay launchers. Run `tests/test_milestone_advice_*.py`, `tests/test_milestone_large.py`, `tests/test_milestone_entrypoints.py` and `tests/test_advice_callbacks.py` after changing this flow. See [design](design/milestone-advisories.md) and [observations](../results/milestone-advisories/README.md).
