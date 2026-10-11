# 73 — A patch needs its own identity

2026-10-11

A portable report could tell someone which commands ran and whether their inputs
were fresh. It could not say which committed patch that evidence described.
HEAD alone was insufficient: checks can precede a commit and still observe the
same bytes; a receipt can name the same HEAD and be stale after an edit.

PatchProof v1 connects these facts without replacing the verdict. Git supplies
the full base/head commits, tree identities, paths, modes and blob IDs. A
versioned digest binds each commit pair, and another binds the full tree pair.
The existing exporter still decides task state and freshness. The new bundle
qualifies whether those observations can be associated with the requested patch.

The first real producer was Git, before its output parser was written. A rename
has two NUL-delimited paths; binary numstat uses dashes. Exact binary capture was
added to the existing contained runner because text newline normalization would
change metadata bytes. Default text behavior and lifecycle limits stayed intact.

One adversarial control asked Git to hide changed files using `assume-unchanged`
and `skip-worktree`. Porcelain said clean. Both controls initially qualified a
checkout and exposed why a clean status alone cannot carry this promise. Hidden
index flags now leave binding unavailable. A damaged ledger similarly became a
qualified unavailable bundle rather than a traceback.

The real Python/Node exercise caught a different mistake in its own setup:
`suite_green` names an obligation, while `tests` is the declared command key.
The parser correctly refused to label the invented declaration. We corrected the
fixture and kept the failing observation; changing runtime recognition to fit it
would have made the experiment worse.

The fresh branch review then found three defects the first controls missed.
Filter commands from worktree configuration escaped the local-only enumeration;
missing promisor blobs launched a configured retrieval helper; and a passing
individual test tied with a failed suite could win the declared-check selector.
Real helper markers and `pytest -v -rN` exposed them before the repair. Effective
filters are now suppressed, lazy retrieval/transports are prohibited under the
explicit Git 2.45+ requirement, and only the appropriate aggregate can describe
a declared command. The full suite was restarted against those repairs.

Failing and incomplete receipts can be bound to an unchanged inspected patch.
That is useful evidence, but not approval. Missing declared checks, unrelated
scopes, stale declarations, unobserved paths and unsupported compatibility stay
visible. No claim set is manufactured from a passing command.

The two installed Claude Code language successes from the previous milestone
remain dated observations at their original runtime fingerprint. PatchProof
changes that runtime; it does not requalify those sessions, prove advice was used
or establish improved coding. The intermittent Linux descendant-cleanup CI
failure also remains unresolved. This feature provides a reviewer with a more
precise artifact, not a new outcome-improvement claim.

The final regression qualification passed locally and across four hosted
Ubuntu/Windows and Python 3.11/3.13 jobs. CI also exposed an advice test that
mistook a contention diagnostic for a second worker. A held-lock control
recorded one worker and one reservation; the repaired assertion measures
those facts and retains the diagnostic. Advice runtime behavior stayed intact.

See [design](../docs/design/patchproof-v1.md), [guide](../the-guide/patchproof.md),
[implementation plan](../docs/superpowers/plans/2026-10-11-patchproof-v1.md) and
[validation](../docs/validation/2026-10-11-patchproof-v1.md).
