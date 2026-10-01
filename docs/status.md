# Current delivery status

Reviewed **2026-10-01**. ElevenPowers remains a research prototype. All five hosts
share project-independent onboarding, command discovery, repository evidence and
verification. Claude Code, Codex, Gemini CLI, Cursor Agent and GitHub Copilot CLI
have reversible project wiring; the four additions also have portable bundles.
This delivery does not establish improved patch outcomes.

## Shipped and exercised

| Capability | Delivered behavior | Evidence boundary |
|---|---|---|
| Repository selection | Git-aware tracked/untracked inputs, inherited ignores, nested boundaries and project exclusions | Supported source extensions and named dependency files; excluded inputs are outside the fingerprint |
| Scan coverage | Explicit file/byte/deadline/unreadable-input diagnostics | Default 20,000 files and 256 MiB; filesystem operations are not a hard wall-clock guarantee |
| Command receipts | Exact configured/discovered commands; complete pass, complete fail and incomplete execution | Opaque wrappers retain command-level evidence; transport success/prose alone cannot prove process success |
| Five-host onboarding | Ownership-preserving setup, explicit or unambiguous auto host selection, command/environment discovery and readiness actions | Host trust/policy remains under the host; custom/ambiguous manifests need overrides |
| Callback activation | Waiting, received, processed startup, errors/history, changed wiring and removal | Launcher observations only; replay excluded; callbacks are not sender authentication |
| Native patch attribution | Bounded pre/post target content comparisons; dirty/non-Git files, add/delete/move | Stable task/session/call/input required; target coverage cannot prove absence of unrelated side effects |
| Missing callbacks | Pending coverage visible in status/readiness; completion reconciles missing post-events; eviction uncertainty persists | Interrupted/missing/unsafe/budget-limited observations stay UNVERIFIED even with passing tests |
| Completion checks | Missing/stale checks in guide/strict; same commands deduplicated; receipts persist immediately | Off remains passive; one shared 480-second work budget and 300-second command cap |
| Process lifecycle | Windows Job containment, POSIX process-group cleanup and 8 MiB combined capture limit | Deliberate group escape and abrupt SIGKILL are outside cleanup guarantees |
| Durable progress | Project ownership, atomic short ledger writes, running/deferred/interrupted journal | Journal and activation are diagnostics, never proof of command success |
| Portable verification report | Local Markdown/versioned JSON, computed claims, obligation caveats, latest receipts, fresh input observations and next actions | Read-only, unsigned; no active claim or incomplete coverage stays UNVERIFIED; no mutation findings or stronger patch-outcome claim |

See [onboarding validation](validation/2026-10-01-live-onboarding.md),
[platform guide](../the-guide/platforms.md), and [journey 50](../journey/50-project-readiness.md).
Historical delivery counts remain in the [validation index](validation/README.md).

## Real-project acceptance

Snag is an acceptance repository, not a runtime special case. Its own manifest
discovered `npm run ci`, `npm run typecheck`, `npm run build` and `npm run lint`.
Read-only selection covered **4,418 files / 81,841,401 bytes** before setup and
**4,417 files / 81,841,184 bytes** afterward, with complete selection coverage.
These are selection measurements, not complete content-fingerprint timings.

Ownership-preserving project setup installed Claude and Codex hooks. An installed
**Claude Code 2.1.281** session delivered and processed SessionStart without a
prompt/model call. Claude activation is active; Codex is configured and waiting.
No business source or Snag branch was changed.

The actual external **`npm run ci` exited 1: 14/15 checks passed**. Its production
dependency audit reported five unexcused high-or-critical package findings:
electron, mailparser, next, nodemailer and undici. The check was not bypassed.
An explicit diagnostic relay recorded the real result as **complete/fail**, with
complete source coverage; it did not mark Codex active. This is separate from
capturing CI through an installed host's native command events.

## Remaining readiness limits

- Versioned live sessions on Codex, Gemini CLI, Cursor Agent and Copilot CLI remain open.
- A full native-host Snag command receipt and normal-session latency measurements remain open.
- Snag's dependency audit must be resolved in that project before its full CI is green.
- Unknown tool input/result envelopes, missing identities/events, unsafe paths and budgets remain explicit gaps.
- Cursor/Copilot normal completion has no ordinary report field; use the stored status.
- Per-test dependency invalidation, mutation-based runtime coverage and improved outcome claims remain outside this delivery.
- The prior Linux proc-read probe race was fixed; the historical intermittent five-second descendant-survival assertion has no established runtime cause.

## Portable report acceptance

`ep_report.py --project PATH` exports Markdown by default, or JSON with
`--format json`. It reads fresh source and explicit-path inputs in one scoped
view, preserves evidence qualifications, and shares a cooperative deadline and
project scan budgets. Known credentials are scrubbed and project-root text is
substituted. Prompts, transcripts, outputs and receipt details are excluded.
Saving requires `--output`; replacing a file requires `--force`.

The actual Snag export records revision
`1906da4576f29b02131ff50a29204529b8bcbb5e`, complete selection of 4,417 files /
81,841,184 bytes, and a fresh **complete/fail** `npm run ci` receipt under the
same account/ignore policy as the original relay. Overall task state is
**UNVERIFIED** because no active claim is recorded. No project command was run
to generate it. See [report validation](validation/2026-10-01-portable-report.md)
and [journey 51](../journey/51-receipts-another-person-can-read.md).

## Next readiness milestone

Exercise versioned native sessions on the four added hosts and capture an actual
declared-command result through their installed hooks. This closes the largest
remaining usability uncertainty across projects. Mutation findings and measured
outcome improvements remain separate research work.

Use focused behavioral checks and a broad integration check at the delivery
boundary; repeat when new corrections or failures warrant it. Documentation,
journey and rendered architecture are part of delivery.
