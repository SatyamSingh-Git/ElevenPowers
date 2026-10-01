# Portable verification report

Build a local, host-independent Markdown/JSON report that another person can read
without the session. The user authorized the next most important delivery after
onboarding; this follows PLAN's report-as-product direction.

Include task claims and their computed obligations, latest command receipts,
execution and current source freshness, target paths, project revision, coverage,
pending/native edit uncertainty and specific next actions. An absent active claim
is unverified, never a claim that a passing command proves completed work.

Exclude prompts, transcripts, captured output and receipt details. Scrub known
credential patterns and substitute the project root in displayed text. Reporting
is read-only and executes no project commands. Source freshness uses one fresh,
bounded content snapshot shared only within this report and this root; partial
coverage cannot certify verification. Explicit-path receipts also read fresh
bytes, including documentation and fixtures outside source selection, within
the shared file/byte budgets. Nested views cannot reuse an outer snapshot.
The cooperative deadline defaults to 120 seconds, starts at entry, bounds Git
lookups and observation/discovery loops, and marks exhaustion incomplete after
in-flight work returns. It cannot preempt a blocking filesystem call.

Latest receipts follow the ledger's timestamp and later-entry tie rule, and are
bounded at 1,024; omitted records are explicit and make the
report incomplete. Observed-path inventories are summarized by count and stored
scope/fingerprint rather than duplicating entire source inventories. JSON has a
versioned schema. Markdown escapes supplied text.
Both formats preserve substantive obligation caveats. Revision lookup reads Git
metadata directly with a remaining-time allowance; it cannot enqueue verification
jobs or mutate an ambient journal, including a journal for another project.
Output is stdout by default; an explicit output path uses atomic creation and
refuses overwrite unless forced.
This is an unsigned local report, not independent authentication or a patch-outcome
claim. Live host acceptance limits continue to apply separately.
