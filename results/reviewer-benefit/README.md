# Does ep_review's report help a reviewer? (PLAN §13 A.3)

[Design](../../docs/superpowers/specs/2026-11-01-reviewer-benefit-design.md).
PLAN §12's falsifier reads: *a reviewer does not act on a list of unpinned
lines.* This study tests it.

## Pre-registration (written 2026-11-02, before any study call)

**Seeds** come from real v3 changes: the superpowers arm, conversation 0,
pinned and resolved stages only ([`eval/reviewer_seeds.py`](../../eval/reviewer_seeds.py)).
- **W, wrong:** the change plus one Cosmic Ray mutation on a changed line.
  The stage's own tests miss it, and the case's behaviour oracle catches it.
  There are up to three W seeds per case, from different stages.
- **C, control:** the change as the agent left it. One per case, from the
  first stage that gave a W seed.
- **U, untested:** the same change with its test changes taken back out. One
  per case, from the same stage as C.

**The report** is `ep_review --strength` with a stated budget of **32
mutations in 300 seconds**. At the default budget of 8, the seeded line
surfaced in 6 of 11 first-round W seeds, and every miss hit the attempt
limit. At 32 it surfaced in 11 of 11
([8](gate-first-seeds-8-mutants.json), [32](gate-first-seeds-32-mutants.json)).
The reports are computed once at prepare, frozen and sealed. The gate below
judges exactly those frozen reports.

**The reviewer:**
- Claude Sonnet 5.5 at medium effort, on the subscription (CLI 2.1.292).
- No tools; one prompt sent on stdin; the user's own `CLAUDE.md` is excluded.
- Claude Code's own background model also appears in model usage, in both
  arms.

**What each arm reads:**
- **diff:** the stage's request and the diff;
- **report:** the same, plus the report.

**How the calls run.** Each seed is reviewed once in each arm. The seed
order is shuffled with seed 20261101, and which arm goes first alternates.
Calls are sealed and never retried, and launching stops if the quota is
spent. The runner is [`eval/reviewer_run.py`](../../eval/reviewer_run.py).

**Grading is fixed in [`eval/reviewer_study.py`](../../eval/reviewer_study.py):**
- **W caught:** a problem names the seeded file within two lines of the
  seeded line.
- **U caught:** `request_changes` with a `missing_test` problem.
- **C false alarm:** `request_changes`.
- An unreadable reply is kept, but not scored.

**Primary:** W caught, report arm against diff arm. The test is an exact
two-sided sign test on the discordant seed pairs, at α = 0.05.

**Secondary, reported beside the primary, never in its place:**
- U caught;
- C false alarms;
- cost, seconds and output tokens per arm.

**Falsified** if the report arm catches no more W seeds than the diff arm.
The report was then read and not acted on, and by §12 the reporting
direction fails, not just this feature.

**Bounds, stated now:**
- The reviewer is a model, not a person.
- W seeds are mutation-shaped. That favours the report's pointing, since it
  mutates with the same engine. So the study measures whether a reviewer
  acts on named lines, not whether ep_review finds arbitrary bugs.
- There is one call per seed per arm, on the twelve v3 projects only.

**The final seed set, recorded before any study call:**
- **21 W, 11 C and 11 U seeds, so 86 calls**
  ([`seeds.json`](seeds.json)).
- **Where the W seeds come from:** at most three per case. Three cases gave
  only one, and `parcelpost` gave none in any of its eight stages.
- **The rebuild is deterministic:** it reproduced all 33 first-round seeds
  exactly.
- **Power:** if the report arm catches 50% against 15%, the expected p is
  about 0.04. A smaller effect would likely go undetected.

**Size and cost, stated before starting.** About 110 calls:
- up to 33 W, 11 C and 11 U seeds, in two arms each;
- a full-size qualification call (the largest seed, 44.5K characters) took
  11.7 s and cost $0.103, and smaller prompts cost less;
- so the expected total is under $11, and about 10 minutes at four calls at
  a time.

## Result (2026-11-02, $5.23, 86 calls)

All 86 calls ran. 83 replies were graded and 3 were unreadable; the quota
never ran out. Every reply is kept in [`replies.json`](replies.json) and the
summary in [`summary.json`](summary.json).

| | diff alone | diff + report | report only / diff only | exact sign test |
|---|---|---|---|---|
| **W caught (primary)** | 18 of 21 | 20 of 21 | 2 / 0 | **p = 0.5** |
| U caught | 9 of 9 | 9 of 9 | 0 / 0 | 1.0 |
| C false alarm | 9 of 10 | 9 of 10 | 1 / 1 | 1.0 |

- **Cost per arm:** $2.49 diff alone, $2.74 with the report.
- **Mean seconds per call:** 9.6 against 10.0.
- **Mean output tokens:** 766 against 862.
- **Unpaired seeds:** U has 2 and C has 1, from the unreadable replies.

**As pre-registered:** the primary is **not significant**. The report arm
caught two more wrong lines and none fewer, so the falsifier's literal
condition ("no more") is not met. But no benefit is shown either.

**Exploratory, not pre-registered:**
- **Ceiling.** The reviewer with the diff alone named 18 of 21 (86%)
  mutation-shaped wrong lines, which left almost no room for the report.
- **The grading is not specific.** In the correct control from the same
  stage, the reviewer named the very spot later seeded in 2 of 9 diff-arm
  replies and in 6 of 9 report-arm replies. The report lists unpinned
  changed lines, and the seeded line is one of them, so in the report arm,
  naming the seeded spot is not evidence of finding the defect.
- **The report is acted on, not ignored.** Report-arm replies raise more
  problems (mean 4.4 against 3.1) and name the report's lines. So §12's
  "read and ignored" does not fire. What is missing is a gain.
- **The decision does not separate right from wrong.** The model reviewer
  asked for changes on 9 of 10 correct controls in both arms.
- **The unreadable replies.** All 3 came from the diff-only arm: with tools
  off, the model wrote tool calls asking to read the source instead of
  answering.

**Reading.** With seeds of this kind and a model reviewer, the report does
not measurably help find wrong lines. A wrong line in a small diff is
visible from the diff itself. The reviewer does use the report, but what it
adds is more flagged lines, on correct changes as well as wrong ones. A
test of the reporting direction needs defects the diff does not show,
or reviewers for whom reading the diff is the cost (people, large changes).
This study covers neither.
