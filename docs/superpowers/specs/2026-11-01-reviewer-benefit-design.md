# Does the report help a reviewer? (PLAN §13 A.3)

*2026-11-01. The user asked to proceed without a round of questions; every
decision here not quoted from PLAN is marked **my call**.*

## The question

PLAN §12 names the falsifier: *a reviewer does not act on a list of unpinned
lines.* If a reviewer given `ep_review`'s report catches no more seeded
defects than one given the diff alone, then the reporting direction fails, not
just one feature. That is the claim to test, and it gets tested before
anything else is built on the report.

## Seeds: real agent changes, with known defects ($0)

The changes are the kept v3 snapshots: 12 projects, real Sonnet 5.5 changes,
one stage at a time. Each seed is a commit pair, base = snapshot *n−1* and
head = a version of snapshot *n*. There are three kinds:

| kind | head | what a good reviewer does |
|---|---|---|
| **C**, control | snapshot *n* as the agent left it, PINNED | accepts |
| **U**, unpinned | snapshot *n* with the stage's test changes taken back out; the adversarial control showed this flips to NOT PINNED (24 of 24) | asks for a test |
| **W**, wrong | snapshot *n* with one mutation on a changed line that the stage's own tests do **not** detect but the case's behaviour oracle **does** | names the wrong line or behaviour |

W seeds are what matters most: real, behaviour-changing defects that the
project's tests miss. They come from the shipping Cosmic Ray adapter
(`core.strength.engines.cosmic`) on the stage's changed regions. A candidate
becomes a seed only if two things hold:
1. the stage's test command still passes (undetected);
2. at least one oracle group that passed on snapshot *n* now fails
   (`eval.multistage_oracles.groups`).

The second condition excludes equivalent mutants by construction (**my call**).

**$0 gate before any model call.** Run `ep_review --strength` on every seed:
- On U seeds the report must say NOT PINNED.
- On W seeds the seeded line must appear among the unpinned lines.

If the report itself does not surface the W seeds, a reviewer cannot benefit
from it, and the paid phase is not run. The rate is reported either way.

## Reviewers (paid, after the gate)

**Reviewer:** Claude Sonnet 5.5 at medium effort, through the subscription
launcher (`eval/subscription.py`), under the standing authorization. A model
reviewer stands in for a person, and the result is bounded to it (**my
call**; no human reviewers are available).

**What the reviewer sees.** One prompt, no tools:
- the stage's request;
- the diff;
- arm B only: the `ep_review` report.

**What it answers.** A fixed JSON answer:
- `decision`: `accept` or `request_changes`;
- `problems`, each with `file`, `line`, `kind` and a description. `kind` is
  one of `missing_test`, `wrong_behaviour` or `other`.

**Arms and pairing.**
- **A:** diff only. **B:** diff plus report. Each seed is reviewed once in
  each arm, in alternating order, sealed and never retried, as in v3.
- The paired seed is the unit.

**Grading** is automatic and fixed in advance:
- **W caught:** a problem names the seeded file, at a line within 2 of the
  seeded line.
- **U caught:** `request_changes` with a `missing_test` problem.
- **C false alarm:** `request_changes`.
- The raw answers are kept for a blind re-read.

**Primary outcome:** W caught, arm B against arm A. The test is an exact
McNemar test on the discordant pairs.

**Secondary outcomes:**
- U caught;
- the C false-alarm rate;
- output tokens and seconds per review ("sooner").

**Falsified** if arm B catches no more W seeds than arm A, or if arm B's
decisions match arm A's on the seeds where the report differs from the diff.
In either case the report was read and ignored.

## Size and cost

The number of W seeds is unknown until the $0 phase counts them. The paid run
is sized from that count with `eval.multistage_power`'s method and stated
(runs, wall time, cost) before it starts. A rough guide: 36 seeds × 2 arms =
72 calls at the held-out sweep's $0.08 per call is about $6. Prompts carrying
whole reports will cost more.

## Non-goals

- No claim about human reviewers.
- No change to `ep_review` while the paid phase runs; it is sealed like v3's
  harness.
- No seeds from projects outside the twelve v3 cases in this round.
