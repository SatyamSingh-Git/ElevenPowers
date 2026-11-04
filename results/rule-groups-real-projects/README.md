# Rule-group proposals on real projects

*Plan written 2026-11-05, before the measurements below were taken. $0, no model.*

Every measurement of `ep_milestones --propose` so far is on the twelve v3
cases, which were written for the experiment. The project's standing rule
is to check portable behaviour on unrelated projects. One run on `click`,
made only to read the output's shape, showed its top three proposals were
two `__repr__` methods, two `__getattr__` methods and two `writelines`
methods. That is boilerplate no one would certify. This check asks how
typical that is.

## Projects

Copied as they are installed, `git init`-ed, and run with the defaults
(`--limit 50`, 30 seconds):

- `attr` (13 Python files), `click` (17), `_pytest` (78), `rich` (100),
  `sqlalchemy` (258), from site-packages;
- ElevenPowers itself at `HEAD`, as a user would run it.

## Measures

1. **Runs:** exit status, wall time, whether coverage is complete, and the
   gaps it names. Pass: every project exits 0 within the deadline plus
   5 seconds, and any gap is named.
2. **What fills the top 50**, sorted into three kinds by the two function
   names:
   - **dunder:** both are `__x__` methods;
   - **same name:** both have one ordinary name, such as an override or a
     copied helper;
   - **different names.**
3. **The same sort on the v3 cases,** for all top-50 proposals and for the
   27 certified pairs, the pairs some stage breaks.
4. **Co-change, on ElevenPowers only,** because it has history. For each
   top-50 pair: has any commit modified both files, neither being added?
   The base rate is the same question over every pair of files that both
   define functions.

## What follows

- **If dunder pairs fill a real share of real projects' top 50 and none of
  the 27 v3 truth pairs is one,** excluding them is a candidate. It is
  adopted only if, re-run on v3, it loses none of the 20 never-read
  dependents the proposals cover, and on the real projects it frees slots
  for pairs of the other kinds.
- **Same-name pairs are not a candidate for exclusion,** whatever they
  show. A rule copied under one name, such as `parcelpost`'s two `vat`
  functions, is the case the method exists for.
- Otherwise the findings are recorded as they are.

## As found ([`measure.py`](measure.py), [output](measure-as-found.json))

Run 2026-11-05 on the code at `23dc0d8`, while the full test suite ran
alongside, so wall times are upper bounds.

| project | Python files | functions | exit | seconds | dunder | same name | different names |
|---|---|---|---|---|---|---|---|
| `attr` | 13 | 208 | 0 | 0.7 | 7 | 2 | 41 |
| `click` | 17 | 579 | 0 | 1.2 | 22 | 4 | 24 |
| `_pytest` | 78 | 2,029 | 0 | 4.2 | 22 | 20 | 8 |
| `rich` | 100 | | **2** | 3.3 | | | |
| `sqlalchemy` | 245 | 10,994 | 0 | 32.3 | **no proposals** | | |
| ElevenPowers | 1,454 | 6,385 | 0 | 28.1 | 3 | 47 | 0 |
| v3, 12 cases (600) | | | | | 34 | 19 | 547 |
| v3 truth (27) | | | | | 1 | 1 | 25 |

**Runs: failed.** Three defects, none visible on the v3 cases:

1. **`rich` crashed the command:** `'charmap' codec can't encode
   character '▄'`. A proposal quotes the project's own words, and a
   Windows pipe's code page cannot encode all of them. The sibling
   commands already set their output to UTF-8; this one never did.
2. **`sqlalchemy` used the whole 30 s and proposed nothing,** while its
   coverage said "proposals are partial". Timing each phase found 25.4 s
   spent cutting functions out of their files: `ast.get_source_segment`
   splits the whole file again, character by character, for every
   function. The deadline was checked only in the scoring that followed,
   which then stopped on its first word.
3. **The list was not the same from one run to the next.** On `sqlalchemy`,
   the old code gave different lists under hash seeds 1 and 2. Many
   dialects copy the same method, so their pairs tie at a score of 1, and
   the ties fell in whatever order last-bit rounding put them. That order
   followed the summation order, and so the process's hash seed.

**What fills the top 50:**

- **Dunder pairs** are 44% of `click`'s and `_pytest`'s lists against 6%
  on v3. `rich`'s first five, once it ran, were `__rich_measure__` and
  `__exit__` pairs. The v3 cases understate how much boilerplate a
  reviewer has to wade through on real code.
- **But one of the 27 v3 truth pairs is a dunder pair** (`survey_tally`'s
  two `__init__` methods). By the rule fixed in advance, excluding dunder
  pairs is therefore not a candidate.
- **Fixtures fill ElevenPowers' own list.** Its top ten pair files across
  the example projects bundled under `eval/`, such as `throttle`'s
  `clock.py` with `parcelpost`'s. None of the 50 was ever modified
  together with its partner, against a base rate of 993 in 828,828 pairs.
  The [milestones guide](../../the-guide/milestones.md) already says to
  exclude fixtures with `scan.exclude`.

## After the repairs ([output](measure.json))

The three defects were fixed in `33cecbd`, with tests in both directions
and nine mutants killed. On all twelve v3 cases the proposals are
byte-identical before and after, and certification recomputes the same
for all 17 sealed case-batches, so no published figure moves.

| project | exit | seconds, first run | seconds, warm | dunder | same name | different names |
|---|---|---|---|---|---|---|
| `attr` | 0 | 0.6 | | 7 | 2 | 41 |
| `click` | 0 | 1.0 | | 22 | 4 | 24 |
| `_pytest` | 0 | 3.1 | | 22 | 20 | 8 |
| `rich` | 0 | 2.7 | | 42 | 3 | 5 |
| `sqlalchemy` | 0 | 13.9 | 7.8–9.0 | 17 | 33 | 0 |
| ElevenPowers | 0 | 30.7 | 14.6–14.7 | 3 | 47 | 0 |

- **Runs: pass.** Every project exits 0, and none reaches the 30 s
  budget. The first run reads freshly copied files; run again, the same
  trees take about half as long.
- **Stable:** on each of the 18 projects, the new code gave the same list
  under hash seeds 0 and 1; the old code did not on `sqlalchemy`. The
  test checks six seeds.
- **`rich` is 84% dunder pairs** (`__rich_measure__`, `__exit__`), the
  most of any project. `sqlalchemy`'s list is 33 same-name and 17 dunder
  pairs, led by one method copied across dialects (`autocommit`,
  `rollback`).

**Limits found and left as they are:**

- **The budget binds on very large trees.** With `--seconds 2`,
  `sqlalchemy` returned no proposals, with the issue "time budget
  reached; proposals are partial". With 5 seconds it returned 50, with the
  same issue. Rerun with a larger `--seconds`.
- **The budget is not checked while functions are cut out.** With
  `--seconds 1`, `sqlalchemy` took 4.9 s. That is within the plan's bar
  of the deadline plus 5 seconds, and grows with the tree. Bounding that
  step would also need a test that forces the deadline to land between
  two phases, which was not worth it for a few seconds.

**Exploratory, added after seeing the above:** with the bundled cases and
`results/` excluded, ElevenPowers' top 50 are all same-name pairs. They
are mostly copied helpers, such as one `_harness` function in five
evaluation runners and `_hash` in four. Twelve of the 50 were modified
together in some commit, against 2.21% of all pairs of the same 237 files
(619 of 27,966).
