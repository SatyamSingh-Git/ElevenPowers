# GitHub evidence presentation — 2026-10-13

Scope: a generalized read-only PatchProof presentation API, CLI and GitHub cloud
composite Action. No installed-host/model session, new coding comparison,
automatic correctness gate, PR comment or Check Run was run or added.

Runtime/Action revision after review repairs:
`b7627614dcc48ed048ba1647aedbadd433cd346f`.
Documentation and architecture follow separately. Final local and hosted gates
passed; publication identity is recorded below after the authorized main update.

## Baseline reliability and established repair

The prior final-code [matrix 38286815118](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38286815118)
passed. Its later main [repeat 38291777650](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38291777650)
failed the creation-handoff survival assertion on Windows 3.11 and 3.13 while
both Linux cells passed. That repeat is retained, not replaced by the earlier
green qualification. Windows 3.11: 1 failed, 2,126 passed, 4 skipped in 1452.40s;
Windows 3.13: 1 failed, 2,126 passed, 4 skipped in 1304.73s.

An actual twenty-attempt local probe returned cached exit 1 but kernel wait
258 (not terminated) in nineteen attempts. CPython's Windows `terminate()` can
cache an exit code after access-denied while asynchronous termination completes;
`wait()` then returns that cached code without waiting on the original handle.
The new original-handle assertion failed before repair in 0.34s. `_reap`
now waits on that handle using the remaining existing cleanup allowance.
Survival assertions and the five-second cleanup deadline were retained.

Process/host/recovery controls: 31 passed, 2 skipped in 18.10s. Five local
expanded repetition rounds passed in 12.713s. Hosted
[38297117685](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38297117685)
passed all four OS/Python cells with thirty expanded rounds each. The added
controls use finite aggregate allowances of 240s for ten rounds and 600s for
thirty; this is a larger diagnostic allowance, not a latency improvement.
Earlier unrelated POSIX cleanup, quoted-launch and SQLite incident causes remain
unresolved; green repeats do not establish their repair.

## Forward and adversarial controls

The presentation wraps the existing bundle without changing verdict semantics.
Controls cover exact fork/base/head context, wrong repository and synthetic
merge, strict bounded events, stale/dirty/unavailable input, actual Node TAP
receipts, literal Markdown, known credentials, output bounds, omission counts,
hash mismatch, new external directories and no overwrite.

Task 2: fourteen missing-module failures, then fourteen passing controls in
22.01s; actual Node acceptance brought the task to fifteen passing in 25.32s.
Task 3: seven missing-module failures; its prototype passed six but lost
row-omission notes in fallback. A further failing control caught coverage counts
being lost. Repairs preserved both; final seven passed in 23.13s.
CLI: nine initial failures and one missing-CLI negative refusal, which was not
credited as metadata validation. Its reason assertion was strengthened; ten
controls then passed in 13.10s. The actual-command exercise failed before its
module existed, then passed in 14.05s. Final CLI/exercise controls passed eleven
in 61.25s. Authored interrupted checks use a two-second launch allowance; no
product or prior individual quoted-launch deadline was relaxed.

The independent disposable exercise executes assertions once in each of three
separate projects, retains `current`, `failed` and `incomplete`, and includes an
absent typecheck. Check counters are `[1, 1, 1]`. Presentation leaves each
project's file bytes unchanged and never reruns these checks. This is capability
acceptance, not population coding benefit or real installed-host acceptance.

## One independent review and one repair pass

One fresh-context GPT-6-astra high review of the whole branch returned three
Important findings, no Critical or Minor findings. All three were independently
reproduced and regraded correct by effect:

1. Credential-shaped public dictionary keys leaked despite value redaction.
   Public export now scrubs keys and refuses collisions, preserving private
   configuration/ledger identities.
2. Hard-linked runner targets outside the project could modify source bytes.
   Preflight and opened-descriptor checks require exactly one hard link.
3. A cold vendored runtime wrote bytecode inside inspected source because
   isolated Python ignores the environment cache setting. The CLI suppresses
   caches before imports, and both Action calls add `-B`.

Five new controls failed in 14.68s, then complete GitHub and existing portable
report controls passed **60 in 87.60s**. An accidentally displaced test tail was
restored before the green run. A command naming nonexistent `test_export.py`
ran no tests and is not counted as evidence. There was no second review.

Declined review scopes remain explicit: generic saved-bundle import, external
write-token publishing, independent event/repository authentication, live
PR/fork publication, GHES transport, universal secret detection, hostile
concurrent parent replacement and atomic filesystem snapshots. These are limits,
not implicitly accepted guarantees. No Minor/Deferred findings were returned.

## Actual GitHub producer and downloaded bytes

The [initial real Action acceptance](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38300130371/job/114980761111)
passed at `0bcb5b42f82daea744eaa4256c402065fa6cfad8`, before review repairs.
It wrote a hosted summary, used the pinned official MIT v4 uploader and
attached its actual URL. Artifact ID `11769613874`, archive digest
`0a19062e1c67da72e6e59d7246978c2abce429541990f8656c7d934417a9348c`.
Downloading yielded only `evidence.json` (7,848 bytes) and `summary.md`
(3,470 bytes). Recomputed canonical bundle digest:
`c85b2c6f3cfd9cdb91b90331b24150922789c74efe4acc9faca774256306e3ad`.

