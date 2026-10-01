# Live onboarding implementation plan

Goal: make first use observable and native edits attributable in any project.
Architecture: extend existing setup and doctor; add bounded project-local activation and targeted patch state; keep shared hook/ledger engine.
Tech stack: Python 3.11+ standard library, pytest, native JSON hook configurations.
Spec: docs/design/live-onboarding.md.
Constraints: preserve foreign configuration; no silent coverage gaps; no paid runs; no Snag source changes or branch changes.
Review focus: activation truth, cross-project isolation, interrupted edits, concurrent callbacks, safe removal, receipt freshness.

## Task 1: Activation and unified setup

Consumes existing setup/wiring and ledger lock. Produces activation state, five-host setup, launcher ingress and readable readiness.
Write behavioral tests for waiting/received/error/reset, replay exclusion, Claude preservation/removal and ambiguous auto detection; run red, implement, run focused green. Expected: new tests fail before code and pass afterward; existing setup/doctor tests pass.

## Task 2: Targeted native edit attribution

Consumes canonical patch inputs and task ledger. Produces pre/post content attribution and explicit missing-coverage decisions.
Write non-Git/dirty-file, add/delete/move, duplicate/missing baseline, unsafe-path and interruption tests; run red, implement, run focused green. Expected: proven changed paths are observed; uncertain events remain unverified.

## Task 3: Acceptance, documentation and delivery

Consumes readiness and attribution. Produces Snag acceptance evidence, full verification record, current docs/journey and architecture views.
Run the project checks, Snag readiness/CI, one fresh final review, fix consequential findings with red/green coverage, render architecture, update documentation, commit and push meaningful parts. Expected: actual results and remaining host-session limitations are recorded precisely.
