# Current delivery status

Reviewed **2026-09-29**, against runtime commit `a548d03`. ElevenPowers remains a research prototype for **Claude Code**. This page tracks product delivery; it does not replace the historical research results or claim an improvement in patch quality.

## Shipped and exercised

| Capability | Delivered behavior | Evidence boundary |
|---|---|---|
| Repository selection | Git-aware tracked/untracked inputs, inherited ignores, nested repository boundaries, configurable exclusions | Uses supported source extensions and named dependency files; excluded inputs are outside the fingerprint |
| Scan coverage | Explicit diagnostics for budgets, unsafe inputs and unreadable files; incomplete coverage prevents freshness | Defaults: 20,000 selected files and 256 MiB; these are not wall-clock guarantees |
| Command receipts | Exact configured/discovered commands; completed pass, completed fail and incomplete execution | Known summary failures override exit zero; opaque wrappers retain uncounted command-level evidence |
| Automatic setup | Root manifest discovery, startup health and coverage summary, no generated configuration file | Supported conventions: Node scripts/managers, pytest configuration, Cargo and Go; ambiguous/custom setups need overrides |
| Completion checks | Missing or stale verification in guide/strict; identical commands deduplicated per attempt | Baseline execution requires a relevant obligation and matching passing evidence; off remains passive |
| Compatibility | Historical receipt identities and single-file scope preserved | An interruption cannot stand in for a reproduced failure |

The initial portable-evidence delivery used ten pushes ending at `f432658`. Automatic setup used three more: `2636ded`, `fc527d9`, and `a548d03`. Each commit carries its implementation and validation details.

## What the checks established

The portable-evidence full run passed **831 tests with 26 skips**; final follow-up checks passed 137 relevant tests. The automatic-setup broad run passed **857 tests with 26 skips and one outdated baseline-cache fixture failure**. The fixture was updated to supply an active task claim and passed in focused checks. Final publication checks passed **103 command/execution tests** and **63 startup/scanning/hook tests**. No full run was repeated after that fixture-only correction. These counts describe specific runs, not a promise about today's collection size.

A disposable Node project was exercised through the shipped launcher: SessionStart reported activation; Stop discovered and executed `npm run ci`, recorded exactly one passing test, and created no config file. Architecture validation rendered all four views.

Read-only Snag selection discovered its verification scripts automatically and covered **4,418 files / 81,841,401 bytes** using defaults in about **1.11 seconds**. That timing is source selection, not a complete fingerprint or full CI. Earlier evidence included a real 19-test Node sample and parser replay. Snag was not edited or configured by these checks.

See the [validation index](validation/README.md) for the detailed records and qualifications.

## Next product milestone

**ElevenPowers works comfortably in an installed Snag session.** Generalized implementation is shipped; the installed integration remains open. Acceptance requires:

1. The current plugin loads in Claude Code with the intended project root and usable project environment.
2. The full `npm run ci` completes and produces a receipt through real host events; failures and interruption remain distinguishable.
3. Editing a selected input invalidates prior evidence, while excluded generated noise does not.
4. Startup, evidence capture and completion latency are measured during ordinary work.
5. Remaining environment or coverage limits are visible and actionable.

A full Snag CI run and live installed-plugin session have **not** been performed. The Codex host adapter, per-test dependency invalidation, mutation-based runtime coverage and improved patch-outcome claims remain outside this delivery.

## Delivery cadence

Use a concrete project milestone, focused regression checks for changed behavior, and an integration check at the delivery boundary. Broaden or repeat tests when new changes or failures warrant it. Keep historical experiments separate from readiness evidence, and update the guide, status, journey and architecture when their claims change.
