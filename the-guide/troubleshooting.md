# Troubleshooting

For milestone reports, inspect exact command spelling, declared inputs and the
root declaration file before rerunning a check. A receipt must actually observe
the declaration plus every input; narrowing the declaration does not narrow a
source-scoped receipt. An unrelated selected-source edit can make native evidence
stale. Repair invalid declarations, then capture fresh matching checks. Unknown
history gaps clear only after new observations cover every current declared check;
re-saving old receipts is insufficient. Missing change observations or graph gaps
make requested impact advice incomplete. See [milestone states and limits](milestones.md).

Read test-strength state and issues before counts. `unavailable` means a missing
or incompatible optional engine. `incomplete` can mean red/empty baseline, dirty
attribution, unsafe inputs, import redirection, source changes or exhausted attempts.
`deferred` means the shared deadline prevented completion. None changes the verdict.

Use an explicit full base for a deliberate comparison of existing edits and a
focused command that executes tests in the copy. Do not bypass a failed baseline
or count a timeout as detection. Install dependencies explicitly; declare required
ignored inputs with `strength.dependencies`. Symlinked dependencies are refused.
Python `.pth`/editable paths into original source produce incomplete isolation:
use an isolated dependency environment or supported command. Path/startup overrides
that disable the import diagnostic are unsupported. Local test files are reset
between attempts; external services and deliberate escape are outside a filesystem
copy's guarantee. Old findings can become stale after test, asset, command or
environment changes. Export reads saved metadata and never reruns analysis.

For any supported host, begin with `ep_ready.py PLATFORM --project PATH` and
`python plugin/bin/ep_doctor.py --platform PLATFORM --cwd PATH`. Missing launcher
or interpreter means setup must be rerun from the current checkout/environment.
Healthy configuration still requires the host to load and trust the hooks. Use
one installation route per project, and begin a new session after changes.

An incomplete native command result often means the host supplied text or a
tool-transport outcome without a process exit code. It is not evidence of a
failing command. Guide/strict can run a declared check to obtain its own receipt.
A native patch coverage warning means target observation was incomplete: missing
session/call identity, a missing pre/post callback, unsupported patch input,
unsafe paths, changed execution directory, interruption or exhausted budgets.
Supported patch headers with complete pre/post content observations attribute
dirty and non-Git files. Pending callbacks are visible before completion;
unpaired or evicted calls remain UNVERIFIED. Check host stderr and callback
delivery. A passing suite does not resolve an unknown edit history.
See [native platforms](platforms.md) for per-host limits.

If readiness says **waiting**, review trust/enablement and restart the project
session. **Received** means callbacks arrived but startup has not been processed.
**Active** means startup was processed, not that the project tests pass.
**Error** includes the exception class; inspect host stderr for its details.
Historical callback failure counts remain visible after later successful events.
**Configuration-changed** means recorded activation predates current wiring;
rerun setup. Doctor replay cannot activate a project.

Cursor and Copilot do not expose a normal final-report field. Read the stored
verdict with `python plugin/bin/ep_status.py --cwd PATH`.

For a shareable diagnosis, use `ep_report.py --project PATH --output report.md`.
Exit 0 means export succeeded, even if the report is UNVERIFIED; add
`--require-verified` when a caller needs verification to determine the exit code.
Existing output is preserved unless `--force` is supplied. Incomplete source or
explicit-input coverage requires resolving the reported boundary or budget.
A receipt can become stale when edits, declarations or account-specific Git
ignore rules change the observed inputs. Rerun the relevant check in the intended
project/account rather than treating an old receipt as current.

[← The Guide](README.md)

Start every investigation the same way:

```bash
python plugin/bin/ep_doctor.py --host
```

Six green lines mean the local diagnostic checks passed. They do not by themselves prove the plugin is enabled in the active host session; use `--host` for the deeper launcher check and confirm real tool events create receipts. Anything else, fix that first — nothing downstream works if this layer is broken, and **its failure mode is silence, not an error**.

---

## The runtime says nothing at all

By far the most common report, and it has an innocent explanation more often than not.

**It may be correct.** Ask a question, request a code read, or change only documentation, and no claim opens. The runtime deliberately stays out of the way. Confirm with `ep_status.py` — if it reports no open claim after an actual source edit, keep reading.

