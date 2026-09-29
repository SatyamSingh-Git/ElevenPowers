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
[the delivery record](../docs/validation/2026-09-29-platforms.md) for contracts,
publication parts and measured limits.

Gemini's delivery made two host differences concrete: timeouts are milliseconds,
and a successful transport does not imply a process exit status is present.
Its adapter preserves structured status but leaves display-only results
incomplete. Background work and alternate execution directories cannot certify
the root. A configuration removal probe also caught a shared bug: another hook
inside the same group was removed with ours. Removal now works per handler and
the regression preserves the neighboring hook. The combined native/Claude group
passed 87 tests. Installed Gemini behavior remains an open acceptance check.

Cursor exposed a race that a synchronous-host mindset missed. Startup can finish
after another event has opened a new task, and saving the old startup ledger
overwrote that new task. A controlled interleaving reproduced it. Startup now
appends its note to the current ledger under the short write lock, a fix shared
by every host. Cursor abort/error events also bypass verification and ambiguous
workspace roots never select the first folder. The focused integration group
passed 212 tests. CI additionally exposed intermittent POSIX cleanup-probe
failures; later green runs are not enough to explain those and final integration
investigated them as described below.

Copilot completed the four additions. Its native camelCase input differs from
the compatible VS Code format; its tool transport can say success without
reporting the process exit status. The adapter keeps that observation incomplete.
Project hooks use direct executable arguments and native timeout seconds.
Cancelled agent completion never schedules checks. Prompt context and ordinary
final-report fields are not available in every host, so the guide describes
where the user must read persisted status.

The independent review reproduced four defects before final publication. Tool
delivery deduplication preceded receipt persistence, so a failed write consumed
the retry. The identity now commits atomically in the same ledger as the receipt;
two simultaneous deliveries also produce one observation. Windows argument
quoting did not protect a launcher inside `R&D`; project shell invocations now
encode literal arguments for PowerShell. Doctor checked the subscription suffix
without checking whether the launcher existed; it now checks both paths. Native
patch events could bypass verification in non-Git or already-dirty projects;
they now open a conservative claim and preserve an explicit attribution gap,
which keeps the task UNVERIFIED. Complete native patch attribution remains work
for real producer captures, not an invented path parser.

The Linux `/proc` diagnostic race was reproduced with a process vanishing between
the existence check and the read. The corrected probe recognizes that exit.
The separate intermittent five-second descendant-survival assertion has no
established runtime cause. Later green matrix runs do not establish its cause;
the validation record retains that open question.

The full local integration run passed 1,024 tests with 28 skips. The final focused
integration passed 210 tests. These are code/launcher results, not measurements
of improved patch quality or real installed-host sessions.

Final runtime CI `36530709458` passed all four Ubuntu/Windows and Python 3.11/3.13 jobs on `518411d`, including full suites, audit probes, grader controls and the Claude launcher seam. Exact counts and timings are in the validation record.
