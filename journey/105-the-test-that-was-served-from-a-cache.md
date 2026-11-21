# 105 — The test that was served from a cache

*2026-11-21. TestMiner's second slice ([spec](../docs/superpowers/specs/2026-11-21-testminer-slice2-design.md),
[results](../results/testminer/README.md)).*

Slice 1's last line named this slice: try more than one extreme value per
function, and record a real run. Both are built. `record` runs the
person's own program in their own folder under coverage.py and keeps line
numbers and file hashes, never arguments. `--observed` examines what that
run used. Each function's body is now replaced by every extreme value its
return type allows, and Descartes' *partially-tested* becomes
`partly checked`.

## What running it found that writing it did not

Five things, each found by executing something real:

- **The attempt cap the spec scaled was never in force.** A mutant that
  reverted the scaling survived every test. `execute` never calls
  `Budget.attempt()`; only test strength's mutation loop does. The decision
  is withdrawn and the line was left alone.
- **`SIG_IGN` would have disabled Ctrl-C in the program.** An ignored
  signal is inherited across exec, so the program would have ignored the
  key that is meant to end it. A no-op handler is reset instead.
- **The `python` on PATH had no coverage.py**, so the first real `record`
  saved nothing and said only that. It now names the install line.
- **`…` printed as a replacement character** in a Windows console.
- **The rehearsal's one finding was false.** On charset_normalizer,
  `unicode_range_languages` came back `partly checked`: returning `[]`
  failed none of the four tests coverage said reach it. A test that checks
  the exact languages does exist. It calls through `encoding_languages`,
  which is `@lru_cache`d, and an earlier test had already filled the cache.
  So coverage credited the function only to the earlier test. Emptying it
  fails five cases of the test that checks it.

The last is a property of per-test contexts, not of this function: any
state one test leaves for another can hide a test from the reach set. Only
the whole command can say that no test noticed. A value that survives the
selected tests now runs once more with the whole command. Survivors are
the findings, so the extra cost lands where it matters. After the fix, all
eleven examined functions were `checked`.

## The spec was wrong once more

Decision 2 said cachetools' `__getstate__` would stay
`reached, not checked`, because it has no annotation. Its body is
`return {}`, which the inference reads as `dict`. It is now
`partly checked`, with `{None: None}` detected and `None` and `{}`
surviving. It is still a false candidate: both survivors leave no pickled
state. More values narrowed it; they did not remove it.

## Bounds

One project and twelve functions; no rate. Equivalent values remain the
main false-candidate source. A project class or alias as the return type
gets `None` only. `record` sees the main process only.
