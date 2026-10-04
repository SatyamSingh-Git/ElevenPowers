# 60 — An impact path needs a reason

The user asked to start ImpactGraph and keep pushing working parts. The requested
feature was broader than an import diagram: explain what might be affected
across an end-to-end project, including tests, storage and routes, without relying
on an AI opinion or building a special case for one repository.

The first decision was to build one shared module inside ElevenPowers, with a
standalone CLI. Existing repository selection and optional tree-sitter parsing
already solve parts of the problem. A separate repository would duplicate their
policy; the older radius's name references cannot carry provenance. The design
and implementation plan were written and pushed before runtime code.

## What the first version does

Every query reads a new bounded snapshot. Typed edges distinguish source-derived
imports/calls, project-declared contracts, content-bound unsigned observations and
historical co-change. Reverse traversal returns actual witness paths and candidate
tests. There are no breakage percentages, and a test relationship is not a green
test receipt.

Python imports use supported project-root and `src/` layouts. The optional real
grammar reads JavaScript/TypeScript imports, including barrels and unique
workspace entries. Framework routes, database contracts and infrastructure can
be declared now; built-in framework/runtime/coverage adapters remain unfinished.

## Where the first implementation was wrong

The independent reviewer reproduced false callable witnesses from match captures,
reassigned module attributes, rebound exports and a shadowed CommonJS `require`.
Package initializer precedence and overlapping module aliases also exposed wrong
or missing targets. Arbitrary suffix indexing guessed unsupported import roots;
an escaping relative import collapsed into an unrelated root file.

Those cases now have explicit controls. Binding resolution uses known module
roots and stable exported definitions, longest applicable aliases and conservative
shadow/mutation invalidation. Unknowns remain visible rather than becoming calls.
The reviewer also measured a large alias loop outrunning a short budget; inner
deadline checks and indexed lookup now bound that work.

The more serious discovery was below the new module. Git source selection could
execute a repository's configured filesystem-monitor hook. The reproduced hook
wrote a marker during an ostensibly read-only graph build. Shared scans now
disable fsmonitor. ImpactGraph also stopped using command-discovering config
loads: those read an oversized manifest twice before the graph's input cap could
apply. Scan policy has its own bounded safe read. `.mts`/`.cts` now reach shared
source selection, and malformed deeply nested manifests become parse gaps.

The first full regression run reported 1,449 passing checks, two skips and one
failure in an existing descendant audit probe. Its parent waited only for a PID
file to exist; the child could be stopped between creating and writing that file,
leaving `int('')`. The probe producer now publishes a fully written PID atomically.
This keeps the containment assertion intact; it fixes the measuring instrument.
Final execution evidence is in the [dated validation](../docs/validation/2026-10-04-impact-graph.md).

## A useful check, with a bounded claim

A session-expiration fixture has API and worker consumers plus declared route
and storage relationships. The graph selected two test files containing four
independent behavior checks, while excluding an unrelated same-name function.
All four checks passed on valid behavior. Changing the expiry boundary from
`>=` to `>` caused two selected checks to fail. An equivalent repair passed all
four again. The graph selected checks; a separate Python process graded behavior.

That establishes useful impact/test selection and fault sensitivity on this
fixture. It does not show that an agent makes better patches because of the
graph. Earlier coding comparisons still tie. Larger real-project relevance,
false positives, elapsed cost, automatic-hook integration and held-out outcome
measurement remain the next acceptance work.

The feature is shared infrastructure for PatchProof, OpenCodeMap and TestMiner.
Shipping it does not claim those products have been built.
