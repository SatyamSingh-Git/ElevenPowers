# PatchProof v1 capability controls

2026-10-11. [Observations](observations.json) record real Python and JavaScript
commands in two independently created disposable Git repositories. Each retained
one passing test, one assertion failure, a terminated timeout and an absent
declared check, with dirty checkout binding unavailable. Exact head identities
were checked directly against Git independently of bundle construction.

These controls establish local patch/receipt representation and qualification.
They do not establish installed-host acceptance, independent attestation, safe
patches or improved agent coding. No model call was made. Raw outputs, model
prompts and source content are not included in these public observations.

Reproduce explicitly into a **new disposable directory outside another Git
repository**, with Python/pytest, Node and Git available:

```bash
python -m eval.patchproof --output NEW_DIR
```

The command creates test repositories and executes checks only because the
operator requested this exercise. Ordinary PatchProof export executes no project
commands. Commit IDs and timings can differ; expected semantic states are
`current`, `failed`, `incomplete`, `absent`, with actual exits `0`, `1`, absent
completed exit. The exercise preserves its full observations in `NEW_DIR`.

See [design](../../docs/design/patchproof-v1.md),
[validation](../../docs/validation/2026-10-11-patchproof-v1.md) and
[usage](../../the-guide/patchproof.md).
