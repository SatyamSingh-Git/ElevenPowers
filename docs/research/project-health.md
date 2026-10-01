# Project-health provenance and limits

2026-10-01. This delivery builds on ElevenPowers' existing shared runtime.
It adds no third-party runtime dependency and copies no new upstream
implementation. The [license register](licenses.md) retains the project's
existing license decision and upstream attribution qualifications.

| Existing implementation | What it supplies | What this delivery adds |
|---|---|---|
| `core/export.py`, `core/evidence.py` | One scoped fresh source/explicit-input view, qualified receipts and task interpretation | Shared receipt identity, measured read duration and staged health consuming the same view |
| `core/hosts/doctor.py`, setup and adapters | Owned wiring, path/subscription validation and canonical native lifecycle | One read-only configuration/environment/delivery/verification/completion view |
| `core/hosts/readiness.py`, `core/jobs.py` | Atomic local registry, generation, progress and locking | Bounded private phase/timing/receipt links, current task/session correlation and explicit unresolved errors |
| `core/process.py` | Contained command execution and cleanup | Disposable Git preparation only on explicit invocation |
| `core/hosts/edits.py` | Target observations and incomplete native coverage | Read-only integration qualification; no new edit policy |

The exercise uses Python's [unittest framework](https://docs.python.org/3/library/unittest.html)
for actual boundary assertions and a small TAP rendering of its real result.
JavaScript uses [Node's built-in test runner](https://nodejs.org/download/release/latest-jod/docs/api/test.html)
and strict assertions. Those standard APIs provide execution and assertions;
the generated application/test files are original exercise code. No framework
implementation, host prompt or documentation text is vendored. Tests ran on
Python 3.13.2 and Node 22.17.1; references describe APIs, not installed-version
acceptance. Ten producer/launcher controls genuinely fail, pass, time out and
become stale before a rerun.

The host troubleshooting approach follows the already documented native
boundaries: distinguish wiring, execution/outcome, output delivery and policy.
New health behavior reuses those adapters; it does not infer new host APIs from
fixture schemas. Existing adapter provenance is in the [platform guide](../../the-guide/platforms.md)
and [platform validation](../validation/2026-09-29-platforms.md).

One new sentence defines the contribution: compose fresh evidence with bounded
native delivery stages and provide the same explicit disposable acceptance
recipe for every supported project and host.

Limits: local observations and operator versions are unsigned; a prepared or
replayed exercise is not installed acceptance. The earlier manual stale-view
instruction is not independently attested. Timing summaries describe retained
samples. Optional engine metadata is availability information, not an executed
engine check. None of these observations establishes production correctness,
cross-version compatibility, speed improvement or better patch outcomes.
See [delivery validation](../validation/2026-10-01-project-health.md).
