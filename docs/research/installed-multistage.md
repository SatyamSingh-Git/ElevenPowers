# Provenance of installed multi-stage verification

This work extends the existing subscription and preservation harnesses; it adds
no external runtime dependency. The repository declares Apache-2.0. Reused code:
`eval/subscription.py` (explicit subscription authentication, no API fallback),
`eval/transcript.py` (native tool/result reading), `eval/input_scope_pilot.py`
(independent consumers), `eval/preservation.py` and its versioned source grader
and archival helpers. Shipping execution, milestone and export primitives stay
project-independent. The added piece is an opt-in installed three-task trial and
a frozen cross-language four-stage comparison.

Existing [two-stage findings](../../results/behavior-preservation/README.md)
are correctness ties. New authored contracts test leases/retries, exact integer
accounting, restarts, migrations and replay; they are not held-out upstream
samples. Reference implementations are forward controls, not oracle definitions
for model output. Behavioral assertions use literal independently calculated
outcomes and named groups; known variants must actually fail.

Ordinary/assisted inputs and budgets are matched. Outcome comparison remains
separate from native delivery, and partial/negative attempts stay visible. Raw
runtime/harness guards during execution do not become an authenticity claim for
unsigned local records. Reproduced source grades retain exact source/oracle and
public-case identities while separately reporting historical harness matching.

The first native trial refuted a synthetic diagnostic assumption: the observer
expected prompt/tool task hashes that the real callback producer did not emit.
Python actually used the owned runner despite a false native-adoption flag.
Both language trials still failed independent readiness predicates, including
missing build evidence and recovery-task reuse. The repaired shared producer
records task association, recognizes explicit new subjects and exposes independent
command guidance; it does not weaken the gate or replace the original results.
Actual callback ingress now supplies forward controls, alongside unbound-event
and continuation refusals. Fresh installed evidence belongs to a new producer
and requires a new allowance.

See [design](../superpowers/specs/2026-10-16-installed-multistage-design.md),
[plan](../superpowers/plans/2026-10-16-installed-multistage.md) and
[dated checks](../validation/2026-10-16-installed-multistage.md).
