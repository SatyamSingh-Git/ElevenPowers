# 76 — A check needs time to leave a receipt

2026-10-12

ImpactGraph could explain possible effects and PatchProof could show existing
evidence. The missing step was obtaining the project's declared evidence through
one explicit bounded workflow. Reusing the command configuration, ownership,
parser and ledger was more useful than introducing another test runner.

We investigated execution first. The retained Linux interrupt failure, Windows
quoted-launch timeout and earlier SQLite reference errors did not reproduce in
the initial hosted matrix. All four jobs passed, including ten real repetitions
of interrupt, termination and quoted-launch controls per cell. That is a dated
qualification, not an explanation or repair of the earlier incidents. Diagnostics
now identify surviving processes and kernel process state if cleanup fails again.

Two different defects were established. An exhausted allowance still reached
`Popen`; zero and negative budgets launched real processes before reporting
timeout. The cleanup path also called `wait()` without a timeout, allowing process
reaping to outlive every declared execution bound. Both controls were observed
failing before their repairs and passing afterward. Launch/resume now require
remaining time, and reaping uses the remaining cleanup allowance.

The first executor fixtures had a different mistake: configuration was saved
without ordinary runtime-state exclusion, making the project dirty. Refusing
that fixture was correct. We repaired fixture setup instead of weakening the
clean committed-patch condition. A later command passed within an authored
30-second operation, but final input inspection exhausted the remainder. Its
overall result stayed incomplete. Success controls now use the product's
120-second default; actual command-timeout and historical launcher deadlines
remain unchanged. No latency improvement is inferred from those observations.

`--plan` reads every applicable declaration. `--verify` explicitly executes the
plan, saving an incomplete attempt before launch and each result before continuing.
Identical commands can serve multiple properties; unsupported properties do not
disappear. Impact candidates remain advice and never generate commands or safe
exclusions. Source/configuration/policy/patch changes stop later checks.

Final provenance matters too. A passing command followed by an environment change
must not yield qualified success. A later moving state read must not preserve an
older success. Zero executed tests are missing evidence, not a failed assertion.
These defects were reproduced and repaired through actual commands and controlled
producer-boundary races. An empty committed pair can retain its actual execution
head without inventing changed paths or affected behavior.

The actual CLI termination control completed one command, interrupted the next,
verified that its child stopped and then resumed. The completed command was
reused once its exact inputs and latest receipts qualified; the interrupted
command ran again. Earlier pass, incomplete attempt and recovered result stayed
available. `--rerun` handles the deliberately unobserved case: changed services
or installed dependencies need new execution even when local source hashes match.

The new saved associations are local unsigned evidence. Source/configuration,
repository policy, runtime producer and environment digests qualify reuse; raw
environment values and outputs stay out of exported bundles. This establishes
workflow behavior, not causal AI code-quality or performance improvement. Broader
installed qualification, richer external-input witnesses and GitHub presentation
remain independent work.

See [usage](../the-guide/patchproof-verification.md),
[design](../docs/design/patchproof-verification.md) and
[dated delivery qualification](../docs/validation/2026-10-12-patchproof-verification.md).
