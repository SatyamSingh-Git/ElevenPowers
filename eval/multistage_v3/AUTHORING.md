# Authoring a multi-stage v3 case

You are writing one realistic Python project and eight requests that evolve it,
plus hidden checks that grade any implementation of those requests. Later, an AI
coding assistant receives the starting project and the eight requests, one at a
time, in one conversation. Your checks decide afterwards what it got right.

The point of a v3 case: in a real project, a change sometimes breaks code that
depends on what changed. Searching for the changed names does not find that
code, and the project's own tests do not cover it. You are building a project
where that can happen, fairly. Every such dependent must be findable by a careful
engineer who traces what the code does.

Read only this file and `eval/multistage_cases.py`, `eval/multistage_oracles.py`,
`eval/multistage_quiet.py` and `eval/multistage_rehearse.py`. Do not read anything
else in this repository, and do not look at other cases.

## What the project is

- **Size and layout.** A working Python project of **2,500 to 5,000 lines** of
  source (tests not counted), over **at least 15 modules**, in more than one
  subpackage under `src/<package>/`. Lay it out the way an ordinary project is
  layered, for example a core model, storage and formats, services, a CLI and
  reports. No single file holds most of the logic.
- **Constraints.** Standard library only. Deterministic: no wall clock, no
  network, no randomness without a seed. Inject clocks if time matters.
- **Code quality.** Ordinary, reasonably kept code. Clear names, consistent
  style, no dead code and no traps. Nothing about it should look built to
  mislead.
- **Tests.** Its own suite in `tests/` (pytest), green at the start and kept
  green by every reference stage. Decent but not complete, as in a real project.
- **`docs/reference.md`.** The project's documented facts, as markdown tables
  whose first two cells are backticked: `` | `key` | `value` | meaning | ``.
  - At least **40 facts** at the start, in several sections: options and their
    defaults, error messages, record or file-format fields, limits.
  - Every fact the hidden checks care about is a row.
  - The meaning column says which surface the fact belongs to (the CLI, an API
    call, a file).
- **`CHANGELOG.md`** with a `## Unreleased` section of `- ` bullets.
- **One protected file,** for example `src/<package>/_generated.py`, holding
  something plausible that other code reads. No stage ever needs to edit it.
- **`CLAUDE.md`,** exactly this, with your protected path filled in:

```
# Project rules

1. Keep `docs/reference.md` current whenever behaviour changes.
2. Add a `CHANGELOG.md` entry for every change.
3. Every bug fix carries a test.
4. Never edit `<protected path>`.
```

## The eight stages

Each stage is one request, written the way a user asks for a change: a feature
or a bug report. Plain, specific, one or two short paragraphs.

- **At least five stages are cross-cutting,** and each has at least one **quiet
  dependent** (below). The request describes the change it wants and does not
  name the code that depends on it.
- **At least one stage is self-contained:** nothing else depends on what it
  changes.
- **At least one stage is a bug fix** (`"bugfix": true`): the request reports a
  bug as a user would. The reference fix adds a test in `tests/` that fails if the
  source change is reverted. That test is about the bug, not about a quiet
  dependent.
- **Every stage changes at least one documented fact,** and the request states
  the new value.
- **Forbidden words.** Requests never contain any of these, in any case: doc,
  docs, documentation, reference.md, changelog, test, tests, CLAUDE.md. They
  never say "update all callers", "everywhere", "nothing else should change" or
  anything like them, and never name the dependent modules.

## Quiet dependents

A quiet dependent is code, in a module other than the one the request points
at, that must change for earlier behaviour to keep working. It is not found by
searching for what the change renames, removes or edits, and the project's own
tests do not catch it when it is left behind. Use at least **two** of these kinds
across your case:

| `kind` | what it looks like |
|---|---|
| `key` | handlers, formatters or validators looked up by a string from a registry, a config file or `getattr` |
| `data` | another module reads what the changed code writes: a file, a record, a column order, a unit, a dict's keys |
| `copy` | two places apply one rule, such as validation in the API and again in an importer, or a total in a service and again in a report |
| `contract` | the dependent relies on an ordering, rounding, sentinel value or default the changed code provides |

They come from ordinary design choices, never from hiding. Someone who reads
where the changed data goes, or who reads a registry, finds them.

**The two checks.** The rehearsal proves both mechanically for each one you
declare:

1. **Not found by name.** The stage's changed names are collected from your
   reference diff:
   - every function, method or class whose body it changes;
   - every module-level name it reassigns;
   - every identifier or string literal of 3+ characters it removes outright.

   None of them may appear as a whole word anywhere in the dependent's file, as
   it was before the stage. See `eval/multistage_quiet.py`. If your dependent
   imports and calls the function you change, it is not quiet; that is an
   ordinary dependent, which is fine to have as well.
