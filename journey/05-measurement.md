# 5. Measuring the gate

## Why this measurement and not another

A gate that blocks work which was actually finished is worse than no gate,
because it teaches people to switch it off. So the gate is a classifier and was
measured as one:

| | Work actually incomplete | Work actually complete |
|---|---|---|
| Gate blocked | true block | **false block** |
| Gate passed | **miss** | true pass |

False-block rate decides whether anyone keeps the tool installed. Miss rate is
what the tool exists to reduce. Target for the first: under 5 percent.

Thirty scenarios were written with ground-truth labels, deliberately including
cases the design looked weak against: unusual toolchains, projects with no tests,
repositories that are already red, an agent stopping to ask a question. Each
scenario is a repository, a request, a sequence of actions, and a label.

## The first number: 75 percent

```
scenarios          30  (20 complete, 10 incomplete)
false-block rate   75%  (15/20)   target <5%
miss rate           0%  (0/10)
```

Fifteen of twenty completed tasks were blocked. This tool would have been
uninstalled within an hour of release.

The zero miss rate was not reassurance. A gate that blocks nearly everything
naturally misses nothing.

## What was actually wrong

The failures were structural, not incidental.

**Risk scoring was absurd.** Any file whose name contained "auth" scored highest
risk, so a toy project with an `auth.py` demanded reproduction and repeated-run
stability for every change. Fix: match directory components rather than
filename substrings, and only let filename hints raise risk when the request text
is also sensitive.

**Expensive obligations had no trigger.** Repeated-run stability was demanded of
every high-risk bug fix. It is only meaningful for nondeterministic bugs. Fix:
trigger it on the request describing intermittency, not on a tier.

**Whole toolchains produced nothing.** Ruby, Java, .NET, Elixir and PHP had no
parser, and neither did `npm test`, `make test` or `tox`. A stack that produces
no evidence can never discharge an obligation, so every task on it is blocked
forever. Fix: wrappers where only the exit code is recoverable, five more
runners, and recognition by output shape so a project's own runner script works.

**Obligations were demanded that the project could not meet.** A repository with
no test suite was asked for suite evidence. Fix: a surface scan reporting what
the project can prove, with obligations filtered to that, and the scan corrected
by evidence actually seen.

**Repositories that are already red were unusable.** Any failing test read as
contradiction, even one failing before the task began. Fix: an identity failing
on its first observation is pre-existing and cannot contradict. This mirrors how
linters are applied to agent edits, counting only newly introduced errors.

**Asking a question was punished.** The gate fires whenever the agent finishes
responding, including when it stops to ask which of two flows is meant. Blocking
that forces the agent to guess. Fix: read the final message; a question is not a
completion claim.

**Abstention was impossible.** An agent reporting a genuine blocker was blocked
for not having completed the work. Fix: a stated blocker converts the task to
`cannot_complete`, whose obligation is the reason itself.

## The path down

| After | False block | Miss | What changed |
|---|---|---|---|
| first run | 75% | 0% | |
| risk and surface | 30% | 20% | Narrower risk, obligations filtered by capability, wrappers and five runners |
| broad and scoped split | 20% | 10% | One test file no longer proves the suite; a red-to-green transition counts as a covering test |
| pre-existing tolerance | 15% | 10% | Already-red suites judged on introducing no new failures |
| message reading | 10% | 10% | Questions and abstentions handled |
| runtime evidence | 0% | 10% | Plain program runs recorded for projects with no tests |
| coverage warning | 0% | 0% | Unrelated-test warning, and risk informed by the request |

## The held-out set, and why the zero was a lie

Those thirty scenarios were the ones the fixes were tuned against, so scoring
zero on them means very little. Twelve more were written afterwards, choosing
cases the design looked weakest against: workspace-filtered commands, a Maven
project, a project-specific test runner, a formatter rewriting files with
identical content, fabricated evidence via `echo`, a failing test deleted rather
than fixed.

