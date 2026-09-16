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

---

## Postscript: the sweep finished, and it was worth it for the wrong reason

*Later the same day.* The 16-run sweep completed - $24.97, 62.5% resolved, an
interval of 37.5% to 87.5% that bounds nothing. It was run to measure how often
passing evidence is vacuous. **It cannot answer that**: `stress` reached only 8
of the 16 runs.

It earned its money anyway, twice over.

**One real VACUOUS verdict.** `itsdangerous-6c58e969` came back *resolved* in 9
turns and 56 seconds, and its evidence would have passed without the change.
Every previous demonstration of that mechanism was a fixture. This is the first
time it caught a live agent calling a task done on evidence that could not fail.

**And the instrument was 37% blind.** Six of sixteen ledgers carried no base
commit, so there was no old tree to build and the check never ran. The
correlation was exact: **6 of 6** of them had `claim opened by an edit` in their
decisions, and none of the other ten did. The cause is one line of control flow
- a prompt that states no claim still opens a task, `Ledger.open_by_edit`
attaches `feature_added` later, and only the claim-bearing path recorded a base.
The split was decided by whether `infer()` matched the task's commit message:
bug-shaped text got a claim and a base, feature-shaped text got neither.

The honest accounting: at this per-run cost a 50-run sweep is about $78, of
which roughly $29 would have bought nothing while producing a number that looked
real. Finding it at $25 was cheap.

**What did not catch it, and why.** `eval/rehearse.py:54` already checks for a
missing base and bails with *"no base commit after seeding"*. It rehearses
several tasks, not one - an earlier draft of this entry said one, which was
wrong. The real gap was narrower and more interesting: it **constructed the
`Ledger` itself**, passing in `base=base` and `claims=[Claim.BUG_FIXED]`. That
is to say it built the ledger the way a correct run would have built one, and
then confirmed that a correct ledger works. The defect was in how the *runtime*
builds one.

So the rehearsal now drives `core.hook` with the task's real prompt text and a
real `PostToolUse` edit per touched file, and only the evidence record is still
injected, because there is no agent here to run a command. The rule it now
encodes: **a rehearsal may stand in for the agent, never for the runtime.**

Seen to flip, on the same task that lost the sweep. With the hook fix reverted,
`python -m eval.rehearse --tasks 3` reports `attrs-577c782c` as
`base=NO claims=feature_added`, prints *"1 of 3 opened with NO BASE COMMIT"* and
exits 1 - which would have stopped the sweep before a penny was spent. With the
fix in place, three of three.

The fix was verified without spending anything further: the exact prompt from
`jinja2-065334d1` that produced no base now produces one, replayed through the
real hook process against a temporary repository.

---

## The rehearsal, widened and re-run: 16 of 16

With the base recorded at task open and the rehearsal driving the real hook,
the same 16 tasks the paid sweep used now all reach the check - **16 of 16**,
against 8 of 16 when money was spent on them. The blindness is gone, and it
was established for nothing.

It also produced the reminder its own docstring warns about. Every task came
back `verdict=yes` and `reproduced=True`, because the rehearsal applies the
**gold patch** and a correct fix discriminates by construction. A rehearsal
where everything discriminates is a rehearsal, not a result. The interesting
verdict is VACUOUS, and it only exists where an agent's evidence is weak -
precisely what a gold patch removes.

And it surfaced something nobody asked it: `click-d340b0c1` reports 48 tests red
on the base tree, all of them real identities rather than collection errors, and
all in `tests/test_arguments.py` - the one file the task carried across.
Carrying an updated test file onto old source turns **the whole file** red, not
just the test that targets the change. So `reproduced=True` on 16 of 16 is true
but much cheaper than the phrase suggests, and §5.13's reproduction inherits the
same coarseness already recorded for the `yes` verdict.

That one is written down rather than fixed. Tightening what counts as a
reproduction would move a published figure, and the decision is not a detail to
settle inside a debugging session. `results/b3-stress/rehearsal-16.md` holds the
numbers and the open question.

---

## The reproduction was not coarse. It was not independent at all.

Following the whole-file observation properly produced a worse answer than the
one it started from, and corrected something said here a few hours earlier.

`Ledger._reproduction` has two paths. The targeted one matches a *passing*
evidence record against the identities that were red on the base tree. The suite
one fires whenever the declared check `DISCRIMINATES` and any fresh passing
suite exists. Measured across the eight B3 runs where the base tree was asked:
**7 of 7** reproductions came from the suite path, **0** from a named test.

The targeted path is starved by construction. It needs a passing record carrying
a node id, and `pytest -q` prints passes as dots - the parsers hold 1,256 failing
node records against four passing ones. That was already known and is why suites
were allowed to count. What was not said is the consequence: on real runs
`reproduced` and `discriminates` are **the same single base-tree run**, and the
report was printing two green lines for one fact.

Also corrected: this entry said tightening the rule would move a published
figure. It would not. §5.13's +28pp is a cited external result about handing an
agent a reproduction test, not a measurement of this detector, so nothing
published rests on how `_reproduction` decides. The real reason not to tighten is
that the node-only version engaged on 1.4% of runs.

So the rule is unchanged and the **grain is now named**: a suite-level
reproduction says outright that no individual test was seen red there and green
here, and that it is the same run that decided discrimination. Both directions
have a probe - removing the caveat fails the suite case, and the targeted case
still carries none, because a named test red-there-and-green-here genuinely is a
second finding and understating it would be the opposite error.

What would restore real independence is written down and not built: `stress`
already knows which node ids were red on the old tree, so the runtime could run
*those* against the current tree rather than waiting for a passing record the
agent's command never emits.

---

## Asked, not waited for: 0 of 16 becomes 6 of 16

*2026-09-17.* The thing written down yesterday as "what would restore real
independence" is built. `stress.confirm` runs the tests just found red on the
base tree against the tree as it is, so a reproduction can be established by
name instead of inferred from the run that already decided discrimination.

On the same 16 rehearsed tasks: **targeted reproductions went from 0 of 16 to
6 of 16**, with the other 10 falling back to suite grain.

Three things had to be right and two were wrong first, both caught by running it
rather than by reasoning about it.

**Appending was the wrong verb.** Every corpus task declares `python -m pytest
tests -q`. Appending node ids runs the directory *and* the ids, so the first
version declined whenever the command named a path - a mechanism that was
correct and would have fired on none of the sixteen. Substituting the path for
the ids is strictly narrower. A token counts as a path only if it exists in the
repository, which is the only thing separating `tests` from the
`no:cacheprovider` in `-p no:cacheprovider`: identical in shape, and not a path.

**The passes still cannot be read.** `pytest -q` prints failures by name and
passes as dots - the very asymmetry that starved the old path, met again at the
other end. But the ids were chosen here, so subtracting the ones pytest names
leaves the ones that passed. Any exit code but 0 or 1 means the question went
unanswered and nothing is claimed.

**And the stronger evidence has to be asked for first.** It was not. All sixteen
tasks kept reporting suite grain while the targeted records sat in the ledger
unread, because `_reproduction` asked the suite question before the named one.

## The ten that still fall back are the point, not the shortfall

For `attrs-6e3786c5` all twelve chosen tests were still red on the current tree,
failing with `TypeError`, because they are **pre-existing breakage in that
seeded repository** and not tests the fix repairs. The check declined to call
that a reproduction - exactly the adversarial behaviour it is probed for, seen
on real code rather than in a fixture.

Which makes it the sharpest confirmation yet of the `red_before` caveat: where
that number is large it is mostly pre-existing failure, and the targeted check
is what tells the two apart. The suite grain never could, and for seven measured
runs it did not.
