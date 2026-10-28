# Multi-stage v3: test projects where a dependent is hard to find

**Status: pilot run 2026-10-28; GO.** Two cases were built, reviewed and
frozen. Superpowers alone broke earlier behaviour on both, and a blind
classifier called both misses genuine
([results](../../../results/multistage-v3/README.md)). Next: ten more cases. It replaces v2's cases. It keeps v2's runner, arms, oracles and analysis
([v2 design](2026-10-23-multistage-field-claims-design.md)).

## Intent

The field report says that with superpowers alone, a fix sometimes changed
something other code depended on, the dependent code was not updated, and a new
bug followed. It also says docs were often forgotten. With ElevenPowers added,
neither happened ([field report](../../field/2026-10-real-project.md)).

The v2 pilot could not see either effect, because nothing went wrong in either
arm ([journey 92](../../../journey/92-the-pilot-found-nothing-to-prevent.md)).
Its transcripts show why the cases were easy for Sonnet 5.5:

- **Small enough to read whole.** About 700 lines. The agent's first command
  printed every source file.
- **Dependents found by name.** Every dependent mentioned the changed name, so
  one `grep` for it found all of them.
- **The public suite caught the rest.** The agent ran it after every change.

v3 builds projects where those three shortcuts are not enough. A dependent
exists, a careful engineer can find it, and the obvious search does not reach
it. That is the situation the field report describes. The question stays the
same: does superpowers plus ElevenPowers lose less earlier behaviour, and leave
fewer stale docs, than superpowers alone?

## Goals

- Twelve new cases, each a realistic project an agent cannot take in with one
  command.
- In every cross-cutting stage, at least one **quiet dependent**: code that
  breaks if only the obvious place changes, where neither a search for the
  changed names nor the public suite reveals the break.
- Oracles that cannot score correct, accurately documented work as stale. Both
  defect kinds the v2 pilot found are closed by a general rule.
- Before all twelve are written, a pilot on the first two shows that the
  superpowers-only arm makes at least one **genuine** miss.

## Non-goals

- No change to ElevenPowers, its profile or its settings. It runs as shipped.
- No change to the arms, the model (Sonnet 5.5, medium), the per-stage time
  (900 s), the never-retry and sealing rules, or the analysis (exact two-sided
  signed-rank over cases, Holm across the two co-primaries).
- Not a population estimate. The cases are built so that dependents are hard to
  find. The result says whether the effect appears there, not how often real
  work looks like this.
- v2's cases and its pilot record stay as published. They are not edited.

## Anti-goals

These would make v3 a failure even if it ran cleanly:

- **Obfuscation.** No misleading names, dead-code traps, deliberately
  inconsistent style or `eval` tricks. The code reads like an ordinary,
  reasonably kept project. Quiet dependents come from ordinary design choices
  (registries, file formats, two places that apply one rule), not from hiding.
- **Undiscoverable dependents.** A quiet dependent must be findable by a careful
  engineer: by tracing where data goes, reading a registry, or checking who
  reads a file the change writes. Each case's review confirms a path to it.
- **Cases shaped around ElevenPowers.** Authors and reviewers are told nothing
  about how ElevenPowers works, as in v2.
- **Cases adjusted after an arm's outcome is seen, or filtered on it.**
- **Requests that mention docs, tests or dependents,** or that say "everything
  that uses it" or anything like it.

## What changes from v2

### Size

- **Source:** 2,500 to 5,000 lines (tests not counted), over at least 15 modules,
  in more than one subpackage. Standard library only. Deterministic.
- **Structure:** an ordinary layered project, such as a core model, storage or
  formats, services, a CLI and reports. No single file holds most of the logic.
- **Public suite:** decent but not complete, as in a real project.

### Stages

- **Eight stages,** up from six, so earlier work is further back in the
  conversation.
- **At least five cross-cutting, at least one self-contained, at least one bug
  fix.** Two hidden groups per stage plus two base groups, cumulative, as in v2.

### Quiet dependents (the core of v3)

Every cross-cutting stage has at least one dependent of one of these kinds:

