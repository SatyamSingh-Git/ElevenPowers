# Current delivery status

**2026-10-22 — Held-out corpus complete: 40 tasks rehearse clean; no paid run yet.**
Sourcing finished by the frozen rule: 40 tasks from 12 of 90 repositories tried
(cachetools, charset_normalizer, more-itertools, pycparser, pyjwt, tenacity,
uvicorn, wheel, wrapt 4 each; oauthlib 2; iniconfig, tomli 1), 909 candidates
rejected with reasons, three resumes after Windows file-handle errors that are now
handled. Rehearsing the one task that first failed found that pytest 9 prints
`PASSED` for a test whose subtests failed: grading credited an empty patch on
such a task, and mining and the vacuity probe misread them too. The readers now
count `SUBFAILED`; all 40 tasks were re-validated (three moved subtest-only tests
from preservation to fail-to-pass), and the rehearsal then passed 40/40 on every
check. Frame limits, applied before outcomes and to both arms alike: build-
generated modules, suites reading their own installed metadata, test
dependencies outside the install order, and candidates rejected only through
subtest failures (not re-mined). Next: the paid pilot, 8 runs, on approval.
See [corpus](../results/heldout/corpus.json), [rehearsal](../results/heldout/rehearsal.json)
and [journey 88](../journey/88-the-harness-is-checked-before-it-is-paid.md).

**2026-10-21 — Held-out sourcing paused at 21 of 40 tasks; no paid run yet.**
The held-out vacuity comparison has its no-model harness built and tested:
closed-book per-repository interpreters, a sealed never-retry runner, a gold-patch
rehearsal and an analysis fixed before outcomes. Running it found four defects
before any spend (a text-pipe patch that could not apply on Windows, a one-way
environment check, sponsor links taken as repositories, and a disk-full crash that
truncated the first sourcing journal). Sourcing now journals atomically, resumes,
prunes non-contributing repositories and reads history to 2026-10-20. It was
stopped by request after 57 repositories with 21 tasks (charset_normalizer,
pycparser, pyjwt, uvicorn, wrapt 4 each; iniconfig 1); the snapshot,
`results/heldout/corpus-partial-2026-10-21.json`, was later superseded by the corpus.
Rerunning the same `eval.heldout_sample` command resumes after tzdata; fastapi,
interrupted, is redone. Not a corpus until 40 validate and rehearse.
See [journey 88](../journey/88-the-harness-is-checked-before-it-is-paid.md).

