# Local development and verification

Run owned-check controls with `python -m pytest tests/test_checks.py tests/test_check_cli.py tests/test_declared_check_protocol.py -q`, and actual disposable acceptance with `python -m eval.declared_checks --output NEW_DIR`. No model calls. The manual execution-reliability workflow also retains twenty JavaScript advice repetitions per OS/Python cell, with component diagnostics on failure.

## External input witness controls

```sh
python -m pytest tests/test_input_definitions.py tests/test_input_collection.py tests/test_input_io.py tests/test_input_cli.py tests/test_external_input_reuse.py tests/test_external_input_execution.py tests/test_external_input_review.py tests/test_external_inputs_exercise.py -q
python -S -c "import core.inputs.definition; import core.inputs.bindings; import core.inputs.collection; import core.inputs.access; import eval.external_inputs"
python -m eval.external_inputs --output NEW_EXTERNAL_DIRECTORY
python -m eval.github_presentation --output ANOTHER_NEW_DIRECTORY --repository OWNER/REPO --external-inputs
```

The dependency exercise requires Python, Git and Node, creates fresh disposable
projects, launches actual Python/JavaScript checks, and measures unchanged reuse,
independently failing drift, required rerun and missing-input refusal. No model
or package installation runs. CI repeats the exercise across Windows/Linux and
Python 3.11/3.13. See [qualification](validation/2026-10-13-external-inputs.md).

## GitHub presentation controls

```sh
python -m pytest tests/test_patchproof_github.py tests/test_patchproof_github_output.py tests/test_patchproof_github_cli.py tests/test_github_presentation_exercise.py tests/test_portable_report.py -q
python -S -c "import core.patchproof.github_context; import core.patchproof.github; import core.patchproof.github_output; import eval.github_presentation"
python -m eval.github_presentation --output NEW_EXTERNAL_DIRECTORY --repository OWNER/REPO
```

The explicit disposable exercise runs real passing, failing and interrupted
checks; it asserts one execution each and no report-side source changes.
The hosted dispatch/push job calls the actual composite Action; inspect and
download its two-file artifact, then recompute the canonical bundle hash.
PR-shaped controls do not qualify live fork transport. Cold vendored runtime,
credential-key collision, hard links, event mismatch, literal output and byte
limits are retained controls. See [qualification](validation/2026-10-13-github-evidence.md).

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

## Explicit PatchProof verification controls

```sh
python -m pytest tests/test_process.py tests/test_patchproof_planning.py tests/test_patchproof_execution.py tests/test_patchproof_verification_cli.py -q
python -m eval.execution_reliability --repetitions 10 --seconds 240
python -S -c "import core.patchproof.planning; import core.patchproof.execution; import core.patchproof.execution_report"
```

Actual Python/Node assertions, source/configuration/environment drift, malformed
and moving state/refs, late real failed receipts, verbose aggregate recovery,
redacted command collisions, launch handoff signals, zero executed tests,
exhausted budgets, output limits and actual
CLI termination/recovery qualify the explicit workflow. The historical 20-second
quoted-launch deadline remains unchanged. These controls run no model and do not
establish coding benefit; [operation limits](../the-guide/patchproof-verification.md)
and [dated observations](validation/2026-10-12-patchproof-verification.md) remain explicit.

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

Confirm the output says all five views draw; a skipped render is not a rendered check. These tools are not runtime dependencies. Use [the validation index](validation/README.md) for dated outcomes and [current status](status.md) for remaining integration work.

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

## External input session controls

For command scopes and operation-local report collection:

```sh
python -m pytest tests/test_input_scopes.py tests/test_input_scope_details.py tests/test_input_shared.py tests/test_input_scope_review.py -q
python -m eval.input_scopes --output NEW_DISPOSABLE_DIR
python -m eval.input_scope_pilot --output NEW_DISPOSABLE_DIR --language python --rehearse
python -m eval.input_scope_pilot --output NEW_DISPOSABLE_DIR --language javascript --rehearse
```

The portable protocol runs actual Python/Node consumers and five synthetic host
envelopes, comparing scoped declarations with broad controls. CI retains one
`command-input-scopes-OS-PYTHON` JSON artifact per matrix cell. These are
mechanism controls, separate from installed sessions and coding-quality claims.
Removing `--rehearse` launches a subscription model and requires an explicit
allowance. The installed pilot uses two tasks under one persistent conversation
UUID per language, one shared 180-second cap and no API fallback. Its destination
must be a new system-temp directory outside any Git ancestor. It records host
task transitions, per-turn outcomes and timings, and retained milestone states;
controller-driven checks are labeled separately.

```sh
python -m pytest tests/test_input_sessions_gap.py tests/test_input_receipts.py tests/test_input_native.py tests/test_input_owned.py tests/test_input_views.py tests/test_input_sessions_review.py -q
python -m eval.input_sessions --output NEW_DISPOSABLE_DIR
python -S -c "import core.inputs.receipts; import core.inputs.native; import core.inputs.execution; import eval.input_sessions"
```

The exercise requires Python, Node and Git and runs actual independent checks in
unrelated temporary Python/JavaScript projects. Its five host envelopes are
synthetic adapter controls, not installed-host acceptance. It retains exact
command launch counters, cross-task states and read-only inspection controls;
it launches no model. Review regressions reproduce delayed results after detail
eviction, task replacement, missing-ID policy removal and source/configuration/
external movement during report closure. Optional receipt metadata stays absent
for unconfigured legacy evidence. See [the design](design/external-input-sessions.md).

## Installed multi-stage controls

Use the [installed multi-stage guide](../the-guide/installed-multistage.md) for free rehearsals and source reproduction. Installation/CI launch no model. Live adoption and matched outcome comparison require explicit user authorization, which may be standing approval; do not ask again when it already covers the work. No-model qualification comes first, and native delivery remains separate from correctness.

The installed trial's real callback controls are in
`tests/test_installed_workflow_boundaries.py`: explicit task declarations,
ordinary continuations, task-correlated prompt/tool ingress, unbound callbacks
and independent/bounded command guidance. They launch no model. Original
failed trials and repaired-source qualification remain separate in the
[validation record](validation/2026-10-16-installed-multistage.md).

Both approved repaired-runtime requalification conversations completed but
failed acceptance. The next free controls must reproduce ordinary compound
commands and no-edit prompt/completion guidance at actual callback ingress.
Keep native command execution, emitted advice, owned receipts and independent
behavior separate; never turn shell trailers into authenticated child outcomes.
The original and fresh results are retained in the validation record above.

## Owned batch adoption controls

`python -m eval.check_adoption --output NEW_DIR` executes actual Python/Node
batch pass/fail/drift/recovery/missing-input controls and synthetic five-host
outer callbacks, with zero model calls. `core/check_batch.py` reuses the existing
owned single-check body; tests pin one owner, shared deadline, selected denominator
and frozen-command/context guards. See [validation](validation/2026-10-17-check-adoption.md).
