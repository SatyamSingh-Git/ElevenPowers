# Command scope and collection provenance

This delivery extends ElevenPowers' existing declared-command parser,
descriptor-checked external collection, receipt metadata and ContextVar freshness
views, following the repository's existing attribution register. It introduces no package, command inference,
dependency graph authority or independent attestation service.

The addition is an explicit project assertion selecting witness IDs for a
recognized declared command, plus an operation-local opening/closing external
collection shared by nested report consumers. Source snapshots remain independent.

Strict declaration parsing reuses duplicate-key, finite-budget and portable-path
validation. Existing native attempt identities, bounded replay memory, task guards
and owned execution locks remain the execution authority. Existing exact patch,
configuration, producer and environment guards remain distinct from selected
external bytes. Old broad receipts and pending attempts retain their meaning.

The actual producers are Python runpy and Node require consumers in disposable
projects. Direct fault execution is the independent behavior oracle; per-command
counter files reveal reruns. A selected-file read spy delegates to the real checked
descriptor reader, and opening/closing mutation probes test retained guards.

The independent scope is a project declaration, not measured completeness of
runtime dependencies. Collection limits still apply to the project union, so
exhausting a shared budget can conservatively leave observations incomplete.
Before/after sampling cannot detect reverted changes between observations.
Installed acceptance and generalized coding benefit remain separate conclusions.

Final [qualification](../validation/2026-10-14-command-input-scopes.md) and
[retained observations](../../results/command-input-scopes/README.md) include
the failed first full candidate, its repair, all four hosted cells and partial
installed-session results at their actual producer identity.
