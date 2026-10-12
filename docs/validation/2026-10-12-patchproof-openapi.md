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

Full regression, independent review, hosted matrix and final publication are
pending. [Design](../design/patchproof-openapi.md) and
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
is pending against the repaired code; do not substitute that earlier count.
