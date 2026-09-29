# 49 — One engine, several hosts

2026-09-29. The user approved four additions to Claude Code: Codex, Gemini CLI,
Cursor and GitHub Copilot CLI, with eight pushes per platform. The shared engine
stays shared; host events and response fields become explicit adapters.

Codex is the first delivery. The extraction preserves Claude behavior while
collecting engine responses for native serialization. Setup merges owned hooks,
and bundles include the runtime instead of importing a sibling checkout that
would disappear when a host copied the plugin directory.

Three lifecycle probes were consequential. A repeated successful tool event
after an edit could create a fresh-looking receipt for old output. A generated
continuation prompt could reset the task's retry count. A tool running in a
different directory could attach a success to the wrong project. Each probe
failed before the correction and passed afterward.

The distinction between tool transport and command status stays explicit. A
host handing us output successfully does not establish the command's exit code.
Unknown outcomes remain incomplete and the shared runner can obtain independent
evidence by executing declared checks. Schema fixtures and launcher subprocesses
are useful checks, but neither is a real installed-session observation.

See [platform installation](../the-guide/platforms.md) and
[the delivery record](../docs/validation/2026-09-29-platforms.md). Subsequent
platform sections will record their own contracts and measured limits.

Gemini's delivery made two host differences concrete: timeouts are milliseconds,
and a successful transport does not imply a process exit status is present.
Its adapter preserves structured status but leaves display-only results
incomplete. Background work and alternate execution directories cannot certify
the root. A configuration removal probe also caught a shared bug: another hook
inside the same group was removed with ours. Removal now works per handler and
the regression preserves the neighboring hook. The combined native/Claude group
passed 87 tests. Installed Gemini behavior remains an open acceptance check.
