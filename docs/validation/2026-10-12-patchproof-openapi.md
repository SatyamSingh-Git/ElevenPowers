# PatchProof OpenAPI validation — 2026-10-12

Scope: project-declared standalone OpenAPI compatibility, exact committed inputs,
real oasdiff 1.33.0 provenance and read-only evidence association. No model calls.

Development observations:

- Ten manifest/history filesystem controls failed against the missing interface,
  then passed (final store qualification 10 passed in 1.35 seconds).
- Seven real checker/protocol controls failed before the runner, then combined
  declaration/runner controls passed: 17 in 26.10 seconds.
- Six real saved-receipt controls failed before bundle integration. New/old
  PatchProof and portable-report controls then passed: 45 in 116.46 seconds.
- Expanded state/executable movement qualification passed 25 in 81.53 seconds.
- Three real CLI controls failed with no executable, then passed in 23.27 seconds.
- The unrelated-project exercise failed without an implementation, then exposed
  an over-restrictive ancestor-repository guard. Its own fresh Git roots now
  isolate operations; the real JSON/YAML exercise passed in 60.47 seconds.
- A glob/Unicode path control passed against actual Git without a parser change.
- The explicit installer downloaded and verified the official archive; version
  1.33.0 and standard-library imports were observed.

Final repaired qualification is recorded below; the development counts retain
their producing stage. [Design](../design/patchproof-openapi.md) and
[guide](../../the-guide/contracts.md) state the implementation boundaries.
Earlier installed successes remain dated at their recorded runtime identity;
this extension runs no new installed session and establishes no coding benefit.
The earlier Linux cleanup and initial Windows SQLite-reference causes remain open.

One independent whole-branch review found three Important findings and no
Critical/Minor findings. Real duplicate JSON (also with YAML suffix) and unobserved
dynamic references produced complete passes; malformed nested history raised
uncaught AttributeError/RecursionError with the CLI's exit 1. Five regression
cases failed before repair and passed after it: **5 passed in 24.70 seconds**.
The single repair pass qualified all contract controls: **37 passed in 189.79
seconds**, including dynamic YAML and stale retained legacy profiles. No re-review
or additional model session was run.

The earlier combined new/existing focused suite passed **105 checks, 2 skipped in
326.29 seconds** before the input-policy repairs. Final full/hosted qualification
below uses the repaired code; the earlier count is not substituted.

## Completed repaired qualification

Local full regression: **2063 passed, 2 skipped in 1368.86s (0:22:48)**. Named audit probes: **107 passed
in 100.64 seconds**. All 37 contract controls passed after review repairs;
the [four-job hosted qualification](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38214465591) passed on Ubuntu/Windows, Python 3.11/3.13, at
`02b1c55`. Official pinned binaries are installed explicitly in CI;
real producer acceptance is not replaced by launcher fixtures.

Standard-library imports, all 11 host probes, four independent grader
controls and preserved source grades passed. Both earlier stage-one 6/6
and final 8/8 ties remain; no agent session was rerun. Architecture
143 nodes / 338 edges, all five views rendered.

[Final observations](../../results/patchproof-openapi/final-observations.json)
retain the five expected states and independently matching Git/input
identities in both projects. [Initial observations](../../results/patchproof-openapi/observations.json)
remain unchanged at their earlier producer/configuration identity. Final
runtime fingerprint: `57ab817aa257d22915e60260b1f4d633d8c10f3dbddfba0cd9bb503d9c68df28`.
No deferred Minor findings and no new model calls. Prior intermittent
cleanup/SQLite-reference observations remain unresolved; these green runs
do not establish repairs for them.
