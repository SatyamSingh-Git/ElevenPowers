# 61 — The graph must face a missed regression

2026-10-04

The first graph could explain a supported import path and distinguish a boundary
fault from equivalent behavior. That did not establish useful test selection in
a repository with fixture injection, dynamic imports, package barrels and many
shared dependencies. The next milestone froze the question before repairing
adapters: three real repositories, 24 known consumer/test scenarios, eight held
out by family. The references were independently read but authored and visible,
not blinded. Extra graph recommendations were left unlabelled rather than
silently called wrong.

ElevenPowers, Jinja and Zod passed their actual bounded baseline suites. Jinja
first failed collection because trio was missing; installing its pinned 0.27.0
requirement resolved the environment without discarding the failure. The
published corpus also corrected an initial private license assumption:
ElevenPowers declares Apache-2.0 in its README, not MIT.

The static comparison found all 31 known consumer references and 23 of 26 known
tests. Two missing references point to a CLI subprocess test; the third reaches Jinja nodes through
the pytest environment fixture. Ordinary imports cannot explain those paths.
Actual coverage.py execution recovered the Jinja relationship. We added an
offline converter with counted-run receipts, raw report hashes, current source
fingerprints and explicit context mapping. It observes execution, not assertions.
Native Node V8 works through the same contract for isolated JS runs; transformed
TypeScript and source maps stay unsupported.

TypeScript's own compiler supplies a better resolver than another collection of
specifier guesses. The optional 5.7.3 adapter reads selected virtual bytes,
resolves aliases, exports and barrels, and identifies qualified imported calls.
It runs no target source/config and proves no runtime dispatch or type-check
success. It still produces broad candidates and many gaps on Zod, and hits its
explicit 32 MiB input cap on the frozen owner-project snapshot.

Eight independent fault attempts were executed alongside unchanged and comment
controls. Six met the strict assertion-only qualification. Both original and
final graph selections detected five. The process-output-cap regression failed
its real test while the selected tests passed: the process test obtains its
module through `importlib.import_module`, a missing dynamic relationship. The
string-boundary attempt had mixed assertions and uncaught runtime failures, and
the default-export change passed the existing tests. Both remain in the record,
outside the qualified denominator.

Review found four concrete defects. Reusing a function type was enough to invent
a concrete compiler call. Runtime-error prose could masquerade as an assertion.
A missing executed-line context could still produce a complete conversion.
Evaluator reads checked their limits after loading the whole file. Each was
reproduced before repair. Current regrades preserve original producers and code
identities; a fresh post-review selected run still detects five of six.

The proposed 90% detection exit failed at 83.3%. Candidate sets remain wide:
23 files on Jinja and roughly a whole Zod suite. Local read samples describe
explicit query cost, not installed-session overhead. We therefore left automatic
advisories pending. The next contribution should freeze new dynamic-import and
fixture scenarios, measure specific queries, and repair those relationships
before reusing this corpus as a fresh acceptance set.

The new capabilities are useful: a real missed relationship can now be recovered,
compiler paths are more precise, and the benchmark can identify an unsafe test
selection. The experiment did not improve fault detection over the old graph,
and it did not measure better agent patches. Those are different claims.

See [all outcomes and reproduction](../results/impact-acceptance/README.md),
[producer sources](../docs/research/impact-producers.md),
[validation](../docs/validation/2026-10-04-impact-acceptance.md), and
[the approved plan](../docs/superpowers/plans/2026-10-04-impact-acceptance.md).
