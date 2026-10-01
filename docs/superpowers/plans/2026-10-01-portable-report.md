# Portable report implementation plan

Goal: export reviewable verification evidence for a change in any project.
Architecture: a read-only report over the shared ledger, using one scoped fresh
source snapshot and existing verdict logic; no parallel verification engine.
Tech stack: Python 3.11+ standard library and pytest.
Spec: docs/design/portable-report.md.
Publication: the user requested 15 separate pushes for this new work after the
earlier ten onboarding pushes. Publish meaningful parts on `codex/portable-report`
and advance main only with the final tested revision. Preserve the unpublished
implementation snapshot while repartitioning; no remote history rewrite.
Constraints: no commands or model calls; bounded/explicit coverage; no raw prompt,
output or detail; safe Markdown and atomic explicit output.
Review focus: false verification, stale evidence, deadlines, privacy, output races.

The fresh review identified six export boundaries: explicit content freshness,
literal Markdown, read-only revision lookup, timestamp ordering, obligation
caveats and the shared deadline. Each was reproduced by failing controls and
corrected. A nested-snapshot control also flipped before its isolation fix.

## Task 1: Export and CLI

Consumes ledger, evidence freshness and edit coverage; produces schema version 1,
Markdown rendering, output CLI and atomic writer. Write failing controls for fresh,
stale, incomplete, no claim, coverage budget, redaction and output preservation.
Run red, implement, run focused green. Expected: source content changes invalidate
receipts; partial coverage and absent claims cannot certify completion.

## Task 2: Acceptance and delivery

Consumes report API; produces actual Snag report, final fresh review, broad checks,
updated guides/status/journey/architecture and publication. Expected: failed Snag
CI remains visible, its caller activation is separate, no project state is mutated
by report creation, and all four architecture views render.
