# Command-scoped witnesses and shared collection — 2026-10-14

Final qualification is in progress. Do not treat the earlier pre-review protocol
or the first failed qualification attempt as final-runtime release evidence.

The installed-observation runtime fingerprint was
`06f5bc356d5cac035cd9334e3737887c6ee9c215050570a8a5d553c77ecde7e3`.
The reviewed repairs and new regressions are committed at `3201312`.
The first hosted qualification ran at
[38610603850](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38610603850).
Its Linux Python 3.13 cell failed: 23 failed, 2,389 passed and 8 skipped in
529.15 seconds. A real Markdown formatter shadowing bug caused most failures;
older regression probes also targeted interfaces/read counts changed by this
milestone. The formatter correction passed all four actual CLI export tests in
21.21 seconds. Race probes now target actual collection/source boundaries,
forward scope arguments and assert that the injected mutation occurred. The
remaining hosted jobs and the local full run at 20% were stopped rather than
treated as qualification. A fresh full run is required after the repair group.

All seven retargeted adversarial cases passed in 165.26 seconds. The final
candidate is `25a9771`; the runtime differs from `3201312` only by the formatter
alias correction in `core/patchproof/report.py`. Fresh qualification runs at
[38613186556](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38613186556).
The local full suite is running on raw runtime identity
`7c435fe720b68fe1948b6dafdb8492a81262334f9a1388ed2673b31d9408ba92`.
All 135 runtime Git blobs were compared with local files: only checkout newline
representations differ. [Recorded identities](../../results/command-input-scopes/runtime-identities.json)
are not normalized by runtime freshness checks.

## Witnessed controls

Actual Python/JavaScript consumers exercise independent command scope,
partial/unmatched broad fallback, legacy receipt retention, native identified
pairing, owned execution and exact-patch reuse. Opening/closing descriptor reads
delegate to the real producer. New controls were observed failing before their
implementation; intermediate results and limits remain in
[the preliminary record](../../results/command-input-scopes/README.md).

One fresh whole-branch review found three Important issues, no Critical or Minor.
All eight regressions failed before the single repair pass. The repaired group
passed **30 tests in 311.06 seconds**, including the stronger sole-required-command
case with an unused missing witness. Repairs refuse ambiguous redacted command
identities, retain per-command saved execution and source qualification, defer
public invalidation until original source comparisons finish, admit required
scopes independently, and clear late external association fields consistently.

## Installed allowance

The user approved two Claude Code subscription conversations, Sonnet 5.5 medium,
at most 180 seconds each, with no API fallback. Each conversation can perform a
coding task and a resumed evidence-review task under the same UUID and shared
deadline. Actual host callbacks must create distinct task identities. Model-free
producer/reference/oracle rehearsals passed for both languages before launch.
Both conversations returned successfully under the cap: Python 62.547 seconds,
JavaScript 63.477 seconds, with model-process wall time including cleanup of
60.928 and 62.000 seconds. Both host-created distinct task identities, protected
inputs were unchanged, and both fixes passed the independent four-case arithmetic
oracle. The first-task milestones were `CURRENT/CURRENT`; after first-input drift
and the second task they were `STALE/CURRENT`. Each agent reran only the affected
command (delta `[1,0]`).

Full installed exact-failure acceptance remains incomplete. Inspection of the
actual generated conversations showed both agents appended `; echo "exit=$?"`
to the declared failing command. That shell chain did not match the exact
declaration, so no new declared failure receipt was attributed. The conservative
mapping behavior stands; do not treat a trailer's exit status as the inner
command's success or invent an exact identity. Controller continuation separately
observed `passed/failed` with only the affected command rerun. See
[retained installed observations](../../results/command-input-scopes/README.md).

The GitHub artifact job passed; downloaded JSON/Markdown are 9,418 and 4,113
bytes. The canonical bundle SHA-256 recomputed as
`7bb6ad7f9e74a96ee22fa14f8b631fa9d9ebddceeef824b0a201c22d0c749d56`.
Declared base/head/patch/content identities match the embedded bundle; current
and absent required checks and bound external receipt qualifications are retained.
The remaining full local and hosted matrix gates must be rerun after the
formatter repair. The installed observations remain at their recorded identity;
no new installed claim is made for the later formatter-only runtime change.

## Interpretation and limits

Complete mappings are trusted project declarations. Unknown, partial, redacted
and old broad identities cannot license narrowing. Every declared check remains
required. An unavailable unrelated witness remains an overall coverage gap while
an independently available complete command scope may run or reuse its evidence.
Source/configuration/producer/task guards remain separate.

Collection still reads the configured union with aggregate budgets. The two-phase
report context lives only inside one operation and root; it never shares source
snapshots or execution phases. A bounded late stamp/declaration/approval guard
does not add a third byte read. These are sampled unsigned local observations,
not atomic snapshots, malicious-state attestation, complete-environment coverage,
or detection of reverted changes. Command counts and selected-file reads do not
establish total latency, population performance or improved coding quality.
