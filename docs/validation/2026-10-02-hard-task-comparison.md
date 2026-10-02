# Four interacting repair tasks — 2026-10-02

Eight subscription Claude Sonnet 5 medium slots were attempted on installed
Claude Code 2.1.287: one baseline and one ElevenPowers guide run for each task,
with 480 seconds per call. Seven completed; the async-cache tool slot was
interrupted. Every completed first proposal and final candidate passed all its
frozen hidden groups. The three completed pairs tied. **No coding-correctness
improvement, causal repair or speed improvement was demonstrated.** The overall
comparison is inconclusive because one planned slot did not complete.

Ordinary completion added fresh exact-command success records in all three
completed tool runs. Recorded final coverage was **3/3 completed tool runs**,
or **3/4 attempted tool slots**, versus **0/4 baseline runs**. Missing records do
not prove baseline skipped testing: wrapped commands may have executed the same
visible tests without matching the declared standalone command. This is additional
retained verification evidence, not proof of better code.

## Tasks and independent controls

These are authored synthetic repairs with four planted faults per task, not
sampled real repository issues or a validated difficulty benchmark. The initial
implementations were made by applying those faults to authored correct references.
The larger interaction contracts address the earlier comparison's ceiling, but
their size alone cannot establish difficulty for a particular model.

| Task | Interacting contract | Hidden groups | Initial faulty code |
|---|---|---:|---:|
| Durable lease queue | SQLite transactions, competing workers, tenant isolation, fencing tokens, exact expiry, durable acknowledgment and renewal | 23 | 17/23 |
| Async cache | Coalescing, cancellation shielding, TTL/LRU, invalidation generations, tenant isolation and shutdown | 22 | 13/22 |
| Incremental build planner | Old/new dependency propagation, removed and added nodes, cycles, deterministic order and input preservation | 24 | 13/24 |
| Resumable byte stream | Split UTF-8, record identity, checkpoint restoration, exact offsets and rollback of malformed chunks | 25 | 8/25 |

The controller owns literal expected traces; candidate workers return bounded
behavior rather than grades. The queue probe uses eight real competing worker
threads over 32 jobs; cache probes use controlled asynchronous event schedules.
Before any coding call, the four correct references passed all **94 groups**, and
all **16 single-fault controls** were rejected. One initially equivalent planner
mutation was replaced with a genuine one-hop propagation fault before freezing
the suite. Unicode canonicalization was made explicit in the stream contract
before any coding call. Hidden assertions never supplied completion feedback.

## Frozen conditions and observed outcomes

Both arms received matching task text, initial source, visible checks,
conventions, allowed files, model, effort, tools and call budget. A passive
before/after Stop recorder ran in both arms; treatment alone delegated to ordinary
ElevenPowers guide hooks. Optional mutation engines were disabled. The editable
surface was `app/service.py`, `app/helpers.py` and `tests/test_regression.py`;
seed tests and configuration stayed frozen. Arm order alternated across tasks.
Authentication used the Claude subscription, with no API fallback.

| Task | Baseline first → final | Tool first → final | Baseline seconds | Tool seconds |
|---|---|---|---:|---:|
| Lease queue | 23/23 → 23/23 | 23/23 → 23/23 | 167.963 | 158.212 |
| Async cache | 22/22 → 22/22 | No Stop; interrupted saved code 13/22 | 399.357 | Unknown |
| Build planner | 24/24 → 24/24 | 24/24 → 24/24 | 120.849 | 102.295 |
| Resumable stream | 25/25 → 25/25 | 25/25 → 25/25 | 156.339 | 165.096 |

Each completed run proposed Stop once and was allowed. No block or code repair
after a block occurred. The three complete matched pairs cover **72 hidden groups
per arm** with no correctness difference. Timing includes model, recording,
grading and ordinary verification work. Two paired samples were faster with the
tool; one was slower. Matched-pair arm medians were **156.339 seconds baseline**
and **158.212 seconds tool**. Four-versus-three unmatched medians would omit the
long cache treatment and mislead; these few samples establish neither throughput
gain nor pure plugin overhead.

The initial producer was `db67dc9`; continuation executed from `be17b5b`.
Task, scenario, model, effort, runtime and budget identities stayed unchanged.
The [context](2026-10-02-hard-task-comparison/evaluation-context.json),
[summary](2026-10-02-hard-task-comparison/summary.json) and
[archive](2026-10-02-hard-task-comparison/completion-archive.json) retain both
producer identities and every attempted slot.

## Interruption and continuation

After two completed queue runs, the comparison controller and a concurrent
full-suite process exited abruptly during the async tool slot, with no traceback.
No destructive candidate command or surviving comparison-owned model process was
established. The cause is unknown. The interrupted source and original running
journal were retained; that slot was not retried or counted as a completed call.
Its elapsed time is unknown, not zero or the allotted maximum.

