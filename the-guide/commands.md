# Commands

## ep_impact — explained consumers and candidate tests

```bash
python plugin/bin/ep_impact.py --project PATH src/session.py
python plugin/bin/ep_impact.py --project PATH src/session.py --json
python plugin/bin/ep_impact.py --project PATH --graph --output impact.json
```

Each query reads fresh bounded project inputs. Python imported calls and optional
JS/TS imports join declared contracts and explicit current observations. Candidate
tests carry actual relationship paths; bounded history remains a separate hint.
Reads launch no test or host and write no project state. Optional flags include
`--observations`, `--history`, `--seconds`, `--max-files`, `--max-bytes`,
`--max-depth`, `--max-results`, `--change`, `--output` and `--force`.
`--check` exits 1 for incomplete coverage; ordinary reports exit 0 even when
qualified; invalid arguments or failed exports exit 2. See the
[ImpactGraph guide](impactgraph.md) for schemas, dependencies and supported limits.


## ep_ready — fresh health for the whole integration

```sh
python plugin/bin/ep_ready.py HOST --project PATH --json
python plugin/bin/ep_ready.py HOST --project PATH --seconds 30 --check
```

`HOST` is `claude`, `codex`, `gemini`, `cursor` or `copilot`. Readiness shows
configuration, runtime lookup, native startup, edit delivery, command capture,
current declared verification, completion, report coverage and optional strength.
It freshly reads source and explicit receipt inputs once. A failing captured run
can establish capture while verification remains failed. An observed pipeline
does not change the task verdict; no active claim still means UNVERIFIED.

`--seconds` defaults to 10 and accepts finite values from 0 through 120. This
cooperative budget qualifies slow filesystem reads as incomplete. Normal exit 0
means the diagnostic report was produced; explicit `--check` exits 1 unless all
required stages are observed and every declared command is fresh and passing.
Invalid flags exit 2. Readiness runs no project command, mutation engine, package
installer or host, and writes no project state.

Timings include fresh source/report/read duration and median/p95 of retained
callback and automatic-command samples. They are observations of at most 32
samples, not a speed improvement or future latency guarantee. Optional engine
availability checks package metadata and runtime lookup; they do not execute
the engine or block ordinary pipeline health.

## ep_doctor — repeatable native acceptance

Run each declared command as its own tool call from the exercise directory.
Directory prefixes, echo suffixes, pipelines and timeout wrappers change the
command and may hide its exit status. Use native interruption controls for the
incomplete step. Inspect with the same account/Git ignore policy as the host.

```sh
python plugin/bin/ep_doctor.py --prepare-acceptance NEW_DIR --platform HOST --language python --host-version INSTALLED_VERSION --json
python plugin/bin/ep_doctor.py --prepare-acceptance ANOTHER_NEW_DIR --platform HOST --language javascript --host-version INSTALLED_VERSION
python plugin/bin/ep_doctor.py --acceptance DIR --platform HOST --seconds 30 --json
```

Preparation explicitly creates a new disposable Git repository with owned host
wiring, an intentionally failing unittest/Node test and `EXERCISE.md`. Existing
or linked destinations are refused. Python is the default exercise language;
JavaScript needs Node on PATH. No host/model session or package download runs.
Preparation exits 0; invalid setup exits 2.

Follow the exercise in one installed host task/session: startup, real failure,
source fix, passing run, interruption, later source edit, stale view, rerun and
normal completion. Inspection is read-only. It requires unchanged tests/project
configuration/wiring, the current generation, native pass/fail/incomplete history
and a fresh completed pipeline. It exits 0 for `passed`, 1 for waiting/failed/
incomplete observations and 2 for invalid invocation. `--seconds` has the same
10-second default and 120-second maximum as readiness. Language/version flags
apply only to preparation; `--cwd`/`--host` cannot be combined with exercise modes.

The operator version is required to qualify versioned acceptance. It is metadata,
not host authentication. Prepared projects, replay and launcher contract fixtures
do not establish an installed-session result. Current freshness is checked; the
earlier manual stale-view step is not independently attested. Local acceptance
does not certify a production patch or other host versions.

## ep_strength — inspect changed-code test strength

```bash
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_strength.py --root .
python PATH_TO_ELEVENPOWERS/plugin/bin/ep_strength.py --root . --base FULL_COMMIT --command "python -m pytest tests -q" --seconds 60 --max-mutants 8 --json
```

