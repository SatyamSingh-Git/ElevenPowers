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
- **Two projects, eighteen functions in all.** That is an illustration, not
  a rate.
