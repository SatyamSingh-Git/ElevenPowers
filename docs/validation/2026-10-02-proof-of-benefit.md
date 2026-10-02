# Controlled completion comparison — 2026-10-02

The new comparison completed eight subscription coding calls on installed Claude
Code 2.1.287, using `claude-sonnet-5-5` at medium. All eight final candidates and
all eight first proposed candidates passed the independent 16-check evaluator.
**No improvement in patch correctness was observed.** There were no completion
blocks or subsequent code repairs. This does not show the tool cannot help;
it shows these proposals left no correctness defect for it to repair.

The plugin did supply additional current verification evidence. Three of four
treatment proposals had no exact declared-command receipt before completion;
the ordinary guide completion ran the declared check and saved a fresh success.
The fourth already had fresh evidence. At final completion, **4/4 treatment
and 1/4 baseline runs had a recorded fresh exact-command success**. Missing
means absent exact-command evidence, not proof that baseline skipped testing:
wrapped commands can have run successfully without meeting that declaration.
This is a measured receipt-coverage improvement, not demonstrated better code,
faster delivery, avoided bugs or a general effect estimate.

## Frozen design and actual conditions

Two original cases: repair an atomic/idempotent bank update, and refactor a
correct view implementation while preserving behavior. Two arms and two repeats,
240 seconds per call. Arm order reversed in the second repeat. Issue, initial
files, visible checks, project conventions, tools and exact model/effort matched
within each pair. A passive observer ran in both arms; only treatment delegated
to ordinary ElevenPowers guide hooks. Mutation engines were disabled. No prompt
asked the baseline to omit or weaken verification. The original inconclusive
pilot remains unchanged in its earlier dated record.

The native preflight established startup/edit/failing-command/passing-command/
completion and fresh pipeline health under the same account as the CLI. Both
actual preparation attempts are retained. The first used `cd ... &&` and
`; echo ...` wrappers and produced no declared receipts. Generalized exercise
instructions now require standalone calls. The second established exact fail/
pass receipts and observed pipeline health, but its intended interruption was
not retained as incomplete. Full acceptance therefore remains **0/10**. Codex
delivery and the other host/language cells remain open.

Owner-account scans excluded a host-config file through Git policy; a sandbox
account could not read that same policy and selected it as an additional input.
Its stale result was correct for that selection. Inspect native receipts with
the same account/ignore policy as their producer; do not convert stale to fresh
by ignoring the difference. No runtime branch names Snag or this fixture.

## Results and costs

| Case / repeat | Baseline first / final | Treatment first / final | Treatment completion receipt |
|---|---|---|---|
| Atomic repair / 0 | 16/16 → 16/16 | 16/16 → 16/16 | fresh → fresh |
| Correct control / 0 | 16/16 → 16/16 | 16/16 → 16/16 | missing → fresh |
| Atomic repair / 1 | 16/16 → 16/16 | 16/16 → 16/16 | missing → fresh |
| Correct control / 1 | 16/16 → 16/16 | 16/16 → 16/16 | missing → fresh |

Elapsed run samples (seconds, schedule order within arm): baseline 21.875,
18.242, 19.601, 17.120; treatment 39.442, 22.690, 29.163, 19.604. Medians were
18.921 and 25.926 seconds respectively. These include model and verification
time; four samples per arm do not establish performance differences or pure
plugin overhead. Calls used subscription authentication and no API fallback.

## Reproduce without model calls

The [archive](2026-10-02-proof-of-benefit/completion-archive.json) includes all
eight run records, immutable protocol, before/after proposal snapshots and final
synthetic source snapshots. [Qualified summary](2026-10-02-proof-of-benefit/qualified-summary.json)
separates receipt gains from coding gains. The original producer
[summary](2026-10-02-proof-of-benefit/recorded-summary.json) is preserved: its
earlier generic `benefit_observed: true` meant receipt refresh and is superseded
by the qualified interpretation. No candidate or observation was replaced.

```bash
python -m eval.benefit_archive docs/validation/2026-10-02-proof-of-benefit/completion-archive.json
python -m eval.benefit_archive docs/validation/2026-10-02-proof-of-benefit/completion-archive.json --regrade
```

The first command only inspects bounded whitelisted records. The second
explicitly executes the independent evaluator against disposable reconstructions
of every saved proposed/final candidate. All **24 snapshot grades matched**.
`current_harness: false` preserves the earlier frozen producer identity; later
changes clarified benefit fields and hardened budget validation, preparation
seals, capture completeness and failure journals. Task/evaluator sources were
unchanged for the original runs. `current_evaluator` reports whether recorded
grader bytes match this checkout; line-ending conversion can change that flag.
Explicit regrading uses this checkout's evaluator and compares saved grades;
it never replaces the recorded identity. Local checksums/hash chains are not authentication.
The checksum manifest hashes canonical JSON, so Git checkout newline conversion
does not break consistency checks; pass `--checksums CHECKSUMS.json` explicitly.
Candidate separation and process containment are not an OS security boundary.