```
=== HELD OUT ===
false-block rate   43%  (3/7)
miss rate           0%  (0/5)
```

Three quarters of the apparent success was overfitting. Two of the three were
genuine bugs:

- `pnpm --filter api test` did not match the wrapper pattern, because the flags
  sit between the tool and the word "test".
- `python run_tests.py` was recorded as a program run rather than a test run.
  Fixed by classifying on output shape rather than command name, which is more
  robust anyway: a project's own runner is a test run whatever it is called.

The third was a deliberate trade-off, and it produced the best fix of the day.

## The formatter problem, and the fix that came from it

Evidence is bound to a signature over the files it observed. Content hashing was
measured at about 6 seconds on an 8,000 file repository, paid on every test run,
which would make the tool unusable on real codebases. Switching to size and
modification time brought that to 383 milliseconds, a 16x improvement.

The cost: a formatter rewriting a file with identical bytes changes its
modification time, so evidence reads as stale and the agent is asked to re-run
for no reason.

Several fixes were considered and rejected: content-hashing with a file-count
cap (still too slow on real repositories), comparing sizes only (a same-size
content change would be missed, which is a miss risk and unacceptable in a
verification tool), storing per-file maps (megabytes per record).

The answer was already in the repository. Git compares content, using timestamps
only as a cache. If `git status --porcelain` and HEAD are unchanged between two
moments, no file content changed. So freshness became: timestamps match, or
version control says nothing changed. Fast in the common case, correct in the
awkward one, and it falls back to timestamps outside a repository.

Cost: about 70 milliseconds added to the hook that fires after a shell command.
The hot path, the check before every edit, is unchanged at about 102
milliseconds.

## Where it stands

```
=== TUNING SET ===   false block 0% (0/20)   miss 0% (0/10)
=== HELD OUT ===     false block 0% (0/7)    miss 0% (0/5)
=== COMBINED ===     false block 0% (0/27)   miss 0% (0/15)
```

Latency, measured on this repository:

| Hook | Best | Fires |
|---|---|---|
| PreToolUse | 102 ms | before every edit and command |
| PostToolUse | 192 ms | after every command |
| Stop | 178 ms | when the agent finishes |

Signature cost by repository size: 9 ms at 200 files, 86 ms at 2,000, 383 ms at
8,000.

## What this does not prove

Stated plainly, because the number is easy to over-read.

- **Forty-two scenarios, all written by one person.** Real agent behaviour is
  more varied and stranger than anything imagined here.
- **The held-out set is weakly held out.** It was written by someone who knew
  the design. Genuinely independent tasks would be harder.
- **No real agent has been run through this at scale.** The scenarios replay
  command output; they do not exercise an agent's actual choices.
- **Coarse invalidation is untested in anger.** Any source edit stales
  everything. Whether that is tolerable in daily use is P4 and unmeasured.
- **One known gap survives by choice.** A test that does not cover the change can
  satisfy the covering-test obligation. Deciding that properly needs a
  test-to-source map. Guessing from names would block correct work whenever a
  test is named differently from the code it exercises, so it is reported as an
  advisory note instead. A missed warning costs less than a false block.

The honest summary: the gate now behaves sensibly on 46 constructed cases and no
longer fails in the structural ways it did at the start. Whether it survives real
use is the next measurement, not this one.

## Postscript, written after phase 9

The list of limits above missed the one that mattered most, and it is worth
stating plainly rather than quietly correcting.

Every scenario in this suite is a piece of work. Real sessions are mostly
conversation: questions, pasted context, "continue", statements of fact. So a 0
percent false-block rate here was compatible with attaching obligations to 51
percent of real turns that changed nothing, which
[09-claims.md](09-claims.md) measured on 3,557 turns from real sessions.

Both numbers were correct. They describe different populations, and the one this
file describes was constructed by the person whose code it grades. That is a
sharper version of the held-out lesson: writing fresh cases guards against
overfitting to the cases, and does nothing about overfitting to the *kind* of
case you think to write.
