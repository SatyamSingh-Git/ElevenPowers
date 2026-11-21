# TestMiner, first slice: rehearsal on two held-out projects ($0)

[`rehearse.py`](rehearse.py), [output](rehearsal.txt), [JSON](rehearsal.json).
Design: [spec](../../docs/superpowers/specs/2026-11-13-testminer-design.md).

Two projects, one file each, the first 10 functions, run twice:

- **in the project's own prepared environment;**
- **with ElevenPowers' interpreter,** which has pytest 9.1.1 and coverage.py
  7.10.7. Both projects have no runtime dependencies.

## In their own environments: `unknown`, with the line to fix it

Neither held-out environment has coverage.py, which is the usual case.
Every function came back `unknown`, with "install it there: python -m pip
install coverage". There was no false certainty.

## With coverage.py available

| project | function | verdict | reached by |
|---|---|---|---|
| cachetools | `_HashedTuple.__hash__`, `__add__`, `__radd__` | checked | `test_cached`, `test_keys` |
| cachetools | `_HashedTuple.__getstate__` | **reached, not checked** | `CacheKeysTest.test_pickle` |
| cachetools | `hashkey`, `methodkey`, `typedkey`, `typedmethodkey` | checked | many |
| more-itertools | `take` | checked, by a timeout | doctests and `test_more` |
| more-itertools | `tabulate`, `tail`, `consume`, `nth`, `all_equal`, `quantify`, `pad_none`, `ncycles`, `dotproduct` | checked | their own recipe tests |

### Two verdicts checked by hand

- **`__getstate__` is a false candidate.** `test_pickle` checks the
  behaviour: it asserts the cached hash is not pickled. The function returns
  `{}`, and `return None` happens to give the same result: pickle sets no
  state either way. This is an equivalent mutant, the known weakness of
  replacing a whole body. Descartes, which TestMiner borrows from, tries
  several extreme values per return type for this reason. So `reached, not
  checked` is a candidate to look at, not proof.
- **`take` is a real detection.** `chunked` calls it through
  `iter(partial(take, n, it), [])`. When `take` returns `None` it never
  equals the `[]` sentinel, so the loop never ends. PIT counts a timeout as
  detected, and so does TestMiner.

## What the rehearsal fixed

1. **ElevenPowers' main output parser read pytest 9's quiet summary
   `366 passed, 8 subtests passed` as 0 passed** (`core/parsers.py`). It
   affected every hook, test strength's baseline included, not only
   TestMiner. Fixed in 575d24e; both pattern changes were seen to flip.
2. **The text report printed about 60 `unknown (budget)` lines for one
   file.** It now prints one line.
3. **more-itertools' baseline under coverage did not finish in 90 s.** Its
   plain run takes 14–32 s; with per-test contexts it took longer, and
   `--test-seconds 300` was needed.

## Limits seen

- **Doctest contexts** (`doctest.DocTestCase.runTest`) cannot be mapped to
  a runnable test. Every more-itertools mutant therefore ran the whole
  command: correct, but slow.
- **Equivalent mutants** give false `reached, not checked` candidates, as
  above.
- **Under that whole-command fallback, any failure counts as `checked`**
  (PIT's convention). A flaky test elsewhere can hide a candidate, never
  invent one.
- **Two projects, eighteen functions in all.** That is an illustration, not
  a rate.

## The final review (2026-11-13)

An independent review of the whole change reproduced one Critical and seven
Important findings. All but one were fixed, test first. The one ruling is
the flaky-fallback point above.

- **Critical: `--path ./svc.py`, `.\svc.py` or an absolute path gave
  `not reached` everywhere.** coverage.py reports POSIX paths relative to
  the project, and the lookup used the raw string. False certainty, now
  normalised; a path outside the project is refused.
- **Bodies of only `pass` or `...`** were mutated, a guaranteed false
  candidate. They are now refused.
- **A body on the closing line of a multi-line signature.** Emptying it
  broke the signature, and the resulting error read as `checked`. It is now
  refused as a one-line function.
- **`--base` from a folder below the repository root** returned an empty
  report with no issue. It is now refused with the reason.
- **A property's getter and setter** share one name, and one was dropped
  silently. Both are now examined.
- **A file whose lines never ran at all** (never imported, or imported from
  an installed copy) was `not reached`. It is now `unknown`.
- **`--base` had no tests.** It has two now.

Eight minor findings are recorded in the ledger, deferred.

## Slice 2: a recorded run and more than one value (2026-11-21)

[`rehearse_slice2.py`](rehearse_slice2.py), [JSON](rehearsal_slice2.json).
Design: [spec](../../docs/superpowers/specs/2026-11-21-testminer-slice2-design.md).

charset_normalizer at 3985662, in its own prepared environment
(coverage.py 7.16.2, pytest 9.0.3), with `PYTHONPATH=src`.

- **`record`** ran its real command line,
  `python -m charset_normalizer` on three of its sample files. It kept 1308
  executed lines in 12 project files. The record holds
  `python -m charset_normalizer` and "3 arguments", not the file names.
- **`--observed`** selected 88 functions from that run. With `--limit 12`,
  the first 12 in file order were examined; the rest are `unknown (budget)`.

### First run: one false candidate, found and fixed

`unicode_range_languages` (`-> list[str]`) came back **partly checked**:
returning `[]` failed none of the four tests coverage said reach it.
Checked by hand, that was false. `test_infer_language_from_cp` asserts the
exact languages through `encoding_languages`, which is `@lru_cache`d. An
earlier test fills that cache, so coverage credits the function only to the
earlier test. Emptying the body to `return []` fails 5 cases of that test.

So a value that survives the selected tests is now run once more with the
whole command, and reported only if that also passes (d3f4f89). The same
gap exists for any state one test leaves for another, not only caches.

### Second run

| function | values tried | verdict |
|---|---|---|
| `from_bytes`, `from_fp`, `merge_coherence_ratios`, `filter_alt_coherence_matches`, `coherence_ratio` | `None` (return types are project classes or aliases) | checked |
| `encoding_unicode_range`, `unicode_range_languages`, `encoding_languages`, `mb_encoding_languages`, `alpha_unicode_split` | `None`, `[]`, `[None]` | checked |
| `characters_popularity_compare` | `None`, `0.0`, `1.0` | checked |
| `FileType.__init__` | none | unknown (`__init__`) |

No candidates in those 12. That is one project and twelve functions: an
illustration that the selection and the values work on real code, not a
rate.

### The slice 1 false candidate

cachetools' `_HashedTuple.__getstate__` has no annotation, but its body is
`return {}`, so it is inferred as `dict` (the spec expected `None` only).
It is now **partly checked**: `{None: None}` fails `test_pickle`, while
`None` and `{}` do not. Both of those leave no pickled state, so they are
equivalent mutants. The candidate is still false, now named precisely:
"returning None or {} failed no test".

### Limits seen

- **Equivalent values** remain the main source of false candidates.
- **Return types that are project classes or aliases get `None` only**, as
  five of the twelve did here.
- **The whole-command confirmation costs a full run per surviving value.**
  Survivors are the findings, so this is usually small.
