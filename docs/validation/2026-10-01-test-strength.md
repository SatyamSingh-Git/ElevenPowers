# Changed-file test-strength delivery — 2026-10-01

Scope: generalized, optional, report-only mutation observations for any repository.
The branch starts at portable report `523d6a9`; the user requested 25 meaningful
pushes during implementation. Earlier onboarding/report publications are separate.

## Observed checks

- Final local suite after independent-review fixes: **1,127 passed, 28 skipped in
  413.70 seconds**, native Windows / Python 3.13.2. Log:
  `.venv/strength-final-full.log` (ignored local artifact).
- Before review corrections: 1,123 passed, 28 skipped in 443.26 seconds. A green
  suite did not replace review: three later reproduced defects were corrected.
- Actual engine acceptance on unrelated Python, JavaScript and TypeScript project
  fixtures: weak tests leave changes undetected; boundary assertions detect them;
  original source bytes remain identical. All three controls passed in 21.63 seconds
  before review; all seven language/review controls passed in 26.42 seconds after
  the correction. TypeScript executes through Node's type stripping in that fixture;
  projects with builds must supply their own command.
- Four review controls watched RED before the three fixes: null/numeric dependency
  configuration, marker/secondary-file contamination, and actual `.pth` import
  redirection using a disposable interpreter. GREEN after validation-before-conversion,
  clean trials and original-source Python import/read diagnostics.
- Focused integration before final review: 82 strength/report/hook controls passed.
- `python -m eval.validate`: all four grader cases correct.
- `ep_doctor.py --host`: local replay prompt/pass/fail/report/blocking join passed;
  replay is not native installed-host acceptance.
- `python -S`: runtime/export imports pass without site packages.
- `architecture/check.py --render`: **92 nodes / 200 edges / 7 planes**, all four
  tabs draw after adding the import guard. An overlong workflow caption initially
  failed the check and was shortened before publication.
- CLI help, guide links and final diff whitespace checked. The pinned optional
  producers are included in the Windows/Linux, Python 3.11/3.13 CI matrix. This
  record's count is local; final main publication triggers independent hosted CI.

## Boundaries

The first release selects whole changed production files, not an exhaustive diff
or semantic-equivalence analysis. Attempts, source/copy bytes and elapsed time are
bounded. Missing engines, unknown base, pre-existing dirty attribution, failed or
empty baselines, linked/nested inputs, source changes and partial execution are
explicit. Baseline and each mutation get fresh inputs, not a source-only reset.
Python startup/path overrides that disable the diagnostic remain unsupported.
The copy is not an OS sandbox; trusted test commands may affect external services.

Only completed exact samples are reused. Saved records contain bounded metadata,
not mutated source or captured outputs. Human reports check input freshness and
do not execute analysis. Findings do not alter completion verdicts or enter agent
feedback as individual targets. Controlled fixture success is not improved patch
outcomes, independent semantic review of every survivor, or native readiness in
the four added hosts. Snag CI was not rerun or bypassed for this delivery.

## Incremental publication

Each numbered part is a separate actual push on `codex/test-strength`. Main is
advanced atomically with the complete final feature at part 25; no force push or
remote history rewrite is used. Parts 1–20 were already pushed before final review.

| Part | Commit | Published change |
|---|---|---|
| 1 | ff46245 | Approved design and plan |
| 2 | 8554c8d | Observation contract |
| 3 | edeb014 | Optional project settings |
| 4 | 957ad02 | Changed production scope |
| 5 | 5f497bb | Bounded copy inputs |
| 6 | a2ce8ff | Private snapshot lifecycle |
| 7 | 89c23f3 | Shared contained execution budgets |
| 8 | 01cb1ad | Passing isolated baseline |
| 9 | 3816e1b | Atomic bounded metadata |
| 10 | d648c16 | Cosmic Ray producer and provenance |
| 11 | 7d8b523 | Qualified mutation execution |
| 12 | 1d104de | Stryker JS/TS producer |
| 13 | 7960a86 | Actual Node weak/strong execution controls |
| 14 | 8b6ee33 | Generalized orchestration |
| 15 | 00ded54 | Exact-input reuse |
| 16 | ee52885 | Explicit CLI |
| 17 | a4f2e22 | Silent shared completion integration |
| 18 | 19988f6 | Human report section |
| 19 | 58d68bb | State validation and task ownership |
| 20 | 8961d2d | Three-language acceptance and CI producers |
| 21 | 59c6fc8 | Three independently reviewed isolation/configuration fixes |
| 22 | 95e18d1 | Rendered architecture and workflows |
| 23 | 5c82ad2 | All six guides |
| 24 | This record's commit | Status, roadmap, development, journey and validation |
| 25 | Final README/release commit | Completed feature and atomic main publication |

Final publication identifiers are available in Git history by their `(24/25)` and
`(25/25)` subjects; this avoids inventing a self-referential commit hash.

## Review decisions

All three Important findings were fixed in one RED→GREEN pass, followed by the
green full suite. No minor findings were deferred. The reviewer's set-aside areas
were explicitly judged:

- Documentation and final 25-part/main publication remain parent delivery work,
  completed after code review; omitting them would leave an incomplete release.
- Trusted-command filesystem isolation stands; malicious escape, external writes
  and database/network effects require a separate sandbox design. Cost: external
  side effects are not contained by this feature.
- Equivalent mutants, every-file coverage and exhaustive exploration remain
  qualified observations. Cost: survivors can be irrelevant and samples incomplete.
- Argument-requiring Cosmic operators and Stryker runner/coverage/dashboard/cache
  facilities remain omitted. Cost: fewer operators and additional copy/test work.
- No automatic engine download, unpinned engine compatibility or unsafe dependency
  aliasing. Cost: explicit setup, version pins and incomplete results for some trees.
- Unknown runner output remains incomplete. Cost: custom projects may need supported
  positive-count output or a focused command.
- The reviewer did not establish independent Linux, permission/junction or signal
  behavior. Hosted CI is the execution boundary; fixture success on Windows alone
  cannot justify those claims.
- Upstream engine internals/licensing and pre-existing parser/journal/redaction/
  containment behavior were not independently audited. Cost: their documented
  limits remain; provenance, existing controls and final regression still apply.
- The existing clean feature checkout was reused instead of creating another
  worktree. Cost: branch isolation is weaker than checkout isolation.
- Shared contained execution was chosen over engine-native runners, and named
  test failures were accepted when count summaries were absent. Cost: no upstream
  runner optimizations; outcome quality remains bounded by supported parsers.