The exact disposable subject was base
`4e696acad8d6b8befa6993c1e32756b33efa7aa9`, head
`323d1819b4f737340a734bfcd0f82914b1c45c1a`, patch
`c3cd24636b814ddf7e76766ebb308f593276512580306607517b5fbc3cb06268`.
The downloaded bundle retained `current` and `absent`; the summary retained
full identities, coverage counts and its “not patch safety” qualification.
Declared fixture repository context does not authenticate ownership. Dispatch/
push hosted exercises do not qualify live PR/fork transport; PR-shaped offline
controls and the actual PR API metadata read establish only their declared scope.

The initial full matrix ultimately failed its Windows 3.11 cell:
`test_reference_worker_setup_does_not_spend_competing_claim_barrier_budget`
raised `PermissionError`/WinError 32 deleting its temporary `jobs.db`. It reported
1 failed, 2,160 passed, 4 skipped in 1595.23s; the other three suite cells and
presentation job passed. The log establishes a retained open-file symptom, not
which process held the file or a demonstrated SQLite/runner repair. The final
post-review matrix remains a separate qualification, not a replacement for this
failure. No assertion, cleanup deadline or correctness grade was weakened.
Both unchanged reference controls passed in five local repetitions (7.31,
7.05, 7.04, 7.00 and 7.02 seconds per pair). This did not reproduce the hosted
open-file symptom and does not establish its cause or repair.

## Final qualification and publication

Post-review hosted presentation passed again in
[38302638722](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38302638722).
Its actual artifact ID is `11771766692`, archive digest
`6bd54165e09232ffe0ffcd8771fc3c0444fb824c6dbb44c5f806a1b6641e8d75`.
Downloaded files: JSON 7,849 bytes, Markdown 3,470 bytes. Recomputed canonical
bundle hash `1ca29132df620c75da05fe9270822f733c73b65ff5af0e345ed3f982d5065ad7`
matched. Exact subject base `d24809895b04ad4c1a46f9d1ae8bd423d8ca8707`,
head `2436ae0b2b448d4e4917e48bddc313a354689613`, patch
`28f2ae5330bfaaaccedb9e5e68edd243f4b1d8b16dea412e2048e683e702a5f8`.
The downloaded summary and JSON preserve `current`/`absent`, full identities,
coverage counts and the informational qualification. Archive and bundle hashes
remain distinct; neither creates authenticated attestation.

Named audit probes: **107 passed in 90.32s**. The grader's four cases passed;
saved independent staged source grades reproduced without rerunning native
sessions or advice-use experiments. Host doctor checks and stdlib-only new
imports passed. Architecture rendering passed all five tabs, cards, filters,
keyboard, shared links and narrow layout: **153 nodes, 363 edges, seven planes**.
Changed Markdown local-link check resolved 572 targets at this stage.
Qualified local raw runtime fingerprint:
`675c4576688d7874fba3a474061221423a96e120eed95da4a8d9b9f479b10c13`.
This identity is local source bytes; hosted platform checkout bytes can differ.

Post-review runtime matrix
[38302638722](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38302638722),
at the exact post-review revision completed successfully in all five jobs.
Each suite cell also passed its ten expanded reliability repetitions, stdlib
imports, independent grader/source reproduction and host doctor.

| Cell | Full regressions | Named audits |
|---|---|---|
| Windows / Python 3.11 | 2,166 passed, 4 skipped / 1641.03s | 107 passed / 76.72s |
| Windows / Python 3.13 | 2,166 passed, 4 skipped / 1614.63s | 107 passed / 53.97s |
| Linux / Python 3.11 | 2,162 passed, 8 skipped / 351.09s | 105 passed, 2 skipped / 22.20s |
| Linux / Python 3.13 | 2,162 passed, 8 skipped / 365.79s | 105 passed, 2 skipped / 17.83s |

Platform/privilege skips retain their qualified scope; these are not four
identical denominators. The presentation job separately passed actual cloud
transport. The earlier failed SQLite cleanup remains unresolved; this passing
matrix does not establish its repair. Subsequent changes so far are only docs
and architecture, with runtime/test/evaluation/Action/workflow files identical
to the qualified revision.

The final local full suite passed **2,168 tests, 2 skipped in 2585.32s
(43m05s)**, exit 0, after the single review repair pass. Named gates above and
the completed four-cell hosted matrix qualify this runtime; the difference in
local and hosted durations is not a performance-improvement result.
Final documentation changes do not alter runtime/test/evaluation/Action/workflow
files. All changed local Markdown links resolved (574 at release), and the final
architecture render again passed all five views and contributor interactions.

The complete delivery was normally fast-forwarded and pushed to main at
[`b36bbe5ad292a604f58786df3924bc21edc0c99e`](https://github.com/SatyamSingh-Git/ElevenPowers/commit/b36bbe5ad292a604f58786df3924bc21edc0c99e).
Both main and `codex/github-evidence` remote refs matched that commit. The
inactive-ref/identical-tree switch preserved the local qualified runtime byte
fingerprint above. The publication-record follow-up changes documentation only.
Automatic main [repeat 38307508233](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38307508233)
was still running when this record was written. It is separate from the completed
final-code qualification, never credited as passing before completion. Pages
publication and the served architecture bytes are checked independently.

See [guide](../../the-guide/patchproof-github.md),
[design](../design/patchproof-github.md) and
[journey](../../journey/77-the-upload-is-not-the-evidence.md).
