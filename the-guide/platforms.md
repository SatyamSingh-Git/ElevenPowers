# Native platforms

Optional milestone advice now has [read-only delivery observations](advice-delivery.md)
across all five host launchers. Successful context emission and subsequent native
checks remain separate from model comprehension and installed-session acceptance.

Optional changed-file test strength uses one backend across all five platforms.
The shared completion handler considers it after ordinary verification and
confirmation; host choice does not change operators, isolation, limits or report
format. Native live acceptance remains a separate readiness requirement. Passing
mutation fixtures does not establish native delivery in an installed host.

ElevenPowers uses one repository/evidence engine with native host adapters.
Claude Code retains its existing installation. Codex, Gemini CLI, Cursor Agent
and GitHub Copilot CLI have native adapters, reversible project setup,
configuration diagnostics and self-contained bundles. The four new integrations
have documented-contract and launcher checks; live installed sessions remain an
acceptance step. This distinction applies to every platform below.

All five ingress paths share [declared-command capture](command-capture.md),
including qualified literal project-directory wrappers and explicit failure or
incomplete outcomes. Contract and replay checks do not establish fresh installed
acceptance; actual host delivery remains separately qualified.

## Unified project readiness

All five hosts use `ep_setup.py HOST --project PATH` and the read-only
`ep_ready.py HOST --project PATH [--json]`. Claude project setup merges
`.claude/settings.local.json`; its plugin installation remains an alternative.
Omitting the setup host selects only a single available executable and refuses
ambiguity. Settings, commands and scan budgets belong to each project; no runtime
rule depends on an acceptance repository or its command names.

Setup validates native wiring, including delivery matchers, interpreter and
launcher. Activation records waiting, received, active startup, error, changed
configuration and removal separately. Only launcher ingress updates observations;
doctor replay does not. These records diagnose delivery rather than authenticate
the caller. The readiness report includes discovered commands, missing runtimes,
selection coverage, latest execution (freshness unchecked) and next actions.

On 2026-10-01, an installed Claude Code 2.1.281 startup in Snag delivered a real
SessionStart callback with no prompt/model call. Codex wiring there is configured
and waiting. Snag's actual external `npm run ci` failed its dependency audit,
passing 14 of 15 checks; explicit replay recorded that result as complete/fail.
That relay is separate from an installed-host command capture. The four added
hosts still require versioned live-session acceptance. See
[onboarding validation](../docs/validation/2026-10-01-live-onboarding.md).