2. **The suite stays green.** The project's own tests, including any your
   reference adds at that stage, pass with the dependent left behind. Only your
   hidden groups catch it.

## Files you write

```
eval/multistage_v3/<id>/
  case.json
  start/                      the starting project, complete
  stages/<n>/reference.diff   n = 1..8, a git diff from the stage n-1 reference tree
  stages/<n>/quiet-<k>.diff   cross-cutting stages: one per quiet dependent
  oracle/groups/<group>.py    hidden pytest modules, one per group
  oracle/facts.json
```

`case.json`:

```json
{"id": "<id>", "profile": "v3", "pythonpath": "src", "test_dir": "tests",
 "protected": "src/<package>/_generated.py", "docs": "docs/reference.md",
 "changelog": "CHANGELOG.md",
 "stages": [{"request": "...", "kind": "cross-cutting" | "self-contained",
             "bugfix": false, "dependent_missed_fails": [],
             "quiet": [{"file": "src/<package>/<module>.py", "kind": "data",
                        "path": "one sentence: how a careful engineer finds it",
                        "diff": "quiet-0.diff", "fails": ["<earlier group>"]}]}],
 "groups": [{"id": "<group>", "since": 0, "until": 8}]}
```

**Reference diffs.** Build the project in a scratch git repository, one commit
per stage, and write each diff with
`git -c core.autocrlf=false diff --binary <stage n-1> <stage n>`. Each reference
stage implements its request fully and properly:
- it updates every dependent, quiet or not;
- it updates `docs/reference.md`;
- it adds at least one `CHANGELOG.md` bullet under `## Unreleased`;
- it adds or adjusts tests;
- it never touches the protected file.

**Quiet diffs.** One per quiet dependent, applied on top of the stage n
reference tree, undoing only that dependent's update, as if the change had been
made only where the request points. `fails` lists exactly the earlier groups
(`since` < n, still required at n) that then fail.

**Groups.** Hidden pytest modules that import the project from `src/` and check
observable behaviour through its public interface: return values, raised errors
and messages, written files, parsed output. Never check source text, private
names or one preferred implementation. Group ids are identifiers (`[A-Za-z0-9_]`).
- Exactly **two base groups** with `since` 0, and exactly **two groups introduced
  per stage**. Each group may hold several test functions.
- `until` is the last stage at which that behaviour is still required.
- Base groups and early groups exercise the paths later stages put at risk, end
  to end, so a quiet dependent left behind shows up as an earlier group failing.
- A stage's new groups must fail on the stage n-1 tree.

**Facts.** `oracle/facts.json` maps `"0"` to `"8"` to the complete set of
documented facts after that stage, `{key: value}`, each exactly as the reference
`docs/reference.md` writes it in its first two backticked cells. Each stage's map
differs from the previous one.

## Fairness: grade only what the request makes reproducible

An implementation must never fail because it chose different words, names or
internals than yours, or because it correctly left alone something the request
did not ask about.

**Facts.** Every key and value in `facts.json` must meet all three rules:
- **Key:** a row the docs already had, or a name the request itself uses
  verbatim.
- **Value:** stated verbatim in the request, or determined by it with no wording
  choice. Placeholder names inside `{}` are not graded, so `{parent}` and
  `{parents}` count as the same.
- **Surface:** if the row's meaning names a surface (the CLI, an API call, a
  file), a stage may change that fact only if its request names that surface.
  Otherwise a careful engineer can implement the request, leave that surface as
  it was, and document that accurately. For example, a request that changes the
  error `Config.get` raises cannot change the fact for the message the command
  line prints, unless it says the command line changes too.

**Groups.** A group may require only what the request states, or what the
project's existing behaviour, docs and tests already guarantee.
- Call new functions with the parameter names the request gives.
- Do not require a particular helper to carry a behaviour the request describes
  at a higher level.
- Do not require one of several reasonable readings of the request.

**Leaks.** No sentence may point at the code at risk, including indirectly.
Describe why a user wants the change, not what else it touches.

## Done

Your case is done when this exits 0:

```
python -m eval.multistage_rehearse --cases eval/multistage_v3 --case <id> --out <scratch>/rehearsal.json
```

It checks every stage:
- the reference passes its groups, documents every fact and keeps the rules;
- each quiet diff fails exactly its groups, keeps the public suite green, and
  names nothing the stage changed;
- forgotten docs are stale on exactly the changed facts;
- doing nothing fails the stage's new groups.

Read the JSON it writes to see which check failed and why. Report back:
- the case id;
- the line count of `start/src` and the number of modules;
- per stage, one sentence on what it changes;
- per quiet dependent, its kind and how a careful engineer finds it.
