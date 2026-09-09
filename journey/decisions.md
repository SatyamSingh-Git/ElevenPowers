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
