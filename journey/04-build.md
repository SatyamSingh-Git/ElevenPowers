# 4. Building it

The plan called for seven days to a working slice, with something demonstrable
each day. It ran end to end on day one, which was less impressive than it sounds:
the scope had been cut hard enough that there was not much to build.

## What exists

| Module | Job | Lines |
|---|---|---|
| `core/evidence.py` | Evidence records, tree signature, freshness | ~170 |
| `core/parsers.py` | Command output to typed records | ~280 |
| `core/obligations.py` | Claim types, risk tiers, the obligation table | ~280 |
| `core/ledger.py` | Task state, computes the completion status | ~230 |
| `core/surface.py` | What a project is capable of proving | ~80 |
| `core/claims.py` | Request to claims, no model call | ~55 |
| `core/intent.py` | Reading the final message for questions and blockers | ~40 |
| `core/report.py` | The banner, the gate message, the end report | ~110 |
| `core/hook.py` | Claude Code hook entry point | ~210 |
| `eval/` | Labelled scenarios and the confusion matrix | ~400 |
| `tests/` | 50 tests | ~460 |

Roughly 1,450 lines of implementation, close to the 1,400 estimate.

## Decisions taken during the build

**Claim inference is deterministic.** The plan said "one cheap model call".
Pattern matching was tried first, and it works: no tokens, no latency, and
testable offline against labelled cases. The seam for a model call is documented
but unused. This follows the principle that anything the runtime can decide
deterministically should not be handed to the model.

**Questions produce no claim.** A request beginning "what", "why", "explain" or
"review" yields nothing and the runtime stays out of the way entirely. The
studied frameworks over-route: three of them contain instructions amounting to
"when in doubt, invoke the skill".

**Hook output must use the JSON form.** The host card recorded that hook stdout
on exit 0 goes to the debug log and never reaches the model. Only
`additionalContext` or exit 2 works. Reading that in advance saved a day of
confusion.

**A launcher, not a module path.** Hooks run with the working directory set to
the user's project, so `python -m core.hook` cannot find the package. A small
launcher inserts the path.

## The three defects dogfooding found

None of these came from testing. All three appeared the first time the whole
cycle ran in order on a real repository.

### Risk inherited from a parent repository

`git status --porcelain` walks up the directory tree. A project that is not
itself a repository reported an unrelated parent's changed files and was scored
medium risk instead of low.

Consequence: mysterious over-strictness for anyone working in a subdirectory of a
monorepo. Fix: confirm `rev-parse --show-toplevel` matches the working root
before trusting the output.

### An obligation nothing could satisfy

The `test_added` obligation wanted a per-test record, but `pytest -q` prints no
per-test lines. An agent that ran exactly the right test could never discharge
it.

Two options: instruct the model to pass `-v`, or accept a scoped suite run as
evidence. The second is right, and it generalised into a rule that later became
central: an obligation that no amount of good work can discharge is a design
error, not a standard.

### Reproduction read as contradiction

The worst of the three. A high-risk bug fix demands that the failure be on record
before the fix, so the correct sequence produces a failing record followed by a
passing one for the same test. The gate treated any fresh failure as
CONTRADICTED, so doing exactly what was asked produced a permanent block.

Fix: only the most recent record per identity counts. A failure that was later
resolved is reproduction evidence, not contradiction.

No unit test would have suggested this. It only appears when the whole cycle runs
in order, which is the argument for dogfooding in one example.

## What it looks like in use

The gate, when the agent claims completion having run nothing:

```
UNVERIFIED  bug_fixed
  missing  a test covering the change passes
           run the test that exercises this change, by name or by file
  missing  that test failed before the fix
           run it before applying the fix so the failure is on record
  met      the related test suite passes
```

The staleness message, after editing a file that was green:

```
STALE  bug_fixed
  stale    a test covering the change passes
           recorded at tree fb7fb4ae5570c0da, files have changed since
           re-run: python -m pytest tests/test_core.py -q
```

And the end report on success:

```
VERIFIED
  bug_fixed (verified)
    ok      a test covering the change passes  <- tests/test_core.py 19 passed, 0 failed
    ok      that test failed before the fix  <- tests/test_core.py 18 passed, 1 failed
    ok      the related test suite passes  <- tests/ 46 passed, 0 failed
  evidence: 3 record(s), 3 fresh
```

Those three messages are the product. Everything else exists to produce them.
