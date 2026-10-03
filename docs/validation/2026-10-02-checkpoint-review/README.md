# Reproduce the fixed-patch review pilot

Eight Claude Sonnet 5 medium subscription reviews were completed, one ordinary
and one ElevenPowers-assisted review per case. Only new test files were allowed.
Every starting source, existing test and configuration input stayed fixed.
The [dated record](../2026-10-02-checkpoint-review.md) explains the outcome and limits.

The corrected 2026-10-03 reproduction detection counts are:

| Checkpoint | Untouched | Ordinary review | Assisted review |
|---|---:|---:|---:|
| ItsDangerous | 6/8 | 6/8 | 6/8 |
| Click | 2/8 + 1 setup | 2/8 + 1 setup | 2/8 + 1 setup |
| Jinja2 | 2/7 | 7/7 | 7/7 |
| attrs | 2/2 | 2/2 | 2/2 |

Jinja2 supplies five previously undetected, prior dual-rater meaningful faults
detected by both reviews. The incremental assisted advantage is zero in all
four selected pairs. Click's two dual-rater meaningful survivors involve FD
capture that is unsupported on Windows; they are not an exercised Windows gain
endpoint. Other unlabeled/disputed faults are exploratory. All twelve ordinary
suites pass, and all twelve formatting controls remain accepted.

All twelve grade sets were reproduced locally on 2026-10-03 in 1,461.765 seconds,
without new model calls. Nine match the historical states/counts exactly.
Click F03 produces actual failures together with 1,049 setup errors in all
three arms. The corrected evaluator retains `setup`, rather than crediting a
complete detection. The original 3/8 counts remain in the frozen case/review
JSON; [reproduction-2026-10-03.json](reproduction-2026-10-03.json) contains all
twelve current grades, grader hashes and the three explicit corrections.
This changes neither Jinja2's five-fault improvement in both arms nor the four
ties. `grades_match: false` is the expected comparison with historical grades.

`case-*.json` contains pinned upstream changes, complete frozen fault content,
prior labels where available and untouched grades. `reviews-*.json` contains
the eight new test files and grades, plus whitelisted native model/budget/scope
metadata. `observations-*.json` contains the retained whole-suite and frozen
focused-command engine audits, and the function-level feedback. No exact mutant
target was sent to a reviewer. Private prompts, transcripts, native tool payloads
and captured outputs are omitted.

`protocol.json` retains the original pre-call hashes and alternating schedule.
`producer-harness.json` preserves the five producer files' original byte identity
at commit `87c882d`. Current grading fixes are deliberately separate, so ordinary
inspection reports `current_harness: false`. That is an identity difference,
not permission to relabel the original producer. Regrading uses the corrected
current evaluator. The separately versioned reproduction records its hashes and
actual outcome. Hashes are unsigned internal consistency checks,
not authentication of the native run or authorship.

Inspect without tests or model calls:

```bash
python -m eval.review_archive --archive docs/validation/2026-10-02-checkpoint-review
```

For explicit regrading, prepare local Git caches containing the exact base
commits in the case files. The upstream origins are recorded; no download occurs
during regrading. Supply a JSON mapping such as:

```json
{"attrs":"LOCAL/attrs","click":"LOCAL/click","itsdangerous":"LOCAL/itsdangerous","jinja2":"LOCAL/jinja2"}
```

Use a trusted test interpreter with pytest 9.0.2, freezegun 1.5.5, hypothesis
6.168.0, cloudpickle 3.1.1 and MarkupSafe 3.0.2. The observed host used Python
3.13.2 on Windows; platform/version differences can change skip counts.
Cosmic Ray 8.7.0 generated the retained feedback and is unnecessary for grading
saved tests. The research interpreter inherited system site packages, so this
version list is an environment observation rather than a hermetic lock.

```bash
python -m eval.review_archive --archive docs/validation/2026-10-02-checkpoint-review --repositories cache-map.json --python TEST_PYTHON --regrade NEW_DIRECTORY
```

This explicitly executes trusted upstream code and saved tests in fresh private
copies, with a 120-second cap per suite. It launches no model, performs no install
and accepts no reused destination. Grade identities compare states and counts,
excluding elapsed time. Collection errors, invalid faults, timeout, empty output,
changed inputs and unavailable commands remain separate from detection. A
filesystem copy and native Bash tools do not establish an OS exposure boundary.

The Pallets fixtures retain BSD-3-Clause notices and attrs retains its MIT
notice in [licenses.json](licenses.json). AST-mutated source is a research fixture,
not a change distributed to those upstream projects.