**Check the plugin actually loaded.** `--plugin-dir` has to point at [`plugin/`](../plugin/), not at the repository root:

```bash
claude --plugin-dir ElevenPowers/plugin     # correct
claude --plugin-dir ElevenPowers            # wrong, loads nothing
```

**Check the subscriptions.** If `ep_doctor` reports a drifted subscription:

```bash
python -m core.wiring
```

**Check your profile.** `profile: "off"` records silently by design. So does `EP_PROFILE=off` left over in your environment:

```bash
echo $EP_PROFILE        # bash
echo $env:EP_PROFILE    # PowerShell
```

---

## `ep_doctor` fails a line

### `FAIL  python 3.x`

Python 3.11 or later is required. If you have a newer Python that Claude Code is not using, the hook runs whatever `python` resolves to on the host's `PATH`, which may not be the interpreter you tested with. Check with:

```bash
python --version
```

### `FAIL  a failing command is recorded as failing`

The most serious one. It means the host's failure shape is not being recognised, so **every failing command is being recorded as a pass** — a gate that verifies everything. This exact defect shipped once and survived 119 passing unit tests.

Usually a Claude Code version whose payload shape has changed. Run `ep_doctor.py --host` for the fuller check, then send me the output — this is worth an immediate fix on my side, not a workaround on yours.

### `FAIL  hooks.json subscribes to every event the runtime handles`

```bash
python -m core.wiring
```

Rewrites the subscription file. Re-run `ep_doctor` to confirm.

### `FAIL  the ledger directory is writable`

The runtime cannot create or write `.elevenpowers/` in your project. Check permissions on the project directory; on Windows check that the folder is not marked read-only and that a security tool is not locking it.

### `FAIL  nothing unreadable has arrived from the host`

Something came from the host that the runtime could not parse, and it was appended to `.elevenpowers/blindspots.jsonl` rather than silently dropped. That file **is** the diagnosis:

```bash
cat .elevenpowers/blindspots.jsonl
```

This is the designed behaviour for a host that changes a field — it becomes a diagnosable symptom instead of a tool that quietly went quiet. Please send me the file; that is exactly what it is for.

### `unknown option(s): --whatever` (exit 2)

`ep_doctor` refuses flags it does not know rather than ignoring them. Known flags are `--cwd`, `--host` and `--platform`. This strictness exists because the script once accepted `--host` silently and printed six green lines about something else entirely.

---

## I am blocked and cannot finish

The `strict` profile refuses to stop while obligations are unmet. That is the point, but you are allowed to overrule it.

**For one session:**
```bash
EP_PROFILE=guide claude
```

**For the project**, in `.elevenpowers/config.json`:
```json
{"profile": "guide"}
```

**Then ask why it blocked.** `ep_status.py` shows exactly which obligation has no evidence. In the great majority of cases the work was already done and simply not shown — which is why declaring your commands matters:

```json
{"commands": {"tests": "make test"}}
```

With that, the runtime runs the suite itself and computes the evidence instead of interrupting to demand it. This one change took live blocking from 75% of runs to 12%.

---

## Everything keeps going `STALE`

Known limitation, honestly documented. Invalidation is **coarse** today: a change within selected source inputs stales source-scoped evidence, rather than only the evidence whose files actually changed.

On a small project this is barely noticeable. On a large one it can be tiresome, and the fix — narrowing the observed set to the import closure of each test — is written down with a trigger in [`docs/postponed.md`](../docs/postponed.md). The trigger is exactly this complaint being measured in real use.

**So please report it.** "This is annoying on my repository of N files" is the measurement that starts that work. Until then, `profile: "guide"` removes the interruption while keeping the information.

---

## The hint names a command that does not exist

Check the startup summary or `ep_status` for the effective command. Root manifests provide conventional defaults; an unsupported wrapper, conflicting package-manager declarations or a project-specific choice may need an override:

```json
{"commands": {"tests": "pnpm vitest run", "typecheck": "pnpm tsc --noEmit"}}
```

See [configuration.md](configuration.md). Guessed hints were a real defect; declaring commands is the cure.

