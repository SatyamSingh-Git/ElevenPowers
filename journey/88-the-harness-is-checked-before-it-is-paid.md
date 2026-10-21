# 88 — the harness is checked before it is paid

Journey 87 closed the authored cases and named the question they cannot answer:
does an installed ElevenPowers change how often an agent's fix is VACUOUS, on
code nobody here wrote? B7/B9 measured 22% against 8% on a corpus this project
picked; `PLAN.md` §10 says what would settle it, which is vacuity by arm on tasks
sourced independently, in one sweep, by one method.

## Sourcing by a rule fixed first

The frame is the public top-PyPI ranking of 2026-10-01: GitHub, pure Python,
permissive licence, the five previously tuned projects excluded. Repositories are
taken in ranking order, commits after 2026-06-01 in a seeded hash order, at most
four per repository, forty in all. Each repository gets a closed-book
interpreter: its test dependencies installed, its own distribution removed, and a
canary that the answer is not importable. The analysis and its power (about 0.8
at the B9 odds ratio, about 0.44 at 0.5) were committed before any outcome.

## Four things that would have cost a sweep

None of these was found by reading. Each surfaced when the real thing ran.

**The vacuity probe could not have applied a single patch.** It piped the patch
to `git apply` as text, and on Windows a text pipe turns every LF into CRLF, so
no patch matches a real checkout. Its own tests passed only because their
fixture files were written in text mode too, with the same corruption on both
sides. The runner's first fake-host run showed it. B7's probe sent bytes and is
not affected; the port was where it broke.

**The environment check ran one way.** The canary proved the package absent
without its source; nothing proved it present with it. urllib3's build writes an
ignored `_version.py` into the clone, so the clone imported and every mined tree,
which holds tracked files only, failed: 27 candidates spent on a suite run each.
The forward control now imports from a `git archive` of HEAD. My first version
imported from the clone and accepted urllib3 too; running it said so.

**A funding link was taken for a repository.** `github.com/sponsors/<user>` has
the shape of an owner and a name. Nine accepted packages, pydantic, starlette and
uvicorn among them, would have been dropped as unclonable. Only those rows were
re-derived: a full re-fetch showed seventeen projects' metadata had drifted in a
day, and re-deriving everything would have moved a frozen frame.

**The disk filled and the journal went with it.** The sourcing run reached 58
repositories, about 5.4 GB of clones and environments, and died inside a journal
write. `write_text` truncates before it writes, so `corpus.json` was left at zero
bytes and its tasks were gone (13 when last counted, at 19:05; the crash came at
20:22). The sampler now writes through tmp-and-replace,
resumes from what it has processed, deletes a repository that contributed nothing,
stops before the next repository below 2 GB, and reads history only up to
2026-10-20 so a fresh clone reproduces what a deleted one held.

## What the frame cannot contain

Three kinds of project fall out by the rule rather than by chance, and the report
will name them: those whose package imports a module the build generates; those
whose tests read their own installed metadata, red at every parent once the
package is removed (pluggy); and those whose test dependencies sit outside the
frozen install order (pygments, idna).

Nothing has been spent. The rehearsal runs every task on its own fix with no
model: it must fail at base, resolve with the fix, keep its answer unreachable,
and calibrate the probe both ways. On the first four tasks it did, in 20–42
seconds each.
