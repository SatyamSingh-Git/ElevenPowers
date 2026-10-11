# Ordinary-session evidence — 2026-10-11

This milestone repairs existing generalized runtime behavior rather than adding
repository-specific heuristics. It applies to all five host launchers.

## Witnessed repairs

| Boundary | Failing observation | Fresh qualification |
|---|---|---|
| Concurrent reference grader | A 5.2-second delayed SQLite constructor made another worker's barrier expire before claims began | Seven actual reference/mutant/setup controls passed; setup moved before thread start, same concurrent claims and deadlines |
| Prompt identity | Seven failures: missing first/legacy task IDs and evidence inherited by a new read subject | Initial lifecycle/claims/history group: 82 passed |
| Continuation classification | Two failures: `continue` overwrote a claim-less subject, changing later edit classification | Lifecycle, claims, seeded tasks and milestone history: 187 passed |
| Pytest scope | Nine failures in twenty controls: warning/config option values read as targets and real selectors read as broad | Parser, declared-command, core and audit group: 189 passed, including actual pytest subprocesses |
| Ordinary prompt rehearsal | Producer lacked prompt-driven task creation | Four producer controls passed; no model calls |

The original main CI [run](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/38081488525)
failed its Windows/Python 3.11 reference control at 22/23. The failed-job rerun
passed on attempt two. The original log did not identify the failed scenario:
the setup control proves a harness defect, not the exact cause of that CI failure.
Frozen expected outcomes, reference behavior and previous published grades remain
unchanged.

## Fresh review repairs

One independent whole-branch reviewer reproduced four Important defects. Six
failing controls witnessed thread-owned SQLite connections, stepwise-skip
selection, combined short flags and optional debug filenames. The single repair
pass retained worker-owned queues, separated bounded setup readiness from the
unchanged claim barrier and completed the built-in option grammar. All 34
reference/actual-pytest controls passed. No deferred Minor findings.

## Scope and limits

Known built-in pytest argument options consume their values separately from
positional targets. File/node targets and `-k`, `-m`, `--deselect`, last-failed and
stepwise selection remain scoped. An unsupported plugin option or missing option
value leaves an explicit coverage qualification; completed process status and
raw/configured command strings are retained. No pytest dependency enters the
runtime.

Task correlation is independent of claim inference. Questions and read requests
open identities without invented coding obligations. Continuations preserve the
original request and current evidence; clear new subjects isolate both. Legacy
empty identities are repaired when their next prompt arrives.

## Delivery observations

The final-runtime rehearsal qualified 20/20 cells across five hosts, two
languages and replay/synthetic-native modes (251.844 seconds summed local time).
Native follow-ups were current/failed/incomplete/current; replays stayed
unobserved. All prompt-created IDs survived edits without invented claims.

See [results](../../results/ordinary-session-evidence/README.md) for the five-host
Python/JavaScript replay and synthetic native matrix, plus separately qualified
installed observations. Model-free launcher ingress cannot qualify an installed
agent. Matching native commands cannot prove comprehension or coding benefit.
Final review, full compatibility, hosted CI and published-map checks are recorded
with delivery, rather than inferred from an earlier green revision.

## Fresh installed sessions

Two explicitly approved Claude Code 2.1.292 subscription sessions used Sonnet 5.5
at medium, 180 seconds each, with no API fallback. Python and JavaScript both
passed 12/12 acceptance checks and retained native pass/fail/incomplete outcomes,
prompt-created identity without claims and fresh completion. Total observed host
execution was 206.184 seconds, below the 360-second approval. Advice was
emitted and a later current native receipt matched in each session. The sealed
exercise requested those checks already: consumption and coding benefit remain
unproven. Full bounded observations are [published separately](../../results/ordinary-session-evidence/installed.json).
Private attempts and outputs are preserved; no failed attempt was retried into
success. Only 2/10 installed host/language cells are qualified for this runtime.

## Post-commit gates

The final local suite and four hosted Linux/Windows, Python 3.11/3.13 jobs must
pass before integrating the verified commit on main. Hosted outcomes are visible
in [the workflow history](https://github.com/SatyamSingh-Git/ElevenPowers/actions/workflows/tests.yml).
The architecture renderer validates all five views (133 nodes, 311 edges), and
448 local documentation links resolved before delivery. Standard-library imports,
11 host-doctor probes, all four independent grader probes and the preserved
source-grade reproduction passed. Published HTML/mirror bytes are checked after
Pages deployment, with final gate results recorded in the delivery report.
