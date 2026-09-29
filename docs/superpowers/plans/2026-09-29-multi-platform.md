# Multi-platform implementation plan

> Execute with superpowers:executing-plans in this session. The user approved the
> design and explicitly requested immediate implementation, with eight pushes
> per new platform. Preserve that authorization rather than adding another gate.

**Goal:** Deliver automatic ElevenPowers integration for Codex, Gemini CLI,
Cursor Agent and GitHub Copilot CLI while preserving Claude Code.

**Architecture:** Pure host adapters normalize lifecycle, root, tools and
outcomes. A transport boundary carries engine responses into native serializers.
Shared setup, packaging and doctor helpers consume each adapter's definitions.

**Tech stack:** Python 3.11+ standard library runtime, pytest, native JSON hooks.

**Spec:** [Approved design](../specs/2026-09-29-multi-platform-design.md).

## Global constraints

- Thirty-two substantive pushes, eight per platform, on the authorized main delivery branch.
- No paid agent experiments or changes to Snag; live validation remains separately labeled.
- Off stays passive. Unknown outcome never becomes success or reproduced failure.
- Retain 480-second work budget and 600-second completion allowance; convert native units.
- Preserve unrelated configuration, normal host trust and existing Claude entry points.
- Update guides, status, validation, journey and rendered architecture at each platform boundary.

## Interfaces and files

`core/hosts/contract.py`: `Event(phase, payload, root)` and `Outcome(output,
exit_code, state)`; explicit root validation and normalized outcomes.
`core/hosts/{codex,gemini,cursor,copilot}.py`: `normalize(event, payload) -> Event`,
`outcome(payload) -> Outcome`, `render(event, messages, code, error) -> dict`,
and native event subscriptions. Adapter functions do no project writes.
`core/hosts/bridge.py`: `run(platform, event, payload) -> (dict, int)`; invokes
existing engine handlers with a collected response, never inventing receipts.
`core/hook.py`: reusable `dispatch` and response collector; default Claude stdout
and stderr behavior preserved.
`core/hosts/wiring.py`: `configuration(platform, command) -> dict` generated
from adapter event definitions. `core/hosts/package.py`: self-contained native
bundle, including runtime, without copying local project state.
`core/hosts/setup.py`: `install(platform, project, python, source)` and `remove`
merge owned configuration entries atomically. `core/hosts/doctor.py`: configuration
and contract diagnostics with explicit evidence level.
`plugin/bin/ep_host.py`, `ep_setup.py`: public launchers.

## Review focus

1. Resumed/asynchronous startup must not erase an active task (parts 7, 15, 23, 31).
2. Continuation prompts must not reset bounded completion retries (same parts).
3. Windows quoting and paths with spaces must launch the intended interpreter (parts 5, 13, 21, 29).
4. Conflicting roots and symlinked config must not cause writes to another project (setup and hardening parts).
5. A completed tool transport with missing process status must remain incomplete (parts 2, 10, 18, 26).

## Test and publication cycle

Each code part first adds its behavioral tests and runs them to establish the
missing behavior, then implements the smallest change and runs the focused group.
Commit only a passing deliverable; push it separately with part number, behavior,
validation and remaining boundary in the commit body. Use `.venv/Scripts/python.exe
-m pytest` and a unique `.venv` basetemp. No full-suite repetition per small part.

Canonical adapter contract example (parameterized for all shipped adapters):

```python
event = adapter.normalize(native_event, {"cwd": str(project), **input_fields})
assert event.root == project.resolve()
assert event.phase == "PostToolUse"
assert adapter.outcome(result_with_exit_1).state == "failed"
assert adapter.outcome(result_without_status).state == "unknown"
```

Configuration preservation example:

```python
before = {"hooks": {"SomeOtherEvent": [{"command": "existing"}]}}
write_config(before)
install(platform, project, sys.executable, checkout)
first = config_path.read_bytes()
install(platform, project, sys.executable, checkout)
assert config_path.read_bytes() == first
remove(platform, project)
assert read_config() == before
```

## Tasks / pushes

