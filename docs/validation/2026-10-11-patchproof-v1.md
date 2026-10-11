# PatchProof v1 validation — 2026-10-11

Scope: exact committed patch description, conservative existing receipt binding
and standalone evidence export. Generalized standard-library runtime, no model
calls or changes to completion policy. [Design](../design/patchproof-v1.md).

## Observed development controls

- Binary output regression failed with the missing `text` keyword, then all
  process controls passed: 14 passed, two platform skips in 9.67 seconds.
- Twelve real Git identity controls failed before the API existed, then the
  combined identity/process run passed: 26 passed, two skips in 29.17 seconds.
- Fifteen receipt controls failed before the bundle API, then PatchProof and
  existing portable report controls passed: 37 passed in 63.17 seconds.
- Four real CLI controls failed before the executable existed; combined
  CLI/receipt/portable export checks passed: 41 passed in 205.63 seconds.
- Hidden index controls witnessed clean porcelain on modified files and initially
  qualified incorrectly. Malformed ledger state initially raised `KeyError`.
  Both were repaired; the final focused run passed 57 checks in 200.94 seconds.
- The first real Python/Node exercise exposed a fixture declaration error:
  `suite_green` was corrected to supported `tests`; no parser behavior was changed.

## Delivery qualification

Focused qualification: 57 passed, including real Python/JavaScript current,
failed, incomplete and absent outcomes, dirty binding and independent Git IDs.
Saved [observations](../../results/patchproof-v1/README.md) retain actual exits
0, 1 and no completed exit. Standard-library imports passed. Architecture:
137 nodes / 320 edges; all five views and contributor interactions rendered.
The first render caught an outdated search assertion: PatchProof now also
mentions ImpactGraph, so the two expected cards must remain searchable.

Independent review, full regression and final hosted CI are in progress; their
results will be recorded when complete. No pending check is called passed.

## Boundaries retained

Current input association is separate from pass/fail/incomplete, claim verdict,
execution-at-commit and unsupported compatibility. Exact tree identities include
unchanged inputs; no raw diff or file contents are exported. Bounded observations
are unsigned and non-atomic. No installed-host or coding-benefit comparison ran.
Two earlier installed Claude language successes remain historical at their
recorded fingerprint; other cells and current-runtime requalification are open.
The earlier intermittent Linux cleanup failure remains unresolved.
