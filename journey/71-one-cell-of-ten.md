# 71 — One cell of ten

Installed acceptance had been 0/10 for nine days. The exercise was prepared,
the advice path rehearsed in twenty model-free cells, and every launcher
contract passed. What had never happened was a real agent doing the work while
the runtime watched. It took three sessions and $1.44.

The first opened no task. Its prompt began "Read EXERCISE.md" and named no
change, so no claim was inferred, no task id was minted, and the first edit did
not open one either: a leading "read" is taken to mean the user wants something
other than a change. All twenty-seven callbacks arrived and were processed, and
nothing they carried could be linked to anything. That gap is still open. A new
subject without a claim should probably still be a task; it is a semantic
change to how continuations are told apart, and it was not made in a hurry.

The second stated the fix, and everything joined: task, edits, captured fail
and pass, completion, and advice generated, flushed and followed by a matching
check. Everything except `incomplete`. Claude Code no longer kills a command at
its tool timeout; it moves it to the background and reports it with no exit
code. The runtime had a branch for timeouts, looking for `timed_out` — a field
the host never sends. A passive probe hook captured the real payload in one
call, and the fix read the fields that are actually there.

The third session passed. It is one host, one language, one version, and the
model's use of the advice remains unproven: the matching check is the one the
exercise told it to run. But every stage of the pipeline has now been seen
working end to end in a real session, which until today it had not.

Reading run 2 after the fix also showed the acceptance check doing its job:
against the changed runtime it refused, because the code that ran the session
was no longer the code being asked.

See the [results](../results/advice-delivery/installed-2026-10-11/README.md).