The explicit `--finish-unstarted` operation launched only the five never-started
slots. Recovery is hard-suite-only, one-shot and refuses a live recorded
controller. The legacy journal lacked a PID, so controller exit was established
before continuation. The original attempt remains historical; the continuation
records its new executor hash separately. All eight approved slots were consumed;
no extra model call sought a favorable outcome. This accidental interruption does
not close the intentional native incomplete-command acceptance requirement.

## Fresh review and separate saved-code audit

The fresh reviewer found three Important issues and no Critical findings:

- Final sealing omitted nested instruction paths frozen at preparation. A
  failing regression was reproduced, then sealing was corrected. No such added
  instruction file was observed in the eight actual candidates.
- A candidate could pass the hidden score while its added regression failed.
  The hidden `regressions` field covers only two basic guards per task. A separate
  audit now executes the preserved and added visible suite explicitly.
- The frozen cache scenarios missed shutdown with both an invalidated old fetch
  and a new fetch pending. A separate black-box audit now checks old-only and
  old-plus-new shutdown. The reproduced old-fetch leak is retained as evidence
  of the frozen grader's coverage limit.

Each regression failed before its correction and passed afterward. The original
94-group evaluator and scores were preserved. The
[supplemental audit](2026-10-02-hard-task-comparison/supplemental-audit.json) is
versioned separately and was authored after the run began; it must not be
presented as part of the frozen score.

All **seven completed final snapshots passed their visible suites**. The complete
baseline cache also passed both supplementary shutdown probes. The interrupted
tool snapshot's visible suite **timed out**, and it **failed old-plus-new fetch
closure** while passing the old-only case. It stays unqualified. A partial saved
candidate is not a final model proposal, and these observations do not establish
that the plugin caused its defect or the controller interruption.

## Reproduce without models

```bash
python -m eval.hard_archive docs/validation/2026-10-02-hard-task-comparison/completion-archive.json --checksums docs/validation/2026-10-02-hard-task-comparison/checksums.json
python -m eval.hard_archive docs/validation/2026-10-02-hard-task-comparison/completion-archive.json --regrade --checksums docs/validation/2026-10-02-hard-task-comparison/checksums.json
python -m eval.hard_audit docs/validation/2026-10-02-hard-task-comparison/completion-archive.json --output NEW_AUDIT.json
```

Inspection reads bounded whitelisted records and executes no saved source.
Explicit regrading reproduced **all 22 saved grades**: seven before/after
proposal pairs and eight final snapshots, including interrupted code. The
earlier comparison's **24 grades** also still matched with its checksums verified.
Explicit audit executes reconstructed saved code under isolated local processes;
neither candidate separation nor process containment is an OS security boundary.

`current_harness: false` preserves the initial producer's identity through the
recovery and audit changes. `continuation_harness_current: true` and
`current_evaluator: true` matched at publication inspection. Checkout line-ending
conversion can change a byte-identity flag; explicit regrading compares outcomes
without replacing the producer. Canonical JSON checksums survive newline
conversion. Local checksums, native observations and hash chains are unsigned.
Public records contain the synthetic source, whitelisted observations and
provenance, not model transcripts, outputs, authentication identity or project roots.

## Delivery checks and next exit

Nineteen new regression controls cover independent hard cases, runner selection,
every-attempt archives, separate audits and interruption recovery. Focused checks
included **25 original/runner/archive compatibility controls**, **six final
audit/archive controls**, standard-library-only imports and unchanged native
`ep_ready.py --check` health. The architecture maps **105 nodes / 240 edges /
7 planes**, including the new modules; all four tabs rendered.

All four hosted Windows/Linux × Python 3.11/3.13 jobs passed on `e650248`:
[exact-code CI](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/37021310922).
The workflow also ran the named audit probes, grader controls, standard-library
imports and host doctor. Windows jobs each passed **1,290 tests with 30 skips**;
Linux jobs each passed **1,288 tests with 32 skips**. The separately named audit
checks passed **104** on Windows and **102 with two skips** on Linux; the old
grader classified all **four** controls correctly on every job.
The first local full-suite attempt exited abruptly during model execution and
is not a pass. The fresh final Windows suite, run after all model calls ended,
passed **1,292 tests with 28 skips in 986.78 seconds**. Pass/skip counts differ
between environments; all runs collected 1,320 tests. Documentation link and
artifact-denominator checks also passed.

The proof exit remains open: measure ordinary defective or stale proposals and
their actual correction on held-out work, retaining correct, failed and
interrupted outcomes. Use representative real issues with independent behavioral
checks, and qualify any new grader before another frozen comparison. Do not
instruct baseline to fail, expose hidden targets or retry only unfavorable slots.
This delivery makes the test and adverse outcomes reproducible; it does not
justify a claim that ElevenPowers improves coding quality or speed.
