# Automatic setup validation - 2026-09-29

Follow-up to the portable evidence delivery: loading ElevenPowers in Claude Code now activates manifest-backed command discovery, startup diagnostics and repository coverage reporting without a generated project configuration file.

## Changes

- Root package scripts supply ci/test, typecheck, build, lint and benchmark commands using the declared package manager or an unambiguous lockfile.
- Conventional pytest, Cargo and Go declarations fill missing needs. Mixed native test stacks require an explicit aggregate command. Explicit values override discovery; empty values disable individual needs; auto_detect false disables discovery.
- Startup checks hook subscriptions, state writability, prior unreadable host events and availability of detected command executables. It reports selected commands and source coverage, without running the suite at startup.
- Defaults permit 20,000 selected files and 256 MiB. Startup and observation hooks allow 120 seconds for cold selection/fingerprinting; prompt/edit guards stay at 20 seconds.
- Missing verification runs at completion in guide/strict. Shared commands are deduplicated per discharge. Baseline checks require a relevant task obligation and matching passing evidence, so a passing test cannot trigger an unrelated benchmark or build.
- Passive mode stays silent and does not run automatic checks. No environment dependency installer or background watcher was added.

## Executed checks

The initial automatic-setup regression cases failed before implementation (11 failures), and the first combined feature/configuration/wiring check passed 104 tests. Additional review findings were reproduced before their fixes: mixed frontend/backend discovery, unrelated baseline commands and TAP output counted as Go packages. Automatic/stress/verification checks passed 63 tests; the automatic/recovery selection passed 34 tests. Final push checks passed **103 command/parser/stress/verification/recovery tests** and **63 startup/scanning/wiring/hook tests**.

A disposable Node project under the ignored development environment was driven through the real plugin launcher. SessionStart reported activation. Stop automatically ran its package.json ci script, saved one passing test receipt with complete coverage, and exited successfully. No .elevenpowers/config.json was created. This exercises the shipped launcher and command execution; it is not a live Claude Code host session.

Read-only selection in E:/snag automatically discovered npm run ci, npm run typecheck, npm run build and npm run lint. Default coverage was complete: 4,418 files, 81,841,401 bytes, no diagnostics, about 1.11 seconds for selection. No in-memory configuration override was used, and no Snag file was edited. The complete Snag CI and installed host session remain unexecuted.

The final broad regression run completed with 857 passes, 26 skips and one failure in a baseline-cache fixture that omitted the now-required active task claim. Adding that claim preserved the cache test's intent; the corrected case passed in the 34-test automatic/recovery run. The earlier broad run also exposed a timeout-policy assertion, which was updated to distinguish scan hooks from prompt/edit guards. No full run was repeated after the final fixture-only correction.

The updated architecture check passed with all four tabs rendering. Earlier validation's 64 MiB limit is historical; the new default removes that setup step for the measured Snag checkout. Byte/file limits are not wall-clock guarantees, and unknown project conventions still require an explicit command.

## Publishing

Three pushes requested: (1) command discovery and execution controls with regression tests; (2) automatic startup, larger bounded scans and observation allowances; (3) final documentation, validation record and architecture views.