## Delivery checks and next exit

Focused controls observed missing behavior RED before implementation; a real
NTFS read advancing access time exposed a snapshot bug, reproduced separately
RED and fixed by checking content metadata. Forward/adversarial cases cover
index neutrality, deletions, linked/oversized/moving inputs, command freshness,
unchanged native child decisions, conservative claims and bounded archive reads.
Final suite/review/CI evidence is recorded at the delivery boundary below.

The fresh whole-branch review identified four important future-run gaps:
an earlier valid history could hide a failed later capture; active project
settings and prepared inputs were not fully sealed before later launches;
the grading entry point was absent from the harness identity; and setup/auth
failures could occur before a durable batch journal. Eight regression cases
failed first and passed after one correction pass. New protocol version 2
seals candidates during preparation, records a batch attempt before preflight,
reconciles independent Stop attempt markers and treatment native Stop counts,
and includes the grading entry point in its fingerprint. The original eight-run
archive remains unchanged and valid under its recorded producer; these controls
strengthen subsequent comparisons rather than retroactively relabeling it.

A separate archive portability regression failed before the reader was changed
to retain a different recorded evaluator byte identity. Task/prompt changes
remain rejected. The reader intentionally handles the original eight successful
records; future failed batch journals remain available in their batch directory.

The first delivery suite also exposed two old fixture assumptions: ratchet and
old-tree stress non-Git controls used temporary paths that inherited the checkout
when `--basetemp` was inside the writable workspace. Both failed independently
before correction. The fixtures now use Git's discovery ceiling and assert a
real `git rev-parse` failure before checking unknown/no-snapshot behavior. All
7 ratchet and 32 stress controls passed. Production Git behavior was unchanged.

Delivery controls observed before publication:

- Recorder/comparison/review boundaries: **28 passed**; archive controls:
  **5 passed**, including the observed evaluator-identity regression.
- Named audit probes: **104 passed in 127.24 seconds**.
- Independent grader validation: all **4/4** fix/regression/unfixed/setup cases
  classified correctly. All **24** saved candidate grades matched again, with
  canonical archive checksums verified.
- Standard-library imports passed with `python -S`; host doctor passed; the
  owned exact-command native fixture still passed `ep_ready.py --check` with
  fresh source/receipt observations and no new model call.
- Architecture: **104 nodes, 237 edges, 7 planes**; all four tabs rendered.
- Two non-Git fixture corrections: **7** ratchet and **32** stress controls
  passed independently after each reproduced failure.

The first complete suite recorded **2 failed, 1,268 passed, 28 skipped** in
1,164.09 seconds. The two failures were the corrected fixture assumptions above.
The skips were 26 optional language-grammar cases and two POSIX-only process
cases on Windows. A fresh corrected complete suite and the four hosted
Windows/Linux × Python 3.11/3.13 jobs are required before publishing to main.
The [tests workflow](https://github.com/SatyamSingh-Git/ElevenPowers/actions/workflows/tests.yml)
retains the exact commit and final hosted results; final delivery reports use
that result rather than treating targeted controls as the full gate.

The fresh whole-branch reviewer reported no Critical or Minor findings. All four
Important findings were corrected in one RED→GREEN pass. Broader effectiveness,
full installed-host acceptance, authentication/security isolation and arbitrary
future failure-archive qualification remain outside these measured results.

The corrected local Windows suite subsequently passed **1,270 tests with 28
skips in 882.00 seconds**. Its longest existing check was the no-test completion
gate at 304.15 seconds. Hosted CI on `0858e21` passed both Linux jobs but exposed
one snapshot-grade failure on both Windows jobs. A real Windows short-name probe
reproduced the cause: the snapshot was complete, while the frozen contract
compared canonical file paths with an unresolved temporary-root alias and
returned unavailable. Equivalent `child/..` roots reproduced it independently.
Canonicalizing the root preserves the boundary and accepts these equivalent
paths. Both new regressions failed before correction, and all 24 archived grades
still matched afterward. All **35** affected recorder, comparison, boundary and
archive controls passed in 29.89 seconds. All four architecture tabs rendered
again after the path-boundary documentation update. This changes no frozen task, evaluator assertion or
recorded candidate; hosted full gates are repeated on the corrected head.

Next proof exit: freeze held-out tasks where ordinary first proposals actually
contain an independently checked defect or stale source evidence. Observe the
existing intervention and whether it corrects that state. Preserve all ordinary
successes and failures; do not instruct baseline to fail or choose only favorable
runs. The current small comparison supplies a working measurement path, not a
marketing claim that ElevenPowers improves coding outcomes.