**2026-10-20 — Installed declared-check observation completed on both authored cases.**
At the repaired runtime (full local suite 2658 passed, 3 skipped; no-model 20/20),
one frozen Sonnet 5.5 medium Python conversation completed four turns at
4/6/8/10 groups, emitted the declared-check feedback in turn 1 with a `current`
follow-up, and used the owned runner in every turn. With attempt 3's completed
JavaScript run, each authored case now has one completed installed run in which
feedback was emitted and the owned path followed. Two conversations with startup
guidance naming the same runner: no adoption rate, causal effect or coding
benefit is claimed. Hosted Windows cells on two docs-only commits hit two recorded
intermittents, retained and unexplained. Next: the held-out benefit question,
with independently sourced cases and an ordinary arm.
See [results](../results/declared-check-closure/README.md#attempt-4-python-completed-2026-10-20).

**2026-10-20 — unittest summary read; both installed cases follow declared-check feedback.**
Python's standard `unittest` summary is now counted as test evidence (failures,
errors and unexpected successes fail; skips and expected failures are neither;
zero tests is not proof), so filtered `python -m unittest` runs can trigger
declared-check feedback. After a clean full local suite (2655 passed, 3 skipped),
all four hosted cells and a 20/20 no-model run, one frozen batch ran both authored
cases with Sonnet 5.5 medium. Each emitted the feedback in turn 1 and used the
owned runner in all four turns. JavaScript completed at 4/6/8/10 groups. Python
also graded 4/6/8/10, but its turn 4 is recorded `scope_violation`: a host
scratchpad edit outside the project made milestone impact advice raise after scope
had already been verified. That runtime defect and the harness label are fixed;
the record is kept as written. Two conversations on authored cases with startup
guidance naming the same runner: no rate, cause or coding benefit is claimed.
Next: one completed Python run at the repaired runtime.
See [results](../results/declared-check-closure/README.md#attempt-3-both-cases-2026-10-20)
and [journey 87](../journey/87-a-scratch-file-is-not-a-scope-violation.md).

**2026-10-20 — First installed declared-check feedback observation: followed, run incomplete.**
One frozen Sonnet 5.5 medium conversation on the authored JavaScript four-stage
case. In turn 2 a generic `node --test` run left the exact check unqualified, the
hook emitted the feedback, and the agent's next call was `ep_check.py --all`; the
exact receipt is CURRENT and its native follow-up `current`. Turn 3 used the owned
runner again, then timed out at its time share; turn 4 never ran (410.343
model-process seconds). An earlier attempt stopped on a host auxiliary Haiku call
under the exact-model rule; it is retained uncounted, and launches now pin the
host's small model to the protocol model. One conversation and one case: temporal
correlation, not an adoption rate or a causal or coding-benefit claim. Filtered
`python -m unittest` produces no generic evidence, so Python feedback cannot fire
yet. Next: read the standard `unittest` summary, then a completed run on both cases.
See [results](../results/declared-check-closure/README.md#installed-observation-2026-10-20).

**2026-10-19 — Declared-check completion closure delivered, no-model.**
The completion report lists every configured exact declaration as `CURRENT`,
`FAILED`, `STALE`, `ABSENT` or `INCOMPLETE` beside the unchanged verdict; a
generic filtered pass no longer hides an exact gap. Declared-check feedback
leaves three separate hashed observations: intent, a native emission recorded
only after a supported context field was flushed, and a later exact receipt
from the same session that itself postdates the emission. The report labels
them *model consumption unproven*. Owned runs print their attempt digest, so the
path the feedback recommends is observable; those links stay apart from native
receipt history and never count toward health or installed acceptance.

The no-model launcher exercise qualifies 20/20 cases across five hosts,
Python/Node and replay/native. The affected groups pass 610 tests. The full local
suite has 2629 passed and 1 failure caused by a repository-local temporary
directory. Hosted cells at the repaired commit pass where finished. A fresh review
found four defects after the first push, including a CLI crash that reached `main`
for two commits; each was witnessed failing and then fixed. No model was run, and
no adoption, comprehension or coding benefit is claimed.
Next: an installed session observing whether the agent takes the owned path after
feedback arrives, with every non-adoption retained.
See [results](../results/declared-check-closure/README.md),
[validation](validation/2026-10-19-declared-check-closure.md) and
[journey 86](../journey/86-a-gap-is-visible-at-done.md).

**2026-10-17 — Generalized workflow feedback and guarded report reads delivered.**
Completed generic verification now offers bounded owned-runner advice when
the corresponding exact declaration is absent, stale or incomplete. Current
exact failures and unfinished callbacks retain their existing distinctions;
advice runs no command and creates no stronger receipt. Human source-backed
reports share fresh opening/closing inspection, refusing green text after
late source/configuration movement, incomplete scans or deadline exhaustion.

All four current-source hosted cells pass full suites and actual no-model
acceptance artifacts. The local affected group passes 162 controls and the
named audit passes 107; counts overlap. Other named gates, actual Python/Node
runner exercises, sixteen reference snapshot regrades and all five rendered
architecture views pass. Five-to-two report scans and about 0.63→0.28–0.29
second local component medians do not establish whole-workflow speedup. A
one-receipt report adds a closing scan instead: one becomes two.

One fresh Sonnet 5.5 medium JavaScript conversation completed all four turns, with 4/6/8/10 independently recorded cumulative passing groups and 166.434 model-process seconds. The fresh JavaScript acceptance retains 0/4 qualifying owned turns; installed adoption remains incomplete. Both exact declared milestones were CURRENT after turns 1, 3 and 4, STALE after turn 2, and CURRENT at the end. It has no comparison arm and establishes no coding-quality or model-speed advantage.

The earlier comparison stays two correctness ties with higher assisted
times, Python 4/4 and JavaScript 0/4 owned adoption at its own producer.
Next: close the remaining installed declared-check/advice-consumption loop
before another benefit comparison. Independent longitudinal sampling, total
overhead and remaining host/language acceptance also stay open. See [results](../results/workflow-checks/README.md), [validation](validation/2026-10-17-workflow-checks.md) and
[journey 85](../journey/85-a-result-needs-the-right-check.md). Entries below retain their dated producers and next-step context.

**2026-10-17 — Matched four-stage comparison completed: two correctness ties.**
All four Sonnet 5.5 medium conversations complete sixteen turns and qualify for
outcome comparison. All trajectories pass 4/6/8/10 groups, with no observed
regressions; sixteen exported source snapshots independently reproduce.
Assisted model-process time is higher in both cases: 2.34× Python, 1.90×
JavaScript. Python qualifies owned-runner adoption in 4/4 turns and leaves its
declared milestones CURRENT. JavaScript qualifies 0/4 and leaves both exact
milestones STALE despite a fresh generic passing task receipt. That pair stays
in the comparison. No coding-quality or speed improvement was observed.

Twenty focused no-model controls passed. Runtime and frozen harness bytes remain
unchanged from the separately qualified source; this is not a fresh full-suite
claim. Earlier installed failures, controlled successes and the unexplained
advice CI incident keep their own records. Next: no-model diagnosis of the
JavaScript declared-check gap and native/hook overhead, then a generalized repair
if justified. Further benefit experiments need independently sourced longitudinal
cases and frozen sampling, not harder replacements tuned against these results.
See [findings](../results/matched-workflow/README.md),
[validation](validation/2026-10-17-matched-workflow.md) and
[journey 84](../journey/84-a-tie-is-still-a-result.md). Entries below are dated
history; their earlier next-step statements do not override this status.

**2026-10-17 — Readable runner guidance and owned declared-check batches qualified.**
Explicit new verification tasks receive bounded advice even without edits or
inferred coding claims. Readable arguments accompany executable commands.
`ep_check.py --all` runs declared properties under one owner and deadline while
retaining independent receipts, failed checks, unrun selections and drift guards.
Advice launches nothing; filtered rechecks, off and continuation behavior remain.

Current qualification: **all four hosted cells passed their full suites**, alongside 107 local audits. Local disjoint coverage retains 2,557 passes/4 skips across two environments; the original full invocation remains a diagnosed, repaired setup failure, not a fresh single full-suite pass. Two fresh Sonnet 5.5 medium conversations retain **2/2 installed acceptances**, using 212.329 model-process seconds in total. All previous negative trials remain unchanged at their own producers. These authored cases do not establish a causal coding-quality advantage.

Next: prepare a fresh comparison batch at this qualified producer using the unchanged frozen requests/oracles, then run the matched multi-stage outcome comparison as a separate experiment, with all scheduled stages, both arms and adverse/incomplete outcomes retained.

See [plan](superpowers/plans/2026-10-17-declared-check-adoption.md), [validation](validation/2026-10-17-check-adoption.md) and [journey 83](../journey/83-one-entry-point-separate-receipts.md).

**2026-10-17 — Repaired-runtime installed requalification completed; zero of two qualify.**
Two newly approved Sonnet 5.5 medium conversations completed all six turns with
no API fallback or retries, using 94.763 model-process seconds for Python and
47.005 for JavaScript. Both preserve protected inputs, pass the independent
arithmetic check and now have three distinct task identities. Python records
owned receipts on initial and recovery turns, but its dependency failure stays
stale. JavaScript uses compound ordinary commands throughout and retains no
qualifying receipts. Original failures remain separately retained.
The repaired source still has 2,519 local passes (3 skipped), all four hosted
cells and 107 audits. The two requalification allowances are consumed; no
further conversation or larger comparison is approved or run. Next reproduce
and improve bounded runner guidance/adoption during ordinary verification and
tasks with no edits, without treating shell trailers as owned child evidence.
The independent outcome comparison remains blocked; no new coding-quality
advantage is established.
Main delivery `366048d` and published architecture byte identities are verified;
see the [delivery record](../results/installed-multistage/repaired/delivery.json).
See [guide](../the-guide/installed-multistage.md), [journey 82](../journey/82-a-workflow-needs-a-native-trial.md) and [validation](validation/2026-10-16-installed-multistage.md).

**2026-10-16 — Reliable Declared-Check Execution v1 qualified.**
The explicit [runner](../the-guide/declared-checks.md) selects an effective declared
property and saves the actual child result even when an outer shell exits zero.
Durable provisional receipts, task ownership and before/after qualification reuse
the existing runtime. Startup, recheck and completion guidance expose the CLI.
Actual Python/Node controls retain independent milestones and missing-input refusal;
five synthetic host callbacks do not replace owned failure evidence. They are not
installed acceptance. The original Windows advice CI cause remains open after
successful repetitions with retained diagnostics. See [validation](validation/2026-10-16-declared-check-execution.md).
Qualification: 2,458 local tests passed with three skips; all four hosted cells,
107 named audits and five rendered architecture views passed. Main delivery and
published-body identities are retained in the dated validation record.
Next: ordinary installed adoption and independently graded multi-stage benefit.

**2026-10-15 — command-scoped witnesses and shared collection qualified.**
Complete command maps retain independent receipt, milestone and PatchProof
execution evidence, including when an unused witness is unavailable. Every
declared check remains required. Shared external opening/closing reads and late
guards keep gaps explicit. 2,417 local tests passed, 3 skipped in 3663.14 seconds.
All four hosted cells, actual scoped/broad
protocols and artifact acceptance passed, with named audits and independent gates.
The first failed full candidate and its formatter/probe repairs remain recorded.
The two approved Claude conversations established native task transitions and
retained independent milestones; echoed shell trailers prevented exact failure
attribution. Installed acceptance remains partial at the recorded earlier runtime.
See [qualification](validation/2026-10-14-command-input-scopes.md) and
[journey 80](../journey/80-one-input-should-not-expire-every-check.md).

Delivery is verified on main and the published architecture. The final closure
preserves the qualified code and map bytes; automatic main CI repeats remain
separate from the successful final-code qualification.

Next: safe exact invocation in installed workflows and broader behavior
preservation. Further producers, remote observations and live PR/fork transport
remain separate. Earlier per-command/read-multiplication notes below describe
past deliveries; scopes and nested sharing are now implemented and qualified.

**2026-10-13 — External Input Witnesses v2 delivered and qualified.**
Ordinary identified native receipts, completion-owned verification, confirmation
and reuse, retained milestones and public views now share selected approved local
input qualifications. Actual unrelated Python/Node projects pass the seven-state
drift/failure/repair/incomplete/recovery protocol, with source/HEAD/environment
unchanged during the independent dependency fault. Inspection is read-only and
ordinary export shares two selected-target reads. Five synthetic host adapters
are exercised; no fresh installed-session or causal coding-benefit claim.
One final review exposed five Important defects; the first repair group passed
74 tests including all 18 regression controls; the broader affected-path group
passed 91. The final local suite passed 2,357 tests with 3 skips in 3,606.33
seconds. All four final-code hosted cells and artifact acceptance passed,
alongside named audits, independent grader/source reproduction, doctor, stdlib
imports and all five rendered architecture views. Delivery uses a normal main
fast-forward with unchanged qualified runtime bytes. See
[qualification](validation/2026-10-13-external-input-sessions.md) and
[journey 79](../journey/79-a-pass-needs-its-before.md).

Next: qualify broader adoption and behavior preservation. Further producers,
per-command selections, remote observations and live PR/fork transport remain
separate work. Deferred operation cost: native-only PatchProof bundles can still
collect selected targets eight times; monotone native-ID filter collisions
conservatively leave attempts incomplete.

**2026-10-13 — External Input Witnesses v1 delivered and qualified.**
Project-owned literal selections and explicit private root approval add bounded
file/tree observations to PatchProof execution, reuse and read-only evidence.
Actual Python/Node controls show unchanged reuse, independent dependency failure,
required rerun and missing-input refusal. One review exposed five Important
defects; all seven regression checks passed after one repair pass. 2,236 local tests passed, 3 skipped, in 3056.55s.
All four final-code hosted cells and actual artifact transport passed. Named
audits, independent grader/source reproduction, doctor, stdlib imports and all
five rendered architecture views passed. Qualification is recorded in [qualification](validation/2026-10-13-external-inputs.md).
See [usage](../the-guide/external-inputs.md).

Next: qualify broader end-to-end adoption and behavior preservation before claiming
coding benefit. Native passive/milestone witness adapters, additional producers,
per-command input selection, remote observations and live PR/fork transport remain
separately scoped work. No new model or installed session was launched.

**2026-10-13 — GitHub evidence presentation delivered and qualified.**
The reusable cloud Action and portable CLI expose exact declared subjects,
unchanged receipt states, coverage gaps and canonical public bundle hashes.
Actual command controls and hosted summary/upload/download acceptance passed;
three independently reproduced review defects were repaired. Presentation runs
no project check, installation or model and export success is informational.
The latest main repeat revealed a distinct Windows cached-return-code race;
an original-handle wait repaired it within the existing cleanup deadline.
Expanded thirty-round controls passed in all four hosted cells. Earlier
unrelated cleanup/launcher/SQLite causes remain open.
See [guide](../the-guide/patchproof-github.md) and [qualification](validation/2026-10-13-github-evidence.md).

Next: declared external-input/dependency/environment witnesses for conservative
receipt reuse, with independent drift controls. Additional producers, live
PR/fork transport, current-runtime installed qualification and causal coding
benefit remain independent work. No fresh coding comparison or installed session.

**2026-10-12 — explicit PatchProof verification delivered and qualified.**
Read-only plans preserve required commands; separate explicit execution retains
incomplete attempts, exact-head/input/configuration/policy/producer/environment
associations and conservative latest-result reuse. Explicit rerun refreshes
unobserved external inputs. Deadline launch/reap and cancellation handoff
defects were reproduced and repaired. All five review findings, 2,129
local tests, 107 audits and four final-code hosted jobs passed. Earlier
cleanup/launcher/SQLite incident causes remain open.
See [guide](../the-guide/patchproof-verification.md) and
[qualification](validation/2026-10-12-patchproof-verification.md).

Next: read-only GitHub evidence presentation. Additional producers,
external-input witnesses, current-runtime installed qualification and causal
coding benefit remain independent work. No fresh coding comparison or installed-host session.

**2026-10-12 — PatchProof impact integration delivered and qualified.** Optional `--impact`
joins fresh compatible graph snapshots to exact patch/report inputs, explained
consumer paths and focused/fallback/support test candidates. Input association
and semantic completeness remain separate; recommendations never become passing
receipts or safe exclusions. Review repairs, 2,088 local tests, 107 named audit probes and all four hosted
jobs passed. The first Windows 3.11 host-launch timeout remains retained; its
identical-code retry passed without a launcher change. See [guide](../the-guide/patchproof-impact.md).

Next: explicit bounded verification planning/execution, then GitHub presentation.
Other graph/contract producers and broader installed qualification remain open.
No new model run or causal coding-benefit claim. POSIX interrupt cleanup and the
initial Windows 3.11 quoted-launch timeout remain unexplained; successful
qualification must not be described as repairs. Investigate execution reliability
before extending automatic command execution.

**2026-10-12 — declared OpenAPI contract observations delivered and qualified.**
The first PatchProof contract adapter uses pinned oasdiff 1.33.0 against
project-declared committed JSON/YAML specifications. Validation precedes
comparison; producer/input/configuration hashes, limits and retained
incomplete outcomes remain explicit. Exports freshly inspect saved receipts
without launching the checker. See [guide](../the-guide/contracts.md) and [design](design/patchproof-openapi.md).

Full local regressions, 107 named audit probes and all four hosted jobs passed;
see [dated qualification](validation/2026-10-12-patchproof-openapi.md). Three Important review findings
were reproduced and repaired in one pass; no new installed/model run.

Next: compatible ImpactGraph enrichment. Other producers, custom policies,
multi-file specs and broader explicit verification remain independent work.
The completed main CI for PatchProof v1 passed all four jobs. Earlier
installed cells and unresolved cleanup/SQLite observations remain dated;
this new runtime is not installed-session requalification or coding benefit.

**2026-10-11 — PatchProof v1 delivered and qualified.** Exact
committed base/head and full-tree pair identities now wrap existing schema-1
reports with scoped input associations, missing declared checks and explicit
compatibility gaps. The standalone CLI runs no checks or model calls. Dirty,
hidden-index, linked or moving inputs cannot qualify clean committed binding.
See [design](design/patchproof-v1.md) and [guide](../the-guide/patchproof.md).
Local regressions, named audit probes and the corrected four-job hosted matrix
passed; see [dated qualification](validation/2026-10-11-patchproof-v1.md).

Two Claude Code installed language cells succeeded at the ordinary-session
runtime fingerprint `efba988bc33dd96198305a6b77777764a6b2c81e338eefe58d38b4ee97bcfe4e`.
They remain historical successes after this runtime change, not fresh PatchProof
acceptance. Eight other cells, current-runtime requalification, advice consumption
and causal coding benefit remain open. The prior intermittent Linux descendant
cleanup CI failure remains unexplained; the following main CI run completed
successfully. Hosted Windows queue-reference controls also returned SQLite
locking errors in the initial v1 matrix; an instrumented local reference
passed, so that cause remains open. Do not describe later green runs as
demonstrated repairs of either incident.

Next extension: one real contract receipt adapter and compatible
ImpactGraph enrichment, with legitimate/incompatible/stale controls. Explicit
bounded verification and GitHub presentation follow after those interfaces.

**2026-10-11 — ordinary-session identity and pytest scope repairs.** Nonempty
prompts now open a task even without a coding claim. Clearly new subjects get
isolated evidence; continuations retain the original subject and classification.
Known pytest option values, including warning filters containing `::`, are
separate from targets; real files/nodes/selectors stay scoped and unknown options
carry an explicit scope qualification. Queue-grader setup completes before
competing claims start, preserving the concurrency assertions and deadlines.
The original Windows job passed on rerun; its initial failing scenario remains
unknown. Actual launcher rehearsals now support ordinary prompt callbacks without
controller-seeded task IDs. Two approved Sonnet 5.5 medium subscription sessions
now qualify Claude/Python and Claude/JavaScript: 12/12 acceptance checks each,
native pass/fail/incomplete capture and emitted advice with a current follow-up.
These are 2/10 installed cells, not coding-benefit evidence. The final local
suite passed 1,985 tests with 2 skips; all four hosted jobs passed at `8996170`
after one failed-job rerun. The initial Linux process-cleanup failure remains
recorded and unexplained. See [observations](../results/ordinary-session-evidence/README.md).
Final delivery checks are recorded in [the milestone validation](validation/2026-10-11-ordinary-session-evidence.md). Previous coding
comparisons remain ties; none of these repairs establish causal coding benefit.

**2026-10-11 — first installed acceptance cell, with advice emitted.** Three
real Claude Code 2.1.292 sessions ran the prepared claude/python advice exercise
(Sonnet 5 high, $1.44 including probes). The third reached acceptance `passed`:
pass, fail and incomplete outcomes captured natively, every check met, and
advice emitted 3/3 with one subsequent matching native receipt. Two runtime
defects surfaced on the way. A Bash call past its tool timeout is moved to the
background and reported with no exit code; it was recorded as a complete pass
and is now unfinished (`82b67e6`). And a prompt that opens a new subject without
an inferable claim gets no task id, so nothing links: the first session began
"Read EXERCISE.md" and stayed waiting throughout; this was repaired in the ordinary-session milestone above. One historical cell of
ten; model consumption of advice remains unproven. See
[results](../results/advice-delivery/installed-2026-10-11/README.md) and
[journey 71](../journey/71-one-cell-of-ten.md).

**2026-10-11 — untested behaviour claims are qualified.** Replaying two
test-less `bug_fixed` runs from the reverted-tree sweep through the current
runtime reached plain VERIFIED: `test_added` is met by any passing test covering
the changed file, and `feature_added` at low/medium risk asks only for a green
suite. Both claims now carry a stated qualification on every met check when no
touched test file still declares a test; the status is unchanged (reported, not
refused, per §5.12) and refactors are exempt. Found then, and repaired in the ordinary-session milestone above: the parser
reads a `-W filter::Name` value as a test node id, so a broad run with a warning
filter counts as scoped and cannot meet `suite_green`. See
[journey 70](../journey/70-verified-is-not-tested.md).

**2026-10-10 — reverted-tree discrimination and runner provenance.** Run
manifests now record pytest/ruff/mypy through the harness interpreter, node/npm
and the installed package set; before this, 18 of 22 corpus base trees could not
be re-collected today and nothing recorded why. `eval/reverted.py` re-runs
agents' recorded passing pytest checks forward on base+patch and adversarially
on the old source carrying the patch's tests. Across all 106 saved ledgers, 101
checks from 68 bundles: 40 discriminate, 8 are vacuous and 53 do not reproduce
today (missing `hypothesis`/`freezegun`, pytest 9.1.1). Seven of the eight
vacuous checks come from patches with no test; 1 of 41 where the patch carried
tests. All runs predate toolchain recording; the classified checks come from 14
tasks; no model was called.
See [results](../results/reverted/README.md) and
[validation](validation/2026-10-10-reverted-evidence.md).

**2026-10-08 — observable advice delivery.** Optional milestone advice now
distinguishes worker-generated context, a native launcher flushing supported
context, and subsequent exact matching native check outcomes. Readiness joins
task, startup session, wiring generation and runtime with fresh receipts. Only
fully visible, untruncated command recommendations qualify. Optional moving or
damaged state affects its own view; required health and completion gates remain
separate. Bounded hashes retain no context or command bodies. Model-free actual
Python/Node commands exercise five hosts in replay and synthetic native modes.
Fresh installed advice qualification, model comprehension and causal coding
benefit remain open; earlier installed correctness ties are unchanged. See
[guide](../the-guide/advice-delivery.md), [protocol](design/advice-delivery-observations.md), [observations](../results/advice-delivery/README.md) and [validation](validation/2026-10-08-advice-delivery-observations.md).

**2026-10-08 — literal native command qualification.** The shared runtime now
recognizes one literal project-directory wrapper around an exact declared check,
retains raw and configured identities, and preserves failed/incomplete latest
attempts across milestone history and reuse. Targeted checks retain their scope;
ambiguous drive-relative and parent-traversal paths are excluded. Twenty-four
actual Python/npm process controls through cmd and Git Bash qualify the local
capture capability. No model calls or fresh installed sessions ran; original
staged comparison archives remain unchanged. Next qualify installed capture and
observe advice consumption before another causal benefit comparison. See
[guide](../the-guide/command-capture.md),
[observations](../results/native-command-recognition/README.md) and
[validation](validation/2026-10-08-native-command-recognition.md).

**2026-10-08 — installed staged preservation comparison.** Four approved
Sonnet 5 medium subscription sessions completed eight resumed requests on two
authored systems. All stage-one outputs pass 6/6 independent groups and all final
outputs pass 8/8 under corrected checks: two correctness ties and no demonstrated
coding gain or speedup. Total observed host execution was 541.873 seconds within
the approved 1,920-second cap. Native startup/prompt/edit/completion and five
worker attempts were observed, but exact declared-command links were absent for
`cd PROJECT &&` wrappers. Completion-created current milestone receipts do not
qualify native command capture. Original producer grades/protocols are preserved
alongside source-checked corrected regrades; no extra model call was used.
Advice stays opt-in; default activation and end-to-end benefit remain open.
See [protocol](design/behavior-preservation.md), [observations](../results/behavior-preservation/README.md) and [validation](validation/2026-10-08-behavior-preservation.md).

**2026-10-07 — bounded optional milestone advice.** Shared saved-edit callbacks
now deliver bounded exact-check context after explicit project opt-in, with
isolated worker deadlines, atomic reservations, deduplication and task budgets.
Declared file relationships cover known process boundaries without executing
them. Three sealed upstream snapshots recover six selected required leads;
four cross-reference leads remain unknown after unsupported negative labels were
withdrawn. All static reports are incomplete. Eighteen paired report reads add
median 947.254 ms; 135 replay launcher processes show no nonzero exits or
duplicate advice, with median added 1282.703 ms. Installed Claude startup was
observed without a prompt; installed advice cost and coding benefit remain open.
Advice stays opt-in and creates no new gate. See
[design](design/milestone-advisories.md),
[observations](../results/milestone-advisories/README.md) and
[validation](validation/2026-10-07-milestone-advisories.md).

**2026-10-07 — explained milestone rechecks.** Delivered explicit exact-command
grouping, preserved per-milestone evidence, direct/dependency/fallback priority,
bounded explained reasons and compatible byte-derived scan identities. All
fallback checks remain visible. The six authored projects record 36 actual runs
(30 passes, six assertion failures), 5/6 known required relationships and no leads
to six labelled unrelated references. The subprocess relationship is missed and
kept as fallback. Paired small-project reads add median 82.05 ms; native/large
repository cost and incremental coding benefit remain open. Automatic integration
is deferred. See [results](../results/milestone-rechecks/README.md) and
[validation](validation/2026-10-07-milestone-rechecks.md).

The 2026-10-06 delivery below subsequently passed all four hosted compatibility
jobs and was fast-forwarded to main at `1009532`; its integration gate is complete.
The following dated observations retain that delivery's original test counts.

Reviewed **2026-10-06**. ElevenPowers remains a research prototype. All five hosts
share project-independent onboarding, command discovery, repository evidence and
verification. Claude Code, Codex, Gemini CLI, Cursor Agent and GitHub Copilot CLI
have reversible project wiring; the four additions also have portable bundles.
This delivery does not establish improved patch outcomes.

The milestone-verification delivery passed **1,694 local tests with 2 skips**,
the host doctor and four independent grader controls. All five architecture views
rendered at 126 nodes / 289 edges; 411 local documentation links and 34 published
artifact digests were checked. That delivery subsequently passed hosted exact-head compatibility and main
integration; see [delivery validation](validation/2026-10-06-milestones.md).

The architecture page's [Planned view](https://satyamsingh-git.github.io/ElevenPowers/architecture/#planned)
now gives contributors forty-one expandable entry points into unfinished delivery,
research, conditional extensions and proposals. Cards link to the current
sources, identify acceptance criteria and suggest a small first contribution.
This is contributor navigation; the product's unmet exits below remain open.

ImpactGraph now supplies explicit fresh CLI/API queries with typed provenance,
reverse witness paths and candidate tests. The independent API/worker fixture
rejects a seeded boundary fault and accepts equivalent code. Larger-project
acceptance now includes a frozen three-project corpus, an optional TypeScript
compiler and actual offline Python/Node coverage conversion. It found 31/31 known
consumer references and 23/26 known test references across 24 cases, with no
declared negative hit; unlabelled leads remain unknown. Both old and final graph
selections detect 5/6 qualified faults, below the proposed 90% exit. The missed
process test and broad candidate sets keep automatic integration open. This does
not establish improved agent outcomes. Those earlier outcomes remain at
[real-project validation](validation/2026-10-04-impact-acceptance.md).

The relevance repair now recognizes literal Python dynamic imports and
test-context default pytest fixture relationships. Known test recovery improves
from 4/12 to 11/12 valid new symbol-query references (held out 2/6 to 5/6);
the reused prior corpus retains 31/31 consumers and finds 24/26 tests. One
mistaken test/consumer reference is separately withdrawn, with original labels
and raw grades preserved. The conservative set stays available beside focused,
fallback and support groups; six valid references have focused witnesses.
Three actual fault/control attempts qualify after a separately identified
pytest assertion-format correction: repaired recommendations detect 3/3 versus
0/3 old. One fault is reused, two newly authored; this is selection evidence,
not a new coding comparison. Subprocess CLI links, framework/plugin behavior,
unlabelled breadth and native cost keep automatic integration open. See
[relevance validation](validation/2026-10-04-impact-relevance.md).

Optional milestone verification is now delivered: strict project-owned behavior
declarations, bounded cross-task receipts in the atomic ledger, a separate fresh
read-only view/CLI and an additive portable report. Optional impact paths stay
informational. The actual three-stage Python and unrelated Node exercise ran 18
checks: 15 qualified passes and three assertion-fault rejections. Earlier evidence
survives task changes, becomes stale after edits, records fresh failure, and becomes
current after repair/equivalent checks. Native broad scopes expire on unrelated
source additions; narrower attribution is a separate controller control. This
does not establish coding benefit. See [guide](../the-guide/milestones.md),
[results](../results/milestone-verification/README.md) and
[validation](validation/2026-10-06-milestones.md).

## Shipped and exercised

| Capability | Delivered behavior | Evidence boundary |
|---|---|---|
| Selected external inputs v2 | Explicit root approval and bounded local file/tree witnesses qualify ordinary identified native, owned and explicit receipts, reuse and retained milestones | Actual unrelated Python/Node drift/refusal/recovery; synthetic five-host callbacks; missing identities and legacy provenance stay incomplete; no complete environment or installed-session/causal benefit claim |
| Milestone verification | Optional strict declarations, latest cross-task aggregate receipts, separate current/fail/stale/incomplete/absent view and informational impact leads | 18 local authored attempts qualify; broad native invalidation, explicit user scopes and unsigned observations remain limits; automatic completion and coding benefit stay open |
| ImpactGraph | Fresh Python literal imports, calls and context-bound default pytest fixtures; optional grammar/compiler JS/TS; declared/observed paths; focused/fallback/support tests and separate history | 11/12 new valid test refs, 6/12 focused; corrected authored-fault detection 3/3 versus 0/3 old. Partial oracle, subprocess/custom collection/source maps/runtime dispatch/native cost remain gaps; no safe exclusion or automatic integration |
| Repository selection | Git-aware tracked/untracked inputs, inherited ignores, nested boundaries and project exclusions | Supported source extensions and named dependency files; excluded inputs are outside the fingerprint |
| Scan coverage | Explicit file/byte/deadline/unreadable-input diagnostics | Default 20,000 files and 256 MiB; filesystem operations are not a hard wall-clock guarantee |
| Command receipts | Exact configured/discovered commands; complete pass, complete fail and incomplete execution | Opaque wrappers retain command-level evidence; transport success/prose alone cannot prove process success |
| Five-host onboarding | Ownership-preserving setup, explicit or unambiguous auto host selection, command/environment discovery and readiness actions | Host trust/policy remains under the host; custom/ambiguous manifests need overrides |
| Callback activation | Waiting, received, processed startup, errors/history, changed wiring and removal | Launcher observations only; replay excluded; callbacks are not sender authentication |
| Fresh staged project health | One fresh report view; native startup/edit/capture/completion, every declared command's aggregate outcome, progress and read-only optional metadata | Ten-second cooperative default, 120-second maximum; unresolved current callback errors, corrupt/moving state and incomplete coverage cannot pass `--check` |
| Versioned native reports | Bounded runtime identity, explicit installed-version probes, whitelisted captures and ten-cell matrix | Dated unsigned observations; duplicate, changed and incomplete histories cannot pass; full installed acceptance is 1/10 (claude/python, 2026-10-11) |
| Read-only performance | Every attempted repeated health read retained; finite source/timing checks and separate callback/command history | Descriptive local samples, cooperative deadline; no universal speedup or task certification |
| Subscription coding pilot | Frozen original task, independent 16-check grader, exact requested models/medium effort and eight equal-budget journals | Initial pilot inconclusive due policy/activation/quota; no product benefit established; local separation is not an OS boundary |
| Controlled completion comparison | Two original cases, eight actual Claude subscription runs, neutral before/after Stop snapshots and independent grades | All first/final candidates 16/16; three treatment receipt refreshes; no patch-correctness gain; wrapped baseline verification may be unobserved |
| Fixed-patch test review | Immutable source/existing tests, eight subscription reviews, portable archive and all twelve corrected local regrades | Both arms detect five formerly missed meaningful Jinja2 faults; four ties; no incremental benefit; Click F03 mixed failures/setup is separately corrected in all three arms |
| Hard interacting comparison | Four synthetic repairs, 94 frozen groups, all 16 single-fault controls rejected, every-attempt archive and separate visible/shutdown audit | Seven of eight Sonnet 5 medium slots completed; three complete pairs tied; three fresh receipts; interrupted cache code fails a supplementary probe; no coding gain or established speedup |
| Native acceptance workflow | Explicit new disposable Python/Node repository, owned wiring, immutable contract and current pass/fail/incomplete history qualification | Preparation launches no host; local unsigned observations and operator versions do not establish authenticated or cross-version compatibility |
| Native patch attribution | Bounded pre/post target content comparisons; dirty/non-Git files, add/delete/move | Stable task/session/call/input required; target coverage cannot prove absence of unrelated side effects |
| Missing callbacks | Pending coverage visible in status/readiness; completion reconciles missing post-events; eviction uncertainty persists | Interrupted/missing/unsafe/budget-limited observations stay UNVERIFIED even with passing tests |
| Completion checks | Missing/stale checks in guide/strict; same commands deduplicated; receipts persist immediately | Off remains passive; one shared 480-second work budget and 300-second command cap |
| Process lifecycle | Windows Job containment, POSIX process-group cleanup and 8 MiB combined capture limit | Deliberate group escape and abrupt SIGKILL are outside cleanup guarantees |
| Durable progress | Project ownership, atomic short ledger writes, running/deferred/interrupted journal | Journal and activation are diagnostics, never proof of command success |
| Portable verification report | Local Markdown/versioned JSON, qualified claims, latest receipts, freshness, coverage and saved strength findings | Read-only, unsigned; no active claim or incomplete coverage stays UNVERIFIED; findings never alter verdicts |
| Changed-region test strength | Optional Cosmic Ray/Stryker producers, Git hunks/function targets, full-span containment, file/function rotation, command-only reports and legacy reads | Informational; default 60 seconds/8 attempts/15 seconds per command; deleted behavior, budget gaps and parse failures stay incomplete; better relevance does not establish coding benefit |

See [onboarding validation](validation/2026-10-01-live-onboarding.md),
[platform guide](../the-guide/platforms.md), and [journey 50](../journey/50-project-readiness.md).
Historical delivery counts remain in the [validation index](validation/README.md).

## Real-project acceptance

Snag is an acceptance repository, not a runtime special case. Its own manifest
discovered `npm run ci`, `npm run typecheck`, `npm run build` and `npm run lint`.
Read-only selection covered **4,418 files / 81,841,401 bytes** before setup and
**4,417 files / 81,841,184 bytes** afterward, with complete selection coverage.
These are selection measurements, not complete content-fingerprint timings.

Ownership-preserving project setup installed Claude and Codex hooks. An installed
**Claude Code 2.1.281** session delivered and processed SessionStart without a
prompt/model call. Claude activation is active; Codex is configured and waiting.
No business source or Snag branch was changed.

The actual external **`npm run ci` exited 1: 14/15 checks passed**. Its production
dependency audit reported five unexcused high-or-critical package findings:
electron, mailparser, next, nodemailer and undici. The check was not bypassed.
An explicit diagnostic relay recorded the real result as **complete/fail**, with
complete source coverage; it did not mark Codex active. This is separate from
capturing CI through an installed host's native command events.

## Remaining readiness limits

- Versioned live sessions on Codex, Gemini CLI, Cursor Agent and Copilot CLI remain open.
- Claude 2.1.287 now has observed startup/edit/exact fail/pass/completion and fresh pipeline health; intentional incomplete execution remains unqualified, so full native acceptance remains open on all hosts.
- A full native-host Snag command receipt and normal-session latency measurements remain open.
- Snag's dependency audit must be resolved in that project before its full CI is green.
- Unknown tool input/result envelopes, missing identities/events, unsafe paths and budgets remain explicit gaps.
- Cursor/Copilot normal completion has no ordinary report field; use the stored status.
- Per-test dependency invalidation, mutation-based runtime coverage and improved outcome claims remain outside this delivery.
- The prior Linux proc-read probe race was fixed; the historical intermittent five-second descendant-survival assertion has no established runtime cause.

## Portable report acceptance

`ep_report.py --project PATH` exports Markdown by default, or JSON with
`--format json`. It reads fresh source and explicit-path inputs in one scoped
view, preserves evidence qualifications, and shares a cooperative deadline and
project scan budgets. Known credentials are scrubbed and project-root text is
substituted. Prompts, transcripts, outputs and receipt details are excluded.
Saving requires `--output`; replacing a file requires `--force`.

The actual Snag export records revision
`1906da4576f29b02131ff50a29204529b8bcbb5e`, complete selection of 4,417 files /
81,841,184 bytes, and a fresh **complete/fail** `npm run ci` receipt under the
same account/ignore policy as the original relay. Overall task state is
**UNVERIFIED** because no active claim is recorded. No project command was run
to generate it. See [report validation](validation/2026-10-01-portable-report.md)
and [journey 51](../journey/51-receipts-another-person-can-read.md).

## Next readiness milestone

Literal invocation capture is now implemented and locally exercised. Next
qualify it in an installed session and observe whether edit context reaches the
agent; broaden supported syntax only when an independently reproduced gap
justifies it. The first
installed staged comparison recovered callbacks but no exact receipt links for
wrapped commands, and both correctness pairs tied. Keep command identity,
unknown scope and fallback checks explicit; qualify independently justified
larger-project references before default activation. Any further matched
comparison needs a specified opportunity to improve an actual missed regression,
with equal ordinary verification and independent preservation checks.

The resumed session completed all twelve corrected evaluator regrades and the
generalized changed-region/command qualification milestone. Current source
sampling reaches Jinja2 `do_attr` and attrs `_is_class_var`, missed by the earlier
whole-file sample. New-file, nested-function, uneven-file, mixed-language,
deletion and stale-source controls qualify that behavior. Three final focused
upstream baselines pass; Click's bounded baseline times out and stays incomplete.
This establishes analysis relevance, not additional coding benefit. All four
earlier review comparisons still tie. Next use held-out active behavioral gaps
and equal ordinary-review budgets with independent checks before claiming a
product outcome benefit. See [current validation](validation/2026-10-03-strength-regions.md)
and [review findings](validation/2026-10-02-checkpoint-review.md).

The completion comparisons now have a working installed Claude pipeline and
public proposal archives. The harder four-task comparison completed seven of
eight slots: every complete first proposal passed its hidden groups, three pairs
tied, and three tool completions added fresh declared receipts. Interrupted cache
code retains a visible timeout and a separate shutdown defect. Its next proof
exit is correction of independently checked ordinary defective or stale proposals
on representative held-out real issues. Added native host/language cells and the
intentional interruption receipt remain open. See
[hard-task evidence](validation/2026-10-02-hard-task-comparison.md) and
[earlier completion evidence](validation/2026-10-02-proof-of-benefit.md).

Use the new disposable workflow to exercise versioned installed hosts, then
measure normal-session callback/read/command costs on unrelated projects.
This closes the largest remaining usability uncertainty. Shared health and
acceptance tooling are delivered; launcher contracts alone do not close installed
acceptance. Full exercises on unavailable hosts remain open. Optional mutation
findings ship; measured outcome improvements remain separate research work.
Strength needs installed pinned engines and a sufficiently fast isolated test
command; uncertain attribution, linked inputs and budgets stay incomplete.

See [test-strength validation](validation/2026-10-01-test-strength.md) and
[journey 52](../journey/52-tests-that-notice-a-change.md) for actual language controls,
independent-review fixes and the 25 incremental publication parts.

Use focused behavioral checks and a broad integration check at the delivery
boundary; repeat when new corrections or failures warrant it. Documentation,
journey and rendered architecture are part of delivery.

## Project-health delivery

`ep_ready.py HOST --project PATH [--seconds 10] [--check]` now shares one fresh
source/explicit-input report with task interpretation. Every declared command
needs its latest applicable aggregate receipt; individual passing tests cannot
hide a failing suite. Capture, verification and task certification remain separate.
Automatic native diagnostics retain 32 timing samples per phase and 64 hashed
receipt links, with explicit eviction. Health reads execute no project command,
engine or host, and write no project state. Metadata is availability information.

`ep_doctor.py --prepare-acceptance NEW_DIR --platform HOST --language python|javascript
--host-version VERSION` creates an opt-in exercise; `--acceptance DIR --platform
HOST` inspects it read-only. Ten actual language/launcher contract cases passed,
including real process interruption, stale input and rerun. Local version probes
found Claude Code 2.1.286 and Codex CLI 0.159.2; the other executables were absent.
Installed Claude 2.1.286 processed a real startup in the disposable exercise with
no model prompt. Startup is observed; full pipeline and acceptance correctly
remain waiting. One 117.32 ms callback sample is not ordinary-session latency.
Five independent-review defects were reproduced RED, fixed and verified GREEN.
The corrected full suite passed **1,194 tests with 28 skips** in 691.95 seconds.
Exact checks and qualifications are in [health validation](validation/2026-10-01-project-health.md).
See [journey 53](../journey/53-a-working-pipeline-needs-evidence.md).

## Native-validation delivery

The shipped compatibility/performance APIs are generalized. October 2 installed
probes found Codex 0.159.2 and Claude Code 2.1.286; fresh Python/JavaScript
preparations remain waiting and the missing three hosts remain explicit gaps.
Three-read complete samples measured 139.088 ms median on an unrelated small
fixture and 2,511.143 ms on the large external repository. Selected coverage was
3 files/4,008 bytes and 5,209 files/78,409,173 bytes. These samples establish
read costs for those inputs, not ordinary-session overhead or speedup.

All eight frozen subscription pilot records are preserved: Codex candidates
remained unchanged under policy denial, and Claude calls encountered its weekly
limit. Native callbacks were absent. Supported automatic review/local settings
corrections are implemented; native trust was inspected separately through
Codex's normal UI. No coding-outcome improvement is established. Finish native
acceptance and a newly identified, quota-available comparison before claiming
product benefit. [Dated evidence](validation/2026-10-02-native-validation.md) and
[journey 54](../journey/54-a-comparison-needs-a-working-host.md) record the limits.

## Controlled completion delivery

Eight new Claude Code 2.1.287 calls used subscription Sonnet 5.5 medium, equal
240-second budgets and reversed arm order. Passive snapshots in both arms never
stage Git and capture the candidate before/after actual Stop. All first/final
candidates passed 16/16 independent checks. Three treatment completions supplied
a missing exact-command receipt; final fresh receipt coverage was 4/4 versus
1/4 baseline. This is an evidence-coverage improvement, not proof of skipped
baseline tests, better patches or faster work. All 24 saved snapshot grades
reproduced without model calls. [Validation](validation/2026-10-02-proof-of-benefit.md)
and [journey 55](../journey/55-at-the-moment-of-done.md) preserve the protocol and limits.

Subsequent comparisons use preparation-time source/configuration seals, durable
preflight journals, independent Stop capture markers and treatment native count
reconciliation. Recorder gaps cannot qualify an earlier history as complete.
Recorder sink failures preserve the native child's output and completion decision;
absent capture markers leave the comparison incomplete.
The original eight-run publication keeps its recorded producer identity;
regrading explicitly compares current evaluator results with saved grades.