---

## `ep-repeat` says "no command given; put it after --"

The command goes after a bare `--`:

```bash
python plugin/bin/ep_repeat.py 50 -- pytest tests/test_login.py     # correct
python plugin/bin/ep_repeat.py 50 pytest tests/test_login.py        # wrong
```

The separator exists so that `ep-repeat`'s own flags are never swallowed into the command being repeated.

---

## Results differ between machines, or between me and CI

Check your Git line-ending configuration before anything else:

```bash
git config core.autocrlf
```

This is not paranoia. In a ninety-run measured sweep on this project, **the grade turned out to be a function of the grader's Git configuration** — a checkout under one `core.autocrlf` setting produced different results from the same commit checked out under another. It cost real money to discover and it is written up in [journey/23-spend.md](../journey/23-spend.md).

If you are comparing results across machines, pin the setting on both.

---

## The Stop hook feels slow

The `Stop` hook has a 600-second timeout because it may run your declared test suite. Startup and source-observation hooks allow 120 seconds for cold scans. Prompt and pre-tool guards retain 20 seconds. Stopping can include input fingerprinting, declared commands, baseline work and targeted confirmation. Inspect `ep_status` for the current phase; these checks share a 480-second work deadline.

If your suite is too slow to sit inside a turn, either declare a faster subset:

```json
{"commands": {"tests": "python -m pytest tests/unit -q"}}
```

To disable automatic verification entirely, use `profile: "off"`. `guide` still executes checks; it only removes blocking. To suppress one discovered command while retaining the other checks, use an empty override such as `{"commands": {"tests": ""}}`. A deliberately narrowed suite proves only the checks it actually runs.

---

## Something else, or something here did not help

Please get in touch. Early software with few users means your bug report is likely the only one, and I would much rather hear about it than not.

