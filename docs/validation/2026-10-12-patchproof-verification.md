# Explicit PatchProof verification qualification — 2026-10-12

Scope: generalized read-only planning, separate explicit execution, durable
attempts, qualified reuse and saved exact-patch observations. No model or fresh
installed-host session ran; no causal coding-benefit result is claimed.

## Reliability investigation

The [initial four-job matrix](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38277583663)
passed at `66bcf9b` on Linux/Windows and Python 3.11/3.13, including ten retained
interrupt/termination/quoted-launch repetitions per cell. This precedes the new
executor and repairs. Original historical failures remain retained and unexplained:
Linux descendant cleanup, Windows 3.11 quoted-launch timeout and Windows SQLite
reference errors. Neither a later pass nor a deadline repair establishes their causes.

Locally, baseline real process/host/recovery controls passed 25 with 2 POSIX skips
in 14.13 seconds. Two exhausted-deadline launch controls failed before the repair;
27 process/host/recovery controls then passed with 2 skips in 15.70 seconds.
The finite-reap control separately failed at an actual `wait(timeout=None)` and
passed with legitimate interrupt/termination controls (3 passes in 1.38 seconds).
These are established separate repairs, not historical incident resolutions.

## Functional observations

- Six initial planner controls: missing module RED, then 6 passed in 16.99 seconds.
- Eleven initial executor controls failed before implementation. Fixture setup
  subsequently exposed correctly refused unignored runtime state. Ordinary setup
  was restored; source dirtiness assertions stayed intact.
- The second prototype run passed 16 controls and retained one incomplete result:
  its command passed but final inspection exceeded its authored 30-second total.
  Success controls use the product's default 120 seconds, not a latency claim.
- Read-only planner, actual Python/Node commands, CLI and process controls:
  36 passed / 2 skipped in 321.74 seconds at the initial completed implementation.
- Malformed/duplicate/deep state and output-preflight controls were witnessed RED;
  repaired controls plus environment/output-limit/actual CLI interruption:
  7 passed in 130.80 seconds. Actual interruption stopped the child, retained the
  first pass and incomplete second attempt, and resumed with reused/passed checks.
- Final environment drift and zero-executed-test classifications failed before
  their repair. Finite cleanup, empty-pair identity and explicit rerun controls
  were also observed RED; 21 focused controls then passed with 2 skips in 113.45 seconds.
- Moving saved execution state returned an older available success before repair.
  Final saved-state reread refused it while legitimate reuse stayed working:
  2 passed in 97.53 seconds. Before/after reads remain non-atomic.

These times describe separate local Windows/Python 3.13 runs, some overlapping
other work. They are not benchmarks or a population benefit estimate. The actual
Python and JavaScript assertions use independently fixed expected values and
detect committed faulty changes; they are workflow smoke controls, not difficult
coding comparisons or proof that an agent writes better code.

## Delivery gates

Whole-branch review, final full suite, named audit probes, independent grader,
doctor, architecture render, hosted final-code matrix and main promotion are
still in progress. This paragraph will be replaced by observed results before
delivery is claimed. Original attempts and private logs are retained in the
milestone workspace; interrupted or failed runs are not silently relabelled.

## Limits

Commands execute trusted project code with caller permissions; process groups
and Jobs are lifecycle management rather than a sandbox. Shared/output/cleanup
bounds are cooperative. Bounded reads cannot detect intervening reverted changes.
Local evidence is unsigned. Dependency bytes, external services, model advice
consumption, current-runtime installed acceptance and causal coding benefit remain
unobserved or unqualified. Use explicit `--rerun` when external inputs may change.
