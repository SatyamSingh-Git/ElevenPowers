# Declared workflow feedback and report work

Status: shared feedback and guarded source-report repairs implemented; full
qualification and any needed installed requalification remain in progress.

[Feedback controls](feedback.json) retain actual Python/Node outcomes, exact
receipt refusal and bounded/concurrent advice. The
[combined affected group](affected-checks.json) passes 265 tests; counts overlap
the earlier targeted group and are not added together.

The [controlled report ablation](report-benchmark.json) uses three alternating
samples per mode/language, fresh 150-file inputs and five source receipts. Shared
opening/closing inspection reduces source scans from five to two. Local report
median times are Python 0.637→0.284 seconds and JavaScript-shaped inputs
0.633→0.286 seconds. This source-only component launches no host, model or project
check and does not measure full Stop or model workflow speedup. Late source or
configuration movement, incomplete reads and deadlines keep report text unverified.

Reproduce the work counts and new timing samples with Python and Git, using a
new output file so the original measurements remain intact:

```sh
python results/workflow-checks/reproduce_report_benchmark.py --output NEW_MEASUREMENT.json
python -m pytest tests/test_report_source_scope.py tests/test_declared_check_feedback.py -q
```

The [diagnosis](diagnosis.json) verifies original retained hashes and keeps actual
native callback samples separate from fresh component profiles. JavaScript's
compound/filtered test commands retain generic receipts but do not establish
exact declared milestones. Startup supplied owned instructions in both languages;
that does not prove the model used them. Shared capture currently supplies no
focused follow-up at the unqualified verification result.

Fresh no-model Python/Node Stop profiles, with strength explicitly disabled,
each perform seven source snapshots. Report rendering costs about 0.61 seconds
locally within 2.20/2.15-second Stop calls. These scoped observations identify
redundant work; they do not explain the entire earlier model-process time gap.

The proposed shared repairs add bounded on-use feedback and operation-scoped
source sharing in read-only reports, with fresh closing source/configuration
guards. They add no command inference from pipelines, automatic execution or
completion gate. The earlier [matched comparison](../matched-workflow/README.md)
and all original sources/grades remain unchanged.

See [design](../../docs/design/workflow-checks.md) and
[plan](../../docs/superpowers/plans/2026-10-17-workflow-declared-checks.md).
