# Two-stage behavior preservation, 2026-10-08

Four approved subscription sessions used **Claude Code 2.1.292, Sonnet 5,
medium effort**, two sequential requests per resumed session and at most 480
seconds per session. All eight requests completed; there were no model retries,
replacement cases or API fallback. Total observed host execution was
**541.873 seconds**, within the 1,920-second approved maximum. Preparation,
independent grading and documentation time are separate.

**Result: two correctness ties, no demonstrated code-quality improvement or
speedup.** Every first-stage output passes 6/6 independent groups and every final
output passes 8/8 under the corrected oracle. These are 56 group executions,
including repeated earlier behavior groups, not 56 distinct contracts. Both
ordinary runs preserved the earlier checked behavior, leaving no observed
regression for ElevenPowers to improve in this comparison.

| Authored project | Ordinary final | Assisted final | Ordinary host time | Assisted host time |
|---|---|---|---|---|
| Leased queue → JSON persistence | 8/8 | 8/8 | 108.707 s | 126.596 s |
| Reservation expiry → JSON persistence | 8/8 | 8/8 | 89.112 s | 217.458 s |

Higher assisted time in both observations is descriptive. It combines model
choices, execution, callbacks and machine conditions; this tiny selected sample
does not isolate hook overhead or establish a general slowdown.

## What was actually exercised

Both arms received the same source, existing public tests, milestone declarations
and feature requirements within each pair. They could edit the permitted source
and add tests, but existing tests/configuration were sealed. Baselines were
independently checked before model calls. Stage one added lease/expiry behavior;
stage two added JSON persistence while retaining the earlier contracts.
Grading ran in private fresh copies, without feeding hidden results back between
requests. There was no deliberately injected agent defect. Native tools still
had filesystem access; this is not an OS exposure boundary.

Assisted projects used shipping hooks, guide-mode completion verification and
optional milestone advice; strength was disabled. This is the combined
intervention, not an isolated ImpactGraph experiment. Project/local settings,
subscription authentication and the three observed host builtin plugins were
shared conditions. No external MCP server was active. Full host streams and
prompts remain in ignored private slots; bounded results, source snapshots,
identities, usage and qualifications are published here.

## Native acceptance and cost

Both assisted sessions processed native startup, prompt, edit/tool and Stop
callbacks, and all four stage-final milestone views were `CURRENT`. However,
**there were no native links for the exact declared test command**. The agent
ran `cd PROJECT && python -m unittest discover -s tests -v`, while the declaration
was `python -m unittest discover -s tests -v`. Exact-command matching deliberately
does not equate arbitrary wrappers. Completion-created receipts and controller
baselines are not native command-capture proof. Full installed-pipeline acceptance
therefore remains **incomplete**, despite correct independently checked code.

Five advisory worker attempts were retained: **three delivered runtime contexts
and two incomplete attempts**. The delivered samples were 389.745, 393.264 and
431.701 ms; the incomplete attempts were 1531.949 and 1538.896 ms. Delivery here
means the runtime worker returned context, not authenticated evidence that the
model used it. The stream exposed startup hook responses but not post-tool
context bodies. No advice-following or causal correction claim follows.

Retained native PostToolUse samples were 15 for queue (median 39.010 ms,
maximum 487.091 ms) and 13 for inventory (median 54.841 ms, maximum 1691.901 ms).
These callback-body observations exclude some launcher/host overhead and are
bounded retained samples, not portable latency guarantees or paired added cost.

## Evaluator corrections and preserved identities

The fresh review found missing queue payload/JSON assertions, a masked direct
inventory-reserve expiry requirement, stale resumed-task edit qualification,
loaded-budget validation and unsealed initial extra tests. They were reproduced
as failing controls and repaired. An archive-focused append found that source
regrading alone could qualify incomparable protocols; protocol/configuration,
model, allowance and paired public-input checks now gate the comparison.
A separate CRLF control repaired future byte-exact source capture. All actual
saved snapshots already matched their recorded raw source hashes; no newline
reconstruction or candidate repair was used.

The two queue sessions retain their original `eda75e7` controller/oracle
observations. Inventory-assisted retains the `8290d68` producer; the final
inventory-ordinary session uses `783e02b`. The corrected free regrader is
identified by source hash in [summary.json](summary.json). Every saved stage is
regraded against the same corrected oracle for that case, while each original
grade and protocol is preserved alongside it. Corrections did not alter either
agent's requirements or source and did not trigger extra model calls.

The first protocol's inventory slots and later protocols' unused companion
slots were prepared without a model and never launched. They are not extra runs
or selectively discarded attempts. Exactly the four named session attempts are
included. All four published records qualify the comparable public inputs,
allowed settings and time/model allowances; native acceptance stays separate.

## Reproduce and inspect

From the repository root, with its Python environment:

```sh
python results/behavior-preservation/reproduce.py
python -m pytest tests/test_preservation_cases.py tests/test_preservation.py tests/test_preservation_archive.py -q
```

The reproduction checks saved source/oracle identities and all eight independent
grades without a host or model. It does not replay native sessions, reconstruct
private configuration or establish fresh installed acceptance. Starting source,
gold/fault controls and public requirements are in
[`eval/preservation_cases.py`](../../eval/preservation_cases.py); independent
checks are in [`eval/preservation_oracles.py`](../../eval/preservation_oracles.py).
Each `SLOT.json` retains its original observation, source/protocol hashes,
protocol qualification and corrected grades. `SLOT-source-N.json` contains the
exact checked production text and `SLOT-protocol.json` the dated protocol.

Next qualify useful native command capture for ordinary host invocation forms
without weakening exact identity, retain independently justified larger-project
references, and observe advice consumption before default activation. Further
paid comparisons should wait for a specified opportunity to improve an actual
missed regression; these ties do not justify a broader benefit claim.
