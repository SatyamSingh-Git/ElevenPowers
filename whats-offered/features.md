# Features

[← What's Offered](README.md)

Everything that exists and runs today. Each entry says what it does, what it is worth, and where it stops — because a feature list without limits is marketing.

---

## Evidence capture from ordinary work

**What it does.** Reads the output of commands your agent already runs — tests, typechecks, builds, the failing reproduction it wrote three minutes ago — and files each one as an evidence record bound to the state of the files it observed.

**Why it matters.** There is no protocol. No sentinel lines to emit, no format to follow, no cooperation required. If the agent never does anything special once, the evidence is still there. Every other system in this space asks the model to participate in its own verification, which means the verification can be skipped by a model having an off day.

**Evidence.** 174 of 174 real failures and 5,916 of 5,916 real successes read correctly, across 241 sessions and 36,034 commands. Reproduce with `python -m eval.replay --all`.

**Where it stops.** Replay proves the *parser* is right. It does not prove the host always delivers — that is a separate layer with its own check (see below), and it has failed before.

---

## Evidence that expires

**What it does.** Each record carries a fingerprint of what it observed. Change those files and the record goes `STALE`, carrying the exact command to re-run.

**Why it matters.** This is the idea at the centre of the project. A green test result is not a fact about your repository, it is a fact about a *version* of your repository, and every other system treats it as the former. The closest analogue is not another agent framework — it is `make`, invalidating an object file whose source changed. The mechanism is borrowed from Test Impact Analysis, which has done this in industry for years, pointed at agent completion instead of test selection.

**Where it stops.** Invalidation is **coarse**: any source edit stales everything, not only the evidence whose files actually changed. Narrowing it to each test's import closure is written down with a trigger. Also worth knowing: the fingerprint is size, mtime and a version-control tie-breaker — not a content hash. A same-length edit defeated it in 220 of 300 attempts before that was found and fixed; [journey/18-evidence.md](../journey/18-evidence.md) has the full account.

---

## A completion gate with four states

**What it does.** When the agent tries to finish, computes a state instead of accepting an assertion.

| State | Meaning |
|---|---|
| `VERIFIED` | every obligation met by fresh evidence |
| `UNVERIFIED` | an obligation has no evidence |
| `STALE` | evidence exists, but the files it observed have changed |
| `CONTRADICTED` | the latest evidence for something is failing |

**Why it matters.** "Done" stops being a sentence the model emits. In all fourteen systems read from source, done means the model said so or the model stopped.

**Evidence.** 0% false blocks and 0% misses on 46 labelled scenarios, twelve of which were written afterwards specifically to break it. Reproduce with `python -m eval.run --all`.

**Where it stops.** That is the gate measured *as a classifier*, which is narrow. Measured for whether it makes the work better, twelve real bugs produced identical outcomes with the gate on and off, at 1.4× the cost. The gate is not currently known to improve anything on its own.

---

## Obligations that scale with risk, stated early

**What it does.** Work touching `auth/`, `payments/`, migrations, infrastructure or secrets carries more proof than work touching a README. The obligations are announced at the **first edit**, while the agent can still act on them, rather than at the end as an ambush.

**Why it matters.** Measured live, end-only reporting stopped nearly every first attempt to finish, and nearly always on work that was already correct. Stating requirements while they can still change what happens is the difference between a gate and an obstacle.

**Evidence.** Live blocking fell from 75% of runs to 12% across four live passes. Turns fell by a quarter and nothing a plain agent reliably resolves regressed.

---

## `cannot_complete` as a real outcome

**What it does.** Lets the system conclude that the task should not be done as asked, with a reason and what was tried, and treats that as a legitimate end state rather than a failure.

**Why it matters.** A system with no way to refuse reproduces the action bias that causes false completion in the first place. This is the same reason a frontier model that submits a patch on every single run resolves only 44% of them.

---

## A repeat runner with a derived run count

**What it does.** Runs a command many times, reports whether it is stable, and — when the claim is about something intermittent — computes how many clean runs actually settle the question from the failure rate the agent itself measured.

```
missing  repeated runs show the failure is gone
         ep-repeat 29 -- python -m pytest tests/test_worker.py -q
         so far: still failed 3 of 30
```

Three failures in thirty is a 10% rate; ruling that out at 95% confidence needs 29 clean runs, because 0.9²⁹ < 0.05.

**Why it matters.** Intermittent failure is the one case where a single green run proves nothing, and it is the case **none of the fourteen surveyed systems tools at all**. Every card's hard-task trace ends with the race analysis left to the model.

**It stands alone.** `ep-repeat 50 --jobs 8 -- pytest tests/test_login.py` is a useful flakiness check with no agent involved, and exits non-zero if anything failed, so it works in CI.

---

## A scope guard that asks rather than denies

**What it does.** When an edit lands somewhere the task has neither read nor been asked about, it asks:

```
src/billing/stripe.py is in billing, which this task has not read or edited,
and the request does not mention it. Edit it anyway, or read it first.
```

**Why it matters.** Agents wander. But scope is never declared up front, because nobody knows which files a change will touch before making it — it is derived from what the task established: files read, files edited, areas the request named. And it asks rather than denying, because you are the judge.

**Evidence.** 0 false questions and 0 misses on 25 labelled cases. Silent for creating a file, changing a manifest or lockfile, editing the test for the code being changed, touching a sibling in the same module, or anything the request mentioned. Reproduce with `python -m eval.scope_run`.

---

## A self-check on the layer that fails silently

**What it does.** `ep-doctor` feeds the runtime a tool result shaped exactly the way the host shapes one, and checks the answer comes back right. With `--host`, it drives the launcher as a real process with a real payload on stdin.

**Why it matters.** Three defects in the layer between this runtime and its host each failed **by doing nothing**, while every unit test stayed green. The worst recorded every failing command as passing. A verification layer that silently stops working is worse than none.

Anything the runtime cannot parse is appended to `.elevenpowers/blindspots.jsonl`, so a host that renames a field becomes a diagnosable symptom rather than a tool that quietly went quiet.

---

## Measurement you can re-run

Less visible than the rest, and arguably the most valuable thing here.

| | |
|---|---|
| **A pinned corpus** | fifteen instances mined from five real repositories, locked so a rerun gets the same tasks. `python -m eval.corpus` |
| **A graded grader** | four patches with known answers — gold resolves, a known regression fails, a wrong patch fails, a broken workspace reports *setup* rather than a failed task. `python -m eval.validate` |
| **Run bundles** | every run preserved well enough to be graded again by someone who was not there: task, base commit, arm, resolved model, candidate patch, host events, runtime records, node outcomes |
| **A score with an interval** | refuses to run unpinned. `python -m eval.baseline --pinned` |
| **A failure taxonomy** | every category citing saved trajectories. `python -m eval.failures` |

**Why it matters.** Every number this project published before this existed came from a run nobody could repeat — the corpus was whatever had been mined that week, the model was an alias that could point elsewhere tomorrow, and the score was a bare percentage with no statement of how much was luck. Twelve candidate patches were once deleted with their temporary directory, so a published null became permanently uncheckable rather than merely wrong.

---

## Tested, including against itself

486 tests. All twenty defects reproduced by an external audit are fixed, each keeping the test that found it — and a probe marked `xfail(strict=True)` that starts passing **fails the run**, so a fix cannot land quietly and a regression cannot hide.

Four of those probes turned out to be unable to detect the repair of the defect they recorded, which is its own lesson: a regression test is not evidence until it has been watched failing before the fix and passing after.

---

## What is deliberately not here

No workflow engine. No repository index. No memory across sessions. No model routing. No subagents. No second host.

None of these are oversights — each is postponed with a written trigger in [`docs/postponed.md`](../docs/postponed.md), and the trigger is a measurement rather than an opinion. See [roadmap.md](roadmap.md).
