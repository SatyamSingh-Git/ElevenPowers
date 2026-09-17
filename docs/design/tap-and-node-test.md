# Reading TAP, and every wrapper that hides it

**Status:** design, 2026-09-17. Written before the code.

Found by pointing the runtime at a real repository outside this project. Three
of its four packages run `node --test`, and the parsers produced **zero
records** for all of them — a passing run left no evidence at all. With the
default `strict` profile that is the worst failure this gate has: it refuses a
stop on work that is genuinely tested.

**This is not a fix for one repository.** `node --test` is the trigger; the
shape of the fix is a format that many runners emit, and a wrapper problem that
affects every ecosystem.

---

## 1. Ground truth, captured rather than remembered

Node 22.17.1, run and recorded rather than recalled — this session has already
been wrong three times about output it had not looked at.

**TAP reporter** — the default when stdout is not a TTY, which is exactly what a
hook captures:

```
not ok 1 - this one fails
ok 2 - adds two numbers
1..3
# tests 3
# pass 2
# fail 1
```

**Spec reporter** — `--test-reporter=spec`, or a TTY:

```
✖ this one fails (2.6348ms)
ℹ tests 3
ℹ pass 2
ℹ fail 1
```

**A file that will not import** becomes a subtest named after the file:
`not ok 2 - src\broken.test.mjs`, backslashes and all on Windows.

**And R10 lives here too**, reproduced on this runner rather than assumed:

```
$ node --test ... | tail -6
# fail 1
EXIT(after pipe)=0
```

The pipe swallows the status. The counted failure has to outrank the exit code,
which is what `_counts_decide` already exists to do.

## 2. The universality problem, which is the larger half

A command name is not a runner. All four of these produce the TAP above:

```
node --test "src/**/*.test.mjs"
npm test          ← verified: emits TAP, command says nothing
yarn test
turbo test        ← a monorepo aggregate
```

Dispatching on the command alone therefore fixes one spelling and misses the
ones people actually type. `parse` sends unrecognised test commands to
`_wrapped`, whose docstring already admits the position — *"a test command whose
runner is not visible. The exit code is the evidence"* — and recovers counts
"opportunistically" for runners it happens to recognise.

So the change is in two parts, and the second is the one that generalises:

1. **A TAP parser**, dispatched when the command names `node --test`.
2. **TAP is dispatched on the OUTPUT, before the wrapper fallback**, so
   `npm test`, `yarn test`, `pnpm -r test` and `turbo test` are *counted*
   rather than trusted to their exit code — whatever underlying runner produced
   the TAP.
3. **A runner it cannot read becomes a blind spot rather than silence.** No
   module can enumerate every runner on earth, so the honest position is not
   "support everything", it is "say when you could not read something".
   `deno test` and `zig build test` are unreadable today and now say so in
   `blindspots.jsonl`, where `ep_status` and `ep_doctor` already look.

*Point 2 changed while building, and the blast radius in §4 is why.* The plan
was to teach `_wrapped` to see TAP. Dispatching earlier on the output does the
same work without touching the fallback that every ecosystem depends on — the
riskiest edit in the change turned out to be unnecessary.

TAP 13 is a published format with many emitters: `node:test`, `tap`, `ava --tap`,
`prove`, and assorted C, Go and Rust harnesses. Reading the *format* rather than
the *tool* is what makes this worth building for anyone but us.

## 3. What it computes

Counters first, because they are exact:

- `# pass N` / `# fail N` (TAP reporter)
- `ℹ pass N` / `ℹ fail N` (spec reporter)

Falling back to counting result lines when a producer emits no summary — plain
TAP from `prove` and older harnesses does not always have one:

- `^ok N` and `^not ok N`

**Gated on a TAP marker.** The fallback only runs when the output actually
declares itself TAP — a `TAP version` line or a `1..N` plan. Without that gate,
any log containing the word `ok` at the start of a line becomes a test result,
which is the false-positive class this project has paid for four times on the
exposure canary.

Everything returns through `_counts_decide`, so a counted failure outranks the
exit code.

## 4. Blast radius, computed rather than guessed

Using this repository's own `core/radius.py` and `core/atlas.py` on the file
about to change:

