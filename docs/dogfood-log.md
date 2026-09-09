# Dogfood log

Every friction event and defect found by using the thing, dated. This log is the
product track's raw data. Bugs found by using it count for more than bugs found
by testing it.

## 2026-09-09, first end-to-end run on this repository

**Defect: risk tier inherited from a parent repository.**
`git status --porcelain` walks up the directory tree, so a project that is not
itself a repository reported an unrelated parent's changed files and was scored
medium risk instead of low. Fixed by confirming `rev-parse --show-toplevel`
matches the working root before trusting the output. Found by a test that ran in
a temp directory; would have shipped as mysterious over-strictness for anyone
running inside a monorepo subdirectory.

**Friction: `pytest -q` made an obligation impossible to satisfy.**
The `test_added` obligation wanted a per-test record, but `-q` prints no
per-test lines, so an agent that ran exactly the right test could never
discharge it. Rather than instructing the model to pass `-v`, a scoped suite run
(one that names a test file or node) now counts. The rule: when the runtime can
infer something deterministically, it should, instead of pushing work onto the
model.

**Defect: reproduction evidence read as contradiction.**
The reproduce-then-fix cycle produced a failing record followed by a passing one
for the same test. The gate treated any fresh failure as CONTRADICTED, so doing
exactly what a high-risk `bug_fixed` claim demands produced a permanent block.
Fixed by counting only the most recent record per identity. This was the most
important find of the day and no unit test would have suggested it; it only
appears when the whole cycle runs in order.

**Friction: wrong closing line on a stale-only verdict.**
The gate said "discharge the missing obligations" when nothing was missing and
everything was merely stale. Now it says to re-run the stale checks.

Ledger for a full cycle: 3 evidence records, all fresh, about 4 KB on disk.
Hook latency: under 200 ms per event on this repository, dominated by hashing
the source set.

## 2026-09-09, measuring the gate as a classifier (P2)

Thirty labelled scenarios, then twelve more written afterwards to break it.

**First honest number: 75 percent false blocks.** Fifteen of twenty completed
tasks were blocked. The design was elegant and unusable. Causes, in order of how
much each contributed:

- Risk scored on filename substrings, so any file named `auth.py` demanded
  reproduction and repeated-run stability.
- Repeated-run stability demanded of every high-risk fix rather than of
  nondeterministic bugs.
- Ruby, Java, .NET, Elixir, PHP and every test wrapper (`npm test`, `make test`,
  `tox`) produced no evidence at all, so obligations were undischargeable.
- Projects with no test suite were asked for suite evidence.
- Repositories already red on their main branch read as contradicted.
- Stopping to ask the user a question was treated as a false completion claim.
- A stated blocker had no way to be accepted.

**The rule that fixed most of it.** An obligation must be dischargeable by an
agent doing a good job. Obligations are now filtered by a scan of what the
project can actually prove, corrected by evidence actually observed.

**The overfitting lesson.** After the fixes the tuning set read zero. The
held-out set read 43 percent. Two were real bugs (`pnpm --filter api test` not
matching, and a project's own runner script classified as a program run rather
than a test run, fixed by classifying on output shape instead of command name).

**Scaling failure found by measurement.** Content-hashing the source tree cost
about 6 seconds per evidence record on 8,000 files, paid on every test run.
Timestamps cost 383 ms. The trade was that a formatter rewriting identical bytes
read as stale. Resolved by asking git, which compares content and uses timestamps
only as a cache: unchanged status means unchanged content. Cost 70 ms on the
after-command hook; the before-edit hot path is unchanged at about 102 ms.

Final: 0 percent false blocks and 0 percent misses across 42 scenarios, 50 unit
tests green. What that does not prove is written down in
`journey/05-measurement.md`, and the short version is that 42 constructed cases
written by one person are not real agent behaviour.


## 2026-09-09, building the repeat runner

**Defect found by reasoning, not testing: a false verification.** The `stable`
obligation was declared as runtime evidence, so any runtime record satisfied it.
One execution of a reproduction script that happened not to fail counted as
"repeated runs are stable". On a one-in-six bug that verdict is wrong five times
in six, and it was on the exact task class named as the differentiator.

