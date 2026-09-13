# Decisions

Every significant decision, why it was made, and whether it still stands.
Reversals are kept rather than edited away, because the reversal is usually the
more useful record.

## Direction

| # | Decision | Reasoning | Status |
|---|---|---|---|
| D1 | Read fourteen systems from source before designing | The first plan was built on recollection and every load-bearing claim carried a marker saying it was unverified | Stands. Prevented at least four pieces of reinvention |
| D2 | Drop SWE-bench Verified as a discriminating suite | Frontier models cluster at 95 to 97 percent and an audit reportedly found widespread flawed tests | Stands |
| D3 | Adopt the published definition of the submit-resolve gap | A 2026 study already measures this exact failure and found prompting does not fix it | Stands. Gave the headline metric an external anchor |
| D4 | Derive obligations from claims rather than classify tasks into workflows | Obligations are stable while plans are contingent, so replanning becomes ordinary and a whole invalidation subsystem disappears | Stands. Made the system smaller |
| D5 | Frame the system as an incremental build system for correctness claims | It matches what the code actually does, and it borrows a mechanism proven at industrial scale rather than inventing one | Stands |
| D6 | Bound every novelty claim to "not found among the systems surveyed" | Searching found three 2026 papers the plan did not know about, one of which already does runtime process enforcement | Stands. One claim was withdrawn entirely |
| D7 | Build the vertical slice before the evaluation harness | Three weeks of infrastructure before touching a repository would have delayed every real lesson | Stands. Three defects surfaced on day one that testing would not have found |
| D8 | Postpone seven subsystems with written triggers | Each failed the test of whether a developer would notice its absence | Stands. Recorded in `docs/postponed.md` |
| D9 | Defer renaming the project | The name probably does read as derivative, but renaming a repository with no users is free later and a distraction now | Open |

## Mechanism

| # | Decision | Reasoning | Status |
|---|---|---|---|
| D10 | Claim inference by pattern, not by model call | No tokens, no latency, testable offline. The seam for a model call is documented but unused | Stands. Deterministic where possible is a principle, not a shortcut |
| D11 | Questions and code-reading requests produce no claim | Three of the studied frameworks over-route, with instructions amounting to "when in doubt, invoke the skill" | Stands |
| D12 | Coarse invalidation first: any source edit stales everything | Correct but pessimistic. Narrowing to an import closure is standard practice and can wait for evidence that it is needed | Stands, untested in daily use |
| D13 | Only the latest record per identity counts | A test that failed then passed is reproduction, not contradiction | Reversal of the original rule. Found by dogfooding |
| D14 | An obligation must be dischargeable by good work | An obligation nothing can satisfy is a design error. Obligations are filtered by what the project can actually prove | Stands. This one rule removed most of a 75 percent false-block rate |
| D15 | Expensive obligations need a specific trigger | Repeated-run stability was demanded of every high-risk fix; it is only meaningful for nondeterministic bugs | Stands |
| D16 | Risk from directory components, not filename substrings | Any file named `auth.py` was scoring highest risk | Reversal. Found by measurement |
| D17 | Pre-existing failures cannot contradict | Real repositories are often red on their main branch, and blaming the agent blocks every task there | Stands. Mirrors how linters are applied to agent edits |
| D18 | A scoped run and a broad run are different evidence | Running one test file proves nothing about the suite, and running the suite proves nothing about a specific change | Stands. Fixing one direction created a miss in the other until both were separated |
| D19 | A red-to-green transition counts as a covering test | Where tests run through an opaque wrapper, no scoped record exists, but watching a target go from failing to passing is the same proof | Stands |
| D20 | Read the agent's final message | A gate that blocks a question forces the agent to guess; a gate with no abstention pushes it to invent a completion | Stands |
| D21 | Timestamps for the tree signature, with version control as the tie-breaker | Content hashing cost 6 seconds per record on an 8,000 file repository. Timestamps cost 383 ms but misread a formatter's rewrite. Git already compares content | Stands. Best fix of the measurement day |
| D22 | The unrelated-test gap is a warning, not a block | Deciding it properly needs a test-to-source map. Guessing from names would block correct work | Stands, consciously accepting one known miss |

## Evaluation

