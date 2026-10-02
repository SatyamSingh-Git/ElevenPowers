# Configuration

Optional changed-file test strength is shared by every host and considered at
completion in guide/strict mode. Off stays passive; runtime never installs engines.
Project-owned `.elevenpowers/config.json` can include:

```json
{
  "strength": {
    "enabled": true,
    "seconds": 60,
    "max_mutants": 8,
    "test_seconds": 15,
    "max_files": 20000,
    "max_bytes": 268435456,
    "dependencies": [],
    "command": ""
  }
}
```

An empty command uses the project's declared/discovered `tests` command. Set a
focused command if full CI is too slow for the baseline budget. Limits must be
positive and finite: seconds <=480, test_seconds <=300, mutants <=256,
files <=100000, bytes <=1 GiB. Invalid settings stay advisory and incomplete.

`python` optionally chooses an interpreter containing Cosmic Ray 8.7.0; otherwise
the runtime interpreter is used. `stryker` optionally chooses the directory of
`@stryker-mutator/instrumenter` 9.5.1; otherwise the root's installed package is used.
Explicit paths can be machine-specific. `dependencies` lists additional required
ignored inputs as relative paths. Conventional `node_modules` is copied when
present, under the same limits. Linked/nested trees and missing inputs are explicit.

`.elevenpowers/strength.json` saves bounded schema-v1 task metadata, never mutant
replacements or test output. Every test starts from fresh inputs. Known editable
Python paths into original source are refused; path/startup overrides that disable
the diagnostic are unsupported. Completed samples can be reused only for matching
tests, assets, environment, command, settings, engine versions and runtime code.
Interrupted and timed-out execution is not reused as a completed sample.

Repository configuration under `.elevenpowers/` is shared by all five host
integrations. The four additional hosts use separate native subscription files;
manage those with `ep_setup.py` as described in [platforms](platforms.md).
Host-specific configuration does not change scan boundaries, receipt semantics,
profiles or completion budgets. The project's declared/discovered commands remain
the authority for automatic checks.

Project wiring now supports Claude as well as the four additions. Setup discovers
manifest commands without executing them and does not generate or replace
`.elevenpowers/config.json`. Readiness uses the same effective configuration.
Explicit quoted interpreter paths are checked without shell expansion.

`.elevenpowers/integrations.json` stores bounded callback diagnostics: counters,
event names, timestamps, wiring generations and exception class names. It stores
no raw session identifiers, prompts, command outputs or exception messages.
`.elevenpowers/patches.json` stores target paths and content digests, not patch
text or source bytes. These files use the existing short project write lock and
atomic replacement. Project-local state ignores itself in Git.

Startup health/discovery, supported event recording and profile-dependent
completion checks run automatically after the host loads/trusts the integration.
Setup cannot override host or administrator policies. The read-only readiness
command adds activation, coverage and environment actions without starting tests.

