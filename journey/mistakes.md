# Mistakes

Kept in full, because the corrections are the most transferable part of the
record. Each entry: what happened, what caused it, what it cost, what changed.

## Planning

### Writing a plan from memory

A 522-line plan was produced without opening a single repository. Every claim
about the fourteen systems came from recollection and was tagged as unverified.

*Cause:* the brief asked for research and a plan, and the plan was easier.

*Cost:* two full rewrites.

*Changed:* when every load-bearing claim in a document carries a marker saying it
has not been checked, that is not a caveat, it is the finding, and it should stop
the work.

### Designing what already existed

The first architecture proposed an evidence ledger, task state surviving
compaction, a repository model, and blind review ordering. Each already existed
in some form in a system that had not been read.

*Cost:* would have been weeks of reinvention.

*Changed:* the research phase now produces a complementarity matrix mapping every
strength to the weakness it covers, so building starts from what exists.

### Writing decision rules the sample size could not support

Confidence intervals excluding zero were specified for three tasks per category
at three runs each. That design cannot produce those verdicts.

*Cause:* rigorous-sounding language substituted for statistical thinking.

*Changed:* measure the noise floor, publish the minimum detectable effect, then
size the suite. Where an effect is too small to detect affordably, say so rather
than writing a rule that pretends otherwise.

### Unbounded novelty claims

"The only system that will refuse to say done without evidence" and "no prior art
at all" were written without the searches that would justify them.

*Cost:* one claim was withdrawn entirely after finding a paper that already does
runtime process enforcement over agent traces.

*Changed:* a novelty claim now names the search that failed to find prior art.
Bounding them made the remaining claims stronger, because the mechanism turned
out to be proven industrial practice and only its application was new.

### An architecture protected through a milestone that did not exist

The plan promised a component would be protected "through M3" while defining only
M0 to M2.

*Cause:* editing a roadmap without re-reading what referenced it.

*Changed:* three more inconsistencies were found in the same pass, including two
competing verification philosophies in one document.

## Implementation

### Risk inherited from a parent repository

`git status` walks up the directory tree, so a directory that was not itself a
repository reported an unrelated parent's changes and scored the wrong risk tier.

*Found by:* a test running in a temporary directory.

*Would have shipped as:* mysterious over-strictness for anyone working in a
monorepo subdirectory.

*Changed:* confirm the repository toplevel matches the working root before
trusting anything git says about it.

### An obligation nothing could satisfy

`test_added` demanded a per-test record, but the most common way to run tests
prints no per-test lines.

*Changed:* this generalised into the rule that fixed most of the false-block
problem later. An obligation that no amount of good work can discharge is a
design error, not a standard.

### Reproduction read as contradiction

The correct sequence for a high-risk bug fix produces a failing record then a
passing one. The gate treated any fresh failure as contradiction, so doing
exactly what was demanded produced a permanent block.

*Found by:* running the whole cycle in order on a real repository. No unit test
suggested it.

*Changed:* only the latest record per identity counts. And dogfooding earned its
place in one example.

### Believing a tuned number

After nine fixes the false-block rate reached zero, and for a few minutes that
looked like success.

*Cause:* the fixes had been tuned against the same thirty scenarios that produced
the score.

*Cost:* would have been shipping a tool that fails on nearly half of real cases.

*Changed:* twelve scenarios written afterwards scored 43 percent on the same
code. The held-out set is now the number that counts.

### Not measuring scaling until late

Content hashing every source file was fine on a small repository and took about 6
seconds per evidence record on an 8,000 file one, paid on every test run.

*Cause:* correctness was measured before cost.

*Changed:* measure latency and scaling alongside accuracy. The fix was a 16x
improvement and produced a better mechanism than the original.

### Testing the halves and never the join

Three defects lived in the layer between the runtime and its host, and 119
passing tests never touched any of them. The subscription delivered `Bash` alone
to `PostToolUse`, so the scope guard was inert one commit after it shipped;
failing tool calls raise a different event nothing listened to; and the reader
looked for an exit code the host does not send, scoring every failing command as
a pass.

*Cause:* the test payloads were written by the same person who wrote the code,
from the same idea of what the host sends. Both halves shared the error, so they
agreed perfectly. Each defect also fails by doing nothing, which looks exactly
like having nothing to do.

*Cost:* the product's central promise was unreachable in real use. A failing
suite would have satisfied "the related test suite passes".

*Changed:* fixtures are now captured from real session transcripts; the hook
subscription is generated from the constants the handlers use, with a test
asserting the file has not drifted; anything unreadable is appended to a
blind-spot log; and `ep-doctor` checks the join rather than either half.

