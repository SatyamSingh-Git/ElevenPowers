# Reliable Declared-Check Execution v1

Approved scope: the five-part proposal accepted on 2026-10-16. The goal is a
project-independent explicit entry point for exact configured checks, with real
child outcomes retained even when an agent wraps the entry point in shell text.

## Contract

`python plugin/bin/ep_check.py tests --project PATH` runs the effective `tests`
command; `--list` is read-only. Supported selectors are the existing declared
properties (`tests`, `build`, `typecheck`, `lint`, `benchmark`). Arbitrary command
text is not accepted. Default allowance is 120 seconds; finite positive values
up to 600 seconds are accepted. A run always executes rather than reusing an old
pass. Exit codes are 0 passed, 1 failed, 2 incomplete/refused, 130 interrupted.

Reuse `core.process`, `core.jobs.Session`, parsers, source snapshots, the ledger
and selected external input observations. No new dependency or shell parser.
The added behavior is explicit property selection plus durable exact-check
execution outside completion, with consistent before/after qualification.
Project commands are trusted execution chosen by the operator; this is not a
security sandbox or proof that a project's command is itself sound.

Persist an incomplete receipt before launch. Save actual exit status and parsed
evidence under the existing task. No task is invented as installed-host evidence.
All aliases of the same exact command receive normal declared aggregate receipts.
The outer host command must not overwrite the owned result or be reinterpreted
as that declaration. Empty/unknown selectors, passive `off`, unavailable inputs,
busy ownership and invalid budgets launch nothing. An empty standalone task is
allowed as an explicit local execution, without claiming native attribution.

Compare fresh source coverage, task, effective/raw configuration and producer
before/after every run, including projects without external declarations. External
qualification uses existing complete command scopes. Movement or incomplete
inspection prevents current passing evidence. Cancellation retains the provisional
receipt; safe caught failures retain a completed diagnostic outcome. Public output
contains redacted metadata and counts, no captured output or exception bodies.
Ordinary dirty/non-Git projects work under existing scan boundaries; PatchProof
keeps its separate committed-patch binding rules. Profiles retain their existing
automatic execution semantics. Read-only reports launch nothing.

## Delivery and evidence

First investigate the Windows 3.13 advice exercise failure from run 38623263659.
Its assertion retained no component diagnostics, so the cause remains unknown;
a local green retry is not a repair. Retain inspectable outcomes, reproduce the
actual failing boundary, and preserve conservative runtime behavior.

Implement the runner, CLI, and portable host startup/recheck guidance, then
qualify actual Python and Node pass/fail/timeout/repair commands, outer-shell
masking, drift, passive/busy/unknown refusal, alias handling and retained milestones.
No new paid or subscription session is authorized. Synthetic host controls and
model-free actual commands stay labeled separately from installed acceptance.

Finish with regression/audit/independent gates, four hosted OS/Python cells,
artifact acceptance, descriptive incremental pushes and normal main integration.
Update commands, platforms, configuration, milestones, PatchProof guidance,
README/status/master plan, research, dated validation, journey and all five
architecture views. A new independently graded coding-benefit comparison remains
a later milestone; this feature alone establishes command/evidence behavior.
