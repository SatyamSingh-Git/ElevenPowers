# Current delivery status

Reviewed **2026-09-29**, through Codex runtime part `98295a9`. ElevenPowers remains a research prototype, with Claude Code integration and a new Codex adapter. This page tracks product delivery; it does not replace the historical research results or claim an improvement in patch quality.

## Shipped and exercised

| Capability | Delivered behavior | Evidence boundary |
|---|---|---|
| Repository selection | Git-aware tracked/untracked inputs, inherited ignores, nested repository boundaries, configurable exclusions | Uses supported source extensions and named dependency files; excluded inputs are outside the fingerprint |
| Scan coverage | Explicit diagnostics for budgets, unsafe inputs and unreadable files; incomplete coverage prevents freshness | Defaults: 20,000 selected files and 256 MiB; these are not wall-clock guarantees |
| Command receipts | Exact configured/discovered commands; completed pass, completed fail and incomplete execution | Known summary failures override exit zero; opaque wrappers retain uncounted command-level evidence |
| Automatic setup | Root manifest discovery, startup health and coverage summary, no generated configuration file | Supported conventions: Node scripts/managers, pytest configuration, Cargo and Go; ambiguous/custom setups need overrides |
| Completion checks | Missing or stale verification in guide/strict; identical commands deduplicated per attempt | Baseline execution requires a relevant obligation and matching passing evidence; off remains passive |
| Durable runner | Project lock and journal; immediate per-check receipts; 480-second shared work deadline; 300-second command cap; fresh before/after input binding | Synchronous; next completion retries unfinished work; filesystem/cleanup/reporting prevent a hard real-time guarantee |
| Process lifecycle | Windows Job containment and POSIX process-group cleanup; 8 MiB combined capture limit | Deliberate POSIX group escape and abrupt SIGKILL are outside cleanup guarantees |
| Progress and ownership | Status/report surfaces show running, deferred and interrupted work; serialized ledger writes protect newer tasks | The journal is diagnostic state, never proof; a live installed session remains a separate acceptance check |
| Compatibility | Historical receipt identities and single-file scope preserved | An interruption cannot stand in for a reproduced failure |

The initial portable-evidence delivery used ten pushes ending at `f432658`. Automatic setup used three more: `2636ded`, `fc527d9`, and `a548d03`. Each commit carries its implementation and validation details. The durable-runner delivery uses six further parts; see [its validation record](validation/2026-09-29-durable-runner.md).

## What the checks established

The portable-evidence full run passed **831 tests with 26 skips**; final follow-up checks passed 137 relevant tests. The automatic-setup broad run passed **857 tests with 26 skips and one outdated baseline-cache fixture failure**. The fixture was updated to supply an active task claim and passed in focused checks. Final publication checks passed **103 command/execution tests** and **63 startup/scanning/hook tests**. No full run was repeated after that fixture-only correction. These counts describe specific runs, not a promise about today's collection size.

A disposable Node project was exercised through the shipped launcher: SessionStart reported activation; Stop discovered and executed `npm run ci`, recorded exactly one passing test, and created no config file. Architecture validation rendered all four views.

The durable-runner integration run passed 914 local tests with 26 skips and exposed one legacy per-test receipt compatibility failure. That regression was fixed and the final focused runner/stress/launcher checks passed 69 tests. Remote CI also exposed ignored B8 input data and a Python 3.11-only test-helper incompatibility, both corrected in the final code part. The final code-head [CI matrix](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/36523624912) passed on Ubuntu and Windows with Python 3.11 and 3.13: 916 passed / 31 skipped on each Ubuntu job and 919 passed / 28 skipped on each Windows job. Separate audit checks passed 102 / 2 skipped on Ubuntu and 104 on Windows.

Read-only Snag selection discovered its verification scripts automatically and covered **4,418 files / 81,841,401 bytes** using defaults in about **1.11 seconds**. That timing is source selection, not a complete fingerprint or full CI. Earlier evidence included a real 19-test Node sample and parser replay. Snag was not edited or configured by these checks. A later fresh, complete content fingerprint covered the same 4,418 files / 81,841,401 bytes with no coverage issues in **55.66 seconds**. Selection time and full fingerprint time are different measurements.

See the [validation index](validation/README.md) for the detailed records and qualifications.

## Next product milestone

**ElevenPowers works comfortably in an installed Snag session.** Generalized implementation is shipped; the installed integration remains open. Acceptance requires:

1. The current plugin loads in Claude Code with the intended project root and usable project environment.
2. The full `npm run ci` completes and produces a receipt through real host events; failures and interruption remain distinguishable.
3. Editing a selected input invalidates prior evidence, while excluded generated noise does not.
4. Startup, evidence capture and completion latency are measured during ordinary work.
5. Remaining environment or coverage limits are visible and actionable.

A full Snag CI run and live installed-plugin session have **not** been performed. Per-test dependency invalidation, mutation-based runtime coverage and improved patch-outcome claims remain outside this delivery. Codex adapter implementation is recorded below; live installation remains unverified.

## Delivery cadence

Use a concrete project milestone, focused regression checks for changed behavior, and an integration check at the delivery boundary. Broaden or repeat tests when new changes or failures warrant it. Keep historical experiments separate from readiness evidence, and update the guide, status, journey and architecture when their claims change.

## Native platform expansion

Codex adapter, native response transport, generated wiring, portable packaging, project setup and configuration doctor are implemented. Sixty focused native/Claude checks passed. Live installed Codex and Snag sessions remain unverified. Gemini CLI is implemented with native extension packaging, reversible settings setup and explicit outcome limits; 87 combined checks passed. Cursor is implemented, with 212 combined native/Claude/task checks passing and explicit completion-display limits. Copilot CLI follows. See [platforms](../the-guide/platforms.md) and [validation](validation/2026-09-29-platforms.md).