### Believing a rate computed over an unbalanced corpus

The first replay reported 79 percent agreement for the new reader and 96 percent
for the old one, which read as a regression.

*Cause:* the corpus is 97 percent successful commands, so a reader that says
"passed" to everything scores well. The 4 percent gap was mostly stability
records being graded against the wrong command.

*Changed:* failing and succeeding commands are scored separately. The real
comparison is 0 of 174 against 174 of 174.

### A scenario suite made entirely of work

The gate scored 0 percent false blocks on 46 scenarios while attaching
obligations to 51 percent of real turns that changed nothing. Both numbers were
correct; they measured different populations.

*Cause:* every scenario in the suite was a piece of work. Real sessions are
mostly conversation, and the suite contained none.

*Changed:* claim inference is measured on 3,557 real turns against what each
turn actually did, and the labelled set includes continuations, questions,
pasted context and statements.

### A component that switched itself off on "continue"

Any prompt with no claim in it cleared the claims of work already in progress,
so the gate stopped watching the moment the user typed the most common thing a
person types mid-task.

*Cause:* claims were treated as a property of the latest prompt rather than of
the task.

*Changed:* a prompt that states no subject leaves an open claim alone. Only a
question or an explicit request for something else clears it.

### Comparing arms before measuring the noise floor

Three live comparisons were run before checking whether the baseline reproduces
itself. It does not: two identical plain passes over the same sixteen tasks
resolved eleven and fifteen, with a quarter of the suite changing answer.

*Cause:* the plan says the noise floor is measured first, "because without it
every later number is unreadable". It was skipped because the first comparison
produced a result that looked good.

*Cost:* about $12 of agent runs and three comparisons that meant nothing,
including one that appeared to close the submit-resolve gap entirely.

*Changed:* `eval/noise.py` reports the flip rate and sorts tasks by whether they
can discriminate at all; `eval/analyse.py` prints the strongest result a run
could possibly produce before it prints any p-value.

### Building harder tasks when the problem was the model

The first suite was too easy, so a harder one was built with careful traps. It
scored identically, because a single-function bug with a stated contract is
inside a strong model's competence whatever the edge case is.

*Cause:* treating difficulty as a property of the task rather than of the
task-and-model pair.

*Changed:* the operating point moved to a weaker model, where a 31 percent gap
exists to study, and both suites are kept.

### Diagnosing a null from the agent's own test, without reading the answer key

The twelve-bug null was explained as the agent misunderstanding the issue, and
from that came a conclusion that no reachable oracle could help. The hidden tests
say otherwise: the agent's answer for the reported case was correct, and it failed
by not generalising to a second type.

*Cause:* the same one as five previous entries — a story built on a source that
was never opened. Committed while writing about the importance of not doing it.

*Cost:* a wrong conclusion in the plan, two citations quoted in the direction that
flattered it, and very nearly a mutation-testing build aimed at a failure mode
that was not occurring.

*Changed:* an audit rule in the plan — for every failure, ask whether the hidden
expectation was reachable from the agent's permitted context, because missing
information and unused information need different remedies. And a citation rule:
quote a result with the number that qualifies it.

## Tooling

### Declaring a plan complete without checking it against its source

v0.7 was written from an audit and presented as incorporating it. Asked directly
whether that was true, a mechanical check found **fourteen of twenty-five
recommendations covered and eleven missing, including an entire section**. The
reading-list updates — eight primary sources — had been skipped altogether.

*Cause:* the plan was written by reading the audit once and writing from memory
of it. The same shape as the first plan in this project, which was written from
recollection of repositories nobody had opened, and as the null diagnosed from an
answer key nobody had read.

*Cost:* a plan presented as finished that was missing a third of its input,
including a source that contradicts an earlier entry in this project's own
reading list.

*Changed:* the check is now a script rather than a reading. Any document claimed
to incorporate a source is verified against that source item by item.

### Adopting a good external framing and losing my own

Rewriting the plan around the audit's structure silently deleted five things v0.4
had earned: the rule for what to work on next, the smallest-useful-slice
discipline, a compute envelope, a statement of what happens to the shipped tool
meanwhile, and exit criteria stated as commands rather than prose. A second
mechanical check found all five missing.

*Cause:* the audit was right about the objective and had nothing to say about how
this project had learned to keep itself honest. Adopting its shape wholesale
replaced the whole document rather than the parts it addressed.

*Cost:* v0.7 as first written was a larger design than the v0.2 that had been
rejected for being a laboratory, with none of the discipline that made v0.3 and
v0.4 work. It would have been unfollowable in exactly the way v0.2 was.