**Three more found by running the whole loop against a real flaky repository.**
None of them appeared in the unit tests.

- The gate's hint named the whole suite rather than the command that had actually
  been measured flaky. Whatever was already measured is by definition the command
  that shows the bug.
- The end report lists failures that predate the task so the agent is not blamed
  for them, and a repeat run that found the bug looked exactly like one. The bug
  being fixed was reported as somebody else's breakage. Stability measurements
  are now excluded from that check.
- The coverage warning fired on `tests/test_race.py` exercising `src/worker.py`,
  which is a correct pairing with no shared name, and describes most real
  projects. The note now speaks only when a better-matching test file exists and
  was not the one run.

**A bug in the tool's own command line.** `argparse.REMAINDER` swallowed
`--cwd` into the command being repeated, so it ran the wrong thing. Splitting on
the first bare `--` by hand is the correct shape for this kind of tool.

Verified end to end against real randomness: measured 3 failures in 30 runs, the
gate computed 29 clean runs as the bar, refused completion, and passed only once
that bar was met.


## 2026-09-09, the scope guard was dead code

`ledger.allow` was read in three places and written by nothing, so an agent
asked to fix authentication could silently edit billing and the guard never
fired. Same class of defect as the missing repeat runner: a core piece that
looks built and does not function.

**The design question was where scope comes from.** It cannot be declared up
front, because nobody knows which files a change will touch before making it,
and a guard built on a guessed list would spend its life questioning correct
work. So it is derived from what the task established: files read, files edited,
and areas the request named.

**The adversarial cases were written before the implementation this time.** That
was the lesson from the 75 percent measurement. Twelve of the fifteen were edits
that look unrelated and are perfectly legitimate: creating a file, changing a
manifest, editing the test for the code being changed, touching a sibling
module.

**All fifteen passed on the first run, which was the overfitting signal again.**
Ten harder cases written afterwards found three real failures:

- A monorepo's container directory counted as a shared name, so two files in
  different packages looked related because both paths contained "packages".
  Fixed by comparing filename tokens only, since directory structure is already
  what the area comparison handles.
- Generic filenames matched across modules: `src/auth/config.py` and
  `src/billing/config.py` share a name that every module has.
- A plural in the request missed its singular file, and the stemming fix
  revealed a second bug where "dates" became "dat" because the "es" rule applied
  everywhere instead of only after a sibilant.

Final: 25 cases, 0 false asks, 0 misses. Verified end to end in a real session,
silent on five legitimate edits and asking on the one drift.

## 2026-09-09, auditing the wiring

Two core pieces had already turned out to be dead, so the next session was spent
asking what else was listed as working and was not. Everything found was in one
place: the layer between the runtime and the host that feeds it, which no
measurement had ever touched.

**The scope guard was inert one commit after it shipped.** `hooks.json`
subscribed `PostToolUse` to `Bash` only, so no file tool reached the handler
that records what a task has read. Its 25 cases and 20 tests passed throughout,
because they called the function directly.

**Failing commands were invisible twice over.** A failing tool call raises
`PostToolUseFailure`, which nothing was subscribed to. And the result reader
looked for an exit code the host does not send, while treating the string form,
which is exactly the failure case, as a success. Every command was recorded as
passing, which makes `CONTRADICTED` unreachable and lets a red suite satisfy
"the suite passes".

**How it was found.** Not by reasoning. The documentation answered the event
question; the shapes came from reading 6 MB of this project's own first session
transcript, where 105 successful Bash results carried `{stdout, stderr,
interrupted, ...}` with no exit code and 3 failures came back as
`'Error: Exit code 1
...'`.

**What it cost to verify.** Nothing, which is the point. 241 stored sessions
replayed offline: 36,034 commands, 958 of them failing per the host. The
previous reader got 0 of 174 gradeable failures right; the current one gets all
174, and all 5,916 successes.

**What the corpus changed.** Real commands do not begin with the thing they run,
so `cd api && npm run build` matched nothing and took its identity from the
directory. `pytest -q` prints its totals bare, so the quiet mode nearly every
agent uses recovered no counts. `npm run typecheck` was unrecognised. Evidence
coverage went from 12 percent of real commands to 17.