**[satyambcnrk@gmail.com](mailto:satyambcnrk@gmail.com)** · [GitHub issues](https://github.com/SatyamSingh-Git/ElevenPowers/issues)

Include, if you can:

```bash
python plugin/bin/ep_doctor.py --host      # the output of this
python --version                            # and this
```

plus your OS, your Claude Code version, and what you expected to happen versus what did. If `.elevenpowers/blindspots.jsonl` exists, attach it — that file exists precisely so this conversation can be short.

## Startup reports incomplete source coverage

Read the specific diagnostic before rerunning. Git failures, unreadable files, unsafe symlinks, invalid settings and file/byte budgets are distinct causes. Default selection permits 20,000 eligible files and 256 MiB. Raise a budget only when the selected inputs belong in coverage; exclude generated data only when it should not invalidate verification. See [scan configuration](configuration.md#repository-scan-configuration).

After resolving the problem, rerun the verification command. Old incomplete receipts do not become complete retroactively. A startup selection check also does not prove every file can later be hashed.

## Startup finds no verification command

Discovery reads supported manifests at the selected root. Check the working directory, packageManager and lockfiles, and whether the intended script uses a conventional name. Explicit overrides win; an empty command disables that need and auto_detect false disables discovery. Unknown wrappers need an exact command in config.json. The runtime still observes known test runners.

## A verification attempt is incomplete

An interruption, timeout, missing runtime or unreadable result is not a passing run or a reproduced test failure. Repair the environment or rerun to completion. Incomplete attempts replace earlier success for that target. The plugin reports missing executables; it does not install the project's dependencies.

## Progress is deferred, interrupted, or still running

Run `python plugin/bin/ep_status.py --cwd YOUR_PROJECT`. The progress journal distinguishes work that never started (`deferred`) from work whose result is unavailable (`incomplete`). A source change during execution is `stale`, even when the process exited zero. Completed check results are already saved; they do not depend on later checks finishing.

An active owner prevents duplicate completion checks. If the owner died, the next normal completion recovers the journal and retries work that is still needed. Status inspection itself does not launch or resume commands. The journal describes process progress; only the evidence ledger determines verification.

The 480-second completion work deadline is shared with baseline and confirmation checks, and each command is limited to 300 seconds. Fingerprinting can also be significant: a fresh Snag fingerprint of 4,418 files / 81,841,401 bytes took 55.66 seconds in the dated local check. That observation is not a general performance promise. Use a suitable declared command or run a longer check yourself; raising the host allowance alone does not change the runner limits. `guide` still runs checks, while `off` stays passive.

An output-cap error means combined output exceeded 8 MiB. Reduce unnecessary verbosity and rerun; partial output is never accepted as a completed result. The plugin does not install missing project dependencies.

## Configuration passes but the integration is not working

Run `ep_ready.py HOST --project YOUR_PROJECT --seconds 30 --json`. Configuration
is one stage; the report separately checks startup, edits, native command capture,
fresh declared verification and completion. A waiting startup needs a new trusted
host session. A waiting capture needs the exact declared command's native result
in the current task/session. A failed or interrupted captured run requires a
completed passing rerun. A later command needs another normal completion.

Corrupt diagnostic/configuration state, pending edits, exhausted source coverage,
moving state or expired read budgets qualify the result. Read the stage-specific
actions before deleting anything. Repair owned wiring with setup; changing it
starts a new observation generation. Optional engine metadata cannot substitute
for a project test run, and an observed pipeline cannot substitute for a task
whose claims remain UNVERIFIED.

## The native acceptance exercise is still waiting

Preparation has only created the repository and instructions. Start its installed
host with owned hooks enabled and trusted, then follow `EXERCISE.md` in one task/
session. Inspection needs a recorded operator version, real pass/fail/incomplete
history, a source correction and current fresh completion. Keep tests/configuration/
wiring unchanged. Replay and synthetic launcher controls do not establish native
installed acceptance. If receipt history was evicted or the contract changed,
prepare a new destination; existing destinations are deliberately refused.

## Validation says waiting or incomplete

A prepared exercise is waiting until a real installed session delivers the
required correlated callbacks and complete pass/fail/incomplete command history.
Check native enablement and accept only your owned hook configuration through the
host's normal trust UI. Do not bypass trust. A changed runtime, legacy unbound
preparation, modified tests/configuration or missing history requires a new
exercise. Explicit `--observe-version` must agree with its declared host version.

A matrix needs one chosen capture per cell; supplying multiple histories is
incomplete. A saved report is dated rather than live readiness. A performance
measurement may be complete while pipeline health waits: it measures reads, not
activation. Budget exhaustion, source movement, unavailable input identity and
failed reads remain visible instead of being dropped.

For subscription pilots, verify `codex login status` and `claude auth status
--json` in the same owner account. Do not print credentials. API/provider
environment overrides are rejected. Claude's 429 weekly limit needs renewed
subscription capacity, not an API fallback. Codex policy rejection requires its
supported automatic approval review; `--approve-for-me` already selects the
workspace sandbox and conflicts with `--sandbox`. Hook trust remains separate.
Preserve failed comparison records before starting a new identified protocol.


If a native hook table shows active subscriptions but ElevenPowers still records
zero callbacks, keep acceptance waiting and inspect the host's native diagnostics.
A shell test passing does not prove callback capture. For Codex, open a new
owned exercise in the installed CLI, review any changed hooks normally, and
follow `EXERCISE.md`; do not use a trust bypass to force a green cell. The dated
October 2 observations preserve this precise gap.

After evaluator updates, use explicit `eval.paired --inspect ... --protocol ...`
to reproduce saved aggregates. This does not call models or repair an older
grader. Private/unknown record fields and unsupported resolved claims are
rejected. Preserve the original protocol when starting a newly identified run.

### Why is an earlier command listed as fallback?

No available graph witness reached its declared inputs. It is still a declared
check, and the dependency may be dynamic, subprocess-based or unsupported.
Fallback does not mean unaffected. A stale fallback still needs refreshed evidence.
Resolve report coverage gaps first; then use the project's normal verification.
See [recheck policy](milestones.md#explained-exact-rechecks).


For missing edit-time milestone context, check project opt-in and `off`, then cooldown, duplicate observations and the per-task cap. Inspect `.elevenpowers/advice.json` locally; reserved/incomplete attempts consume allowance. Repair corrupt state rather than repeatedly bypassing the limiter. Use the explicit milestone report for unsuppressed inspection. See [limits](milestones.md#optional-automatic-edit-advice).
