# Installed multi-stage verification

This directory separates deterministic harness controls, installed adoption and
ordinary-versus-assisted correctness measurement. Passing one does not establish
the others. The new cases are authored Python and JavaScript systems, not a
representative sample of upstream projects.

[Disposable GitHub transport](github-artifact.json) independently verifies the
candidate's canonical bundle, logged subject and current/failed/incomplete
states. It is a separate capability check, not a live workflow outcome.

## Retained controls

[The local rehearsal](local.json) records four scheduled arms, four stages per
arm and sixteen independently reproduced source snapshots. Every reference arm
passes 4/6/8/10 cumulative groups. The two base groups are revisited throughout;
these are ten distinct final groups, not 28 independent behaviors. Model calls
are zero. The control does not qualify native adoption or a benefit comparison.

Recreate the actual commands, source freezes and private regrades in a new
directory:

```sh
python -m eval.workflow_rehearsal --output NEW_DIR
python -m eval.workflow_results --reproduce NEW_DIR/source-archive
```

The result retains the source candidate and raw local/Git/Windows harness forms.
Source grading reports historical harness matching separately; evidence freshness
still uses actual unnormalized runtime bytes. Raw prompts, host streams,
credentials and machine-specific paths are not published here.

## Live gates

Two installed Claude Code Sonnet 5.5 medium conversations are approved, capped at
240 seconds each across three turns. They remain unrun while the corrected
candidate's release qualification is pending. The separate four-conversation,
four-stage correctness comparison has not been approved or run. No coding
improvement follows from these controls. Earlier comparisons remain
[correctness ties](../behavior-preservation/README.md).

[The prepared comparison](prepared-comparison.json) freezes alternating arm
order, equal 720-second allowances, four public requests per case, initial-file
and oracle identities before any outcome is observed. Baselines have been
executed and verified with zero model calls. Preparation grants no live allowance.

See the [contributor guide](../../the-guide/installed-multistage.md),
[design](../../docs/superpowers/specs/2026-10-16-installed-multistage-design.md)
and [dated qualification](../../docs/validation/2026-10-16-installed-multistage.md).
