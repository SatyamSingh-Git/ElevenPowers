# Fresh matched multi-stage comparison

**Both pairs tied on independently checked correctness. Assisted execution was
slower in both cases; no coding-quality or speed improvement was observed.**
All four scheduled Sonnet 5.5 medium subscription conversations completed their
four requests and qualify for outcome comparison. All sixteen exported source
snapshots independently reproduce their original grades. No API fallback,
favorable retry, case replacement, hidden-grade feedback or human candidate
repair occurred between stages.

| Authored case | Ordinary cumulative groups | Assisted cumulative groups | New regressions, ordinary / assisted | Final assisted difference | Model-process seconds, ordinary / assisted |
|---|---|---|---|---|---|
| Python queue | 4 / 6 / 8 / 10 | 4 / 6 / 8 / 10 | 0 / 0 | 0 | 120.899 / 283.349 |
| JavaScript orders | 4 / 6 / 8 / 10 | 4 / 6 / 8 / 10 | 0 / 0 | 0 | 88.215 / 167.510 |

The counts include two established groups plus two introduced per stage: ten
distinct final groups per case, not 28 distinct behaviors per arm. Both arms
pass all applicable groups at every stage; earlier-required and new-feature
failure counts are also zero. There was no observed ordinary regression for
the assisted workflow to prevent. These checks do not establish complete
correctness, a population effect or an individual component's causal effect.

Assisted model-process time was **2.34× Python and 1.90× JavaScript**. Combined
ordinary and assisted totals were 209.114 and 450.858 seconds. The whole batch
used 659.972 model-process seconds. Summed per-arm controller wall time was
718.980 seconds **including** model time; the difference is 59.008 seconds of
preflight, grading and other controller work. Archive/export and source
reproduction took a further 17.522 seconds. These are observed process times,
not production-code performance measurements or API-dollar estimates. The
small single-run sample and native service variation limit time attribution.

## Delivery is a separate result

Python assisted qualifies native owned-runner adoption in all four turns with
four distinct task identities and five completed owned calls/receipts. Its final
declared milestones are CURRENT. JavaScript assisted has zero qualifying owned
calls/receipts in all four turns. It retains a fresh generic passing task receipt
and task state VERIFIED, while both exact declared milestones remain STALE.
Task verification, declared milestone evidence and independent correctness are
different states. The JavaScript pair remains outcome-comparable despite its
delivery gap. Ordinary arms are not expected to emit plugin callbacks.

This demonstrates a working attributable history in the Python workflow and a
remaining adoption/qualification gap in JavaScript. It does not show that the
integration produced better code. The earlier two installed successes remain
valid for their separate controlled exercises, and all four previous failed
native trials remain unchanged at their own producer identities.

## Frozen inputs and reproducible evidence

[Preparation](prepared.json) was pushed before live outcomes. It freezes equal
public inputs, initial baselines, source/configuration/request/oracle identities,
alternating order, model and time policy. Each arm shares 720 model-process
seconds over four resumed turns. Strength engines are off. Queue stages cover
leases/retries, restart, atomic batches and migration/replay; order stages cover
holds, exact refunds, restart and atomic replay. These are authored systems, not
a representative upstream-project sample or an OS-isolated closed-book trial.

- [Readiness](readiness.json): completed source qualification, two installed
  prerequisites, 17 fresh oracle controls and the retained older CI incident.
- [Focused controls](controls.json): seventeen oracle controls plus three
  delivery/adverse-outcome accounting checks, with environment versions.
- [Fresh whole-result review](review.json) found no material defect;
  [verification](verification.json) retains normal-access reproduction and all
  five rendered map views. [Delivery](delivery.json) verifies remote main, all
  thirty fetched branch heads contained, and actual served HTML/data bytes.
- [Fresh reference rehearsal](rehearsal.json): all sixteen reference snapshots
  reproduce 4/6/8/10 groups with zero model calls.
- Original bounded observations: [Python ordinary](workflow-queue-py-ordinary.json),
  [Python assisted](workflow-queue-py-assisted.json),
  [JavaScript assisted](workflow-orders-js-assisted.json),
  [JavaScript ordinary](workflow-orders-js-ordinary.json).
- [All-arm accounting](live-summary.json), [measurements](measurements.json),
  [secondary native counts](call-counts.json) and [exported evidence states](evidence-states.json).
- [Source manifest](source-archive/manifest.json),
  [export-time regrades](source-archive/summary.json) and
  [independent reproduction](reproduction.json): 16/16 snapshots match; current
  raw harness matches the frozen harness. Dirty candidates have no committed
  PatchProof subject; their eligibility gaps remain explicit.
- [Private-original hashes](private-retention.json) identify retained raw host
  streams, prompts, diagnostics and original results without publishing them.
  Unsigned hashes do not authenticate native execution.

Reproduce the exported grades without a model, from the repository checkout
with Python and Node available:

```sh
python -m eval.workflow_results --reproduce results/matched-workflow/source-archive
```

Next: diagnose the JavaScript gap from retained traces and measure native/hook
overhead with no-model controls before any generalized repair. Preserve exact
command attribution and the distinction between optional guidance and owned
execution. A further benefit experiment needs independently sourced longitudinal
cases and a frozen sampling rule; do not tune harder replacements against these
ties or relabel receipt completeness as coding benefit.

See [plan](../../docs/superpowers/plans/2026-10-17-matched-workflow-comparison.md),
[provenance](../../docs/research/matched-workflow.md),
[validation](../../docs/validation/2026-10-17-matched-workflow.md) and
[journey 84](../../journey/84-a-tie-is-still-a-result.md).
