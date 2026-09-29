# Native platforms

ElevenPowers uses one repository/evidence engine with native host adapters.
Claude Code retains its existing installation. Codex has a native adapter,
project setup and portable bundle. Gemini CLI also has its native adapter and
extension package. Cursor Agent has a native adapter and plugin bundle.
GitHub Copilot CLI is the remaining approved delivery target.

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
certify that root. Patch file paths are reconciled through Git at completion.

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