Portable reports use the same project configuration. Their fresh source view and
explicit receipt inputs share `scan.max_files` / `scan.max_bytes`; an explicit
input is still observed even if its extension or an exclusion removes it from
source selection. Unsafe paths or budget exhaustion make report coverage
incomplete. The report's separate cooperative time budget is the `--timeout`
CLI flag, documented in [commands](commands.md#ep_report--evidence-to-share-with-a-reviewer).

[← The Guide](README.md)

Configuration is optional. Supported root manifests supply verification commands automatically; this file overrides those defaults and controls interruption and scanning.

---

## The file

`.elevenpowers/config.json`, in your project root:

```json
{
  "profile": "strict",
  "commands": {
    "tests": "make test",
    "typecheck": "npm run typecheck",
    "build": "npm run build",
    "benchmark": "python bench.py"
  }
}
```

Four optional settings: `profile`, `commands`, `scan`, and `auto_detect`.

---

## `profile` — how much it is allowed to interrupt

| Profile | Behaviour |
|---|---|
| `off` | record evidence, say nothing, never block |
| `guide` | say what would prove the work, report at the end, never block |
| `strict` | all of the above, and refuse to stop while obligations are unmet |

Default is `strict`.

**What `off` does not do, since 2026-09-19.** That row now describes the code.
Previously `off` also built a temporary git worktree at your task's starting
commit and ran your declared test command inside it before going quiet — real
seconds, on the profile chosen by someone who asked for none. An audit measured
the dispatch. Running checks is now a capability held by `guide` and `strict`
only.

**What `guide` and `strict` execute.** Missing or stale checks run against the working tree at completion, using explicit or discovered commands. Relevant checks with matching passing evidence may also run in a temporary worktree at the task's starting commit; that answer is cached by its inputs. These are ordinary project commands and can have their normal side effects. The baseline check isolates its checkout. `off` performs neither automatic execution path.

Override for a single session without touching the file:

```bash
EP_PROFILE=guide claude
EP_PROFILE=off claude
```

### Which one do you want?

**`strict`** if the repository has a real test suite and you want the gate to do its job. This is the intended mode.

**`guide`** if you want the information without the interruption — a good first week, and the right setting for a repository whose suite is slow or partial. You still see what the work would need; you are simply not stopped.

**`off`** for a repository with no tests, for exploratory work, or when you want evidence quietly accumulating without the runtime ever speaking. Everything is still recorded, so `ep_status` still works.

---

## `commands` — how your project actually runs its checks

Explicit commands are overrides for projects whose intended checks differ from the detected conventions.

Supported project manifests now supply conventional commands without this file. Use explicit commands for custom wrappers, unsupported build systems, or to override the detected choice.

With it, three things change:

1. **The runtime knows the suite exists**, even when nothing on disk looks like one.
2. **Hints name your real command** rather than a plausible-looking guess.
3. **The runtime discharges obligations by running the command itself** instead of interrupting to demand that the agent run it.

That third one is not a small convenience. It took live blocking from **75% of runs down to 12%** — the gate used to stop nearly every first attempt to finish, and nearly always on work that was already correct, because the agent had done the job and simply not shown it. Now the runtime goes and checks.

### Keys

Command keys match the obligation they satisfy:

| Key | Satisfies |
|---|---|
| `tests` | "the related test suite passes", "a test covering the change passes" |
| `typecheck` | "typecheck passes" |
| `build` | "the build succeeds" |
| `lint` | lint evidence; no standalone lint completion obligation currently exists |
| `benchmark` | "a benchmark supports the improvement" |

Declare only the overrides you need. Missing keys use discovery; an empty string disables discovery for that key.

### Examples

**Python, pytest:**
```json
{"commands": {"tests": "python -m pytest -q"}}
```

**Node, with a typechecker:**
```json
{"commands": {"tests": "npm test", "typecheck": "npm run typecheck", "build": "npm run build"}}
```

**Behind a Makefile — the case scanning cannot solve:**
```json
{"commands": {"tests": "make test", "build": "make"}}
```

**Quiet mode on a repository with no suite:**
```json
{"profile": "off"}
```

---

## What obligations each claim carries

Claims are inferred from your request by pattern matching — no model call, no added latency. Risk comes from the paths a task touches: anything under `auth/`, `payments/`, migrations, infrastructure or secrets is high risk and carries more. Everything else is scored by size.

| Claim | Low risk | High risk adds |
|---|---|---|
| `bug_fixed` | covering test passes, suite green | prior failure on record, stability over repeated runs |
| `feature_added` | suite green | covering test, typecheck, build |
| `refactor_safe` | suite green | typecheck, build |
| `migration_safe` | applies and reverts | suite green, stability |
| `perf_improved` | benchmark | suite green, stability |
| `deps_updated` | suite green | build, typecheck |
| `docs_changed` | nothing | nothing |
| `cannot_complete` | a reason and what was tried | evidence the blocker is real |

`cannot_complete` is a real outcome, not a failure. A system with no way to say *"this should not be done as asked"* reproduces the action bias that causes false completion in the first place.

---

## The four states

| State | Meaning |
|---|---|
| `VERIFIED` | every obligation met by fresh evidence |
| `UNVERIFIED` | an obligation has no evidence |
| `STALE` | evidence exists, but the files it observed have changed |
| `CONTRADICTED` | the latest evidence for something is failing |

A failure that was later fixed is *reproduction evidence*, not a contradiction — that is the point of asking for the failing test first. Only the most recent record per identity counts.

---

## Version control

**There is nothing to add to your `.gitignore`.** The runtime writes `.elevenpowers/.gitignore` containing `*` on every save, so git ignores the whole directory whatever your own rules say. The ledger holds your prompts, the commands that ran and a bounded amount of what they printed — machine state, and not something to put in a shared history.

`config.json` is the one file there worth committing: it is a statement about how your project is built, and everyone on the team benefits from it. To commit it and nothing else, edit the `.gitignore` the runtime wrote — a file already there is never overwritten:

```
*
!.gitignore
!config.json
```

Deleting that file instead of editing it does not work; the next save writes it back.

---

Questions, or a configuration case this does not cover? **[satyambcnrk@gmail.com](mailto:satyambcnrk@gmail.com)**


## Exact command receipts

Declared `tests`, `typecheck`, `build`, `lint`, and `benchmark` commands are recognized by exact match after trimming outer whitespace. `"tests": "npm run ci"` recognizes that project command even though its name does not contain `test`. This applies to any project or wrapper; no Snag-specific rule exists. Added arguments, aliases, prefixes and pipelines are not normalized into the declaration. Known-runner recognition still applies independently.

A completed zero exit produces a passing command receipt. Recognized failures override zero exits, including mixed runner output. A recognized zero-test summary does not establish that tests ran. An opaque successful wrapper remains an uncounted command receipt. Single-file commands retain their scope. Declarations express the project's claim about a command's purpose; they do not inspect shell-script behavior.

Timeouts, interruptions, unreadable hook results and automatic-verification launch failures produce incomplete receipts for declared commands. These supersede earlier success, do not count as reproduced failures, and require a completed rerun.

## Repository scan configuration

```json
{
  "profile": "guide",
  "commands": { "tests": "npm run ci" },
  "scan": {
    "max_files": 20000,
    "max_bytes": 134217728,
    "exclude": ["local-generated/", "fixtures/disposable-*.json"]
  }
}
```

Defaults are **20,000 selected files and 256 MiB**. The example sets a smaller explicit budget of 128 MiB. Limits must be positive integers and do not guarantee elapsed time. Exclusions use case-sensitive Python `fnmatch` patterns against relative paths with `/` separators; `*` may span separators, and a trailing `/` excludes directory contents. Exclude only inputs that should not invalidate verification.

Git selects tracked and non-ignored untracked source/dependency files, respecting nested ignores and negation. Tracked files remain eligible even when an ignore rule matches. Subprojects inherit repository ignores without scanning siblings. A directory itself ignored by its enclosing repository is an independent filesystem scope, supporting scratch projects.

Non-Git projects use standard generated-directory exclusions. Nested repositories are separate boundaries and symlinks are not followed. Selection uses the runtime's source extensions and named dependency files, not every arbitrary file on disk. Git ignores and explicit exclusions define the intended coverage boundary.

File/byte limits, unreadable inputs, unsafe symlinks, invalid settings and unavailable Git enumeration produce coverage diagnostics. Incomplete coverage cannot be fresh or silently establish verified completion. Correct the limitation and rerun the command. New source files also invalidate earlier empty snapshots.


## Automatic setup after loading the plugin

On Claude Code SessionStart, the plugin checks hook subscription consistency, project state writability, prior unreadable events, and availability on PATH of detected command runtimes. It reports the effective commands and source-selection coverage. This is a lightweight startup check, not a test-suite run or dependency installer. The full `ep_doctor --host` diagnostic remains available for deeper troubleshooting.

Command discovery reads only the selected project root:

| Project declaration | Automatic command |
|---|---|
| `package.json` script `ci`, otherwise `test` | `<manager> run ci` or `<manager> run test` |
| Scripts `typecheck`, `build`, `lint`, `benchmark` or `bench` | Corresponding package-manager script |
| `pytest.ini` or `[tool.pytest.ini_options]` | `python -m pytest` |
| `Cargo.toml` | `cargo test`, `cargo check`, `cargo build` |
| `go.mod` | `go test ./...`, `go build ./...` |

Package-manager selection prefers `packageManager`, then a unique recognized lockfile, then npm. Supported managers are npm, pnpm, yarn and bun. Conflicting lockfiles without an explicit manager do not produce a guessed Node command. Root package scripts take priority; another supported manifest can fill missing needs, such as pytest alongside a frontend-only build script. Conflicting native test stacks require a project-selected aggregate command.

Explicit `commands` values override discovery. Set `"commands": {"tests": ""}` to disable automatic selection for one need, or `"auto_detect": false` to use only explicit commands. Discovery does not create or rewrite `config.json`, and manifest changes are picked up on later hook invocations.

In `guide` and `strict`, missing or stale verification runs at completion. Identical commands serving multiple needs run once per discharge attempt. Old-tree checks require a relevant task obligation and matching passing evidence: passing tests alone cannot launch an unrelated benchmark. No dependency installation, deployment or background test watcher is added. In `off`, startup remains silent and passive, and verification commands are not automatically executed.

Source-observation and startup hooks allow up to 120 seconds, while prompt/edit guards retain 20 seconds. Stop retains its existing 600-second allowance. Extremely large or slow repositories may still need explicit limits or environment changes; incomplete coverage remains visible instead of being certified.

## Durable completion checks

Once the plugin is loaded, `guide` and `strict` use the durable runner automatically. No additional setup or daemon is needed. A completion attempt holds one project verification lock and shares a **480-second work deadline** across source snapshots, declared checks, baseline preparation/execution and targeted confirmation. Each command receives at most **300 seconds**, further limited by the remaining deadline. The Stop hook retains its 600-second host allowance; the difference reserves time for cleanup and reporting. Filesystem calls, Git metadata and final reporting are not a hard real-time guarantee.

Each check writes an incomplete receipt before launch and saves its outcome immediately on completion. The next completion reuses successful receipts only while their inputs and declarations still match. Incomplete, failed or stale checks can run again when required; queued checks that did not start are deferred. There is no background continuation after Stop exits, and a command that consistently needs over 300 seconds cannot finish through this automatic path.

Fresh content snapshots before and after execution prevent a command from certifying changed inputs. A changed command override also makes its declared receipt stale. Baseline checks freshly hash carried tests and retain only completed answers for unchanged inputs. Targeted confirmation uses the latest observed outcome for each named test; a later failure or interruption supersedes an earlier pass.

Use `ep_status` to inspect queued/running/passed/failed/stale/incomplete/deferred work. `.elevenpowers/verification.json` stores diagnostic progress; `ledger.json` stores evidence. Both remain project-local and ignored by Git. A concurrent completion reports that verification is already running. After owner death the OS releases the lock; status identifies interruption and the next completion reconsiders unfinished checks. A newer user task cannot be overwritten by the old verification owner.

The process runner cleans ordinary descendants after success, timeout and interruption. Windows uses a kill-on-close Job assigned before the command resumes. POSIX uses a process group; a deliberately escaping process or abrupt host SIGKILL is outside that cleanup guarantee. Combined stdout/stderr above **8 MiB** produces an explicit incomplete result. Capture is disk-spooled and may exceed the threshold between polls; this is not a disk quota or a security sandbox.

## Fresh staged health and local diagnostic history

`ep_ready.py HOST --project PATH` shares the portable exporter's fresh input view.
All effective declared commands need complete, passing, fresh receipts for the
verification stage. Native capture additionally requires receipt links to the
current wiring generation, task and startup session. Completion must follow the
latest relevant native work. Missing events and source-scan gaps stay explicit;
pipeline health and the four task verification states are separate.

Collection is automatic through trusted hooks and independent of the profile's
permission to execute checks. `off` remains passive. `integrations.json` retains
at most 32 timing samples per canonical phase and 64 receipt links; eviction is
reported. Session/task identities are hashed; no prompts, tool inputs, outputs
or source are added to this diagnostic history. It is local unsigned observation.
Rewiring/removal changes the generation and invalidates the old observations.

Readiness defaults to a cooperative 10-second read budget, adjustable with
`--seconds` up to 120. It executes no checks and writes no state. Raising this
read budget changes neither the completion runner's limits nor source scan
selection. Optional engine metadata distinguishes disabled, unavailable,
unsupported, unchecked custom interpreters and missing Node; package metadata
alone does not establish a working engine. No new configuration is required.

## Runtime identity and explicit validation

New disposable acceptance preparations and actual SessionStart observations
include a bounded content identity of shipped runtime code. Old unbound exercises
and observations from a different runtime cannot qualify the current release.
Prepare a new directory after updating the plugin. This needs no project-specific
policy or new configuration option. Native host trust/enablement still applies.

`ep_validate.py` accepts explicit time/repeat budgets. Performance reads and native
captures do not write project state or launch project tests. The optional installed
version probe executes only `--version`. Reporting/pilot options are operator
commands, not automatic startup or completion work.
