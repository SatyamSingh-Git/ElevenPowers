# Workflow feedback and report-read provenance

Build on the repository's Apache-2.0 command parser, exact declaration and owned
execution contracts, shared host transport, ledger lock, bounded check guidance
and operation-local `freshness_view`. The addition is advice at the observed
generic-verification gap and guarded source sharing within one human report.
No dependency, shell evaluator, agent workflow or project-specific rule is added.

The unchanged [matched comparison](../../results/matched-workflow/README.md)
is the diagnostic input. Its retained raw hashes were checked before inspecting
command shapes or native timing samples. JavaScript wrote source and tests in
compound commands and filtered Node output through tail/grep; it never invoked
the owned runner. Both startup contexts contained readable owned instructions.
That establishes available instruction and observed calls, not the model's reason
for choosing them. A generic task receipt can be fresh while an exact declared
milestone remains stale. Stronger attribution still requires an actual qualified
invocation; successful outer shell output cannot supply it.

`core/check_feedback.py` uses the already parsed completed result and corresponding
effective declarations. Current exact pass or failure suppresses advice; absent,
stale or incomplete exact receipts permit existing runner instructions. Shared
capture skips advice for callbacks already classified as unfinished. The existing
test-command heuristic now includes runner spellings already recognized by the
parser; unrelated output-only fallback does not trigger test advice. This predicate
does not certify shell execution. Atomic diagnostic reservation checks the fresh
task and configuration, hashes task/declaration/configuration identities, and
bounds signatures to sixteen per task. It follows receipt persistence and does
not consume native receipt-delivery identity. No check launches automatically.

`core/report.py` opts source-backed human reports into the existing freshness
context. An opening fresh source/configuration read is shared by the receipt
queries, and a closing fresh inspection checks that the text is still valid.
Explicit file inputs retain their own checks, external-input guards remain in
place, and file-only reports avoid a new full scan. Deadline, incomplete scan,
same-size/restored-timestamp byte movement and configuration movement refuse a
green result and discard the earlier fresh-count wording. Other callers keep
their default behavior. This context covers no command or Stop execution phase
and stores no persistent source cache.

The [benchmark and public reproducer](../../results/workflow-checks/README.md)
retain three alternating samples per mode and language-shaped input set. Each
sample creates 150 source files and five source-wide receipts. The legacy arm
reinstates the former source-only report wrapper in that process; the optimized
arm uses the shipped wrapper. Both ordinary outputs remain VERIFIED with five
fresh receipts; source snapshots fall from five to two. Python/JavaScript-shaped
component medians fell from about 0.63 seconds to 0.28–0.29 seconds locally.
Separate single Stop profiles changed little. Neither exercise measures model
behavior, general repository latency, application performance or coding benefit.

A separate [single-receipt measurement](../../results/workflow-checks/single-receipt-benchmark.json)
exposes the tradeoff: one legacy scan becomes two to supply the closing guard.
It ran during local qualification and partially overlapping component work;
[conditions](../../results/workflow-checks/report-tradeoff.json) prohibit comparing
its absolute times with the earlier measurements. A default five-receipt rerun
still gives five-to-two scans. No blanket speed claim is supported.

Actual Python/Node child controls precede model use. Vitest advice uses an existing
parser summary fixture and is identified as replay rather than an installed
Vitest run. The fresh review's two Important and one Minor findings were all
witnessed by six failing controls before repair. Full qualification and fresh
installed observations, if run, keep their own identities in the
[dated validation](../validation/2026-10-17-workflow-checks.md). Original negative
trials, tied outcomes and the unexplained earlier advice CI incident remain intact.
