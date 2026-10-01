# Commands

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
latest declared execution and next actions. Stored receipt freshness is unchecked
here; status evaluates source freshness. Omitting the setup platform uses
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
| `--host` | additionally drive the launcher as a real process with a payload on stdin — success, failure and stop paths — rather than calling the reader in-process |

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
