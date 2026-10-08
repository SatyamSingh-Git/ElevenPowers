# Staged behavior preservation, 2026-10-08

The approved milestone extends evaluation of the shipping generalized runtime;
it does not add a project-specific feature, automatic model call or default-on
advice. See [protocol](../design/behavior-preservation.md),
[plan](../superpowers/plans/2026-10-08-behavior-preservation.md),
[guide](../../the-guide/preservation-comparison.md) and
[published observations](../../results/behavior-preservation/README.md).

## Independent outcomes

Four subscription Claude Code 2.1.292 sessions used Sonnet 5 medium, two resumed
requests each, at most 480 seconds total per session. All eight requests
completed, using 541.873 seconds of total observed host execution against the
approved 1,920-second maximum. No API fallback, replacement case or model retry
was used. All first-stage outputs pass six independent groups and all final
outputs pass eight under the corrected oracle: two paired correctness ties.
There is no observed coding-quality improvement, speedup or linked correction.

Ordinary/assisted observed host seconds were 108.707/126.596 for the queue and
89.112/217.458 for inventory. These descriptive times include model variance;
they are not isolated measurements of hook overhead.

All four assisted milestone reports were `CURRENT`, but native command receipt
links were absent. The agent used a `cd PROJECT &&` wrapper around the declared
test command. Startup, prompt, edits and completion were observed separately;
completion-created receipts do not qualify native command capture. Installed
pipeline acceptance remains incomplete. Five advice attempts retain three
delivered worker contexts and two incomplete attempts; model consumption is
not established by that diagnostic state.

## Review and producer preservation

The single fresh code review reported four Important findings and one Minor
finding. Payload/JSON preservation, direct reserve-at-expiry behavior, resumed
edit-task identity, loaded allowance validation and initial extra-file equality
were repaired with witnessed failing/passing controls. The same reviewer examined
the subsequently added archive module once: protocol comparability was Important,
and bounded protocol-read ordering was Minor; both were repaired. There was no
second whole-branch review or native rerun.

A separate CRLF source-identity regression was reproduced and repaired. All
actual saved source snapshots matched their recorded raw hashes before
publication; no reconstruction or candidate repair was needed. Original queue
observations (`eda75e7`) and inventory-assisted observations (`8290d68`) remain
alongside corrected regrades. Inventory-ordinary used `783e02b`. Unstarted slots
were prepared under corrected protocols; they are not model retries or omitted
attempts. Every final snapshot was regraded with the same corrected case oracle.

The archive separately validates source identity and paired protocol qualification:
expected model/effort, source/case requests, identical public inputs, preserved
allowed configuration and actual recorded time allowances. An unqualified protocol
can retain an independent source grade but cannot establish a paired advantage.
Captures remain dated unsigned observations, not an OS sandbox or authentication.

## Verification commands

```sh
python -m pytest tests/test_preservation_cases.py tests/test_preservation.py tests/test_preservation_archive.py -q
python results/behavior-preservation/reproduce.py
python -m pytest -q
python plugin/bin/ep_doctor.py --host
python -m eval.validate
python architecture/check.py --render
```

Free source reproduction matched all eight corrected grades and their source/oracle
identities. The host doctor and all four independent grader categories pass.
The final compatibility and hosted CI outcomes are reported against the actual
revision at delivery. No installed acceptance or product-benefit exit is
promoted by a passing regression suite.

Recorded local checks: the focused case/controller group passed 20 controls;
the final archive group passed four controls. All eight published stage grades
reproduced, the host doctor passed and all four grader categories matched.
Standard-library imports passed without site packages. All five architecture
tabs rendered with 128 nodes, 295 edges and seven planes; 358 local documentation
links resolved. CI now runs the published model-free source reproduction on its
Windows/Linux and Python 3.11/3.13 matrix, separately from fresh native acceptance.
The full local suite and hosted exact-revision run are final integration gates;
their measured results belong to the corresponding command output and Actions
run, rather than a predicted count here.