*Changed:* both checks are recorded here, and the plan now states the rule it is
followed by in its own execution section rather than assuming it.

*The general lesson:* an external critique is authoritative about what it
examined and silent about everything else. Silence is not permission to discard.

### Silent failures from shell heredocs

Several file edits were applied through Python scripts in shell heredocs. Escape
sequences were mangled at least four times: a regex lost a word-boundary marker,
a replacement silently matched nothing and reported success, and once a literal
null byte was written into a source file, which produced a syntax error with no
line number.

*Cost:* perhaps forty minutes across the session, and one confusing debugging
detour.

*Changed:* use the editing tools for source changes. They fail loudly when the
target does not match, which is the entire point.

### Guessing before looking

Twice, a failure was diagnosed by reasoning about what the code should do rather
than by running it. Both times the reasoning was wrong and the cause was found in
one command.

*Changed:* run the smallest thing that shows the actual state before forming a
theory.

### Two operations on one working tree

A full test run was in flight when `git stash` was run in the same working tree,
to time the previous code for comparison. The run reported a number measured
against a tree that changed underneath it, and the number happened to be right.

*Cost:* nothing, this time. A corrupted result would have been indistinguishable
from a clean one, which is the part that matters.

*Changed:* a measurement shares its working tree with nothing. This is the same
class of error as **R7**, the concurrent-writer defect still open in the runtime,
committed by hand while its fix sits on the list.

### Numbers written from memory into a document about not doing that

The journey entry for the grader fix said the test suite had gone from about
forty seconds to 164, and drew a conclusion from it: a slowdown accepted as the
price of better tests. Measured against a worktree at the previous commit, the
suite had already been taking 167.79 seconds. It did not get slower. The
trade-off being justified had not occurred.

Correcting that paragraph, the replacement "after" line was typed before the run
that produced it finished. The counts happened to be right; the time was four
seconds out.

*Cost:* nothing, both were caught before the commit. The second one was caught
only because the first had just been caught.

*Changed:* a figure goes into a document after the command that produced it has
returned, not before. The repository's stated rule already said this — *every
figure below comes from a command* — which is why writing one from memory is a
failure of practice rather than of policy.

### Probes that could not observe their own fix

Four of the sixteen audit probes, written in one afternoon, could not detect the
repair of the defect they recorded.

- **E2's** summed `len(v)` over per-task values, counting arms rather than runs.
  It failed against the defect and would have gone on failing against the fix.
- **R1's** pinned `vcs_state` to a constant to work around a platform flake. That
  stubbed out the exact function the fix changed, and silently converted the
  test's demand from *correct the tie-breaker* to *remove it*.
- **R2's** built its evidence record by hand, so it said nothing about what a
  real suite run records.
- **R4's** second probe asserted against a three-line `detail` string rather than
  the per-test records that name failures.

*Cause:* a probe that fails against a defect looks correct. There is no way to
distinguish one that captured the defect from one failing for its own reasons
until the defect is fixed and the test is watched.

*Cost:* none directly — each was caught while implementing the fix. The cost
avoided is larger: `xfail(strict=True)` on a test that can never xpass records a
defect as permanently unfixed, and the file exists to stop defects being
forgotten.

*Changed:* a probe is not evidence that a defect is captured until it has been
seen to flip. Where the fix is behavioural, check it against a worktree at the
previous commit — it must fail there and pass here. And every fix that narrows a
rule needs a control asserting the rule still fires, because "fixed" and
"disabled" are indistinguishable from a test that only asserts refusal.

### A successful exit code that meant nothing, again

`git apply` returned 0 and applied nothing. It resolves paths against the
enclosing git repository rather than the working directory, and this machine's
home directory is itself a repository, so it walked up out of the temporary
workspace, matched no files, and reported success. The skip message appears only
under `--verbose`.

*Cost:* an hour of debugging, and it would have been far worse undetected: every
re-grade would have silently graded the base tree, with bundles written and
verdicts recorded for code nobody had applied.

*Changed:* the evaluator's workspace is now its own repository, so the working
directory is the top level, and the zero exit is checked against the skip list
rather than trusted.

*The general lesson, for the third time in this project:* a successful exit code
is a claim about the process, not about the work. R5 is the same sentence about
`echo pytest`; phase 8 was the same sentence about a host that signals failure by
changing shape. Each time it looked like a different problem.

### A test that asserted the wrong property

