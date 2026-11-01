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

**Size and cost, stated before starting.** About 110 calls:
- up to 33 W, 11 C and 11 U seeds, in two arms each;
- a full-size qualification call (the largest seed, 44.5K characters) took
  11.7 s and cost $0.103, and smaller prompts cost less;
- so the expected total is under $11, and about 10 minutes at four calls at
  a time.
