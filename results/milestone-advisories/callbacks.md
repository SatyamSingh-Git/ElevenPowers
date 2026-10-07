# Bounded launcher and installed startup observations

Runtime source at the beginning of measurements: `9e3f618`, with the additional
replay measurement harness and controls in the delivery that publishes this
record. [Raw callback observations](callbacks.json) retain every sample;
[saved attempt outcomes](attempt-outcomes.json) retain reservation statuses and
elapsed times, separate from context coverage.

Three disposable copies of the sealed Click, attrs and Jinja snapshots exercised
all five launchers, three times each: **45 baseline/advised/duplicate triples,
135 actual launcher processes**. No model or project check was run. Median
paired added delay was **1282.703 ms**; maximum advised callback **1799.336 ms**
on this Windows machine, using one-second cooperative inspection and a
0.5-second worker grace. All 135 exits were zero; no duplicate delivered advice.
All 45 advised contexts were incomplete, as expected from static coverage gaps
and the tight budget. Saved attempt state records **44 delivered contexts and
one incomplete worker attempt**. Delivered context does not mean coverage was
complete. An interrupted process can remain reserved and consumes its allowance.

The launcher replay flag deliberately prevents these calls from activating a
native-host acceptance record. These measurements qualify local bounded replay
behavior, not installed edit/completion latency, agent usefulness or a portable
upper bound on all filesystem/process cleanup costs.

Separately, installed **Claude Code 2.1.287** launched interactively in a new
disposable project with project/local settings and empty strict MCP configuration.
No prompt was submitted. Its native SessionStart was received once and processed
once, with a recorded callback sample **1135.235 ms**, runtime fingerprint
`5e4aec22d498b74ebb3974fff3a113a6518ad82c452bb86bcd0483f057a01285`.
[Saved startup metadata](native-startup.json) preserves that observation.
This is startup delivery only; it does **not** exercise the new edit advice.
The four added hosts and all five installed edit/advice sessions remain open.
Automatic advice therefore remains explicit project opt-in.

Reproduction helper: `eval.advice_callbacks.measure(disposable_root,
changed="src/module.py", repeats=3, seconds=1)`. It intentionally writes project
config and task state; use a disposable source copy. Source snapshots and
declarations are specified in [larger-project results](README.md). Replay and
full native acceptance are separate evidence classes throughout this project.