`--root` chooses the repository (default current directory). `--base` chooses an
explicit full Git commit instead of the task base, deliberately including existing
edits in that comparison. `--command` selects a focused command. `--seconds` and
`--max-mutants` override limits without editing configuration. `--json` prints saved
metadata. Exit 0 means complete, disabled or not applicable; exit 2 means incomplete,
unavailable, deferred or invalid setup. Undetected mutations alone do not fail it.
Caps can leave valid observations with incomplete coverage, so read the issues.
Selection automatically records changed hunks and enclosing functions, partitions
new/multi-function hunks and rotates bounded attempts across files/functions.
Deleted behavior remains an explicit coverage gap. The selected root must be the
Git repository root; unsupported attribution or a moving source snapshot stays
incomplete. No extra relevance flag or project-specific setup is required.

The command writes diagnostic state and never edits original source or installs
packages. It requires positive passing test counts in the private baseline, then
runs every mutation from clean inputs. Automatic completion considers this same
runner. Human `ep_report.py --project PATH` reads saved results without executing
engines or tests. Its additive schema-v1 `test_strength` section contains counts,
operator/path/line metadata, independent freshness, sampling limits and incomplete
execution. New saved records are schema 2, with source spans, edit relationship,
context, selection and recorded-command-only coverage; the portable report's
outer schema remains version 1. Legacy strength records remain explicitly
whole-file samples. Markdown shows complete line ranges. Only the command that
ran is observed; another test command may detect an undetected mutation.
Undetected changes are possible test gaps, including equivalent behavior,
not correctness verdicts. Individual targets never enter automatic agent feedback.

Native-host installation helpers are Python entry points from the ElevenPowers
checkout (or a bundle containing them). Setup/doctor `PLATFORM` includes `claude`,
`codex`, `gemini`, `cursor` and `copilot`; portable bundle generation supports the
four additions:

```sh
python plugin/bin/ep_setup.py PLATFORM --project PATH
python plugin/bin/ep_doctor.py --platform PLATFORM --cwd PATH
python plugin/bin/ep_ready.py PLATFORM --project PATH [--json]
python plugin/bin/ep_setup.py PLATFORM --project PATH --remove
python -m core.hosts.package PLATFORM NEW_OUTPUT_DIRECTORY
```

The doctor checks subscriptions, matchers and interpreter/launcher paths and
reports callback activation. `ep_ready` adds project commands, runtimes, coverage,
latest declared execution, current input freshness, staged health and next actions.
Omitting the setup platform uses
unambiguous PATH detection. Readiness is a report command; configuration health
and activation are available through `--json`. Callback observations do not
authenticate their sender; `--host` remains the separate Claude replay
diagnostic. Use `python plugin/bin/ep_status.py --cwd PATH` for a persisted report,
especially on Cursor and Copilot, whose completion callbacks lack ordinary report
fields. See [platforms](platforms.md) for native capabilities and limitations.

[← The Guide](README.md)

Commands for status, shareable evidence, health and repeat runs, plus evaluation
commands for measuring the project itself.

Pending native patch callbacks, exhausted observation history and unreadable
patch state produce an explicit incomplete-coverage warning in status. At
completion, unpaired pre-events remain UNVERIFIED even if tests pass.

---

## `ep_status` — what does this task still owe?

```bash
python plugin/bin/ep_status.py [--cwd DIR]
```

Ask at any point rather than waiting until completion. Prints the profile, effective commands (explicit or discovered), current claim and obligations with whether they are met, missing or stale. SessionStart separately reports scan coverage and basic health. Status also shows the current verification journal, including active, deferred and interrupted checks. It only reads progress; it does not start a background runner or rerun a command.

```
UNVERIFIED  bug_fixed
  missing  a test covering the change passes
           run the test that exercises this change, by name or by file
  missing  that test failed before the fix
           run it before applying the fix so the failure is on record
  met      the related test suite passes
```

| Flag | |
|---|---|
| `--cwd DIR` | report on a different project directory (default: `.`) |

---

## `ep_report` — evidence to share with a reviewer

Run this entry point from the checkout or from a portable bundle, for any project
and any supported host:

```sh
python plugin/bin/ep_report.py --project PATH
python plugin/bin/ep_report.py --project PATH --output report.md
python plugin/bin/ep_report.py --project PATH --format json --output report.json
```

It exports computed claims, obligations and their evidence qualifications,
timestamp-selected command receipts, execution status, current input freshness,
changed targets, revision, coverage gaps and next actions. Source and explicit
receipt inputs are freshly read within the project scan budgets. An absent claim
is UNVERIFIED, even when command receipts pass. Git revision is metadata, not a
fingerprint of uncommitted changes; receipt fingerprints bind the observed bytes.

