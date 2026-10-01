# Validation records

Dated records distinguish implementation checks from real-project integration. [Current status](../status.md) identifies the next milestone; the documents here preserve what was actually run.

- [2026-10-01 generalized onboarding](2026-10-01-live-onboarding.md): five-host
  setup/readiness, bounded activation, targeted edit observations, review
  regressions, real Claude startup and the actual failed external Snag CI relay.

| Date | Record | What it establishes |
|---|---|---|
| 2026-09-28 | [Portable repository evidence](2026-09-28-portable-evidence.md) | Git-aware selection, coverage limits, declared receipts, review fixes, and read-only Snag/sample-output checks |
| 2026-09-29 | [Automatic setup](2026-09-29-automatic-setup.md) | Manifest discovery, startup diagnostics, real no-config launcher execution, and complete Snag selection under the new default |

The first record's 64 MiB default is historical. The current default is 256 MiB. A successful disposable launcher test is not a live installed Claude Code session, and a Snag sample or selection scan is not the full Snag CI pipeline. Neither record establishes improved patch outcomes.

The [durable verification record](2026-09-29-durable-runner.md) covers per-check persistence, shared deadlines, process cleanup, declaration/input invalidation, read-only Snag fingerprinting and a real launcher kill/recovery check. It does not establish full Snag CI or live installed-host readiness.

- [2026-09-29 native platforms](2026-09-29-platforms.md): eight pushes per additional host, exact checks and installed-session limits.
