# Reliable Declared-Check Execution v1 — validation

Status: corrected runtime qualified locally and in all four hosted cells; no new installed-host evaluation session.

## CI investigation

Main repeat [38623263659](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38623263659)
failed `test_actual_producer_keeps_replay_and_native_ingress_distinct[javascript]`
on Windows 3.13: 1 failed, 2,414 passed, 5 skipped in 2965.32 seconds. The original
assertion retained only `qualified=False`; no failing component summary artifact
exists for that cell. No cause or repair is established by that log.

Twelve subsequent local actual JavaScript exercises qualified. The diagnostic
change exposes the qualification predicates and includes the full result in
pytest failures. Existing producer tests passed 4/4 in 39.33 seconds.
[Diagnostic hosted run 38885046886](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38885046886)
passed all four OS/Python cells: twenty JavaScript exercises per cell, eighty
total, plus retained execution controls configured for thirty repetitions per cell. The original failure
remains unexplained; these are diagnostic coverage and successful repetitions,
not evidence of a repaired root cause.

## Witnessed controls

- Runner controls: 18 failures against the absent API, then 18 passed in 9.33s.
- CLI controls fail before the CLI exists; actual outer-shell masking, real
  child outcomes, read-only listing, invalid requests and private-output
  exclusion passed afterward. Actual CLI termination retains provisional evidence.
- Actual Python/Node integration: both controls passed in 31.18s. Each preserves
  `STALE/CURRENT -> FAILED/CURRENT -> CURRENT/CURRENT`, with launches `[3,1]`
  before missing-input refusal. The outer shell exits zero; all five synthetic
  post callbacks preserve the failed owned receipt.
- Startup executable guidance and guide/strict completion guidance were seen
  missing before implementation. The emitted invocation runs the actual CLI.
- A configuration-only change was initially conflated with source freshness;
  its regression failed before separating the execution association from source
  facts. Final qualification below supersedes intermediate runs.

## Limits and remaining qualification

Full regressions, independent gates, review repairs, hosted protocol/artifact
checks and all five rendered architecture views passed; see final results below. No installed session or model was
launched. Ordinary dirty/non-Git execution and exact committed PatchProof binding
remain distinct. No complete dependency discovery, universal safety, attestation
or causal coding-quality/latency improvement is established.

## Fresh branch review and repair

One fresh review found two Important defects: an undeclared generic outer
typecheck could supersede the owned failed receipt at obligation level, and
accepted allowances above 300 seconds inherited a 300-second child cap.
The authored tests had inspected declared test receipts too narrowly.

Independent regression controls reproduced both the typecheck and benchmark
outer-success laundering and the inherited cap: three failures, five passing
controls before repair. The repair suppresses generic evidence for literal
owned-runner envelopes and the bounded actual Windows encoded producer form;
it never credits arbitrary inner commands. Explicitly declared genuine checks
still work. The runner now passes its requested maximum to the shared deadline.

The review also noted lost protocol artifacts after failure. It is treated as an
acceptance-debuggability issue and repaired using the existing `if: always()`
artifact pattern. No new script-text assertion test was added for this workflow
configuration; hosted artifact retention is part of qualification. No second
review was dispatched; the single repair pass is verified by controls and the
final suite. No deferred Minor finding remains after this regrading.

## Corrected-runtime evidence retained

The repair group passed **121 tests in 69.81 seconds**. The standalone
[actual local protocol](../../results/declared-checks/local.json) qualified in
**45.957 seconds**, preserving both languages' independent milestone states,
actual owned failure through a successful outer shell, and missing-input refusal.
The corrected runtime also passed the four-case independent grader, all eight
retained source grades, eleven doctor checks and 107 named audits.

All five architecture views render, with **169 nodes, 413 edges and seven planes**.
The render found overflowing new labels; shortened labels then passed cards,
filters, keyboard navigation, shared links, contrast and narrow-layout checks.
The changed documentation's relative file-link targets were present.