| Flag | Default | Effect |
|---|---|---|
| `--project PATH` | current directory | select the project independently of the tool's location |
| `--format markdown\|json` | `markdown` | human report or schema-version-1 JSON |
| `--output PATH` | stdout | atomically publish a local file |
| `--force` | off | allow atomic replacement of an existing output |
| `--timeout SECONDS` | `120` | finite cooperative budget from 0 through 600 seconds |
| `--require-verified` | off | exit 1 when the exported state is not VERIFIED |

Normal exit 0 means the report was generated, including when its state is
UNVERIFIED, STALE or CONTRADICTED. Export errors exit 1; invalid flags exit 2.
No project check or model call runs, and report creation does not save ledger or
verification-journal changes. Output creation is the explicitly requested write.
The deadline bounds observation loops and Git calls; an in-flight filesystem call
may return after it, in which case coverage is incomplete.

Prompts, transcripts, captured outputs and receipt details are excluded. Known
credential patterns are scrubbed and project-root text is replaced with
`<project>`. Supplied Markdown remains literal. This is an unsigned local
observation for review; it does not authenticate the ledger or establish that
passing tests exercised every changed behaviour.

---

## `ep_doctor` — is the runtime hearing the host?

```bash
python plugin/bin/ep_doctor.py [--cwd DIR] [--host]
```

The deeper self-check on the layer between this runtime and Claude Code. Basic health is reported automatically at SessionStart; use this diagnostic after a host upgrade or when expected receipts do not arrive. Even `--host` exercises the launcher locally, so a live host session remains a separate integration check.

| Flag | |
|---|---|
| `--cwd DIR` | check a different project directory (default: `.`) |
| `--host` | additionally drive the Claude launcher as a real process with payloads on stdin; this remains replay |
| `--platform HOST` | check a selected host's configuration and launcher availability |
| `--json` | print structured diagnostics |

Exits `0` when everything passes, `1` when a check fails, `2` on an unrecognised flag.

> [!NOTE]
> Unknown flags are refused rather than ignored, deliberately. This script used to accept `--host` silently and then print six green lines about something else entirely — a passing check that meant nothing, and one that passed that way for weeks.

---

## `ep-repeat` — is this actually flaky, and how flaky?

```bash
python plugin/bin/ep_repeat.py <times> [--jobs N] [--timeout S] [--stop-on-fail] [--cwd DIR] -- <command>
```

The one tool here that is worth having on its own, independent of everything else. Nothing else in the field ships one.

```bash
python plugin/bin/ep_repeat.py 50 -- pytest tests/test_login.py
python plugin/bin/ep_repeat.py 50 --jobs 8 -- pytest tests/test_login.py -q
```

| Flag | Default | |
|---|---|---|
| `<times>` | required | how many times to run it |
| `--jobs N` | `1` | run this many at once |
| `--timeout S` | `300` | seconds allowed per run |
| `--stop-on-fail` | off | stop at the first failure instead of measuring a rate |
| `--cwd DIR` | `.` | directory to run in |

The command goes after a bare `--`. Everything before it belongs to `ep-repeat`, everything after belongs to your command — so `--jobs` is never swallowed by the thing being repeated.

Prints a human summary plus one machine-readable line that the runtime turns into stability evidence. Exits non-zero if the command failed at least once, so it works as a plain flakiness check in a shell or in CI, with no agent involved.

### Why the number matters

When a claim is about something intermittent, the runtime does not ask for "a few more runs". It computes how many clean runs actually settle the question, from the failure rate the agent itself measured:

```
missing  repeated runs show the failure is gone
         ep-repeat 29 -- python -m pytest tests/test_worker.py -q
         so far: still failed 3 of 30
```

Three failures in thirty is a 10% rate. Ruling that out at 95% confidence needs 29 clean runs, because 0.9²⁹ < 0.05. You get told the number instead of guessing one.

---

## Evaluation commands

You do not need these to use the tool. They exist so that every number the project publishes can be re-derived by someone who was not there, and they are documented here so you can check the claims yourself.

### Measuring the runtime

