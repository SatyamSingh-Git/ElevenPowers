# 46. The project outside the fixture

2026-09-27 to 2026-09-28. The request was practical: check the current state, fix the documentation/environment/reproducibility gaps, and decide whether ElevenPowers could be used in `E:/snag`. The user also asked for more product progress, with testing tied to delivery rather than becoming the whole activity.

## First make the evidence reproducible

The preceding fixes aligned the current documentation with the measured results, documented a pinned development environment and made saved analyses runnable from a checkout. Those changes did not improve the published research outcomes. They made the claims easier to reproduce and stopped an environment failure from looking like a failed product check. The workflow is in [development.md](../docs/development.md).

## A scan that stopped looking

Snag exposed the difference between a fixture and a repository. Generated data could dominate the old filesystem walk, and a file limit could leave a partial input set looking complete. The implementation moved source selection to Git's tracked and non-ignored inputs, retained repository boundaries, and attached coverage diagnostics to evidence. Non-Git projects retain a bounded filesystem fallback. Projects can own exclusions and budgets.

This is generalized runtime behavior. No Snag directory or command name became a special case. Ignored and explicitly excluded inputs are outside the selected coverage boundary; per-test dependency analysis remains unbuilt.

## A command that did not say test

Snag uses `npm run ci`. A project should be able to declare its actual verification command even when the name is opaque. Exact declarations now produce receipts, retain recognizable counts, and distinguish completed success, completed failure and incomplete execution. A failed sub-run cannot be erased by another package's passing summary or a zero shell exit.

Review found important interactions. Replacing receipt identities lost single-file scope and prevented old failures from being superseded. Incomplete execution could count as a reproduced failure. A subproject could lose its parent repository's ignores. Mixed summaries could hide failures from another runner. The fixes preserved identities and scope, tightened completed-failure semantics, retained inherited ignores and expanded aggregation. Regression probes covered the failures and their legitimate controls.

## What Snag actually proved

At the initial 64 MiB default, Snag's scan explicitly reported incomplete coverage. With a larger in-memory budget it selected 4,418 files, about 78.05 MiB. A real Node sample passed 19 tests, and its output was replayed under the declared wrapper to check receipt recognition. The full `npm run ci` was not executed, and the plugin was not installed in Snag.

One cold fingerprint took 54.44 seconds during concurrent testing; a warm one took 1.72 seconds. Those are different measurements from source selection. The result was enough to justify an integration trial, not a claim that the installed product had been validated there.

The user requested ten pushes. The sequence ended at `f432658`, with documentation last. The full suite passed 831 tests with 26 skips; 137 relevant tests covered the final review corrections. The precise record is [portable evidence validation](../docs/validation/2026-09-28-portable-evidence.md).

The remaining friction was visible: the user still had to declare the command and raise the scan budget. That became the next delivery, [automatic setup](47-installed-should-mean-active.md).
