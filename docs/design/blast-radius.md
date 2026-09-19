# Blast radius: the obligation the code computes for you

**Status:** design, 2026-09-16. Written before the code, at the user's
direction, because the last three things built here were sized or scoped wrong
and each cost something to find out.

---

## 1. The failure this targets

> *"They fix one bug but don't consider the things associated with it, and end
> up creating another bug."*

That is measured, from three directions:

| | |
|---|---|
| **16–37%** of applied agent patches break a pre-existing test | TensorBench, 199 tasks, per-model 16.1% to 36.7% |
| **14.74%** of patches are partially correct — missing cases the fix should have covered | SWE-bench correctness study |
| *recall grows near-linearly while **precision saturates*** — agents keep adding and stop preventing | SWE-Milestone, 98 milestones, 12 models |

And this repository has the case in its own corpus: **`click-762c97ee`**, where
the agent fixed `Choice` and never generalised to `DateTime`. `PLAN.md` §5.2
already names the remedy — *"sibling implementations of the changed interface,
callers with other argument types, exception paths"* — and it has never been
built.

## 2. Why the obvious remedy is the wrong one

The instinct is to demand a detailed plan first. Three measurements say no.

**Instruction files do not survive.** Constraint violation rises **0% → 78%
across four compaction rounds**, and *soft organisational policy decays about
8.3× faster than hard safety norms*. A `CLAUDE.md` rule is soft policy. It is
not that agents are careless; it is that the instruction is gone by the time it
matters.

**Plans have no controlled evidence, and a measured downside.** A survey of
spec-driven frameworks states that no peer-reviewed study has defined,
delimited or measured them. The one large plan study — 16,991 trajectories —
found *"the negative impact of a bad plan is greater than no plan at all"*, and
that best-practice phases misaligned with the model's own strategy **hurt**
performance. Locally: naive "write tests first" prompting raised regressions
from 6.08% to 9.94%.

**An unchecked plan is another thing to be wrong about.** *Inaccurate
self-reporting* is **22.6%** of failures in 20,574 real coding-agent sessions —
larger than faulty implementation at 17.8%.

So: do not ask for a plan. **Compute the checks a good plan would have implied,
from the change itself, and make them obligations.** Nothing is asked of the
agent's memory, so nothing can be forgotten.

## 3. What it computes

Input: the files this task touched, and the commit it started from — both
already on the ledger (`touched`, `base`).

1. **Changed symbols.** `git diff -U0 <base>` gives changed line ranges per
   file. Parse each file with `ast` and take every `def`/`class` whose own line
   range intersects a changed range. Line ranges rather than name matching,
   because a file can define forty symbols and the task changed one.

   A file the task *created* has no diff against the base at all, so the whole
   file counts as changed. **The test for that used to be "the diff is empty and
   the file exists", and an unchanged tracked file satisfies it too** — so a file
   opened and reverted came back with every line altered, which makes a
   non-change look active and pads the radius with noise. An audit measured it
   on 2026-09-19. The question is now asked directly, with `git ls-tree` against
   the base commit, and it distinguishes three states rather than two: present,
   absent, and *could not be asked*. A git failure is not read as "new", because
   inventing a whole file's worth of changed lines out of an error is the
   noisiest guess available.

2. **Siblings.** For a changed *method* `M` on class `C` with bases `B`: other
   classes anywhere in the repository that inherit from something in `B` **and**
   define `M`. This is the `Choice`/`DateTime` case exactly — they never
   reference each other, and the only link is a shared base and a shared
   override.

3. **Callers.** For a changed top-level symbol `S`: files whose AST contains a
   `Name` or `Attribute` reference to `S`. Reference, not text match, so a
   mention inside a string or comment does not count.

4. **Cover.** Which test files correspond to the dependents, reusing
   `report.coverage_note`'s existing token rule rather than inventing a second
   notion of "the test for this file".

Output: *you changed X; these N places depend on it; these test files cover
them; here is the one to run.*

## 4. What it deliberately does not do

- **It does not block.** `guide`-shaped from day one: it reports. §5.12 —
  detection and intervention are separately justified — and this gate already
  blocked 75% of runs once on a signal nobody had measured. Blocking becomes a
  question only after the false-positive rate is known.
- **It does not demand a test that does not exist.** `core/surface.py` exists
  because an obligation nothing can discharge is a design error rather than a
  finding. If no test covers a dependent, the dependent is *named* and nothing
  is required.
- **It does not chase dynamic references.** `getattr(obj, name)` is
  undetectable by this method, and pretending otherwise would be the false
  confidence the whole project is against.
- **It does not rank.** Aider's PageRank exists to *choose context under a token
  budget*. Here every dependent is worth naming, and there is no budget to
  spend.

## 5. The borrow, and why it stops where it does

**Aider's `repomap.py`** is the best repository symbol graph in the field by
this project's own survey — tree-sitter tags, a symbol graph, personalised
PageRank, Apache-2.0 and portable. It is the obvious thing to build on.

It is not what ships here, and the reason is a constraint rather than a
preference: **`core/` has zero third-party imports.** Every module is stdlib.
`repomap.py` needs `tree_sitter`, `grep_ast`, `networkx` and `diskcache`, and a
plugin that must install four packages before it can watch a test run is a
plugin that does not get installed.

So: borrow the *idea and its demonstrated value* — a symbol graph over the
repository is worth having, and Aider proved it — and implement the Python
slice with the standard library's own `ast`, which is exact for Python and free.
**Python only at first, and said so out loud** — with Aider named as the
upgrade path. *Taken 2026-09-17:* `core/polyglot.py` adds nine more languages
through tree-sitter as an optional dependency. The zero-dependency rule is kept
where it matters, since the plugin still installs with nothing, and relaxed
where it was only costing coverage. That is the whole of what is added
beyond the borrow: turning a reference set into an obligation bound to evidence.

## 6. False positives are the risk, so they get the controls

The 75%-block history is the thing to avoid repeating.

| Risk | Control |
|---|---|
| A trivially-named method matches everywhere (`run`, `get`) | A sibling must share a **base class**, not merely a name |
| A huge dependent list drowns the message | Report the top few; say how many more |
| The change is only to tests | Test-only changes produce no radius |
| No covering test exists | Name the dependent, require nothing |
| Parsing a large repository is slow | Bounded by `source_files`, which already caps; skip unparseable files silently into `blindspots` |

## 7. Both ways, before it is believed

Per §5.0, and because a radius that fires on everything and one that fires on
nothing are both indistinguishable from the feature being absent:

- **forward** — change `Choice.convert` in a fixture with a `DateTime` sibling
  and a caller; both are found, and the covering test is named.
- **forward control** — run that covering test; the obligation discharges.
- **adversarial** — change a leaf function nothing references; **silent**.
- **adversarial** — change only a test file; **silent**.
- **adversarial** — two classes sharing a method name but *no base*; **not**
  reported as siblings.
- **adversarial** — a dependent with no test at all; named, nothing demanded.

## 8. Phasing

1. `core/radius.py` — the computation, with the tests above. No wiring.
2. Report-only surfacing in `end_report`, behind the existing profiles.
3. Measure the rate on saved bundles before it becomes an obligation: how often
   does it fire, and on how many dependents? §5.9 — an engagement rate measured
   on the wrong predicate has now cost this project two sweeps, so it gets
   measured on the real one.
4. Only then, if the rate is sane, make it a discharging obligation.

Stopping after (2) is an acceptable outcome. A thing that *names what you are
about to break* is useful even if it never refuses anything.
