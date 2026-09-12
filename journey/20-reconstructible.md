# 20. Closing Phase A: a run that survives, and a grader that gets graded

## What the last four defects had in common

E3 to E6 were the evaluator's infrastructure rather than its arithmetic, and
they shared a shape: **each one made a result impossible to check afterwards.**

- **E3** — the workspace was a `TemporaryDirectory`, so the candidate went with it.
- **E5** — grading happened inside that workspace, so the verdict depended on
  whatever else the agent had left there.
- **E4** — an arm could be labelled present and be absent, so the thing compared
  was not necessarily the thing named.
- **E6** — the run count was derived from a quantity that does not bound it, so
  the sample size had nothing behind it.

Fixing R1 to R9 stopped the runtime giving wrong answers. These four stop the
*evaluator* producing answers nobody can go back and question, which is the
difference between a measurement and an anecdote.

## A run that outlives its workspace

`eval/bundle.py` exports the candidate as a patch against the seeded base, and
keeps it with the manifest, the host's answer, the ledger, the blind-spot log,
and the grade together with the node outcomes behind it.

The patch, not the workspace. A workspace is a machine's worth of state that
reproduces nowhere else; a patch plus a base identity reconstructs the candidate
anywhere. And the grade is recorded with *which required nodes were seen to
pass*, because a stored verdict nobody can recompute is the same problem one
level up — the problem being that a verdict outlived its evidence.

Grading then happens from that patch, in a tree the evaluator builds:

```python
def grade_patch(task, patch, work):
    base_tree(task, work)
    trouble = apply_patch(work, patch)
    if trouble:
        return Graded(False, "setup", trouble[:300])
    return verify(task, work)
```

**E5 is the second line.** Separation in time is not isolation of authority: an
agent that has just spent twenty minutes in a directory can leave a conftest, an
editable install, a patched runner or a build artefact behind, and grading
inside it computes the verdict through all of that. The patch is the answer.
Everything else the workspace acquired stays behind.

My first test for this was wrong in an instructive way. It had the agent write a
`conftest.py` that monkey-patched the broken function, and expected the trick to
survive in-tree and die in court. It survived both — because `conftest.py` is an
ordinary tracked source file and travels *with* the patch, exactly as it should.
The property is not "the workspace can cheat"; it is **the grade is a function
of the base and the patch, and nothing else.** The test now uses a file the
patch cannot carry, and says that is what it stands for.

## `git apply` exits zero and does nothing

The E3 probes failed for a while with the grader reporting `unfixed`, and the
court's `src/app.py` sitting there unmodified.

```
verbose   rc=0   stderr="Skipped patch 'src/app.py'."
toplevel  rc=0   C:/Users/Satyam
```

**The home directory on this machine is a git repository.** `git apply` resolves
paths against the enclosing repository rather than the working directory, so it
walked up out of the temporary workspace, found nothing matching at
`C:/Users/Satyam`, skipped every file — and returned success. The skip message
only appears under `--verbose`.

Every re-grade would have silently graded the base tree. A bundle would have
been written, a verdict recorded, and the whole re-checking apparatus built in
this entry would have been reporting on code nobody had applied.

The workspace now gets its own repository so the working directory *is* the top
level, and the zero exit is checked against the skip list rather than trusted.
That second part is the general lesson and this project keeps relearning it: **a
successful exit code is a claim about the process, not about the work.** It is
the same sentence as R5, in a different tool.

## An arm that was labelled present and was absent

E4's four parts are separate, but one of them could have produced a headline.

```python
plugin = PLUGINS.get(arm)
if plugin:
    command += ["--plugin-dir", plugin]
```

`PLUGINS["superpowers"]` is an environment variable. Unset, it is `""`, and the
`if` quietly does nothing. **The superpowers arm ran as plain vanilla and was
recorded under the name superpowers** — a comparison between two identical
configurations, reported as a composition result. Nothing anywhere said so.

It is now a hard error naming the variable to set. The other three: arm order is
shuffled per task with a recorded seed, so drift during a sweep cannot line up
with one arm; the environment is recorded rather than inherited silently; and the
model written down is the one the host resolved rather than the alias requested.

## A bound that pointed the wrong way

E6's arithmetic said: an effect of this size needs *n* discordant pairs, and
since a task must be able to change answer before the arms can disagree about
it, divide by the flip rate to get the number of runs.

The middle clause is false. A baseline that fails every time against a treatment
that succeeds every time **flips never and disagrees always** — zero flip rate,
complete discordance. Dividing by it gave a run count with nothing behind it, and
the direction of the error is the bad one: the more stable the tasks looked, the
larger and more authoritative the required sample appeared.

Discordance has to be measured with both arms running. `runs_for` now takes it as
an input, and `eval/noise.py` says in plain words that it cannot be got from one
arm.

## Grading the grader

`python -m eval.validate` is new, and it exists because **every measurement this
project published came out of a grader nobody had graded.** Four patches with
four known answers:

```
case                                    expected    got
the maintainer's own fix                resolved    resolved
the fix, and a break elsewhere          regressed   regressed
a patch that changes nothing relevant   unfixed     unfixed
a workspace that cannot be built        setup       setup
```

The third and fourth rows carry as much weight as the first two. A grader that
answers `resolved` to everything passes row one; one that answers `regressed` to
everything passes row two; and harness breakage must read as harness breakage
rather than as an agent that failed. E1 was found by reading the code, not by
running it, because nothing ever ran it against a case whose answer was known.

## The exit criterion that was lying