[The final-candidate artifact](../../results/declared-checks/github-artifact.json)
was downloaded from successful job 117069962378 in run 38929622453.
Its canonical public bundle SHA-256 is
`17fb4d492d457f2e95c4115b64f4557653f645b99ea26abe3f05d65a6a3f863a`.
Independent job-log producer states were current/failed/incomplete, counts
`[1,1,1]`, and read-only `true`. Logged and embedded base/head identities matched
the declared subject; the missing typecheck remained absent. JSON and Markdown
sizes were 9418 and 4113 bytes. This is informational disposable transport.

[Raw runtime identities](../../results/declared-checks/runtime-identities.json)
cover 137 files. The local actual bytes, Git LF form and Windows CRLF form
differ only by newline representation; freshness remains strict over actual
bytes. Candidate `af6dfca` contains the corrected runtime, tests and workflow;
later result/map/documentation commits preserve those qualified inputs.

## Hosted corrected-runtime qualification

The [four portable host bundles](../../results/declared-checks/bundles.json)
were built into new disposable directories. Each included `ep_check.py`, matched
the local raw runtime identity and ran its packaged CLI against an actual failing
child: failed outcome and exit 1 in all four. This verifies distribution of the
entry point, not installed host execution or model adoption.

Run [38929622453](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38929622453)
qualifies candidate `af6dfca`. Completed Linux artifacts were downloaded and
independently checked for expected states, counts and exact producer identity.
Both include the grader, retained source reproduction, doctor and applicable
audit controls. All four hosted cells and the local full suite passed.

| Cell | Suite passed | Skipped | Suite seconds | Protocol seconds |
|---|---:|---:|---:|---:|
| Linux / Python 3.11 | 2452 | 9 | 575.26 | 3.107 |
| Linux / Python 3.13 | 2452 | 9 | 573.94 | 3.291 |
| Windows / Python 3.11 | 2456 | 5 | 3112.02 | 27.063 |
| Windows / Python 3.13 | 2456 | 5 | 3272.58 | 32.305 |

The named audit step passed 105 applicable controls with two platform skips in
each Linux cell. The protocol uses actual child processes with synthetic host
envelopes; it is not installed acceptance or a cross-platform speed comparison.

The completed Windows 3.11 job also passed all 107 named audits in 67.46 seconds,
the independent grader, retained source grades and doctor. Its downloaded
[declared-check artifact](../../results/declared-checks/hosted-windows-latest-3.11.json)
matches the Windows CRLF producer identity. Windows 3.13 also completed all gates;
its [artifact](../../results/declared-checks/hosted-windows-latest-3.13.json) passed
the same independent validation. The full local suite also passed; final results follow below.

## Review decisions and remaining limits

The implementation reuses the existing ownership, process and ledger primitives.
Execution-context metadata remains optional and separate from source-byte facts;
legacy receipts keep their original interpretation. An empty standalone task is
explicit local execution, without native provenance. Ordinary receipts do not
establish execution at a committed patch head; PatchProof binding stays separate.

Before/after observations cannot establish hidden or reverted edits, undeclared
or remote inputs, or resistance to deliberate local-state tampering. Literal
owned envelopes and the shipped Windows encoded form are recognized; arbitrary
renamed wrappers are outside this contract. Synthetic host callbacks and portable
bundles do not establish installed-agent adoption or causal coding benefit.

The clean existing checkout was reused to preserve installed dependencies and
actual runtime bytes. A native Windows ledger replaced an unavailable shell
workspace helper, accepting weaker checkout isolation and manual task tracking.
One fresh review and its single repair pass were checked against real controls
and the full gates; uncovered edge cases remain possible. No Minor finding was
deferred after the failure-artifact issue was regraded and repaired.

## Final local gates and delivery

The full local suite passed **2458 tests, 3 skipped, in 4971.66 seconds**. The named audit run passed **107/107 in 105.87 seconds**. Independent grader 4/4, retained source grades 8/8, doctor 11/11, standard-library imports and all five rendered views passed.

[Machine-readable qualification](../../results/declared-checks/qualification.json) retains the exact candidate and all four hosted results. Main integration uses a normal fast-forward of the same qualified runtime/test/workflow inputs, followed by remote identity and published-body checks. A later documentation closure does not requalify a changed runtime. The original advice CI cause remains open; no new model evaluation session or causal coding-benefit claim.