**Friction events:** none observed, because the layer still has not run live for
a working day. That remains the honest gap.

## 2026-09-09, claim inference on real prompts

Having 3,557 real turns available made a second measurement cheap, and it was
unflattering.

**51 percent of turns that changed nothing had obligations attached.** Any
sentence longer than two words claimed a feature. The 0 percent false-block rate
on 46 scenarios stands, and measures a different population: every scenario in
that suite is a piece of work, and real sessions are mostly conversation.

**The gate switched itself off on "continue".** A prompt with no claim in it
cleared the claims of work in progress. Sixty-four prompts in the corpus were
bare continuations and 53 of them changed code.

**One prompt in five is four words or fewer.** The intent for those lives in the
conversation, not the message, so the claim now follows the work: the first
source edit opens one when the prompt stated none, unless the prompt explicitly
asked for something that is not a change.

**Agents write files through the shell.** 637 turns changed the repository
without touching an edit tool. Redirect targets are now read from the command.

After: over-claiming 21 percent, missed work 25 percent and 11 percent on turns
whose change is visible, 31 of 31 labelled prompts correct, gate and scope
suites unchanged at zero.

**Friction events:** still none observed, because the layer still has not run
live for a working day.

## 2026-09-09, the first live agent runs

Eighty-nine runs through the real CLI, $13.33 of tokens, three task suites, two
models.

**The gate works in a live session.** It fires, refuses the stop, and the agent
goes back and does more work. Three phases of "it has never run live" are over.

**The measurement does not work yet.** Two identical plain passes over the same
sixteen tasks resolved eleven and fifteen. A quarter of the suite answers
differently run to run, which is bigger than the effect, so all three arm
comparisons were noise, including a first one that appeared to close the gap
completely and rested on a single task.

**The suite mostly cannot discriminate.** Eleven of sixteen tasks are resolved by
a plain agent every time, one is never resolved, and four are unstable. Only the
unstable four carry information.

**Difficulty is not a property of the task alone.** A second suite built with
careful traps scored identically to the first on the stronger model. Moving to a
weaker model produced a 31 percent gap immediately, and at a tenth of the cost
per run.

**Friction, measured live for the first time.** The gate blocked 7 of 8 runs on
one model and 12 of 16 on the other, and on nearly all of them the plain agent
had already resolved the task. It buys evidence for work that was mostly already
correct, at 2.5x tokens. That is the design working as intended, and it is also
the thing most likely to make someone switch it off.

**Cost of an answer:** about 252 agent runs per comparison, roughly $25 and
several hours per arm, plus a rebuilt suite.

## 2026-09-09, making the gate usable

Four live passes over the same sixteen tasks and model, 64 runs, about $10. Two
of the four tested ideas that were wrong.

**Guidance did nothing.** Saying what would be needed, once, at the edit that
opens the claim, moved blocking from 12 of 16 runs to 14. The transcripts
confirm the text reached the agent, so the channel works and the theory was
wrong.

**The stability obligation was over-firing badly.** Any of a list of words
appearing anywhere in the request demanded twenty clean repeat runs: "sometimes"
in a deterministic bug report, "race" in a pasted job advert. On 566 real bug
reports that was 26 percent of them; it is now 4.

**The cause was structural.** Blocks now record which obligation was unmet, and
in all fifteen blocked runs the agent had written a test and run it, and had not
run the suite, which is a second invocation of the same tool.

**The fix was to stop demanding and start computing.** When a project declares
how its tests run, the runtime runs them at the stop. Blocking fell from 75
percent of runs to 12, turns by a quarter, cost by 15 percent.

**The held-out set caught the first version cheating.** Accepting "a test file
was touched and the suite is green" also passes an agent that emptied a failing
test. Miss rate went to 6 percent until the file was required to still declare a
test.

**Resolution:** 75 percent against a plain arm that scored 69 and 94 on two
identical passes. None of the eleven tasks a plain agent always resolves
regressed; all four failures were the tasks that fail anyway.