Phase A's fourth exit was `python plugin/bin/ep_doctor.py --host`, and it had
been printing six green lines and exiting zero since the day it was written.

The script parses `--cwd` and nothing else. `--host` was discarded, and what ran
was the ordinary in-process check against no host at all. **A criterion that
passes by ignoring the argument that made it a criterion.**

`--host` now drives the launcher the way the host drives it — a process, a
payload on stdin, an exit code and a pipe — across five paths: a prompt opens a
task, the documented failure shape reaches the ledger, a passing command reaches
the ledger, the report path speaks through a field Stop honours, and the blocking
path refuses the stop and says why. Unknown flags are refused with exit 2 rather
than ignored.

That last part matters more than the mode itself. Every one of the defects that
made `ep-doctor` necessary failed by doing nothing, and a flag silently dropped
is the same failure in the tool built to catch it.

## Two fixtures that were one

Phase A also asked for raw host-event fixtures kept separate from transcript
fixtures, and the reason is H1 exactly.

`tests/fixtures/real_bash_results.json` holds tool *results* lifted from a
session transcript, and `test_payload.py` builds a hook payload around each one
before reading it. That is a fine test of the reader and it is not a test of the
contract: **a payload this project assembles cannot contain a shape this project
did not know about.** Which is how the documented failure form went unread while
a replay score of 174 out of 174 sat in the README.

`tests/fixtures/host_events.json` holds whole payloads, read exactly as they
arrive, with no wrapping or adapting. Every fixture records where its shape came
from — documented contract, captured session, or invented on purpose to be
unrecognisable — and a test asserts that provenance is recorded, because a
fixture whose origin is unrecorded is a fixture somebody invented.

## A Linux worker, without Docker

The plan asked for an isolated Linux worker, and the machine this is built on
cannot run Docker. That was never a reason to skip it: the mistake the audit
named was letting one laptop's limitations define the scientific scope.

`.github/workflows/tests.yml` runs the suite, the probes, `eval.validate` and
`ep_doctor --host` on Ubuntu and Windows, at 3.11 and 3.13. It is not a container
farm and it is enough to stop a result being a property of one machine — which is
not theoretical, since several defects closed this week were platform-shaped: a
shell tool the runtime never subscribed to, and a `git apply` that did nothing
because of where somebody's home directory happened to be.

## The live run, which failed usefully

The fourth exit needed real agent runs. Four of them — `last_page`, vanilla and
gate, two replicates each, on haiku, for $0.36.

All four came back `setup`:

```
error: git diff header lacks filename information when removing
1 leading pathname component (line 4)
```

The seeded workspace had no ignore rules, so `git add -A` staged
`__pycache__`, the pytest cache and the runtime's own ledger. The exported
candidate was mostly `.pyc` blobs and `git apply` rejected the whole patch.

**Two things made that a good outcome rather than a bad one.**

The harness said `setup`, not `unfixed`. Four runs of *I broke*, not four runs of
*the agent failed* — which is the fourth row of `eval.validate` earning its place
on its first real outing. Under the grader this project used last week, those
would have been four silent zeroes against the agent.

And the bundles made it diagnosable. I read the offending `patch.diff` from a run
whose workspace had been deleted twenty minutes earlier, which is the entire
point of E3, demonstrated by accident.

The fix keeps artefacts out through `.git/info/exclude` rather than a
`.gitignore` — per-repository, untracked, so the agent never sees it, it does not
alter the base the task presents, and it cannot collide with an ignore file a
mined repository already ships. Excluding `.elevenpowers/` matters for a reason I
had not thought of: **it is written only under the gated arms**, so leaving it in
would make every gated patch differ from every plain one for a reason that has
nothing to do with the code.

The second sweep worked, and `gate` ran before `vanilla` — E4's shuffling,
visible in the log.

```
arm       runs tasks  claimed  resolved    gap  turns  blocks    cost
vanilla      2     1     100%      100%     0%    7.0       0    0.13
gate         2     1     100%      100%     0%   16.0       2    0.23
```

`runs 2, tasks 1`. Replicates retained on real data, where before E2 the second
run silently overwrote the first.

## Then the bundle caught two more

Reading the preserved manifest, rather than trusting the code that wrote it:

**`"model": "haiku"`.** The alias. The host reports usage per concrete model id
under `modelUsage` and has no top-level `model` key, so `answer.get("model")`
fell back every time — while the docstring immediately above it said "what the
host resolved, not the alias asked for". A false claim in a docstring is still a
false claim, and this one would have survived a model alias being repointed
between two sweeps without a word.

**`"passed": []`.** `_verify_seeded` never filled in the node outcomes that
`_verify_real` does, so every bundle from the simple suite carried a verdict with
nothing behind it — the exact failure this slice exists to fix, reproduced inside
the fix.

Both were repaired against the real `answer.json` the run had preserved, so
neither needed another sweep. That is the second time in one afternoon the
artifacts paid for themselves.

## Where this leaves Phase A

**Twenty of twenty defects closed**, R2 narrowed rather than closed and marked as
such. 436 tests, no xfails. All four exit criteria pass as commands. Total live
spend $0.72 against a $5 envelope, and the half that bought a defect was the
better half.

What Phase A bought is not a better score. It is that the next number this
project produces can be disbelieved productively: the candidate is kept, the
grade is reproducible from it, the arms are what they say they are, and the
grader has itself been graded against answers known in advance.

The first live sweep after all of it still found something no test had. That is
not a failure of the tests — it is the reason the plan says every phase ships
something runnable before it ships something complete.