| kind | what it looks like | why `grep` misses it |
|---|---|---|
| **by key** | handlers, formatters or validators looked up by a string from a registry, a config file or `getattr` | the dependent never names the changed function |
| **by data** | another module reads what the changed code writes: a file, a record, a column order, a unit, a dict's keys | it depends on the shape, not the name |
| **a second copy of a rule** | two places apply one rule, such as validation in the API and again in the CLI importer, or a total computed in the service and again in a report | the copy has its own names |
| **by contract** | the dependent relies on an ordering, rounding, sentinel value or default the changed code provides | nothing ties them by name |

**Each quiet dependent is declared** *(builder's call)*. A cross-cutting stage
in `case.json` lists its quiet dependents. Each entry gives:
- `file`: the dependent's path;
- `kind`: one of the four above;
- `path`: one sentence on how a careful engineer finds it;
- `diff`: its own `stages/<n>/quiet-<k>.diff`, which undoes only that
  dependent's update on the stage-n reference tree;
- `fails`: the earlier groups that then fail.

This replaces v2's single `dependent-missed.diff`. A stage may also have
ordinary dependents, which are not declared. Each case uses at least two kinds,
checked by the loader.

Two mechanical checks run for every declared quiet dependent. Both are added to
the rehearsal, so they are proved without a model:

1. **The suite stays green.** The public suite of the stage-n reference tree
   passes on the quiet-missed tree. That suite includes any tests the stage
   itself added. So the brief tells authors that the reference's own tests
   cover the requested behaviour, not the quiet dependent's path. A bug fix's
   test is about the bug.
2. **Not found by name** *(builder's call)*. A list of changed names is taken
   from the reference diff, and none of them may appear in the dependent's file.
   - **The changed names are:**
     - every function, method and class whose definition the diff changes,
       found by mapping the hunks' line ranges onto the stage n-1 tree with
       `ast`;
     - every identifier or string literal (three characters or more) that is
       net-removed: on the diff's `-` lines and on none of its `+` lines. These
       are read with Python's tokenizer.
   - **The match** is a whole-word search of the dependent file's raw text in
     the stage n-1 tree, any file type, the way `grep` sees it. So a registry
     holding `"format_money"` as a string counts as found, and is not quiet.

   Ordinary names inside a changed body, such as `self` and `value`, are not
   changed names. Only definitions and net removals are.

### Docs

- Same rule, same file, same table shape (`` | `key` | `value` | meaning | ``).
- The reference document grows with the project: at least 40 facts at the
  start, in several sections (options, messages, formats, limits).
- Each stage still changes at least one documented fact, stated in its request.

### Fairness: closing what the v2 pilot found

Both v2 defects scored an accurate docs row as stale. Two general rules,
applied to every case:

1. **Placeholder names are not graded.** When the oracle compares a documented
   value, it treats any `{name}` as `{}`. So `{parent}` and `{parents}` match.
   This is a change to the oracle code, made before any v3 case is authored. v2's
   records stay reproducible at v2's frozen commit.
2. **A fact is graded only on a surface the request names.** If a fact's
   meaning column describes a surface (the CLI, an API call, a file), a stage may
   change that fact only if its request names that surface. Otherwise the
   agent may correctly leave that surface alone, as in `msg.lookup`. This rule
   is added to the authoring brief.

   Reviewers get a third question for every changed fact: "Could a careful
   engineer implement this request, leave this surface as it was, and document
   that accurately?" If yes, the fact is dropped or the request names the
   surface.

All v2 fairness rules still apply: keys, verbatim values, groups requiring only
what is stated, and no leaks.

### Where v3 lives *(builder's call)*

- **Location.** v3 cases live in `eval/multistage_v3/`, and their records in
  `results/multistage-v3/`.
- **Code.** The loader takes the stage count and the minimums from the case
  set: 6 and 4 for v2; 8 and 5 for v3, plus the bug-fix requirement and the
  quiet dependent records. Nothing stays hard-coded at 6. The runner already
  takes `cases` and `manifest` as inputs. Its command line gains them, and the
  withheld-path list comes from the batch's own cases root.
- **v2 stays usable.** v2 cases still load and grade, and every existing v2 test
  stays green. Placeholder normalisation applies to both sets. Regraded under
  it, the v2 pilot loses `lint.redundant-role`; that change is recorded, not
  hidden.
- **Publishing.** v3 cases are published at freeze, in a `v3/` folder of the
  public cases repository.

## Build order and the pilot

The v2 lesson is that headroom must be shown before twelve cases are built.

1. **Oracle and rehearsal code at $0.**
   - Placeholder normalisation.
   - The stage count as a case setting rather than the fixed constant 6.
   - The two quiet-dependent checks in the rehearsal.

   All test-first, watched failing, mutation-checked.
2. **Brief.** The authoring brief is rewritten for v3, with the size, the quiet
   dependent table and checks, and fairness rule 2.
3. **Two cases.** Two fresh authors each write one case.
   - One review round, with the three fairness questions plus "is each quiet
     dependent findable, and by what path?"
   - The rehearsal must pass.
   - Both are hashed and committed before any run.
4. **Pilot, about $10–20.** The two cases × both arms × one replicate: four
   conversations, 32 stage turns. Sealed batch, never retried, outside any
   folder with a CLAUDE.md.
5. **Headroom gate, fixed now.** Go only if a superpowers-only conversation has
   at least one lost group or stale fact that a **blind classifier** calls a
   genuine miss.
   - **Who runs it** *(builder's call)*. A fresh agent in the operator's
     session, not a paid experiment run. It is not told the arm.
   - **What it sees:**
     - the stage's request;
     - the agent's stage diff (snapshot n-1 to n);
     - for a stale fact, the docs row as written and the expected value;
     - for a lost group, the hidden group's source and its failure output.
   - It answers: genuine miss, or oracle defect (correct work refused)? Its
     verdict and reasons are recorded and decide the gate. The operator cannot
     overrule it; the user can.
   - **An oracle defect** is fixed by a general rule and re-rehearsed. The gate
     is then decided by regrading the kept pilot snapshots, with no new pilot.
     A new pilot is needed only if the fix changes a request or a group the
     agents saw.
   - Pilot runs are excluded from analysis, as in v2.
6. **No go:** the stage rules are redesigned again at $0. The two pilot cases are
   not edited to make them fail.
7. **Go:** ten more fresh authors write the remaining cases from the same brief.
   - The two pilot cases stay in the twelve, unchanged.
   - Review, rehearsal, freeze, and power from the pilot's measured rates.
   - The full run is then proposed with its measured cost, and waits for the
     user's go.

## Cost and time

Calibration from the v2 pilot: about $0.14 per stage turn and about 60 s, on
about 700 lines. v3 is larger and longer, so assume 2.5 to 4 times that per turn.
The pilot then reads about $0.35–0.55 per turn.

| | conversations | stage turns | estimated cost | estimated wall time (four at a time) |
|---|---|---|---|---|
| $0 build: code, brief, two cases, rehearsal | 0 | 0 | $0 | a few hours |
| pilot | 4 | 32 | about $10–20 | about 1 h |
| full, 12 × 2 replicates | 48 | 384 | about $135–210 | about 10–14 h |

The pilot replaces these guesses before any full run is proposed. Authoring
agents run in the operator's session, not as experiment runs.

## Built on

- **v2, unchanged:**
  - `eval/multistage_run.py`: the runner, with superpowers checked in both
    arms, Skill allowed and the user's CLAUDE.md excluded;
  - `eval/multistage_oracles.py`;
  - `eval/multistage_rehearse.py`;
  - `eval/multistage_power.py`;
  - the published v2 cases as the format.
- **The v2 pilot's lessons:** the three shortcuts above, and the two oracle
  defect kinds.

What v3 adds:
- cases where a dependent is reachable only by tracing what the code does;
- two mechanical checks that the dependent is quiet;
- oracle rules that stop correct alternatives from being scored as misses.

## Left to the builder

- Case domains, as long as they are varied, and at least four of the twelve
  have a persisted format read by another module.
- How identifiers are taken from a diff, provided it is Python's tokenizer and
  not a regex over raw text.
- The exact mix of quiet-dependent kinds per case, as long as each case uses at
  least two kinds.
- The prompt for the blind classifier, as long as it does not reveal the arm.

## Exit

**Delivered** when the pilot's verdict is recorded, either way. On a go, it
also needs twelve frozen cases and a full-run proposal with measured costs. Each
time, the results README, `PLAN.md`, the status page, a journey entry and the
architecture graph are updated. A no-go is published as one, with the
transcripts' account of why.
