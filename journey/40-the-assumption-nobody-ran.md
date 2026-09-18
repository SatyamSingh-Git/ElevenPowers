# 40 — The assumption nobody ran

*2026-09-17 into 2026-09-18. Four commits that had no entry, and the pattern
underneath all of them.*

This entry exists partly because it was overdue. Four commits shipped without
one — the dirty-tree attribution fix, the nine-language proof, the turbo defect
and the de-naming pass — and the omission was the user's to point out, in a
repository whose own standing rule is to record what was tried and what was
wrong. Writing about discipline while skipping it is its own data point.

---

## What those four commits were

**A task that edited one file was credited with four.** `touched` came from
`git status`, so every already-uncommitted path a developer had in flight was
attributed to whatever they asked next. It inflated the risk tier, demanded
obligations for untouched code, and handed `radius.py` a blast radius computed
from somebody else's half-finished work. The ledger now records what was dirty
at task open and subtracts it.

**Four of nine languages were wrong.** Go attaches methods by receiver at the
top level and lost every one. Rust named the *trait* as the owner of an `impl`
block, which would have grouped siblings by the wrong thing entirely. PHP calls
its identifiers `name` and so dropped every base class. C# read nothing at all,
because the grammar is `csharp` and the table said `c_sharp` — the error
handling degraded to silence exactly as designed, and that is what hid it.
Bigger than any of those: only *classes* were read, so a functional TypeScript
file produced no symbols at all, and most TypeScript is functional.

**`turbo test` produced no records, and hid a failing package behind a passing
one.** It prefixes every line with the package it came from, and the TAP
patterns anchored hard at the line start. Behind that, the counts were
overwritten rather than summed, so a failing package followed by a passing one
reported `fail 0` — a red monorepo laundered into a green record. R10 arriving
by a new road, in code written *because* R10 had taught that lesson once.

**And the tool stopped naming a private project.** Four references gone. Two
over-fits found while checking: a line prefix fixed at the shape of the one
runner that had been looked at, and an import-graph cap of 1200 files sized from
Python's `ast` at 6ms a module when tree-sitter measures 3.8 — so a 1,700-file
TypeScript repository blew past a limit set for a different parser and the
feature silently did nothing on exactly the kind of repository it was built for.

---

## One shape, seven times

| assumption | how it was found |
|---|---|
| TAP counter format | ran `node --test`, looked |
| turbo's line prefix | ran `turbo test`, looked |
| Go methods nest inside their type | ran the parser, looked |
| Rust `impl Trait for Type` names the type first | ran the parser, looked |
| the C# grammar is called `c_sharp` | ran the parser, looked |
| a module costs ~6ms to parse | measured; it was 3.8 |
| turbo is the only prefix shape | looked at a second runner |

**Zero** were found by thinking harder. Every one surfaced the moment the real
producer was executed and its real output read.

Three other habits, all the same family:

- **A written rule was ignored.** The heredoc-backslash note exists, is in
  memory, and was violated **eight times in one day** — once inside the
  paragraph describing it, leaving a literal `0x08` in a sentence about a
  literal `0x08`.
- **Six probes passed for the wrong reason.** Only flipping them exposed it. A
  test that cannot fail is worse than no test, because it reports confidence.
- **Code was fitted to the single example that had been looked at.** Twice.

## Why "be more careful" is not the fix

Because it has been measured, and it does not work.

