# 37 — What the fixture could not show

*2026-09-16. `core/radius.py` and `core/atlas.py`.*

Two components shipped today and they are the same argument made twice: a rule
the agent is asked to remember is soft policy, and soft policy decays. Compute
it instead.

The first came from the user's observation that agents fix one bug and make
another, because they do not consider what the fixed thing was connected to.
The second came from the user's observation that `CLAUDE.md`'s standing
instruction to refresh `architecture/` is forgotten or ignored. Both are §5.14
restated as lived experience, and both were answered the same way: nothing is
asked of the agent's memory, so nothing can be forgotten.

Neither is original, and that is the point. The blast radius is Aider's
repository map with the third-party dependencies removed and the ambition
reduced to Python. The atlas is a **software reflexion model** — Murphy, Notkin
and Sullivan, 1995, validated on 250,000 lines of NetBSD — with the one change
that makes it usable here: the high-level model is not stated by hand, it is the
architecture document the repository already commits.

---

## Four defects, and every one of them came from real code

The tests passed. Nine of them, three forward and six adversarial, on a fixture
built to be the `click-762c97ee` case in miniature. Then each component was run
against something real, and each was wrong.

**The radius found nothing on click.** The fixture writes
`class Choice(ParamType)`. Click writes
`class Choice(ParamType[_ValueT_co], t.Generic[_ValueT_co])`, where the base is
an `ast.Subscript` and not a `Name` at all. Reading only `Name` found no bases,
so no siblings, so nothing — silently, on the exact case the component was built
for.

**Then it found too much.** With subscripted bases read, `ParamType` came back
as a sibling of its own subclass `Choice`, along with every other generic class
defining `convert`. They intersect on `Generic`, which is scaffolding and not an
interface. A fixture can never show this, because nobody writes
`class Choice(ParamType, Generic[T])` in a fixture.

**The probe itself was the third defect.** Before either of those was
understood, the probe reported `changed: []` and the radius looked broken when
the radius was fine. The probe inserted `pass` into the middle of a multi-line
`self.fail(...)` call, the file stopped parsing, and `_symbols` returned an
empty list. Two hours would have gone into the wrong module if the trace had
not been run one function at a time. *A probe is code, and it is the code least
likely to have been tested.*

**The atlas called `radius.py` documented.** Run against this repository, it
reported no divergence for two brand-new modules — because
`docs/design/blast-radius.md`, written an hour earlier, names `core/radius.py`.
Writing about a module is not drawing it. `docs/design/` is documentation, so a
stale reference in it is still stale, but it cannot discharge the map.

Every one of those four is now a test that was watched failing before its fix.

---

## Measuring before believing

Per §5.9, which has cost this project two paid sweeps: the radius was measured
on **125 real commits across five upstream repositories** before anything was
wired. It fires on 43%, and on 36% of the bug-fix-shaped subset. Median 0
siblings and 2 callers. That is a signal, not a klaxon — and the 75%-block
history is why the number was taken before the wiring rather than after.

That measurement found a fifth defect nobody was looking for. The "closest
cover" line was naming `tests/test_mypy.yml` as the test to run, and
`tests/__init__.py` for eight callers. `TEST_NAME` matches the *directory*, so
data and package markers under `tests/` had always qualified — in
`core/report.py`'s existing coverage note as well, for as long as it has
existed. Naming a file that cannot be run is worse than naming none.

---

## What is left undone, and said so

The radius is report-only and the atlas is report-only. Neither blocks. The
design notes both say phase 4 is "measure the engagement rate on real runs, then
decide", and neither has reached it. The atlas's own firing rate has **not** been
measured across the corpus the way the radius's was — it is wired on the
strength of a design argument and a repository-of-one, which is weaker evidence
than this project usually accepts before shipping. It is written here rather
than left for someone to discover.
