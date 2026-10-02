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
changes clarified benefit fields and hardened budget validation. Task/evaluator
identities remain the same. Local checksums/hash chains are not authentication.
Candidate separation and process containment are not an OS security boundary.

## Delivery checks and next exit

Focused controls observed missing behavior RED before implementation; a real
NTFS read advancing access time exposed a snapshot bug, reproduced separately
RED and fixed by checking content metadata. Forward/adversarial cases cover
index neutrality, deletions, linked/oversized/moving inputs, command freshness,
unchanged native child decisions, conservative claims and bounded archive reads.
Final suite/review/CI evidence is recorded at the delivery boundary below.

Next proof exit: freeze held-out tasks where ordinary first proposals actually
contain an independently checked defect or stale source evidence. Observe the
existing intervention and whether it corrects that state. Preserve all ordinary
successes and failures; do not instruct baseline to fail or choose only favorable
runs. The current small comparison supplies a working measurement path, not a
marketing claim that ElevenPowers improves coding outcomes.
