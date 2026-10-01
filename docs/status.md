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
| Fresh staged project health | One fresh report view; native startup/edit/capture/completion, every declared command's aggregate outcome, progress and read-only optional metadata | Ten-second cooperative default, 120-second maximum; unresolved current callback errors, corrupt/moving state and incomplete coverage cannot pass `--check` |
| Native acceptance workflow | Explicit new disposable Python/Node repository, owned wiring, immutable contract and current pass/fail/incomplete history qualification | Preparation launches no host; local unsigned observations and operator versions do not establish authenticated or cross-version compatibility |
| Native patch attribution | Bounded pre/post target content comparisons; dirty/non-Git files, add/delete/move | Stable task/session/call/input required; target coverage cannot prove absence of unrelated side effects |
| Missing callbacks | Pending coverage visible in status/readiness; completion reconciles missing post-events; eviction uncertainty persists | Interrupted/missing/unsafe/budget-limited observations stay UNVERIFIED even with passing tests |
| Completion checks | Missing/stale checks in guide/strict; same commands deduplicated; receipts persist immediately | Off remains passive; one shared 480-second work budget and 300-second command cap |
| Process lifecycle | Windows Job containment, POSIX process-group cleanup and 8 MiB combined capture limit | Deliberate group escape and abrupt SIGKILL are outside cleanup guarantees |
| Durable progress | Project ownership, atomic short ledger writes, running/deferred/interrupted journal | Journal and activation are diagnostics, never proof of command success |
| Portable verification report | Local Markdown/versioned JSON, qualified claims, latest receipts, freshness, coverage and saved strength findings | Read-only, unsigned; no active claim or incomplete coverage stays UNVERIFIED; findings never alter verdicts |
| Changed-file test strength | Optional Cosmic Ray/Stryker producers, clean baseline/attempt copies, contained execution, atomic metadata and exact-input reuse | Informational; default 60 seconds/8 attempts/15 seconds per test command; whole changed files and sampled operators, not correctness or outcome improvement |

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
- A full staged native exercise remains unverified on all five hosts; the historical Claude startup proves only startup.
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

Use the new disposable workflow to exercise versioned installed hosts, then
measure normal-session callback/read/command costs on unrelated projects.
This closes the largest remaining usability uncertainty. Shared health and
acceptance tooling are delivered; launcher contracts alone do not close installed
acceptance. Full exercises on unavailable hosts remain open. Optional mutation
findings ship; measured outcome improvements remain separate research work.
Strength needs installed pinned engines and a sufficiently fast isolated test
command; uncertain attribution, linked inputs and budgets stay incomplete.

See [test-strength validation](validation/2026-10-01-test-strength.md) and
[journey 52](../journey/52-tests-that-notice-a-change.md) for actual language controls,
independent-review fixes and the 25 incremental publication parts.

Use focused behavioral checks and a broad integration check at the delivery
boundary; repeat when new corrections or failures warrant it. Documentation,
journey and rendered architecture are part of delivery.

## Project-health delivery

`ep_ready.py HOST --project PATH [--seconds 10] [--check]` now shares one fresh
source/explicit-input report with task interpretation. Every declared command
needs its latest applicable aggregate receipt; individual passing tests cannot
hide a failing suite. Capture, verification and task certification remain separate.
Automatic native diagnostics retain 32 timing samples per phase and 64 hashed
receipt links, with explicit eviction. Health reads execute no project command,
engine or host, and write no project state. Metadata is availability information.

`ep_doctor.py --prepare-acceptance NEW_DIR --platform HOST --language python|javascript
--host-version VERSION` creates an opt-in exercise; `--acceptance DIR --platform
HOST` inspects it read-only. Ten actual language/launcher contract cases passed,
including real process interruption, stale input and rerun. Local version probes
found Claude Code 2.1.286 and Codex CLI 0.159.2; the other executables were absent.
Installed Claude 2.1.286 processed a real startup in the disposable exercise with
no model prompt. Startup is observed; full pipeline and acceptance correctly
remain waiting. One 117.32 ms callback sample is not ordinary-session latency.
Five independent-review defects were reproduced RED, fixed and verified GREEN.
The corrected full suite passed **1,194 tests with 28 skips** in 691.95 seconds.
Exact checks and qualifications are in [health validation](validation/2026-10-01-project-health.md).
See [journey 53](../journey/53-a-working-pipeline-needs-evidence.md).
