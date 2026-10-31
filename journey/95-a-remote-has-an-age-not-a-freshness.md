# A remote has an age, not a freshness

PatchProof could already say which local bytes a passing check observed. It
explicitly refused to say anything about a resource fetched from elsewhere. The
open milestone called that gap *remote observations*, and the brief added one
constraint that shaped everything else: a tracked declaration must never grant
external access.

The design follows from refusing three shortcuts.

**Reports do not probe.** A report that fetched a URL to decide freshness would
make a read-only command depend on the network, and its answer on the moment it
ran. So fetching happens only in an explicit `observe` command, and every read
path compares recorded history. The controls make that measurable: a loopback
server counts requests, and a full bundle is built while the fetch function and
urllib's opener both raise.

**A remote is never fresh.** Two identical observations an hour apart cannot
exclude a change that was reverted between them, and the first real fetch
showed a second reason. GitHub's raw files come with `Cache-Control:
max-age=300`, so what was observed can be minutes behind the origin. The status
therefore reports an age, and a receipt is placed between the complete
observations that bracket its timestamp. That placement is described as timing
on one clock, not as proof that the check read the resource.

**Validators are not identity.** The first real run also showed GitHub serving
a content-hash `ETag` and PyPI an opaque one. One control serves a changed body
with a stale `ETag`, and the observation still reports `changed`, because the
identity is the SHA-256 of the identity-encoded body. Redirects come from the
same producer run: urllib reports a refused redirect as `HTTPError(302)`, so a
redirect is incomplete and its unapproved target is never requested. The server
count shows zero requests to it.

Approval mirrors local root binding. It is private, refused when tracked or
copied, and bound to the exact declared URL. Editing the committed URL makes
the remote `url-changed` instead of quietly moving the approval.

Writing the private state marker found an upstream defect. The ledger writes
its ignore-everything marker only when none exists. `ep_inputs bind` created a
marker that named only its own files, so on a fresh project a later
`ledger.json`, holding prompt and command text, appeared untracked and
committable. It was reproduced on a scratch project and fixed in its own commit
(`68e65fe`), with a regression test seen to fail before the fix. The new remote
state uses the corrected marker from the start.

The harness had its own mistakes, caught before they could mislead:
- A scripted edit wrote a real newline into a string literal, which looked
  like 20 upstream regressions until the same tests passed on the unmodified
  file.
- Two flip filters containing spaces matched no tests. "No tests ran" is not
  a flip, so they were rerun by parameter ID.

Every guard then failed its probe when removed.

What this does not establish: remote state still influences no execution,
reuse, completion or binding decision; observations are unsigned; and nothing
here measures a coding benefit. See the
[validation record](../docs/validation/2026-10-31-remote-observations.md).