| Command | What it answers |
|---|---|
| `python -m eval.replay --all` | does the runtime agree with the host about which commands failed, across recorded real sessions? |
| `python -m eval.run --all` | does the gate block the right things, on labelled scenarios? |
| `python -m eval.scope_run` | does the scope guard ask only when it should? |
| `python -m eval.claims_run` | does claim inference fire on the right turns, across real prompts? |
| `python -m eval.claims_run --cases` | the same, against hand-labelled cases |
| `python -m pytest tests/ -q` | the full suite |
| `python -m pytest tests/test_audit_probes.py -q` | the external audit's defects, each as a test. Zero xfails means all of them are fixed |

### Measuring against real tasks

| Command | What it does |
|---|---|
| `python -m eval.validate` | grades four patches whose answers are already known — the check on the grader itself |
| `python -m eval.corpus --repos DIR --out corpus.json` | mine several repositories into one task corpus |
| `python -m eval.corpus --lock corpus.json --out corpus.lock` | pin it so a rerun gets the same tasks |
| `python -m eval.mine --repo DIR --out mined.json` | mine a single repository's history into tasks, no Docker needed |
| `python -m eval.live --arm gate --model haiku` | drive the real CLI against real tasks |
| `python -m eval.baseline --pinned` | a score with an interval that a rerun can be checked against |
| `python -m eval.baseline --compare a.json b.json` | did the rerun reproduce? |
| `python -m eval.failures` | a taxonomy of how runs failed, every category citing saved trajectories |
| `python -m eval.analyse` | analysis across replicates, not one row per arm |
| `python -m eval.noise a.json b.json` | how much of a difference between two passes is just noise? |

> [!WARNING]
> `eval.live` and `eval.baseline` spend real money on a real model. Both take an explicit budget. A ninety-run sweep cost $67.42 — see [journey/23-spend.md](../journey/23-spend.md) for what that bought and what it broke. Do not run these casually.

---

## Maintenance

| Command | |
|---|---|
| `python -m core.wiring` | rewrite `hooks.json` when `ep_doctor` reports a drifted subscription |

---

Something behave differently from what is written here? That is a documentation bug and I want to hear about it — **[satyambcnrk@gmail.com](mailto:satyambcnrk@gmail.com)**.

## ep_validate — dated compatibility and read-only costs

```bash
python plugin/bin/ep_validate.py capture codex --project EXERCISE --observe-version --seconds 30 --json --output codex-python.json
python plugin/bin/ep_validate.py matrix codex-python.json claude-python.json --json --output matrix.json
python plugin/bin/ep_validate.py performance codex --project PATH --repeats 3 --seconds 60 --json --output performance.json
```

Omit `--json` for Markdown. Output is printed unless `--output` is explicit; an
existing file requires `--force`. `--check` exits 1 unless capture passes, all ten
matrix cells pass, or the requested performance sample completes. Invalid input
or options exit 2. Supply one selected capture per host/language: duplicates,
malformed fields, incomplete checks and changed runtime cannot inflate success.
Captures read the existing acceptance inspector; `--observe-version` runs only a
bounded contained `--version` probe. They omit paths, prompts and raw diagnostics.

Performance defaults to three reads and 60 seconds; repeats are 1–20 and total
seconds at most 120. Every attempted read remains visible, including failure or
deadline exhaustion. No warmup is discarded. Current scan/report/read timings
are separate from retained callbacks; Stop can include verification. A complete
measurement can describe a waiting pipeline and does not certify a task.

### Explicit subscription coding pilot

```bash
python -m eval.paired --directory NEW_DIR --codex CODEX_EXE --claude CLAUDE_EXE --seconds 240
```

A new unlinked directory is required. The protocol freezes task/prompt/grader
identities and schedules eight runs: two replicates of baseline/tool per host,
reversing arm order. Models are `gpt-6.1-sol` medium and `claude-sonnet-5-5` medium.
Each model call is bounded at 240 seconds; setup, host failures, timeouts, invalid
contracts and independent grades are distinct. API environment/provider overrides
are refused. Authentication must report ChatGPT or Claude subscription mode.
Codex uses supported automatic approval review (which selects workspace-write);
Claude loads project/local hooks. Native hook trust remains a host requirement.
The pilot consumes subscription capacity and is never run automatically. Eight
records are descriptive, not proof of general improvement. See [observations](../docs/validation/2026-10-02-native-validation.md).


### Reproduce an archived pilot without running it

```bash
python -m eval.paired --inspect SAVED_REPORT.json --protocol RECORDED_PROTOCOL.json
python -m eval.paired --inspect SAVED_REPORT.json --protocol RECORDED_PROTOCOL.json --output reproduced.json
```

