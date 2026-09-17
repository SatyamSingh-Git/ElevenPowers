# 39 — The constraint that cost more than it bought

*2026-09-17. `core/polyglot.py`, and what happened when the tool was pointed at
somebody else's repository.*

Everything measured in this project until now was measured on five mature Python
libraries. Then it was aimed at a real TypeScript monorepo — not to evaluate it,
just to use it — and three separate things broke in the first hour.

---

## What using it somewhere real actually exposed

**Three of its four packages produced no evidence at all.** They run
`node --test`, the parsers had never heard of TAP, and a passing run recorded
nothing. With the default `strict` profile that is the worst failure this gate
has: refusing a stop on work that is genuinely tested. Fixed in
[38](38-the-null.md) by reading TAP as a *format* rather than a tool — and then
attacked afterwards, which found that `cat notes.txt` containing `i pass 5`
could fabricate a counted, passing suite. The universality fix had shipped the
exact failure the tool exists to refuse.

**The blast radius had nothing to say about 1,463 files.** `radius.py` and
`atlas.py` read Python's `ast`, so a TypeScript repository was invisible to
them. That was written down as a deliberate constraint: `core/` holds zero
third-party imports, because a plugin that must install four packages before it
can watch a test run is a plugin nobody installs.

The user's answer was blunt and correct: *what is the problem with importing
third-party packages, if they are free and useful?*

## The constraint was real, and it was still wrong

It was never that a dependency is bad. It is that **the install has to be
trivial** or nobody tries the tool at all. Those are different claims, and the
second one does not require the first.

So the rule is kept where it matters and relaxed where it was only costing
coverage: the grammar pack is **optional**, the import is guarded, every entry
point answers "no" when it fails, and without it `radius.py` behaves exactly as
it did the day before. `pip install tree-sitter-language-pack` buys TypeScript,
TSX, JavaScript, Go, Rust, Java, Ruby, PHP and C#. Not installing it costs
nothing that existed before.

**And there was no cleverer answer available.** Asked how other tools manage it,
the honest reply is that they take the dependency: Aider's `repomap.py`,
Continue's index and OpenCode's permission engine are all tree-sitter. Three
independent projects reached the same place. Being different here was not
insight, it was a cost nobody had re-examined.

## What the borrow is, precisely

Aider's `repomap.py` (Apache-2.0) is the reference implementation and the survey
in `docs/research/` already named it the polyglot upgrade path. What is taken is
**the approach and the grammar pack, not the code** — and the distinction is not
a formality. Aider extracts *tags*, definitions and references, to select
context under a token budget. It carries **no inheritance at all**. A sibling is
defined by a shared base class, so that part had to be built here, per language,
because `class_declaration` in TypeScript is `class_specifier` in C++ and
`impl_item` in Rust.

The survey's own note still holds: neither Aider's map nor Continue's index has
test-to-source edges or a blast-radius number. The parsing layer is borrowed;
the thing built on top of it is not.

## The same bug, waiting in a new language

Python taught this project that `Generic` is not an interface: matching on it
made a base class a sibling of its own subclass, and every generic class a
sibling of every other. The fix was a `SCAFFOLD` set of bases that carry no
behaviour contract.

Counting real bases in the real TypeScript repository found it again before it
shipped. Fourteen classes there extend **`Error`**, and almost nothing else
shares a base. Without `Error` in `SCAFFOLD`, changing one custom error would
have made every other custom error in the codebase a sibling of it — the
identical false positive, in a language the project had never run on, found by
counting rather than by reasoning.

`Error`, `Exception`, `Object`, `Component` and their relatives are in the set
now, and there is a test that says so.

## What is honestly still missing

- **`atlas` is still Python-only.** Its import graph needs module *resolution*,
  and TypeScript's is a project in itself: `tsconfig` path aliases, barrel
  files, `package.json` exports, workspace links. The repository that prompted
  this has all four. Not attempted rather than half-attempted.
- **The sibling half may matter less than expected there.** That codebase is
  largely functional — 14 classes extending `Error` and little other
  inheritance — so the *caller* half is where its value will be. Worth knowing
  before promising anything.
- **Nine languages are wired; one is thoroughly tested.** TypeScript has real
  coverage. Go, Rust, Java, Ruby, PHP and C# have a node-shape table and no
  repository behind them yet. A grammar missing from the table is not read at
  all, which is the right failure, but "wired" and "proven" are not the same
  word and should not be written as if they were.