Each row is an independent testable publication boundary. Tests live in
`tests/test_host_<platform>.py`, shared contract/setup/bundle/bridge tests in
`tests/test_hosts.py`, `tests/test_host_setup.py`, `tests/test_host_packages.py`.

| Part | Deliverable | Required behavioral check |
|---|---|---|
| 1 | Codex event/root contract and shared types | explicit cwd, missing cwd, unknown event, apply_patch identity |
| 2 | Codex command outcomes | numeric success/failure, still-running result, malformed status, cancellation |
| 3 | Codex response transport + shared bridge | one native JSON object, permission ask, Stop continuation, Claude unchanged |
| 4 | Codex generated hooks + portable package | all handled events subscribed, timeouts, bundle imports runtime independently |
| 5 | Codex project setup/removal | idempotence, unrelated entries, invalid config, quoted paths |
| 6 | Codex doctor + launcher | disposable project lifecycle, checks labeled replay, source availability |
| 7 | Codex lifecycle hardening | task/retry preservation, unknown result receipt, changed source invalidation |
| 8 | Codex documentation | guide, status, journey, validation and all four architecture views |
| 9 | Gemini events/root mapping | BeforeAgent and AfterAgent, shell/read/edit names, explicit cwd |
| 10 | Gemini outcomes | llmContent envelope, error, unknown exit status, interruption |
| 11 | Gemini native responses | additionalContext, deny retry, no unsupported ask/Claude fields |
| 12 | Gemini subscriptions + extension bundle | milliseconds, extension manifest, complete runtime |
| 13 | Gemini setup/removal | settings preserved, idempotence, quoted paths |
| 14 | Gemini doctor + launcher | native events through process, declared receipt, honest evidence level |
| 15 | Gemini lifecycle hardening | retry task ownership, missing startup, command failure and cancellation |
| 16 | Gemini documentation | guides, status, journey, validation, rendered architecture |
| 17 | Cursor event/root mapping | explicit cwd, unique workspace, ambiguous roots, file edits |
| 18 | Cursor outcomes | JSON tool_output, error versus interrupted, unknown/truncated output |
| 19 | Cursor native responses | permission deny when ask unavailable, context, bounded normal-stop followup |
| 20 | Cursor subscriptions + package | generic tool events, complete command wiring, loop limit |
| 21 | Cursor setup/removal | versioned hooks.json preservation, invalid version, quoted paths |
| 22 | Cursor doctor + launcher | startup, native Shell response, file activity, completion |
| 23 | Cursor lifecycle hardening | asynchronous startup, aborted Stop, multi-root isolation |
| 24 | Cursor documentation | guides, status, journey, validation, rendered architecture |
| 25 | Copilot native events/root mapping | camelCase input, toolArgs object/string, absent final message |
| 26 | Copilot outcomes | success transport without process exit, failure/error, incomplete output |
| 27 | Copilot native responses | permissionDecision, additionalContext, agentStop continuation |
| 28 | Copilot hooks + package | native event set, timeoutSec, complete runtime |
| 29 | Copilot setup/removal | .github/hooks entries, unrelated config preserved, quoted paths |
| 30 | Copilot doctor + launcher | native lifecycle, receipts, honest live-session boundary |
| 31 | Copilot/integration hardening | bounded retries, unknown evidence, final independent review corrections |
| 32 | Final documentation | all five platforms, journey, status, validation, full matrix and rendered architecture |

## Validation boundary

At each platform boundary run all adapter/shared integration tests and relevant
Claude regression tests. Run the complete suite at the final integration boundary;
CI covers Ubuntu/Windows with Python 3.11/3.13. Inspect all failures and fix their
causes. Run `python architecture/check.py --render` after graph updates. Dispatch
one fresh independent final review of spec, implementation and validation limits.
Record actual host versions/captures separately from documented schema fixtures.

## Execution record

- Base: `086e90c`. Native execution authorized by the user's immediate-build instruction.
- Preflight: all adapters consume Event/Outcome and engine response collection;
  setup, bundle and doctor consume generated configuration. Keep these interfaces
  shared and add host details only in adapter modules.
- Ruling: eight pushes means eight per new platform, replacing four per platform;
  thirty-two total. Cost if misunderstood: finer publication granularity only.
