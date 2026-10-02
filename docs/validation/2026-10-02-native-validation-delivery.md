# Native-validation delivery checks, 2026-10-02

The generalized implementation and review corrections passed the final local
delivery checks below. Installed-host acceptance remains **0/10**, and the
original subscription pilot remains **inconclusive**. These checks establish
regression controls, not a coding-outcome improvement.

## Verification

Windows 11, Python 3.13.2, repository virtual environment and existing Node 22
dependencies. The final runtime/grader code is at `872b248`; later publication
parts reconcile observations, guides, plan/status/journey and the README.

| Check | Observed result |
|---|---|
| `python -m pytest -q` | **1,237 passed, 28 skipped**, 537.28 seconds |
| `python -m pytest tests/test_audit_probes.py -q` | **104 passed**, 86.48 seconds |
| `python -m eval.validate` | All **4** known-answer cases correct: resolved, regressed, unfixed, setup |
| `python plugin/bin/ep_doctor.py --host` | Launcher accepts a prompt; failure/pass receipts, report and blocking paths pass |
| `python -S -c "import core.hosts.validation; import core.hosts.performance; import eval.paired"` | Passed without site packages |
| Evaluator/archive/subscription focused controls | **19 passed**, 6.02 seconds after typed transport correction |
| `python architecture/check.py --render` | **102 nodes, 232 edges, 7 planes**; mirror regenerated; all four tabs draw |
| Added local documentation references | Resolve; includes plan, status, journey and validation links |
| Public JSON artifacts | Eleven checked for raw outputs, known credential prefixes and absolute project paths |
| `git diff --check` | Passed |

The skips are retained in the count rather than treated as passed acceptance.
No regression, audit, grader-control, doctor or documentation check calls a
model. Free performance sampling and native capture do not run project checks.

Hosted [run 36980706343](https://github.com/SatyamSingh-Git/ElevenPowers/actions/runs/36980706343)
passed all four Ubuntu/Windows and Python 3.11/3.13 cells at `5ac0c67`.
That run predates the final failure-metadata and typed-transport corrections;
it is not substituted for final-head CI. The existing workflow now also checks
the new standard-library imports in every cell. Publication to main is gated
on a successful workflow at the exact final feature commit, followed by a
history-preserving fast-forward. CI status remains available in the
[tests workflow](https://github.com/SatyamSingh-Git/ElevenPowers/actions/workflows/tests.yml).

## Independent review and observed corrections

One fresh reviewer used the user-requested GPT 6.1 Sol at medium on the whole
branch. The added archived-protocol scope received a focused continuation with
that reviewer. Each Important finding was reproduced failing before correction:

1. Candidate code could impersonate final grading output. The controller owns
   final assertions; candidate behavior runs separately through `core.process`.
2. Legitimate candidate package imports failed. The bounded worker uses ordinary
   package imports and still keeps candidate code out of the controller.
3. Unsupported resolved run records counted as successes. Complete contracts,
   successful host execution, exact grades, equal budgets and identities now
   qualify counted outcomes.
4. Failed archive records could export private strings in exit/grade metadata.
   Every state receives bounded typed metadata and exact grade validation.
5. JSON erased tuple/list distinctions. Bounded tagged behavior preserves Python
   container and scalar types; dictionary order does not affect equality.

All five controls passed after correction, and the final broad suite passed.
The original eight records and original protocol are preserved. Corrected worker
and grader bytes define a new protocol; explicit archive inspection labels the
earlier evaluator and reproduces its aggregates without regrading or model calls.

Two Minor findings remain: deleting sealed metadata is classified as setup
rather than invalidation, and the sixteen behavioral checks omit invalid account
identifiers already present as balance keys. Neither establishes full contract
coverage. Extended cases require a new protocol.

## Acceptance boundary and next work

Normal Codex hook trust was reviewed and accepted only for the owned disposable
fixture. The subsequent source correction and real failed/passing command had
no native callback delivery. The four current captures and later matrix remain
waiting; all six unsupplied cells remain visible. The eight original comparison
runs hit command policy, missing activation and Claude weekly quota. No API
fallback, positive resampling or broader coding-effect claim was introduced.

The next priority is the native delivery gap, then a newly identified comparison
after subscription capacity is available. Any actual coding or verification
improvement through an engaged mechanism can count; task size is not a criterion.
See [observations and public artifacts](2026-10-02-native-validation.md),
[journey 54](../../journey/54-a-comparison-needs-a-working-host.md),
[current status](../status.md) and [reproducible commands](../../the-guide/commands.md).

The requested publication target is twenty-nine meaningful feature pushes,
with descriptive subjects and no counter suffixes. The
[implementation plan](../superpowers/plans/2026-10-02-native-validation.md)
records their boundaries. Default-branch publication uses the same verified
commit; it introduces no separate implementation and preserves prior history.
