# PatchProof impact implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, with TDD and
> one final independent review through superpowers:requesting-code-review.

**Goal:** Explain possible change impact alongside exact patch evidence.
**Architecture:** Reuse fresh ImpactGraph snapshots, qualify their association
against the existing patch and verification reads, and export informational leads.
**Tech stack:** Python standard library, existing optional tree-sitter adapters,
Git 2.45+, existing portable JSON/Markdown exporter.
**Spec:** `docs/design/patchproof-impact.md`.

## Global constraints

Generalized for every project/host. Opt-in, no tests/model/compiler calls during
reporting. Shared bundle deadline; graph scan 30 seconds each; path cap 256;
query depth 6/results 100. Recommendations never become execution evidence.

## Review focus

- Changed Git ignore or project scan settings between reads must invalidate association.
- Unsupported/deleted/renamed and bounded-out inputs must retain explicit gaps.
- Optional graph failure must not suppress usable receipts or falsely change their binding.
- Graph paths/labels and diagnostics must remain safe in both portable exports.
- Large graph snapshots/query output must stay bounded without hiding truncation.

## Tasks

1. Fresh enrichment adapter: create `core/patchproof/impact.py` and
   `tests/test_patchproof_impact.py`. Consume `collect` patch, two portable source
   fingerprints, deadline; produce `inspect(root, patch, fingerprints, deadline)`
   and `qualify(value, eligible)` dictionaries. Write real-project tests first,
   observe absent API failure, implement with existing graph API, run focused
   tests, commit and push the adapter.
2. Bundle and CLI: modify `core/patchproof/report.py` and
   `plugin/bin/ep_patchproof.py`. Add optional `impact` section and `--impact`;
   compare graph association with final patch and bundle binding, render all
   explanations/candidate groups/gaps. Test disabled behavior, JSON/Markdown
   parity and actual CLI state preservation first; run new and existing bundle
   tests, commit and push.
3. Generalized qualification: extend real Python/JavaScript controls and
   adversarial producer-boundary race tests. Cover declared relationship/config
   changes, source fingerprint mismatch, expired budgets, deleted/rename/empty
   patches, missing adapters and cap diagnostics; preserve model-free outcomes.
   Watch missing behavior RED before repairs, run focused regression, push.
4. Delivery: write guide/provenance, journey 75 and dated validation; update
   README, plan/status, indexes, contributor brief and all affected architecture
   views. Execute one fresh independent review, repair Important findings with
   RED/GREEN controls; run full regressions, named audit, host doctor, independent
   graders and architecture `--render`. Push qualified changes, fast-forward main
   after hosted CI, verify main and Pages deployment.

## Execution rulings

User approved the preceding scope and explicitly asked to build, push and finish
on main. Proceed inline without repetitive design/plan approval menus. Reuse the
clean current checkout on a dedicated feature branch; no separate worktree is
created. This provides branch isolation but less filesystem isolation.

## Completion

All four tasks completed. One fresh independent review found one Important
policy-identity gap, repaired with observed RED/GREEN controls. Subsequent
exact-path and display controls retained their initial failures. Final
qualification: 2,088 local passes/2 skips, 107 audit probes, 39 focused
controls, all host/grader probes and all four hosted jobs at `cd19ed5`
(Windows 3.11 retry). See the dated validation for original failures and
unresolved cleanup/launcher causes. No new model session or coding-benefit
claim. All delivery code is intended for the authorized main fast-forward.