These reads launch no model, candidate, project checks or grader. Inputs are
bounded and reject duplicate JSON keys, nonfinite values, unsupported result
claims, conflicting protocol/budgets and private or unknown run fields. Existing
output requires `--force`. Archive mode cannot accept model-launch options.
`current_evaluator: false` means the saved grader identity differs from the
installed one; reading an earlier protocol does not silently upgrade or validate
its results. A complete protocol counts eight records, including failures.

The current grader uses a contained behavior worker with normal package imports
and bounded type-tagged outputs, preserving list/tuple and scalar distinctions.
Its controller never imports candidate code and owns all sixteen assertions.
A passing result means those frozen checks passed; invalid account identifiers
already present as balance keys are outside this grader's checked cases. Local
process separation does not create an OS closed-book boundary.

## Fixed-patch review and reproduction

These commands are explicit evaluation tools. Plugin installation does not
start reviews or consume model capacity. The first pilot measures new behavioral
tests on fixed production code, using the shipping optional analysis through a
function-level brief. Existing source, tests and configuration stay protected.
The workflow is project-independent; a case supplies its own local cache, full
base commit, saved patch, source paths and environment.

```bash
python -m eval.review_pilot --case REVIEW_CASE.json --repository LOCAL_CACHE --arm ordinary --destination NEW_PRIVATE_DIR --executable INSTALLED_CLAUDE --python TEST_PYTHON
python -m eval.review_pilot --case REVIEW_CASE.json --repository LOCAL_CACHE --arm assisted --feedback FROZEN_BRIEF.txt --destination ANOTHER_NEW_DIR --executable INSTALLED_CLAUDE --python TEST_PYTHON
python -m eval.review_archive --archive SAVED_ARCHIVE_DIRECTORY
python -m eval.review_archive --archive SAVED_ARCHIVE_DIRECTORY --repositories LOCAL_CACHES.json --regrade NEW_REPRODUCTION_DIR --python TEST_PYTHON
```

`REVIEW_CASE.json` contains clean case metadata and its source/test patch, without
grading fixtures. The selected model is subscription Claude Sonnet 5 at medium;
the maximum review cap is 480 seconds. API environment overrides are refused,
and an attempted slot cannot be reused. Native outputs stay private. Only
bounded new `tests/**/test_*.py` files are eligible; existing-file changes remain
scope violations. The supported input environment currently provides one
relative Python source directory through `PYTHONPATH`.

Archive inspection is read-only and runs no commands. `--regrade` explicitly
runs trusted saved project tests in fresh copies, using the supplied interpreter
and cache mapping, never a model. The JSON cache mapping associates each
archive `repository_key` with a local Git checkout containing the pinned base.
Dependencies must match the saved environment. Fault errors, empty execution,
timeouts and changed grading inputs remain separate from test detections. The
result reports whether state and count outcomes reproduce, with timing excluded.
Hashes establish unsigned consistency, and local copies are not a security
sandbox for executable project tests. See the [pilot design](../docs/design/checkpoint-review-pilot.md)
and [provenance](../docs/research/checkpoint-review.md).

## Controlled completion comparison

The harder suite is explicit and uses four authored interacting tasks: SQLite
lease ownership, async cache lifecycle races, incremental build impact, and
resumable transactional UTF-8 processing. It runs one baseline/tool pair per
task, alternating arm order. The 94 controller-owned groups are independent of
visible project tests; the grader is checked against correct references and 16
plausibly faulty controls before any model call. Hidden checks never supply agent
feedback. This is an exploratory comparison, not a population benchmark.

```bash
python -m eval.benefit prepare NEW_DIR --suite hard --model claude-sonnet-5 --seconds 480
python -m eval.benefit run NEW_DIR --executable CLAUDE_PATH --native-project OBSERVED_NATIVE_DIR
python -m eval.hard_archive ARCHIVE.json --regrade --checksums CHECKSUMS.json
```

Preparation creates eight new candidates and launches no model. Execution requires
subscription authentication and an already observed native Claude pipeline under
the same account. Sonnet 5 medium is selected explicitly; ordinary defaults remain
Sonnet 5.5 medium for the original protocol. Budgets stop at eight minutes per
hard-task call. Attempted slots cannot be retried in place. Failed calls,
quota errors and incomplete observations stay visible. Regrading executes saved
candidate source in disposable directories but makes no model call; ordinary
archive inspection executes no candidate. Source archives are local diagnostic
evidence, not ordinary product exports or an OS security boundary.