Every integration shares the same portable report entry point:
`python plugin/bin/ep_report.py --project PATH --output report.md`.
The checkout and generated bundles contain it. Exporting receipts works without
an active host session; that does not establish native callback delivery. See
[report commands](commands.md#ep_report--evidence-to-share-with-a-reviewer).

## Codex

Use Python 3.11 or newer. From your ElevenPowers checkout, install project hooks:

```sh
python plugin/bin/ep_setup.py codex --project /absolute/path/to/project
python plugin/bin/ep_doctor.py --platform codex --cwd /absolute/path/to/project
```

Setup writes `.codex/hooks.json`, preserving unrelated entries. It records the
interpreter and checkout's absolute launcher path; keep that checkout available.
Rerunning setup updates owned entries without duplicating them. Review and trust
the hooks in Codex and start a new session. Setup does not change host trust or
enable hooks disabled by user/administrator policy.

After loading, startup reports coverage and discovered commands. Supported tool
events record evidence and completion runs missing checks in guide/strict mode.
Off stays passive. Unknown/unfinished command results stay incomplete; the
automatic runner can still execute the declared check to obtain a known status.
An explicit execution directory different from the event's project root cannot
certify that root. Native apply_patch input uses the documented
`tool_input.command` envelope. Supported headers identify targets; bounded content
comparisons before and after the same session/call/input attribute changes,
including already-dirty and non-Git files, additions, deletions and moves.
Result prose is not parsed for edited paths. This covers declared targets, not
unrelated tool side effects or which concurrent actor wrote those bytes.

Missing session/call identity, missing or expired baselines, unsafe paths,
different execution directories, interruption and budget exhaustion remain
UNVERIFIED. Pending calls are visible in status/readiness; completion reconciles
missing post-events and preserves evicted uncertainty. Bounds are 128 targets,
32 MiB per content snapshot, 128 pending calls, 256 completed observations and
30-minute baseline expiry. Pre/post snapshots have a two-second cooperative
deadline; reconciliation shares three seconds. Filesystem operations are not a
hard wall-clock guarantee. Unsupported host input envelopes remain gaps.

For a portable plugin with its own runtime:

```sh
python -m core.hosts.package codex /absolute/output/elevenpowers
```

Use a new destination. The bundle contains `.codex-plugin/plugin.json`, native
hooks, launchers and `core/`. Install it through your Codex plugin/marketplace
workflow and trust its hooks. Choose either native bundle installation or
project hooks for a project to avoid duplicate delivery. The bundle uses
`python` from the host PATH; it must resolve Python 3.11+. The generated project
configuration uses the interpreter that ran setup.
On Windows, project command hooks use PowerShell's encoded invocation to preserve
literal paths; Copilot uses direct executable arguments. The doctor checks that
the configured interpreter and launcher still exist. Rerun setup after moving
the checkout or changing interpreters.

Remove only the project integration:

```sh
python plugin/bin/ep_setup.py codex --project /absolute/path/to/project --remove
```

## What has been verified

Codex schema contracts, generated configuration, configuration preservation,
bundle manifest validation and real launcher subprocesses have been checked.
The locally available CLI reports `0.158.0-alpha.2.1`; its version/help commands
were executed. No paid agent call or live installed Codex session was run.
Structured exit statuses are supported; model-facing result prose without a
validated status contract remains unknown. A configuration doctor pass does not
prove the host has enabled/trusted hooks or delivered a live event.

Completion keeps the shared 480-second work budget inside a 600-second hook
allowance. Delivery identity history retains the latest 2,048 completed tools;
continuation recognition retains at most 100 pending sessions. These are
diagnostic/coordination limits, not evidence of command success.

See [official Codex hooks](https://learn.chatgpt.com/docs/hooks) and the
[dated validation](../docs/validation/2026-09-29-platforms.md).

## Gemini CLI

```sh
python plugin/bin/ep_setup.py gemini --project /absolute/path/to/project
python plugin/bin/ep_doctor.py --platform gemini --cwd /absolute/path/to/project
python -m core.hosts.package gemini /absolute/output/elevenpowers
```

Project setup merges `.gemini/settings.json` without replacing model settings or
other hooks. The alternative portable extension contains `gemini-extension.json`
and `hooks/hooks.json`; link/install it through Gemini's normal extension flow.
Use one installation route per project, then enable/trust it and restart the
session. Remove project hooks with `ep_setup.py gemini --project PATH --remove`.

Native BeforeAgent/AfterAgent events drive task opening and completion; shell,
read, write and replace tools feed shared evidence/scope handling. Hook timeout
values are converted to milliseconds. An unsupported approval request becomes
an explained denial so the user can review the operation; it is never converted
to approval. Background commands and `dir_path` values targeting a different
directory cannot certify the project root.

Structured status, including nested `data.exitCode`, can distinguish success
and failure. Gemini output envelopes without a structured status remain
incomplete; display text alone is not proof. The upstream shell source was
reviewed, but a live Gemini CLI session was not run. In guide/strict, the shared
automatic runner can execute missing declared commands to collect explicit
status. The doctor reports this limitation separately from configuration health.
See [Gemini hooks](https://geminicli.com/docs/hooks/reference/) and
[extension packaging](https://geminicli.com/docs/extensions/reference/).

## Cursor Agent

```sh
python plugin/bin/ep_setup.py cursor --project /absolute/path/to/project
python plugin/bin/ep_doctor.py --platform cursor --cwd /absolute/path/to/project
python -m core.hosts.package cursor /absolute/output/elevenpowers
```

Project setup merges version 1 `.cursor/hooks.json`. The alternative bundle uses
`.cursor-plugin/plugin.json` and includes its runtime. Enable it through Cursor's
normal trusted-project/plugin flow. Use one route per project. Remove project
hooks with `ep_setup.py cursor --project PATH --remove`.

Generic tool hooks capture Shell/read/write activity. Explicit structured exit
codes, including JSON-encoded tool output, determine command outcomes. Unknown
output and permission denial remain incomplete. Multiple workspace roots need
an explicit `cwd`; a `cwd` outside the declared workspaces is rejected.

Startup is asynchronous in Cursor, so the shared startup diagnostic append now
loads the current task under its write lock. An old startup cannot overwrite a
new prompt. Aborted/error completion skips automatic verification. Normal Stop
uses at most two follow-ups in strict mode. Cursor does not provide an ordinary
Stop report field: use `python plugin/bin/ep_status.py --cwd PATH` to inspect the
persisted verdict. Prompt/pre-tool informational context also has narrower
support than Claude; unsupported fields are omitted. An unenforced native ask
becomes an explained denial, never an automatic approval.

This delivery targets Cursor Agent's documented desktop interface. Cursor CLI,
cloud agents and a live installed desktop session are not certified by these
launcher fixtures. See [Cursor hooks](https://prod.cursor.com/docs/hooks) and
[plugin reference](https://prod.cursor.com/docs/reference/plugins).

## GitHub Copilot CLI

```sh
python plugin/bin/ep_setup.py copilot --project /absolute/path/to/project
python plugin/bin/ep_doctor.py --platform copilot --cwd /absolute/path/to/project
python -m core.hosts.package copilot /absolute/output/elevenpowers
```

Project setup merges `.github/hooks/elevenpowers.json`. Native camelCase events
map to the shared lifecycle, and direct `exec`/`args` subscriptions preserve paths
with spaces without a shell. The alternate portable plugin uses legacy root
`plugin.json` and `hooks/hooks.json`, with the runtime included. Install through
Copilot's plugin flow, review trust/enablement and begin a new session. Use one
installation route per project. Remove project hooks with
`ep_setup.py copilot --project PATH --remove`.

`resultType: success` describes tool transport, not the child process exit code.
Without an explicit numeric process status, the observation stays incomplete;
guide/strict can run missing declared checks independently. Cancelled agent
completion does not start verification. `agentStop` can request a bounded retry,
but has no ordinary final-report field; use `ep_status.py --cwd PATH`. Copilot
ignores extra context from command-based prompt hooks, so context is delivered
only on supported session/tool surfaces. Native patches have the attribution
limitation described under Codex.

This adapter targets local Copilot CLI. It does not certify VS Code, the cloud
agent, or every installed CLI version. See the [official hook reference](https://docs.github.com/en/copilot/reference/hooks-reference)
and [plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference).

## Automatic behavior and remaining acceptance

Once hooks are installed, enabled and trusted, supported lifecycle events invoke
startup health, manifest command discovery, observation and completion checks
automatically. Setup cannot bypass host trust or administrator policy. A doctor
pass establishes project configuration and local path availability, not live
delivery. Bundles require `python` 3.11+ on the host PATH and native plugin-root
resolution. These environment assumptions still need an installed-session check.

All five hosts share staged fresh health, bounded callback timing/receipt history
and one disposable acceptance workflow. Prepare a new directory with
`ep_doctor.py --prepare-acceptance NEW_DIR --platform HOST --language python
--host-version INSTALLED_VERSION`, or choose `javascript` with Node on PATH.
Follow `EXERCISE.md` in one trusted native session, then inspect with
`ep_doctor.py --acceptance DIR --platform HOST --json`. Preparation and replay
do not establish activation or acceptance. Missing/evicted history, changed
contracts and stale inputs remain waiting or incomplete.

Ten actual Python/Node producer cases pass through the five launcher contracts,
including real process interruption and stale/rerun controls. These are contract
checks, not installed agent sessions. Local version probes on 2026-10-01 found
Claude Code 2.1.286 and Codex CLI 0.159.2; Gemini, Cursor and Copilot executables
were unavailable. Full versioned native exercises remain acceptance work.
Host trust/policy and each platform's capability limits still apply.
See [project-health validation](../docs/validation/2026-10-01-project-health.md).

## Versioned compatibility captures

All five adapters share bounded shipped-code identity, explicit installed-version
probes, whitelisted acceptance captures and a ten-cell host/language matrix.
These are unsigned local dated observations; a saved passed cell does not
authenticate a host or certify a later release. Duplicate and mismatched captures
stay incomplete; absent sessions stay waiting. New runtime code needs a new
exercise. See [native validation](../docs/validation/2026-10-02-native-validation.md).

The October 2 installed probes observed Codex 0.159.2 and Claude Code 2.1.286.
Complete acceptance is still 0/10: native trust/activation and Claude subscription
capacity remain gaps, and three other hosts were unavailable. The subscription
pilot preserves all eight inconclusive records. Codex automatic approval review
permits ordinary workspace commands but does not bypass native hook trust.
Claude project setup writes local settings, so a restricted launch must include
`--setting-sources project,local` to load them.


### Native trust and actual delivery are separate

The later October 2 Claude Code 2.1.287 session processed startup/edit/exact
failing and passing commands/completion with fresh pipeline health. Its full
exercise remains waiting for an intentional incomplete receipt. A subsequent
eight-run subscription comparison delivered native treatment callbacks and
preserves proposed/final candidates; it found extra receipt coverage and tied
behavioral correctness. This does not qualify other hosts or full acceptance.
See [controlled completion validation](../docs/validation/2026-10-02-proof-of-benefit.md).

The installed Codex 0.159.2 UI showed five owned exercise hooks awaiting review.
Normal review and trust changed its table to active subscriptions. A bounded
subsequent subscription session repaired the exercise's boundary and ran its
original failure/passing check, but no callback was recorded. The acceptance
therefore remains waiting, including its intentionally incomplete interruption
step. Trust-table metadata is not callback delivery or a passed acceptance cell.
Keep configuration/startup/edit/command/completion stages separate when reporting
a platform as usable. Ordinary native enablement still belongs to the host.