| # | Decision | Reasoning | Status |
|---|---|---|---|
| D23 | Measure the gate as a classifier | A gate with poor precision is worse than no gate. Nobody in the field frames it this way | Stands |
| D24 | Write scenarios adversarially, expecting failures | Several were written specifically because the design looked weak against them | Stands. The first run was 75 percent and every fix came from a specific case |
| D25 | Keep a held-out set written after tuning | The tuned score was zero; the held-out score was 43 percent | Stands. The single most valuable process decision |
| D26 | Measure latency and scaling explicitly | A verification layer that adds seconds per command is unusable regardless of accuracy | Stands. Caught a 6-second-per-record scaling failure |

## Host integration

| # | Decision | Reasoning | Status |
|---|---|---|---|
| D27 | The hook subscription is generated from the constants the handlers branch on | Two pieces shipped inert because the subscription did not deliver their events. A test now asserts the checked-in file matches | Stands. The general fix for a class rather than three specific ones |
| D28 | Accept every field name and shape a host has used for a tool result | The cost is a few lines; the cost of guessing wrong is total, silent inertness | Stands |
| D29 | The event name is treated as evidence of failure | A failing tool call raises `PostToolUseFailure`. That survives the failure string changing shape again | Stands |
| D30 | Anything unreadable is recorded rather than ignored | All three integration defects failed by doing nothing, and nothing is invisible | Stands |
| D31 | Test fixtures are captured from real sessions, not written | Hand-written payloads encoded the same wrong assumption as the code | Stands. This is the decision that would have prevented all three |
| D32 | Replay real transcripts instead of running new agents | The host records whether each command failed, so the ground truth needs no labels from the author, and 241 sessions cost nothing to grade | Stands. It cannot measure freshness, which is stated wherever its numbers appear |

## Claims

| # | Decision | Reasoning | Status |
|---|---|---|---|
| D33 | No fallback claim from prompt length | Claiming a feature for any sentence over two words attached obligations to 51 percent of real turns that changed nothing | Reversal of the original rule. Found by measurement |
| D34 | A prompt that states no subject does not clear an open claim | One real prompt in five is four words or fewer, and a gate that switches off when the user says "continue" is off for much of a session | Stands |
| D35 | The first source edit opens a claim when the prompt stated none | The same move the scope guard makes: derive from what the task does rather than from what it said. This is what makes short prompts work | Stands |
| D36 | An explicit non-work prompt is never overridden by an edit | Answering a question must not become a claim because a file was touched along the way | Stands |
| D37 | Read write targets out of shell commands | 637 turns changed the repository without touching an edit tool. Narrow on purpose: a target needs a file extension | Stands |
| D38 | Nothing from the session corpus is committed | It is one person's real work across thirty private projects. The labelled prompts are written to match observed shapes, not copied | Stands. The tools read from the machine they run on |

## Live measurement

| # | Decision | Reasoning | Status |
|---|---|---|---|
| D39 | Ground truth is a hidden test written after the agent finishes | The agent cannot optimise against what it never sees, and the visible suite is deliberately green both before and after the fix so a green run proves nothing | Stands |
| D40 | Task properties are enforced by tests, not by convention | A task whose hidden test already passes measures nothing, and that failure is silent | Stands |
| D41 | A third arm that asks for diligence in words | The gate buys extra turns by construction, so "you only gave it more compute" needs an answer in the design rather than in the discussion | Stands |
| D42 | Measure the noise floor before believing any comparison | Two identical passes disagreed on a quarter of the suite, which is larger than the effect being hunted | Reinstated after being skipped. The plan had it right |
| D43 | Report the strongest result a run could produce, before its p-values | An arm can only overturn tasks the baseline failed, so a pilot that cannot reach significance should say so up front | Stands |
| D44 | Move the operating point rather than build harder tasks | Difficulty is a property of the task and model together; a weaker model gave a 31 percent gap where a stronger one gave 12 | Stands |

