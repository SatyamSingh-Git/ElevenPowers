# ElevenPowers

Decides when a coding agent's work is actually done, and keeps that answer honest as the code changes.

Status: week-one vertical slice. Working on Claude Code. Not yet evaluated at scale.

## The problem

Ask a coding agent to fix a bug and it will tell you the bug is fixed. Published measurements put the gap between claiming completion and actually resolving the task in the tens of percent: one study found a frontier model that submitted a patch on every run and resolved 44 percent of them. Prompting the model to be careful does not close that gap.

Fourteen agent systems were read from source for this project (notes in `docs/research/`). In all of them, "done" is either the model saying so or the model stopping. One of them binds a single declared command to a working-tree hash. None computes completion from evidence.

## What this does

It watches the commands your agent already runs, turns their output into evidence records, and binds each record to the exact content of the files it observed. A claim like `bug_fixed` carries obligations. The gate computes a state rather than accepting an assertion:

```
UNVERIFIED  bug_fixed
  missing  a test covering the change passes
           run the test that exercises this change, by name or by file
  missing  that test failed before the fix
           run it before applying the fix so the failure is on record
  met      the related test suite passes
```

And because evidence is bound to file content, editing a file after the tests were green invalidates them, the way a build system invalidates an object file:

```
STALE  bug_fixed
  stale    a test covering the change passes
           recorded at tree fb7fb4ae5570c0da, files have changed since
           re-run: python -m pytest tests/test_core.py -q
```

The closest analogue is not another agent framework. It is `make`.

## States

| State | Meaning |
|---|---|
| `VERIFIED` | every obligation met by fresh evidence |
| `UNVERIFIED` | an obligation has no evidence |
| `STALE` | evidence exists but the files it observed have changed |
| `CONTRADICTED` | the latest evidence for something is failing |

A failure that was later fixed is reproduction evidence, not a contradiction. Only the most recent record per identity counts.

## Install

Requires Python 3.11 or later and Claude Code.

```bash
git clone https://github.com/SatyamSingh-Git/ElevenPowers.git
claude --plugin-dir ElevenPowers/plugin
```

Nothing to configure. Ask for a change as you normally would.

To check that the runtime is seeing what the host sends:

```bash
python plugin/bin/ep_doctor.py
```

## How it decides what to prove

Claims are inferred from the request with pattern matching, no model call and no added latency. A question or a request to read code yields no claim at all, and the runtime stays out of the way entirely.

Risk comes from the paths a task touches: anything under auth, payments, migrations, infrastructure or secrets is high risk and carries more obligations. Everything else is scored by size.

| Claim | Low risk | High risk adds |
|---|---|---|
| `bug_fixed` | covering test passes, suite green | prior failure on record, stability over repeated runs |
| `feature_added` | suite green | covering test, typecheck, build |
| `refactor_safe` | suite green | typecheck, build |
| `migration_safe` | applies and reverts | suite green, stability |
| `perf_improved` | benchmark | suite green, stability |
| `deps_updated` | suite green | build, typecheck |
| `docs_changed` | nothing | nothing |
| `cannot_complete` | a reason and what was tried | evidence the blocker is real |

`cannot_complete` is a real outcome. A system with no way to say "this should not be done as asked" reproduces the action bias that causes false completion in the first place.

## Flaky and intermittent bugs

The one case where a single green run proves nothing. Ask about something
intermittent and the runtime requires repeated evidence, and computes how much
is enough from the failure rate the agent actually measured:

```
missing  repeated runs show the failure is gone
         ep-repeat 29 -- python -m pytest tests/test_worker.py -q
         so far: still failed 3 of 30
```

Three failures in thirty runs is a ten percent rate, and ruling that out with 95
percent confidence needs 29 clean runs, since 0.9 to the power 29 is under 0.05.
The agent is told the number rather than left to pick one.

The runner stands alone too:

```bash
ep-repeat 50 -- pytest tests/test_login.py     # is this flaky, and how flaky
ep-repeat 50 --jobs 8 -- pytest tests/test_login.py
```

None of the fourteen systems surveyed ships a repeat runner or any other
tooling for nondeterministic bugs.

## Staying inside the task

Agents wander. The guard asks when an edit lands somewhere the task has neither
read nor been asked about:

```
src/billing/stripe.py is in billing, which this task has not read or edited,
and the request does not mention it. Edit it anyway, or read it first.
```

It asks rather than denies, because the person is the judge. Scope is not
declared up front, since nobody knows which files a change will touch before
making it. It is derived from what the task established: files read, files
edited, and the areas the request named.

Silent for all the edits that look unrelated and are not: creating a file,
changing a manifest or lockfile, editing the test for the code being changed,
touching a sibling in the same module, or anything the request mentioned. On 25
labelled cases the guard raises no question it should not.

## Checking that it is actually working

A verification layer that silently stops working is worse than none, and the
failure mode is real: three defects in the layer between this runtime and its
host each failed by doing nothing, while every unit test passed. So the join is
tested rather than assumed.

`ep-doctor` feeds the runtime a tool result shaped the way the host shapes one
and checks the answer comes back right:

```
ok    python 3.13.2
ok    a failing command is recorded as failing
ok    a passing command is recorded as passing
ok    hooks.json subscribes to every event the runtime handles (6 tools recorded)
ok    the ledger directory is writable
ok    nothing unreadable has arrived from the host
```

Anything the runtime cannot read is appended to `.elevenpowers/blindspots.jsonl`
and reported by that last check, so a host that changes a field becomes a
diagnosable symptom rather than a tool that quietly went quiet.

## Measured against real sessions

Claude Code writes a transcript of every session, including each tool result
exactly as the host produced it. Replaying those costs no inference and needs no
hand labelling, because the host itself records whether each command failed:

```bash
python -m eval.replay --all
```

Across 241 real sessions and 36,034 commands, the runtime agrees with the host
about whether a command failed on 174 of 174 failures and 5,916 of 5,916
successes. The reader this replaced agreed on 0 of 174.

Reported as two rates rather than one, because the corpus is 97 percent
successes: a reader that answers "passed" to everything scores 97 percent
accuracy while being wrong about the only thing the gate needs to know.

## What it does not do yet

No workflow engine, no repository index, no memory, no model routing, no subagents. Each is postponed with a written trigger in `docs/postponed.md`. Invalidation is currently coarse: any source edit stales everything. Narrowing it to the import closure of each test is the documented next step, and only once measurement shows the coarse version is too pessimistic to live with.

It has also not yet been watched running live for a working day. Replay shows the runtime reads correctly what the host wrote down; it does not show the host delivering those events to a running hook.

## Design notes

`PLAN.md` holds the thesis, the architecture, the hypotheses being tested, and the honest bounds on what is new here. `docs/research/` holds the study of fourteen systems that produced it, with every claim cited to a file at a recorded commit.

The mechanism is not invented. Test Impact Analysis has tracked test-to-source dependencies in industry for years, and falls back to running everything when its map goes stale. This borrows that and points it at agent completion instead of test selection.

## License

Apache-2.0. Attribution for every reused idea and file is in `docs/research/licenses.md`.
