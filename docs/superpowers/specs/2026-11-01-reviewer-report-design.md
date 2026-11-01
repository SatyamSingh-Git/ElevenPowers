# The reviewer's report: is this change pinned?

*2026-11-01. PLAN §13 A, step 1. The user chose the reviewer direction and
asked to start building without a round of questions. Every decision below
not quoted from PLAN is marked **my call**.*

## Intent

The person deciding whether to accept a change an agent made needs one
answer first: **would anything notice if this change were undone?** That is
the VACUOUS question, the one direction with a measured effect (84% → 37%,
held-out sweep). A reviewer should be able to read the answer in a minute.

PLAN §13 A.1 fixes what the report contains:
1. pinned or not;
2. the unpinned lines;
3. what was run, and on which tree;
4. what is unknown.

## What exists, and what this adds

Borrowed:
- **The VACUOUS method:** `eval/heldout_vacuity.py`, the exact check behind
  the 84% → 37% result and v3's `test_with_fix`. It puts back the changed
  non-test files, keeps the change's tests, and runs the suite again.
- **Runner-agnostic test identities:** `core.parsers.parse`, which covers
  pytest, unittest, jest, vitest, TAP and others.
- **The test-file rule:** `core.surface.TEST_NAME`.
- **Process control:** `core.process.run`, with its timeouts, output cap and
  process-tree cleanup.
- **The declared test command:** `core.config`.
- **Changed-line mutation analysis:** `core.strength`, used for item 2.

What this adds: the eval-only method made runner-agnostic and pointed at a
commit pair, then composed into one short report a person reads. The
existing PatchProof bundle reports receipts; it runs nothing and does not
answer the pinned question.

## Behaviour

```
python plugin/bin/ep_review.py --project PATH --base BASE [--head HEAD] [--command CMD] [--json]
```

**Where it runs.** In a private detached `git worktree` at `head`. The
user's checkout is never touched (**my call**, the same rule as
`core/stress.py`). The command is the project's declared `tests` command;
`--command` overrides it. Nothing undeclared is run.

**The three runs.**
1. **head:** the suite on the head tree. Its failing tests are recorded.
2. **undone:**
   - Every non-test file the change modified or deleted is put back to `base`.
   - Files the change added are kept, as the measured method keeps them. A
     test that imports a new module tests behaviour, not mere existence.
   - The change's tests stay as they are at head.
   - The suite runs again.
3. **head again:** the suite once more on the restored head tree. If its
   failing set differs from run 1, the suite is not stable enough to judge,
   and the answer is UNKNOWN (**my call**). This replaces the eval method's
   no-op control, which was pytest-specific.

**Verdict.**

| verdict | when |
|---|---|
| **PINNED** | some test fails in *undone* that did not fail at *head*. These are listed by name: they are what pins the change. If the runner prints no names, a clean head plus a failing *undone* still counts, and the report says no names were read. |
| **NOT PINNED** | *undone* fails nothing that *head* did not. Nothing in the declared suite would notice the change undone. |
| **UNKNOWN** | no declared command; no non-test file changed; a run timed out or would not start; *head* failed with no test names to compare; or *head again* disagreed with *head*. The reason is always given. |

**Unpinned lines.** When `--strength` is given and an engine is installed,
the report runs `core.strength` on the changed lines and lists the
survivors: changed lines that can be altered while every test still passes.
Without it, the report says the lines were not measured and how to measure
them (**my call**: mutation is slow and optional, so it stays opt-in).

**What was run.** Each run is listed with:
- the command;
- the commit and tree id;
- the exit code, the duration and the failing count.

**Unknown.** These are always listed:
- files the change added were kept;
- only the declared command was judged, so other test commands may notice
  what this one did not;
- a pass is not a proof of correctness;
- the strength state.

**Report only.** Exit 0 whenever a report was produced, whatever the
verdict. Exit 2 when no report could be produced. A reviewer's tool that
blocks has to earn that with evidence, as §5.12 says.

## Changed after the independent review (2026-11-01)

An independent reviewer reproduced eleven defects in the first version,
and each was fixed with a test that failed first:
- **A base that has moved on.** If `--base` is not an ancestor of head, the
  report compares from the fork point and says so. Before, the base's own
  later edits were credited to the change.
- **Fixtures stay.** `testdata/`, `fixtures/`, `__fixtures__/`,
  `__snapshots__/` and `golden/` count as test material, so they stay when
  the change is undone.
- **A module turned into a package.** When the change replaces
  `pkg/mod.py` with `pkg/mod/`, undoing it restores the module and removes
  the package. Python imports the package first, so keeping it would undo
  nothing.
- **Broken tests.** Tests that fail with the change and pass without it are
  named, and the report no longer says "nothing would notice".
- **Comparable runs only:**
  - a file and the tests inside it count as the same failure;
  - pytest names every outcome (`-rA`);
  - a run that stopped early (`-x`, `--maxfail`, a collection error), or a
    failure head never reached, cannot give NOT PINNED;
  - a Python run that can import the reviewer's checkout makes the verdict
    UNKNOWN. This reuses `core/strength`'s import guard.
- **Hygiene:** hooks are off, a locked worktree is removed, git timeouts
  are errors, runs start in the project's own folder, and a tracked
  `node_modules` is used as checked out.

## Non-goals

- **Not a gate:** no blocking and no `--require-pinned` yet.
- **No GitHub presentation:** a later task reuses `ep_github`.
- **No model calls.**
- **No dirty working tree as the head:** `head` is a commit.

## Measured next (PLAN §13 A.3)

Seeded unpinned and wrong lines: does a reviewer with this report catch more
of them, sooner, than one reading the diff alone? That is a separate design.