| | |
|---|---|
| **module in-edges** | `core/parsers.py` is imported by `doctor`, `hook`, `stress`, `verify` and four more |
| **callers of `parse`** | 15 files, including `eval/replay.py`, `eval/run.py` and five test modules |
| **sibling parsers** | `_counted`, `_pytest`, `_tsc`, `_go`, `_cargo`, `_wrapped`, plus `_counts`, `_counts_decide`, `_record`, `_scope` |

Two consequences that shape the work:

**`_wrapped` is the risky one.** It is the fallback for *every* command this
module does not recognise, reached from two dispatch sites. A change there
touches every ecosystem at once, so it needs adversarial cover proving the
existing behaviour is unchanged when there is no TAP — not just that the new
behaviour works.

**The both-ways guard is itself an enumeration, and it can drift silently.**
`test_the_both_ways_table_covers_every_runner_parse_dispatches_to` counts
dispatch sites with a hardcoded pattern:

```python
re.findall(r"_counted\(|_pytest\(|_tsc\(|_go\(|_cargo\(|_wrapped\(", source)
```

Add `_tap(` and forget to add it to that regex, and the count does not move: the
guard passes while the new runner has no both-ways entry. A guard against
forgetting that can itself be forgotten is worth repairing while we are here —
derive the parser names from the module instead of listing them.

## 5. What it deliberately does not do

**It does not produce per-test identities.** A node:test name is bare — `this
one fails`, with no file qualifier — unlike pytest's `tests/x.py::test_y`. So
TAP evidence is **suite-level**, and two things stay pytest-only and are said so
rather than half-built:

- `stress.confirm`, which re-runs named node ids against the current tree
- `_reproduction`'s targeted path, which matches those identities

A TAP project still gets evidence capture, freshness, the gate, the scope guard
and suite-grain discrimination. It does not get a named reproduction, and
pretending otherwise would be the false confidence this project is against.

**It does not guess at unknown formats.** No TAP marker, no counting.

## 6. Both ways, before it is believed

Per §5.0, and because a parser that never reports failure passes every
adversarial probe by refusing everything:

- **forward** — TAP green, exit 0 → PASS with counts.
- **adversarial** — TAP with `# fail 1`, exit **0** because a pipe ate the
  status → **FAIL**. This is R10 on the real runner.
- **forward** — spec reporter green → PASS.
- **adversarial** — spec reporter with `ℹ fail 1`, exit 0 → FAIL.
- **adversarial, the universality case** — `npm test` with TAP showing failures
  and exit 0 → FAIL, though the command names no runner.
- **adversarial, the regression case** — a wrapped command with **no** TAP in
  its output behaves exactly as before; the exit code still decides.
- **forward** — plain TAP with `ok`/`not ok` and no summary counters → counted.
- **adversarial** — prose containing the words `pass` and `fail`, or lines
  starting `ok`, with no TAP marker → **not** counted.
- **the enforcement** — a `BOTH_WAYS` entry for the new runner, and the
  dispatch-site guard repaired so it cannot be satisfied by forgetting.

## 6b. The monorepo, measured on a real turbo run

Verified after the fact, on the command a turborepo actually uses at its root,
and it failed twice over.

**turbo prefixes every line with the package it came from.**

```
@probe/a:test: # pass 1
@probe/a:test: # fail 1
@probe/b:test: # pass 1
@probe/b:test: # fail 0
```

Anchoring the TAP patterns hard at the line start meant `turbo test` produced
**no records at all** — the same silent failure this whole note exists to fix,
reappearing one layer up. An optional `<package>:<task>:` prefix is now allowed
before every TAP marker.

**And the counts were overwritten rather than summed.** An aggregating runner
reports per package; a dict comprehension keeps the last one. So a failing
package followed by a passing one reported `fail 0` — **a red monorepo
laundered into a green record**, which is R10 arriving by a new road. The
failing package is deliberately first in the test sample, so the bug is not
invisible to a check that merely looks at the total.

Both are probed and were watched failing before their fix.

## 7. Phasing

1. `_tap` plus the `_wrapped` change, with the tests above. Each probe watched
   failing before its fix.
2. Repair the dispatch-site guard to derive its pattern from the module.
3. Re-run the real check that started this: feed genuine `node --test` and
   `npm test` output through `parse` and confirm records come back.
4. Only then is a TAP repository worth trying the plugin on, and in `guide`
   rather than `strict` until its own dirty-tree behaviour is known.
