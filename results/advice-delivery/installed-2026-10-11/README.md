# Installed advice exercise — 2026-10-11

Three real Claude Code 2.1.292 sessions ran the prepared claude/python
exercise (`ep_doctor.py --prepare-acceptance ... --advice`), each in a fresh
disposable directory outside this repository. Sonnet 5 at effort high,
subscription authentication, `--max-budget-usd 3.00` per session, tools limited
to Bash/Read/Edit/Write/Glob/Grep. Total cost of the three sessions plus a
one-call harness probe and one payload-capture probe: **$1.44**.

| Run | Runtime | Prompt opens with | Task | Outcomes | Advice | Acceptance | Cost |
|---|---|---|---|---|---|---|---:|
| [1](run-1/) | `65ba5ad` | "Read EXERCISE.md…" | none | none linked | 0 attempts | waiting | $0.39 |
| [2](run-2/) | `82b67e6~1` | "Fix the boundary bug…" | `bug_fixed` | pass, fail | 3 generated, 3 emitted, 1 matching receipt | waiting: no `incomplete` | $0.39 |
| [3](run-3/) | `82b67e6` | "Fix the boundary bug…" | `bug_fixed` | pass, fail, incomplete | 3 generated, 3 emitted, 1 matching receipt | **passed** | $0.29 |

**Run 1 opened no task.** All 27 callbacks were processed, but the prompt named
no change, so no claim was inferred and `on_prompt` minted no task id; at the
first edit, `observe_edit` declined to open a claim because `opens_new_task`
reads a leading "read" as a request for something other than a change. Every
receipt, completion and advice join keys on the task, so all of them stayed
waiting. The exercise asks the host to fix `app.py`; run 1's prompt did not say
so. The runtime gap — a new subject without a claim gets no task — is open.

**Run 2 and run 3 differ by one fix.** Claude Code moves a Bash call past its
tool timeout to the background and reports it as a plain `PostToolUse` with
`backgroundTaskId` and `timedOutAfterMs` and no exit code (captured by a passive
probe hook). The runtime read that as exit 0, so run 2 recorded the deliberate
timeout as a complete pass and the `incomplete` outcome was never observed.
`82b67e6` treats it as unfinished; run 3 recorded it as an incomplete receipt and
acceptance passed. Run 2 is read against the runtime that ran it; read after the
fix, `runtime_identity` and `startup_runtime` correctly fail
([acceptance-after-runtime-change.json](run-2/acceptance-after-runtime-change.json)).

**Advice reached an installed session.** In runs 2 and 3 the worker generated
context three times, a native launcher flushed all three in a supported context
field, and a later run of the declared check in the same task and session
matched an emitted recommendation (`current`, `pass`, `fresh`).

## What this does not establish

- One host, one language, one version: **1 of 10** acceptance cells.
- `model_consumption` stays `unproven`. In run 1 the agent said no advice was
  visible to it; runs 2 and 3 did not mention advice. The matching receipt is
  the check the exercise told the agent to run anyway, so it shows timing, not
  that the advice was read or followed.
- Local, unsigned observations; the operator supplied the host version.
- No coding benefit is measured: the exercise is a fixed one-line fix.
