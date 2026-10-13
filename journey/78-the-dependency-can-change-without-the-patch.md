# 78 — The dependency can change without the patch

The repository already observed source, common manifests, lockfiles and
environment values. That still left a dependency able to change in place while
all those inputs stayed the same. An old passing execution could remain eligible
for reuse even though an independently run check now failed.

Two actual exercises made the gap concrete. Python loaded a separate dependency
file; Node required a separate CommonJS module. Their expected behavior was fixed
by the controller. The first execution passed. After changing the dependency's
value from two to nine, a direct check failed while the plan still offered reuse.
Source, HEAD and environment values stayed unchanged. The unchanged-input
controls continued to pass, so refusing everything was not the answer.

The first attempt did not establish that gap. It changed a text file outside the
recorded source scope, and PatchProof correctly left the association unavailable.
The exercise was repaired to use an observed source change. A Git helper returned
bytes where the assertion expected text; that fixture error was also corrected.
Neither failed attempt was counted as evidence of the intended defect.

The new layer requires project declarations and explicit local approval. It reads
selected regular files or trees, with aggregate entry, file, byte, depth and time
limits. Missing roots and incomplete coverage cannot qualify reuse. It keeps
source-only receipt facts separate from external-byte association and preserves
the historical passing receipt when those external bytes later change.

Real filesystem controls mattered. Windows path and descriptor creation-time
values differed after atomic replacement; an actual repeated-read control failed
before the comparison was corrected. A parent redirected before file opening
allowed outside content to be consumed before the old check refused the path.
Anchored POSIX access and Windows final-descriptor validation now check the target
before consuming bytes. Tracked-approval hiding through a Git environment redirect
and an uncontrolled busy CLI error also failed before their repairs.

The actual dependency exercise now retains pass, legitimate reuse, independent
failure, a fresh failing execution and missing-input refusal. Its counters are
one, one, two, three, three. Exporting did not run the checks again or change the
project files. The GitHub exercise can show declared current input observations
without inventing an external association for older manually recorded receipts.

The independent review found another behavior-sensitive input: an empty directory
can switch a command's result even when all selected file bytes remain unchanged.
It also reproduced persistent source edits during the added final scan retaining
reuse or launching a check. Six regression failures and a separate late ignore-
policy failure preceded the repairs. Selected directory names now join the
fingerprint; final source/checkout/policy guards extend through input collection.
Nested tracked approvals, weaker duplicate state reads and huge numeric limits
also have controlled refusal paths. All seven review regressions passed.

This demonstrates one mechanism: an obsolete pass cannot be reused after declared
dependency drift. It does not establish a population improvement in agent coding
quality, complete environment identity or installed-host acceptance. Native
passive receipt integration, finer invalidation and further producers remain
separate work. The [dated validation](../docs/validation/2026-10-13-external-inputs.md)
records the review, final gates and retained qualification limits;
the [guide](../the-guide/external-inputs.md) explains the reusable interface.
