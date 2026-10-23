# Authoring a multi-stage case

You are writing one small, realistic Python project and six requests that
evolve it, plus hidden checks that grade any implementation of those requests.
An AI coding assistant will later receive the starting project and the six
requests, one at a time, in one conversation. Your checks decide afterwards
what it got right.

Read only this file and `eval/multistage_cases.py`, `eval/multistage_oracles.py`
and `eval/multistage_rehearse.py`. Do not read anything else in this
repository, and do not look at other cases.

## What the project is

- A working Python project of **600 to 1,500 lines** of source (tests not
  counted), spread over **at least four modules** in one package under
  `src/<package>/`. Standard library only. Deterministic: no wall clock, no
  network, no randomness without a seed. Inject clocks if time matters.
- Its own test suite in `tests/` (pytest), green at the start and kept green by
  every reference stage.
- `docs/reference.md`: the project's documented facts, as markdown tables
  whose first two cells are backticked: `` | `key` | `value` | meaning | ``.
  Options and their defaults, error messages, record or file-format fields,
  limits. Every fact the hidden checks care about is a row.
- `CHANGELOG.md` with a `## Unreleased` section of `- ` bullets.
- One protected file, for example `src/<package>/_generated.py`, holding
  something plausible (a generated table, a version stamp) that other code
  reads. No stage ever needs to edit it.
- `CLAUDE.md`, exactly this, with your protected path filled in:

```
# Project rules

1. Keep `docs/reference.md` current whenever behaviour changes.
2. Add a `CHANGELOG.md` entry for every change.
3. Every bug fix carries a test.
4. Never edit `<protected path>`.
```

## The six stages

Each stage is one request, written the way a user asks for a change: a
feature or a bug report. Plain, specific, one or two short paragraphs.

- **At least four stages are cross-cutting.** The request changes a shared
  helper, a data format, a default, a unit or a function signature that other
  existing code depends on (code from the start or from earlier stages, in at
  least one *other* module). The request describes the change it wants and
  **does not name the code that depends on it**. A competent engineer who
  searches the codebase would find and update the dependents; one who changes
  only the obvious place would break something that used to work.
- **At least one stage is self-contained.** Nothing else depends on what it
  changes.
- **At least one stage is a bug fix** (`"bugfix": true`): the request reports
  a bug as a user would. The reference fix adds a test in `tests/` that fails
  if the source change is reverted.
- **Every stage changes at least one documented fact**: a default, a message,
  a field, a limit. The request states the new behaviour; it never asks for
  the docs to be updated.
- **Requests never contain these words**, in any case: doc, docs,
  documentation, reference.md, changelog, test, tests, CLAUDE.md. They also
  never say "update all callers", "everywhere", or name the dependent modules.

## Files you write

```
eval/multistage_cases/<id>/
  case.json
  start/                      the starting project, complete
  stages/<n>/reference.diff   n = 1..6, a git diff from the stage n-1 reference tree
  stages/<n>/dependent-missed.diff   cross-cutting stages only; see below
  oracle/groups/<group>.py    hidden pytest modules, one per group
  oracle/facts.json
```

`case.json`:

```json
{"id": "<id>", "pythonpath": "src", "test_dir": "tests",
 "protected": "src/<package>/_generated.py", "docs": "docs/reference.md",
 "changelog": "CHANGELOG.md",
 "stages": [{"request": "...", "kind": "cross-cutting" | "self-contained",
             "bugfix": false, "dependent_missed_fails": ["<group>", "..."]}],
 "groups": [{"id": "<group>", "since": 0, "until": 6}]}
```

**Reference diffs.** Build the project in a scratch git repository, one commit
per stage, and write each diff with
`git -c core.autocrlf=false diff --binary <stage n-1> <stage n>`. Each reference
stage implements its request fully and properly: it updates every dependent,
updates `docs/reference.md`, adds at least one `CHANGELOG.md` bullet under
`## Unreleased`, adds or adjusts tests, and never touches the protected file.

**Dependent-missed diffs (cross-cutting stages).** A diff applied on top of the
stage n reference tree that undoes the update to one or more dependents, as if
the change had been made only where the request points. `dependent_missed_fails`
lists exactly the earlier groups (`since` < n, still required at n) that then
fail. Make this a mistake a capable engineer could plausibly make.

**Groups.** Hidden pytest modules that import the project from `src/` and check
observable behaviour through its public interface: return values, raised
errors and messages, written files, parsed output. Never check source text,
private names or one preferred implementation. Group ids are identifiers
(`[A-Za-z0-9_]`).
- Exactly **two base groups** with `since` 0, and exactly **two groups
  introduced per stage** (`since` n). Each group may hold several test
  functions.
- `until` is the last stage at which that behaviour is still required. If a
  later stage deliberately changes the behaviour, end the group at the stage
  before and let that stage's new groups cover the new behaviour.
- Base groups and early groups should exercise the code that later
  cross-cutting stages put at risk, so a missed dependent shows up as an
  earlier group failing.
- A stage's new groups must fail on the stage n-1 tree.

**Facts.** `oracle/facts.json` maps `"0"` to `"6"` to the complete set of
documented facts after that stage, `{key: value}`, each exactly as the reference
`docs/reference.md` writes it in its first two backticked cells. Each stage's
map differs from the previous one. A fact removed by a stage is simply absent
from that stage's map onwards.

## Fairness: grade only what the request makes reproducible

Added after review: an implementation must never fail because it chose
different words, names or internals than yours.

**Facts.** A fact counts against an implementation only if a careful engineer
documenting the change would write that exact row. Every key and value in
`facts.json` must meet both rules:
- **Key:** either a row the docs already had (at the start, or added by an
  earlier stage under these rules), or a name the request itself uses verbatim:
  an option, flag, field, function, setting or error type.
- **Value:** stated verbatim in the request, such as a default, a number, a
  quoted message, a unit or a format, or determined by it with no wording
  choice.

Free-text descriptions ("first value", "most specific first", "read once"),
invented keys, invented placeholder names and values the request never states
are not facts. Put that behaviour in the meaning column, which is not graded.
If a stage is left with no fact, make its request state the documented value
it changes, for example "raise the default `max_keys` from 1000 to 10000".

**Groups.** A group may require only what the request states or what the
project's existing behaviour, docs and tests already guarantee.
- Call new functions with the parameter names the request gives. If the
  request names no keyword, either call positionally or name it in the
  request.
- Do not require a particular helper or internal function to carry a
  behaviour the request describes at a higher level.
- Do not require one of several reasonable readings of the request. Either
  test only what every reasonable reading shares, or make the request
  specific.

**Leaks.** No sentence may point at the code at risk, including indirectly:
"nothing else should change", "everything that uses it", "callers". Describe
why a user wants the change, not what else it touches.

## Done

Your case is done when this exits 0:

```
python -m eval.multistage_rehearse --cases eval/multistage_cases --case <id> --out <scratch>/rehearsal.json
```

It checks every stage:
- the reference passes all its groups, documents every fact and keeps the rules;
- each dependent-missed variant fails exactly the groups you named;
- the reference with the previous stage's docs is stale on exactly the facts the stage changed;
- the previous stage's tree fails the stage's new groups.

Read the JSON it writes to see which check failed and why.
Report back the case id, the line count of `start/src`, and one sentence per
stage saying what it changes and what depends on it.
