# Portable repository evidence validation - 2026-09-28

Follow-up: [automatic setup validation](2026-09-29-automatic-setup.md) records manifest discovery and the new 256 MiB default. The 64 MiB measurements below describe the original delivery.


This delivery implements repository-aware scanning and declared-command receipts in the shared runtime. No Snag-specific path, project name or command rule is embedded in the implementation.

## Delivered behavior

- Git selects tracked and non-ignored untracked inputs, including inherited ignores in subprojects. Nested repositories remain separate.
- File/byte budgets, project exclusions and explicit coverage diagnostics travel into evidence freshness and reports. Partial scans cannot establish fresh evidence.
- Exact project declarations recognize opaque wrappers for tests, typecheck, build, lint and benchmark.
- Declared commands retain completed success, completed failure and incomplete execution. Known summary failures override zero exits across mixed runners.
- Existing receipt identities and single-file scope remain compatible. Incomplete attempts cannot prove reproduced failures or pre-existing breakage.

## Validation

Full suite: **831 passed, 26 skipped** in 236.14 seconds. Final follow-up changes to workspace-prefix parsing and incomplete/failure transitions were then checked with **137 passing tests** across repository scanning, declared commands, core verdicts, intermittency and scope. The full suite was not repeated after those focused changes. Earlier focused checks passed 41 and 119 tests respectively.

The existing runner acceptance/rejection table now runs both with and without declarations. Review reproductions cover mixed Cargo/TAP output, decorated pytest errors, inherited ignores, saved receipt compatibility, single-file scope, and interruption followed by success.

Architecture validation: `python architecture/check.py --render` passed; all four tabs rendered. The development virtual environment supplied pytest and Playwright; no runtime dependency was added.

## Snag compatibility check

Read-only inspection of `E:/snag` found that default Git-aware selection reaches the 64 MiB byte limit at a tracked test-data JSON input. That is now explicitly incomplete, rather than silently treated as verified. Raising the scan budget in memory produced a complete snapshot of **4,418 selected files, about 78.05 MiB**. A 128 MiB configured budget is sufficient for the measured checkout; future repository growth can change this.

A real run of `node --test scripts/lib/analytics-freshness-health.test.mjs` passed **19 tests**. Replaying its real output through the parser with an in-memory `tests: npm run ci` declaration and 128 MiB budget produced a fresh, complete, passing suite receipt with 19 passes and zero failures. This verifies recognition of real output under the declared wrapper, not execution of the complete `npm run ci` pipeline.

One cold snapshot took 54.44 seconds during concurrent testing; a warm snapshot took 1.72 seconds, and the parser replay took 2.09 seconds. These are observations, not latency guarantees. File and byte budgets do not impose a wall-clock deadline on enumeration or hashing.

Snag was not modified and the plugin was not installed there. Claude Code was available, but an installed end-to-end hook session and full Snag CI remain unverified. The supported host remains Claude Code; this work does not add a Codex hook adapter. The evidence supports a configured integration trial, not an unconditional production-readiness claim.

## Delivery sequence

The user requested ten distinct pushes, with documentation last. Pushes 1-8 introduced Git selection, scan diagnostics, coverage-aware freshness, scan configuration, declared recognition, hook interruption receipts, automatic-verification incomplete outcomes, and mixed summary handling. Push 9 contains the review corrections and regression expansion. Push 10 updates this report, configuration guidance, README and the architecture views.
