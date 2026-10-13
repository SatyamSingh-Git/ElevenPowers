# 79 — a pass needs its before

2026-10-13. External Input Witnesses v1 could qualify explicit PatchProof
execution against selected approved local bytes. Ordinary native receipts and
retained behavior history still had a gap: an installed dependency could change
while the project source, HEAD and environment values stayed unchanged, and an
old green check could remain current.

The first four actual Python/JavaScript controls reproduced that gap before the
implementation. The repair reuses the existing approval, bounded collection,
parser, locked state, owned runner and history/report infrastructure. It adds
optional paired observations to receipts, rather than inferring execution
provenance from a dependency that happens to be readable now. Old serialization
remains unchanged when the field is absent.

Native commands qualify only with available platform/session/call/task and
invocation identities and matching source, configuration and producer. The
observer records an incomplete provisional result first. Completion-owned
checks use the same selected inputs, refuse incomplete required scope and
invalidate reuse and baseline caches after drift. Cross-task milestone history
retains the original result while current qualification changes.

The actual exercise seeds unrelated Python and JavaScript projects. It exercises
five synthetic host adapters, a second and third task, independently failing
dependency bytes, an owned failing run, repair, fresh reuse, missing-input
refusal, post-only capture and identified recovery. Its observed milestone
sequence is CURRENT → STALE → FAILED → CURRENT → INCOMPLETE → INCOMPLETE →
CURRENT. Launch counters distinguish actual reruns from inspection and reuse.
Synthetic envelopes do not establish installed-host acceptance or coding gain.

One whole-branch review found five Important gaps. Eighteen actual-command
controls failed before repair: forgotten call IDs could pair delayed results;
an old pre callback could replace a newer task; unknown-ID provisional scope
could disappear when policy was removed; closing source/configuration edits
could leave green nested evidence; and closing input drift could leave a claim
verified even when the top-level report was incomplete.

The repair retains bounded monotone seen-ID memory after detail eviction,
validates native task ownership under the same short write lock, preserves
unidentified provisional scope and guards report closure across source,
configuration and external inputs. Nested claims and milestones lose current
qualification together. Original command outcomes remain intact. The first
repair group passed 74 tests, including all 18 review controls.
The broader integration group passed 91 tests in 706.35 seconds. Final actual
Python/Node acceptance passed both protocols in 46.458 seconds on the frozen
runtime. Final local qualification passed 2,357 tests with 3 skips in 3,606.33
seconds, and all four hosted cells plus artifact acceptance passed. Named audits,
independent grader/source reproduction, doctor, stdlib imports and all five
rendered architecture views passed. Actual limits and platform skips are retained
in validation; these are separate from installed acceptance and coding benefit.

One Minor finding is deferred: an unchanged native-only PatchProof bundle can
collect the selected target eight times through paired witnesses and nested
exports. That is extra read cost within per-capture limits and the shared
deadline. The ordinary report's two external collections are a narrower result.
Seen-ID filter collisions conservatively leave qualification incomplete; they
do not admit an old result. Entirely reverted changes between reads, unsigned
local metadata, undeclared dependencies and remote services remain limits.

Final delivery qualification is recorded in
[the dated validation](../docs/validation/2026-10-13-external-input-sessions.md).
This is evidence that selected dependency drift can invalidate inappropriate
reuse; it is not a measured code-quality, performance or end-to-end coding gain.