| D45 | Resolved means the requested tests pass **and** the preserved ones still do | A bug fix owes two things and the grader checked one, on a project whose gate exists to catch the other. A mined commit that yields no preservation set is discarded rather than graded on half the question | Stands. It reaches backwards: the twelve-bug null was measured without it |
| D46 | Grade on membership in the passing set, not on an exit code | An exit code says the run was green; it does not say the tests anyone cared about were collected. It also removes an argv limit that a real preservation set would exceed threefold | Stands |
| D47 | The test tree is restored from upstream before grading | Otherwise a preservation set is defeated by editing the preserved test, which is the agent marking its own work with the grader as second marker. The upstream copy is the one the run cannot reach | Stands. The hole was opened by D45 and closed in the same change |
| D48 | A probe is not trusted until it has been seen to flip | Four of sixteen could not detect the repair of the defect they recorded. A test that fails against a defect looks identical to one failing for its own reasons | Stands. Behavioural fixes are checked against a worktree at the previous commit |
| D49 | Every narrowing fix ships with a control asserting the rule still fires | "Fixed" and "disabled" are indistinguishable from a test that only asserts something is not verified, and R6 sits on top of the 63 points of live blocking M1 removed | Stands |
| D50 | Refuse the no-new-failures concession when no per-test detail exists | A stable failure count cannot tell a suite that is no worse from one that swapped an old failure for a new one. Deliberate loss of leniency | Stands, and may need revisiting if it blocks projects whose runner hides per-test results |
| D51 | Every check runs in both directions, forward and adversarial | A check that refuses everything passes every adversarial test; one that accepts everything passes every forward test. Either alone is indistinguishable from the feature being deleted, and R6 came within one control of proving it | Stands. A standing requirement, not a testing habit |
| D52 | The system does the breaking itself rather than waiting to observe it | Passive observation cannot tell a test that discriminates from one that agrees with whatever it is handed. Revert the change and the new test must go red; weaken a test and the check must stop being satisfied | Stands. Recorded as PLAN §5.0; not yet built |
| D53 | Conclusions come from the four states, not a pass/fail bit | VERIFIED, UNVERIFIED, STALE and CONTRADICTED already separate no evidence from expired evidence from evidence pointing the other way. A boolean throws that away, which is what the grader's bare bool did before E1 | Stands |
| D54 | A run is preserved as a patch against a recorded base, not as a workspace | A workspace is a machine's worth of state that reproduces nowhere else. Twelve candidates were deleted with their temp directory, so a null published from a defective grader can never be re-graded | Stands |
| D55 | The grade is a function of the base and the patch, and nothing else | Grading inside the candidate's own workspace makes the verdict depend on state no bundle preserves. Separation in time is not isolation of authority | Stands |
| D56 | An arm that cannot be assembled is an error, not a silent fallback | The superpowers arm ran as vanilla under the superpowers name. Two identical configurations reported under two names is worse than no comparison | Stands |
| D57 | Sample size comes from measured discordance, never from the flip rate | Flipping is within one arm and disagreement is between two. A deterministic baseline against a deterministic treatment flips never and disagrees always | Stands. The old bound is withdrawn |
| D58 | The grader is graded against answers known in advance | E1 was found by reading the code, because nothing ever ran the grader on a case whose answer was known. `eval.validate` is that case, four ways | Stands |
| D59 | Host-event fixtures are payloads, kept apart from transcript-derived results | A payload this project assembles cannot contain a shape it did not know about, which is how the documented failure form went unread behind a 174/174 replay score | Stands. Every fixture records its provenance |
| D60 | The corpus is pinned in a lock file, not re-discovered by scanning history | Scanning the last N commits of five repositories gives a different benchmark every week, scored under the same name. 3.8KB of pins instead of 1.8MB of test bodies | Stands. Rebuild verified identical on every field that decides a score |
| D61 | A rebuild refuses rather than substituting | A corpus rebuilt from a nearby commit looks like the original and scores differently, which is worse than no rebuild | Stands |
| D62 | Difficulty is a measured label on the gold patch, never a selection filter | E6: selecting tasks by whether the naive fix breaks the suite chooses the benchmark around the mechanism being measured. Bands make a gain concentrated in one band visible instead of averaged away | Stands |
| D63 | Every rejection names its reason, and setup is distinguished from broken | Three of five repositories contributed nothing and said nothing; the cause was missing test dependencies, which looks identical to a repository with no bugs | Stands |
| D64 | A baseline refuses to run unpinned rather than warning | A model alias, an unidentified corpus and a dirty tree each change what is being measured between two runs carrying the same name | Stands. Refusal tested in both directions, since one that refuses everything is broken rather than pinned |
| D65 | The interval resamples tasks, carrying their replicates | Replicates of one task are one observation seen repeatedly. Resampling runs narrows the interval by about the square root of the replicate count, so an honest rerun would read as a contradiction | Stands. Third time this correction has been needed, after E2 and E6 |
| D66 | Reproduction means overlapping intervals on the same corpus, never equal scores | Agent runs are stochastic; an identical score would be suspicious. Two scores from two benchmarks are refused however close | Stands |
| D67 | Context reaching the model is measured from cache creation, not cache reads | Reads grow with turns and say nothing about configuration. Creation is the stable prefix, and it is the measurement E4 lacked when an absent plugin looked like a null result | Stands. A proxy for how much arrived, never for what |
| D68 | Every failure category is decided by the bundle and cites the bundles it came from | A category nobody can open is one somebody will tell a story about, which this project has done twice | Stands |
| D69 | The taxonomy's order is part of it and is tested | A run that timed out and also changed nothing must be a timeout; without a fixed order the counts describe the implementation rather than the runs | Stands |
| D70 | Localised and misplaced are separated, and unattributed when they cannot be | Touching the maintainer's files means the code was found and the change was wrong; touching none means it was never found. Different problems, different fixes | Stands. Needed the gold file list in the bundle, since one needing the corpus to be read is not self-contained |
| D71 | A configuration flag is checked against the bundle, and a mismatch stops the sweep | `--effort` was parsed, printed and never sent — E4 one field over. A warning is worthless at 3am; the journal is already written, so stopping costs only what is left | Stands. Guard watched failing before the fix: without it the mismatch printed six times and kept paying |
| D72 | Every paid run is journalled the moment it finishes, and a restart resumes per replicate | Ninety runs held in memory lose eighty-nine to one crash at run ninety. Resuming by task name would skip the replicates a mid-task death still owes | Stands |
| D73 | A long unattended run gets a per-run budget cap and inputs outside the scratchpad | An agent looping on a hard task has no natural stopping point, and a sweep that outlives the directory holding its corpus is not an overnight run | Stands |
| D74 | Every git call in the evaluation pipeline pins `core.autocrlf=false` and `core.eol=lf` | `git archive` honours the setting, so a repository without a `.gitattributes` was extracted with CRLF and one declaring `eol=lf` was not. The grade was a function of the grader's git configuration, which is D55 inverted inside the module written to enforce it | Stands |
| D75 | A patch moves as bytes from `git diff` to disk to `git apply`, never through a text pipe | Python translates newlines in both directions. Every saved patch held CRLF git never emitted, and every patch handed to `git apply` had a carriage return added to every line | Stands. The probe asserts bytes, because an "it applied" test passed before the fix |
| D76 | Every mined task is checked end to end against the maintainer's own fix and against an empty patch, before anything is paid for | A pre-flight that sampled two tasks passed while the grader corrupted every patch it was handed. A task whose empty patch already resolves is measuring nothing; a task whose gold patch does not resolve is mined wrong. Neither shows up in a score | Stands. Fifteen of fifteen, five repositories, free |
| D77 | Replicates within one sitting are not independent of each other, and a reproduction needs a second sitting | Two tasks were solved 3/3 in one pass and 0/3 in the next, two hours apart, same model id and effort. Within pass A alone, fourteen of fifteen tasks looked deterministic and the conclusion drawn from that was wrong | Stands. The same clustering correction as E2, E6 and the interval, one level up |
| D78 | A score is reported with the per-task table beside it, never alone | 68.9% and 53.3% differ by 15.6 points and overlap; the per-task detail shows two complete reversals, which the headline hides and the interval does not price | Stands |
| D79 | The agent's package installs are confined to its own workspace | An editable install wrote into the shared user site-packages and broke an import machine-wide when the workspace was deleted. A temp directory bounds files and bounds nothing a package manager does | Stands. `PYTHONUSERBASE` inside the workspace; not a sandbox, just the difference between a run that can damage the next one and one that cannot |
| D80 | A run that observed nothing is the harness's fault unless the unpatched base collects | An agent breaking a module and a machine missing a dependency both observe zero nodes. Only a control tells them apart, and without it twelve runs were scored against agents that had solved their tasks | Stands. Both directions probed: the forward case is that a broken module stays the agent's fault |
| D81 | Every published number must be recomputable from the evidence it summarises, by a command | The interval, the taxonomy and the reproduction were all computed correctly from grades that were wrong, and nothing in the reasoning could have revealed it. `--regrade` is that command; the first grade is kept beside the new one | Stands. Needed within four hours of the first paid sweep |