The first probe for E5 had an agent write a `conftest.py` monkey-patching the
broken function, expecting the trick to work in its own tree and fail when graded
from the patch. It worked in both, because `conftest.py` is an ordinary tracked
file and travels with the patch exactly as it should.

*Cause:* the test was written from a story about cheating rather than from the
property being defended. The property is that the grade is a function of the base
and the patch and nothing else, which is about determinism, not deception.

*Changed:* the probe uses something the patch cannot carry, and says in its
docstring that it stands for the whole class rather than pretending the scenario
is common.

### A docstring that claimed what the code did not do

`bundle.write` said `model` was "what the host resolved, not the alias asked
for". The code read `answer.get("model")`, which the host does not send — it
reports usage per concrete model id under `modelUsage` — so every manifest
recorded the alias, and the sentence directly above the field said otherwise.

*Cost:* none yet. A model alias repointed between two sweeps would have produced
a comparison across two different models with nothing anywhere to show it.

*Changed:* both are recorded, and the probe uses the real `answer.json` shape a
live run preserved rather than an invented one.

*The lesson:* a docstring is a claim and gets checked like one. This one was
written at the same moment as the code it describes, which is exactly when the
intention and the implementation are easiest to confuse.

### A flag parsed, printed, reported, and never sent

`--effort high` was read from the command line, echoed in the run banner and
written into the report. It was never added to the command that launches the
agent. The sweep would have run at the default effort under the name `high`.

*Cause:* the flag was plumbed from the outside in — argument parsing, display,
serialisation — and the one place it had to arrive was the only place with no
output to look at.

*Cost:* none, caught in the dry run. Had it survived the night it would have
produced a scored, intervalled, pinned result for a configuration that was never
used, and the pinning would have made it *more* convincing, not less.

*The lesson:* this is **E4 exactly** — an arm labelled for a plugin whose
directory was unset ran vanilla and was reported under the plugin's name. The
shape recurs because a label and the thing it names are written in different
files, and only the label is ever read back. So the label is now checked against
the bundle, and the sweep stops rather than warns.

### A resume that would have skipped what it still owed

The first version counted completed runs per task and skipped any task already
present in the journal. A task interrupted after its second of three replicates
would have been skipped entirely, and the report would have carried a task with
two replicates while claiming three.

*Cause:* "already done" was written as a property of the task, which is how it
reads in the loop, rather than of the replicate, which is what is paid for.

*Changed:* the count is compared against the replicate index. The probe writes a
journal with one run of a three-replicate task and asserts exactly two follow.

### A round trip through one library agrees with itself

`bundle.write` saved every patch with `write_text`, which translates `\n` to the
platform separator, so every `patch.diff` on disk held carriage returns git had
never emitted. The probe guarding that file asserts `read(bundle)["patch"] ==
patch` and passed the whole time, because `read_text` translates the damage back
out on the way in.

*Cause:* the probe tested a round trip rather than a representation. A file
written and read by the same library agrees with itself whatever it put on disk.

*Cost:* every bundle produced before this was unusable outside Python, and a
patch exported under the defect cannot be applied to a tree extracted after the
fix. The two Phase-A sweeps' bundles are in that state.

*Changed:* the probe compares `patch.diff` on disk to `patch.encode("utf-8")`.

### The pre-flight was green because it got lucky twice

Before spending, two live agent runs were made on two real repositories. Both
scored correctly. A five-way adversarial matrix on one of them returned five
different grades including a `regressed` naming the exact broken test. 480 tests
passed. It was declared ready.

The first task of the real sweep failed to apply its patch at all, twice.

`apply_patch` passed the patch through a text pipe (`input=patch, text=True`),
which adds a carriage return to every line on Windows. `git apply` tolerates
that for some hunks and not others. markupsafe's tolerated it; attrs' did not.
So the grader had been corrupting every patch it was ever handed, and the two
samples chosen to prove it worked both landed on the tolerant side.

*Cause:* the pre-flight sampled outcomes. Two tasks out of fifteen, two
repositories out of five, both from the `small` band — and outcome is exactly
the observable that luck can supply. Nothing checked the *representation* being
passed between stages, which was wrong every single time and would have shown up
on the first look.

*Cost:* two paid runs, about ninety cents, and the finding. Had the corpus been
ordered differently the sweep would have run ninety times and reported a score
that silently excluded every repository without a `.gitattributes`, under the
heading "harness breakage, never the agent".

*The lesson:* **a sample of successes is not a test of a pipeline.** When two
stages hand something to each other, assert on the thing handed over, not on
whether the far end happened to like it. The bytes were checkable for free at
any point in the six hours spent preparing to spend money.