This is **API Knowledge Conflict** — 20.41% of hallucinations in the largest
taxonomy of the phenomenon (Zhang, Wang, Wang, Chen & Zheng,
[arXiv:2409.20550](https://arxiv.org/abs/2409.20550), 1,380 annotated snippets;
Task Requirement Conflicts 43.53%, Factual Knowledge Conflicts 31.91%, Project
Context Conflicts 24.56%).

And the obvious remedy barely moves: their own retrieval-augmented mitigation
improved Pass@1 by **0.87 to 3.05 percentage points**. Worse for the "just read
the docs" instinct:

> *"Documentation mainly helps models identify **what** APIs to use and remains
> insufficient for teaching **how** to use them correctly. Even with **oracle**
> API-document retrieval, LLMs still make recurring errors."*

So the fix is not more context, and it is not a better instruction — §5.14
already says constraint violation rises 0% to 78% across four compaction rounds.
What works is **execution**: grounding generation in execution feedback moved
pass@1 from ~70% to 89% ([RLEF, arXiv:2410.02089](https://arxiv.org/abs/2410.02089)).

Which is this project's whole thesis, pointed at a target it had never aimed at:
*a claim is not evidence until something ran*. It had been applied to the
agent's claims about its work, and never to the developer's claims about the
world.

## What shipped

`core/assumptions.py`, two rules the ledger can answer:

> **A pattern this task introduced, which never matched any output this task
> actually saw, is an assumption nobody verified.**

> **A test this task added, which passes on the tree as it was, did not test
> this change.**

Neither asks the agent anything. The runtime already watched every command and
kept what it printed, and `stress.py` already knew which tests were red on the
base commit. Both questions were answerable all along and nobody asked them.

The report says, at the end of the run:

```
unverified: '^\s*#\s*(pass|fail)\s+\d+\s*$' matched nothing this task ran.
A pattern is a claim about output; run the thing and look
```

## The forward control caught the checker

Both forward tests failed first. The patterns are written with `^` and `$` and
compiled with `re.MULTILINE` in real code; the checker matched without it, so a
pattern that *had* been confirmed was reported as unverified. That is the one
error this must never make — a check that accuses correct work is how the gate
once blocked 75% of runs.

And flipping found **two more vacuous probes**, in the module built to detect
vacuous probes. One guard did nothing and was removed; one was real but no test
reached the state it protects, so a test was written that does.

## What it does not catch, said now

- **Non-regex assumptions.** `"c_sharp"` was a plain string in a lookup table.
  This would not have caught it, and four of the seven above are of that kind.
- **A pattern confirmed in an earlier session.** The ledger is per task.
- **Running the command without reading the output.** Necessary, not sufficient
  — though it is the step that was skipped every single time here.

Half the family is now machine-checked. The other half is still a habit, and
habits decay; that is the honest state and it is written here rather than
implied to be solved.

---

## The improvement that research talked me out of

The obvious next step was placement: say it at step 7 rather than step 27. The
repo's own numbers back that - median decisive error at step 7 of 27, recovery
window one step, 82% of doomed runs keep executing - and `guidance()` exists for
exactly that reason.

Researching *how* to build it found the argument against building it.

*Accurate Failure Prediction in Agents Does Not Imply Effective Failure
Prevention* ([arXiv:2602.03338](https://arxiv.org/abs/2602.03338)) measures the
move directly. A critic with **AUROC 0.94** - detection nobody would question -
caused a **26 percentage point collapse** when allowed to intervene. It helped
only where runs were already failing, and harmed ones that were succeeding. The
authors' conclusion is that the value of such a framework is *"identifying when
not to intervene"*, and that a 50-task pilot is required first.

This repository is the population that paper says gets damaged: **80% of first
proposals are already right**, and it has already blocked 75% of runs once on an
unmeasured signal.

So the feature was built as a **pull**: reachable from `ep_status` at any step,
reported at the stop, and injected nowhere. The blast radius agreed
independently - `core/hook.py` imports fourteen modules and every event passes
through it, while `ep_status` imports one. The riskiest placement was also the
largest.

A test keeps it that way: `test_nothing_is_ever_injected_into_the_loop` reads
`core/hook.py` and fails if either check appears there. §5.12 - detection and
intervention are separately justified - enforced rather than remembered.

**This is the first time in this session that research changed a decision from
"build it" to "do not build it yet".** Every other search confirmed a direction
already chosen. Worth recording, because the value of looking first is not only
that it makes the build better; sometimes it cancels the build.

---

## What it cost, and three defects found while paying

Asked plainly whether the check would *hurt*. It would, twice, and both harms
were created by the fix rather than found in the code it checks.

**It widened what sits on disk.** To ask "did anything you ran look like this",
the ledger began keeping 12 commands x 8KB of output where it had kept three
lines. And the real exposure predated that: `.elevenpowers/ledger.json` already
held the prompt, every command string and a tail of every output, *this*
repository gitignores the directory, and **a user's repository does not**. A
`git add -A` would have committed the lot.

The fix is not a line in a README. The state directory ignores itself - a
`.gitignore` containing `*`, written on every save, which needs no edit to a
file the user owns. On a fresh `git init` that has never heard of the plugin,
`git status` is empty with it and `?? .elevenpowers/` without it.

Redaction is the defence in depth, and the design decision worth recording is
the one that was *refused*: **not entropy**. High entropy is the property of a
git sha, a UUID, a content hash and a long identifier - which is what this
project's output is made of - so an entropy threshold would eat the very text
the check needs. Prefixes instead, from two sources that agree. Measured by
scrubbing 27,700 characters of eight real producers' output: **zero characters
changed**, and **zero** of fifteen documented example credentials survived.

**It assumed every pattern describes command output.** It does not.
`^[^@]+@[^@]+\.[a-z]{2,}$` is a claim about an email address, and no command
will ever print something that matches it. On a scraper or a client library,
that is most of the regexes in the repository, reported every run - which is how
a feature becomes noise and then becomes ignored. Now a pattern is reported only
when its own file's new code names a tool the task actually ran.

### The three defects, all found by running it

| defect | found by |
|---|---|
| a quoted JSON key walked straight past the redactor | scrubbing a real `"refresh_token": "1//0e..."` |
| the tool name was invisible behind its own regex escape | the forward test, first run |
| every pattern in every **new** file was exempt | the flip control on an unrelated test |

The second is the one worth reading twice. `core/parsers.py` names node as
`r"\bnode\s+--test\b"`, so the character before `node` is the `b` of `\b` - and
a word-boundary lookbehind therefore says the file does not mention node. The
narrowing went silent on **the single file the entire feature was built for**,
and the only reason that was noticed within a minute is that a forward control
existed and was watched.

The third came free. `git diff <base> -- <path>` reports nothing at all for an
untracked file, so patterns in files a task *creates* were never checked -
including `core/redact.py`, added in this same change. Nobody was looking for
that; a probe written to prove a *different* test was not vacuous failed, and
the reason it failed was this.

Which is the entry's own thesis arriving a third time, uninvited: **three more
defects, three more found by execution, none by thinking harder.** Including one
inside the module written to punish exactly that habit.

### Then it was pointed at its own diff

The cheapest test of a noise complaint is to run the check on the change that
fixes it. Eighteen patterns came back; eleven were real and **seven were source
code** — `def secret_santa(names):`, `self.token_count = len(tokens)`, test
fixtures holding code. Code is made of brackets and parentheses, so "two or more
metacharacters" reads it as a claim about a tool's output. A literal must now
also carry a construct only a regex has, and that rule was measured against all
67 pattern literals `core/` compiles before being adopted: **none lost, all
seven dropped.**

The same run showed the tool names were too generous — every token was taken, so
`git status` vouched for anything containing "status". First real token now. Ten
runner shapes went through it before the table was written, and **two were
wrong**: `go test` returned nothing because a two-letter name fell below the
length floor, and `bundle exec rspec` returned `bundle`.

Five defects now, in a day's work on a module about not writing things from
memory, every one found the same way. The tally is the argument.

### And then the probes were made to flip

Three of the tests above were written *after* their fix, so none of them had
ever been seen to fail — which is precisely the vacuous probe this module
computes for everybody else. So each fix was broken in turn and its guard
re-run: the strong-construct rule, the escape blanking, the first-token rule,
the scrub on the way into the ledger, the self-ignoring directory, and the quote
before the separator. **Six broken, six red, green again on restore.**

Writing the check and then exempting its own tests from the rule it enforces
would have been the funniest possible way to ship this.

### The sixth defect arrived from outside

The push was **refused by GitHub's push protection**, which named the Slack and
Stripe lines in `tests/test_redact.py`. The values are invented, but they are in
shapes real enough that a production scanner reads them as live.

Two things follow, and the second is the one that matters. The table of prefixes
was confirmed by a scanner that has never heard of this project — better
evidence than re-reading it, and free. And the block was **not** bypassed
through the allow-this-secret link: a fixture shaped exactly like a credential
is one that every tool downstream keeps treating as a credential, so the
fixtures are now assembled from a prefix and a body at import time and no
complete token literal sits in the file.

A commit whose subject is *git would have committed the lot* being stopped by
git for carrying something that looked like a secret is the kind of symmetry
this project keeps running into by accident.
