# 7. Scope, and where it comes from

## Another core piece that was not there

The plan listed a scope guard among seven core pieces. The code existed:

```python
if tool in ("Edit", "Write", "NotebookEdit") and ledger.allow:
    ...
```

`ledger.allow` was read in three places and written by nothing. So an agent
asked to fix authentication could quietly edit billing, and the guard never
fired. Same shape as the missing repeat runner: a piece that looks built,
passes its tests, and does nothing.

Finding it took one grep and one thirty-second session:

```
editing an unrelated file -> (nothing)
ledger.allow = []
```

## The real design question

Not how to enforce a scope, but where a scope comes from.

The obvious answer is to declare it up front, from the request. That does not
work, because nobody knows which files a change will touch before making it. A
guard built on a guessed list would spend its life questioning correct work, and
a guard that interrupts correct work gets switched off, after which it catches
nothing at all.

The answer that does work is the same one the rest of this project uses: derive
it from evidence. A task establishes its own scope as it goes, through the files
it reads, the files it edits, and the areas the request names. An edit that
relates to none of those is drift.

That yields a rule with a useful property: reading a file before editing it
always silences the guard. The remedy is the thing you should have done anyway.

## Writing the failure cases first

The 75 percent measurement taught that adversarial cases belong before the
implementation, not after. So fifteen labelled cases were written first, and
twelve of them were edits that look unrelated and are perfectly legitimate:

- creating a new file, which is not wandering
- changing a manifest or a lockfile as a consequence of real work
- editing the test for the code being changed
- touching a sibling in the same module
- exporting from a package's `__init__`
- editing something the request named
- updating a README alongside the change

Only three were genuine drift. That ratio is the point: the guard's job is
mostly to stay quiet.

## All fifteen passed, which meant nothing

The first implementation scored perfectly, which by now is a recognisable
warning rather than a success. Ten harder cases written afterwards found three
real failures:

**A monorepo's container directory counted as a shared name.**
`packages/api/src/handler.ts` and `packages/web/src/app.tsx` both contain the
word "packages", so they looked related. Fixed by comparing filename tokens
only, since directory structure is already what the area comparison handles.

**Generic filenames matched across modules.** `src/auth/config.py` and
`src/billing/config.py` share a name that every module in every project has.
Words like config, utils, types and index now carry no signal.

**A plural in the request missed its singular file.** "refactor the date
helpers" did not match `dates.py`. Adding stemming then revealed a second bug:
"dates" became "dat", because the rule that strips "es" was applied everywhere
instead of only after a sibilant. Boxes and matches need it; dates does not.

After those fixes both sets pass: 25 cases, no false questions, no misses. The
ten hard cases are now permanent, marked with why they exist.

## What it looks like

```
request: fix the session refresh bug
read  src/auth/session.py

edit  src/auth/session.py            -> allow
edit  src/auth/tokens.py             -> allow
edit  tests/auth/test_session.py     -> allow
edit  pyproject.toml                 -> allow
edit  src/auth/limiter.py            -> allow
edit  src/billing/stripe.py          -> ASK  src/billing/stripe.py is in billing,
                                              which this task has not read or edited,
                                              and the request does not mention it.
                                              Edit it anyway, or read it first.
```

It asks rather than denies. The guard holds a suspicion; the person holds the
judgement.

## Cost

About 120 lines of logic, 25 labelled cases, 20 tests. Nothing was added to the
hot path: the check is string comparison against a list the ledger already
keeps.

## Postscript: it shipped inert anyway

The verification above ran the hook directly. The plugin subscribed
`PostToolUse` to `Bash` alone, so in an actual session no `Read` or `Edit` ever
reached the handler that records what the task has looked at. `ledger.seen`
stayed empty, and an empty seen list is the first early return in `unrelated()`:
the guard answered "not drift" to everything.

So this entry opens by describing a piece of dead code and closes by shipping
another one, for a different reason, one commit later. That was found in the
next phase and is the reason for the audit in [08-wiring.md](08-wiring.md).
