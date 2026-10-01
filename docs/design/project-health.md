# Generalized project health

Approved in chat on 2026-10-01: extend `ep_ready` and `ep_doctor` to show whether
the complete shared integration is working in any project. Repositories are
acceptance cases, never policy special cases. Preserve automatic operation and
the existing lightweight, Python 3.11+ standard-library runtime.

## Read-only health

`ep_ready HOST --project DIR [--json] [--seconds 10]` retains its existing keys
and adds schema-v1 staged health, fresh receipt checks, saved optional strength,
progress and measured timings. It never runs a project command, installs a
dependency, starts a host, imports an optional engine or writes project state.
Use the existing exporter once for the current source/explicit-input snapshot,
receipt interpretation and task verdict. Do not make a second source scan.
The deadline is cooperative, finite and bounded to 120 seconds; incomplete input
coverage never produces an all-observed pipeline. Unreadable diagnostic state
is actionable, not silence or a crash. State changes during a read qualify it.

Stages distinguish configuration, environment, startup, edit delivery, native
command capture, project verification, completion, report and optional strength.
Integration observations and task verification remain separate. A correctly
captured failing command proves capture, not successful verification. Startup
alone does not establish the full pipeline. No active task is still UNVERIFIED.
Readiness exit codes retain their existing behavior; `--check` explicitly returns
nonzero unless the required pipeline stages are observed and verification is
fresh and passing. Optional engine unavailability does not block ordinary health.

## Automatic bounded observations

Extend the existing `integrations.json` generation, not a second logging service.
Only launcher ingress contributes; explicit replay and in-process calls remain
excluded. Canonical phases keep counts, last processed task/session hashes and
32 elapsed samples. Never store prompts, tool input, output, raw session IDs,
source or individual mutations. Real recorded command receipts are linked by a
hash of their bounded identity/timestamp and retain result/execution metadata.
Keep at most 64 links and report eviction. A task or configuration change must
not inherit an earlier completion/capture claim. Metadata is local diagnostic
observation, not authentication or attestation of the sender.

Timings identify measured callback processing, fresh source/report work and
automatic command execution. Median/p95 values describe the retained sample
only; no invented baseline, latency target or performance improvement claim.
Collection performs no additional source scan or package/version subprocess.

## Explicit acceptance workflow

`ep_doctor --prepare-acceptance DIR --platform HOST --language python|javascript`
creates a new disposable Git repository, small intentionally failing tests,
project-owned commands, isolated owned wiring and a human-readable exercise.
Existing or linked destinations are refused. Use Python unittest or Node TAP,
without package downloads. Ordinary verification commands are real producers;
preparation and replay do not mark native activation.

The exercise covers startup, a failing test, a source fix, passing tests, an
interrupted test command, stale evidence after an edit, a rerun and completion.
`ep_doctor --acceptance DIR --platform HOST [--json]` reads bounded observations
and current report, verifies manifest/configuration generation and requires the
exercise's pass/fail/incomplete outcomes plus current native edit/completion
observations. A failure remains distinct from missing, expired or unreadable
observations. Host versions are explicit operator/probe metadata and not inferred
from fixture event schemas. Runtime discovery/readiness never runs this exercise.

Actual installed sessions are recorded separately from contract/launcher tests.
Unavailable hosts stay unverified. Paid model/evaluation calls require the
repository's explicit cost approval; constructing the reusable workflow does
not establish acceptance in an unavailable host.

## Borrowing and delivery

Reuse ElevenPowers' configuration doctor, activation registry, native adapters,
freshness/exporter, command receipts and journal. Borrow the native host
troubleshooting approach of distinguishing wiring, execution, exit/output and
policy (official Gemini/Claude hook documentation). What is added is one staged,
fresh, project-independent health view and a repeatable native acceptance recipe.

Acceptance controls cover all five adapters, two unrelated languages, pass/fail/
incomplete capture, fresh/stale/gone evidence, task/configuration changes, replay,
history caps, malformed state, deadlines, privacy and no-write/no-execution reads.
Run focused controls per change, a full suite at integration, grader/doctor,
rendered architecture, complete guides/status/journey and incremental publication.