Seeded tests, task text and configuration are frozen. Agents may edit only the two
named production files and one named regression-test file. Unexpected source files
invalidate the admitted task contract. A paired check advantage is separate from a
repair linked to a real plugin action, and receipt refresh remains evidence quality.
Elapsed times include the contained coding run, hook work and controller grading;
they are not pure model latency. See the [frozen design](../docs/design/hard-task-comparison.md).

After independently establishing that a hard comparison controller has exited,
`run ... --finish-unstarted` preserves its original journal, retains any started
but unfinished slot as interrupted, and launches only slots with no prior result
journal. A continuation journal records its executor identity. It refuses a live
recorded controller and a second continuation; original protocols cannot resume.
Legacy journals without a recorded PID require operator confirmation of exit.
Never use this to repeat an unfavorable or interrupted model call.

```bash
python -m eval.hard_audit ARCHIVE.json --output NEW_AUDIT.json
```

This explicit free audit runs saved candidates' visible tests and supplementary
async closure checks. It is separately versioned because review found these gaps
after the original scenario grader was frozen. Original scores stay unchanged;
the frozen `regressions` field counts only two basic hidden guards per task, not
all seeded or added tests. A passing saved-code audit cannot qualify an interrupted
native session. Neither regrading nor this audit calls a model.

This explicit evaluation workflow is separate from plugin installation. It
currently qualifies Claude's exit-2 completion decision, using subscription
`claude-sonnet-5-5` medium. It requires an observed native pipeline before calls,
refuses API environment overrides, freezes two cases/eight slots, reverses arm
order and never resumes or overwrites an attempted batch. Both arms use the
same passive observer; treatment delegates to ordinary guide hooks.

```bash
python -m eval.benefit prepare NEW_BATCH_DIRECTORY --seconds 240
python -m eval.benefit run BATCH_DIRECTORY --executable CLAUDE_EXE --native-project QUALIFIED_EXERCISE
python -m eval.benefit_archive docs/validation/2026-10-02-proof-of-benefit/completion-archive.json
python -m eval.benefit_archive docs/validation/2026-10-02-proof-of-benefit/completion-archive.json --regrade
```

Preparation creates only disposable evaluation inputs and launches no model.
New batches use protocol version 2 and seal each candidate's source, tests,
instructions, observer contract and project/local settings at preparation.
Expected absence of project settings is part of that seal. A batch-level
`attempt.json` precedes native health and subscription authentication; failed
preflight is retained and cannot be retried in that directory. Each Stop also
gets an independent attempt marker. A missing, failed or conflicting capture,
or a treatment native Stop count that differs from captured proposals, cannot
qualify an earlier successful history as complete.
An unavailable observation sink does not suppress the native child's decision;
the comparison remains incomplete if its capture markers cannot be saved.
Run consumes subscription allowance and preserves each attempt immediately;
quota exhaustion stops scheduling. The archive read launches no candidate or
model. Explicit `--regrade` executes contained independent checks on disposable
saved synthetic source. This archive reader qualifies the original successful
eight-run publication, rather than arbitrary later failed batch journals.
An older harness/evaluator identity remains visible through `current_harness`
and `current_evaluator`; inspection never silently upgrades it. Regrading uses
the current evaluator and compares its grades with the recorded grades.
Reconstruction uses canonical project roots, so Windows short-name temporary
aliases and equivalent path spellings retain the same file boundary.
Candidate files, prompts and history here are
explicit benchmark artifacts and remain absent from ordinary product reports.

`missing` verification means no exact-command receipt was observed. Wrapped
tests may have run. Receipt refresh, repaired behavior and coding benefit are
separate fields. The first eight-run comparison observed extra fresh receipts
and tied 16/16 behavior in both arms; it establishes no population effect or
speedup. See [dated evidence](../docs/validation/2026-10-02-proof-of-benefit.md).

Optional `--checksums CHECKSUMS.json` checks the explicit canonical-JSON manifest;
its hashes survive checkout newline conversion. This is a local consistency
check, not signature verification or authentication.

The first saved review archive is at
`docs/validation/2026-10-02-checkpoint-review`. Its original producer identity
differs from the corrected current evaluator. All eight recorded reviews qualify.
All twelve corrected local grade sets completed on 2026-10-03; nine match exactly
and Click F03 retains mixed failures/setup in all three arms. Historical originals
and the separate current reproduction remain explicit. Follow its
[reproduction guide](../docs/validation/2026-10-02-checkpoint-review/README.md)
for pinned environment/cache preparation. The inspect command makes no model or
test call; explicit regrading uses only local trusted test execution.
