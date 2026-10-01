# Test-strength implementation plan

Goal: deliver generalized changed-code test-strength analysis.
Spec: docs/design/test-strength.md. Stack: Python 3.11+ standard library, optional
Cosmic Ray and StrykerJS, pytest controls. Execute inline with one fresh final review.
Base: 523d6a9. Branch: codex/test-strength. User explicitly authorized incremental
publication in 25 meaningful pushes. Main advances only at the final complete part.

For each behavior: write a positive and adversarial control, observe RED, implement,
observe focused GREEN, commit and push immediately. Documentation-only parts receive
content/link checks. Engine adapters follow actual producer probes. No paid model run.

## Publication tasks

1. Approved design and publication plan.
2. Shared observation schema and classifications.
3. Project-owned optional configuration and validation.
4. Repository-aware changed production scope.
5. Bounded safe copy selection and dependency declarations.
6. Isolated snapshot lifecycle and source preservation.
7. Shared elapsed/attempt budgets and contained execution.
8. Passing baseline and command isolation qualification.
9. Atomic, bounded durable observations.
10. Cosmic Ray discovery, provenance and producer controls.
11. Cosmic Ray mutation execution and normalized outcomes.
12. StrykerJS discovery, provenance and producer controls.
13. StrykerJS mutation execution and normalized outcomes.
14. Shared analysis orchestration.
15. Exact-input reuse and freshness qualification.
16. Explicit analysis CLI.
17. Automatic completion consideration across hosts.
18. Saved findings in read-only JSON/Markdown reports.
19. Adversarial interruption and coverage controls.
20. Real-engine acceptance on unrelated projects.
21. Fresh whole-branch review corrections and integration checks.
22. Architecture graph and all four rendered views.
23. Configuration, commands, installation and troubleshooting guides.
24. Journey, validation, status and roadmap.
25. README, completed release and atomic main publication.

Interfaces: config produces bounded settings; scope and isolation produce a private
snapshot; engines consume it and return schema observations; runner persists them;
completion invokes only the shared runner; export reads only saved metadata.
Review focus: unsafe paths/symlinks, false baseline success, dependency aliasing,
attempt/time cap enforcement, interrupted writers, stale reuse, optional imports,
engine status interpretation, privacy and raw-mutant feedback to agents.
