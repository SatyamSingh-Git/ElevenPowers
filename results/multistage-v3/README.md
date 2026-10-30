# Multi-stage v3: twelve cases frozen; the full run is running

The pilot was a go, all twelve cases are frozen at `8c3d7b1`, and the full run
started on 2026-10-30 ([below](#the-full-run-started-2026-10-30)).

v3 replaces v2's cases after the v2 pilot found nothing to prevent
([journey 92](../../journey/92-the-pilot-found-nothing-to-prevent.md)). Its
projects are bigger, eight requests long, and every request that changes
shared code has a declared **quiet dependent**: code a search for the changed
names does not find and the project's own tests do not catch. The rehearsal
proves that mechanically
([design](../../docs/superpowers/specs/2026-10-28-multistage-v3-harder-cases-design.md),
[journey 93](../../journey/93-a-dependent-the-search-does-not-find.md)).

## Pilot, 2026-10-28

Four sealed conversations on `gradebook` and `parcelpost`, frozen at `ecee720`
([`pilot-manifest.json`](pilot-manifest.json), [`pilot-protocol.json`](pilot-protocol.json)).
After the pilot, a final code review fixed three checks, and [`manifest.json`](manifest.json)
is refrozen with the cases byte-identical:
- format specs in documented values are graded;
- f-strings read the same on every Python version;
- a quiet diff may touch only its declared file.

The pilot regrades identically under the fixed checks.
Superpowers 7.0.0 was in both arms, with Sonnet 5.5 at medium. All 32 stages
completed and qualified, for $4.09.

| | lost earlier groups | stale facts | cost | model time |
|---|---|---|---|---|
| superpowers, `gradebook` | 1 (stage 4) | 0 | $0.98 | 230 s |
| superpowers, `parcelpost` | 2 (stage 5) | 0 | $0.84 | 291 s |
| + ElevenPowers, `gradebook` | 1 (stage 4, the same miss) | 0 | $0.94 | 367 s |
| + ElevenPowers, `parcelpost` | 0 | 0 | $1.33 | 398 s |

A blind classifier saw only the request, the stage diff, the project before
the stage and the failing check, and was not told the arm. It called both
superpowers-arm misses genuine ([`pilot-classified.json`](pilot-classified.json)):
- **gradebook:** raising the default precision left the grades export at one
  decimal place. The posted percent stopped matching the course grade the docs
  promise.
- **parcelpost:** putting the manifest in booking order broke billing, which
  grouped adjacent rows by account. Each account got two invoices with the same
  number, and the second file overwrote the first.

**The gate is met, in substance and not just mechanically.** Every changelog,
protected file and bug-fix test was kept in both arms, and no docs fact went
stale. The docs claim still shows no headroom on these cases.

**What this pilot does not show:**
- **No comparison between arms.** Pilot runs are excluded by design, and two
  cases at one replicate cannot separate the arms. On these four conversations,
  ElevenPowers made the same gradebook miss and avoided the parcelpost one.
  That is a description, not a result.
- **Statistical power.** At the pilot's rate of 1.5 lost groups per
  superpowers-only conversation, twelve cases at three replicates give only
  0.64–0.67 power at ratio 0.5 ([`power.json`](power.json), computed after
  the pilot; an estimate from v2's table had said 0.45–0.6). The full-run
  proposal below therefore adds replicates.

## How the two pilot cases were checked

- **Rehearsal:** both cases rehearse usable from a fresh CRLF clone
  ([`rehearsal.json`](rehearsal.json)). Every quiet dependent fails exactly its
  groups, keeps the public suite green, and names nothing the stage changed.
- **Review:** one independent reviewer per case ([`review.json`](review.json)).
  - `gradebook` had no blocking findings.
  - `parcelpost` had two docs facts whose value was a wording choice. The author
    fixed them, and the case was rehearsed again.
  - 10 of 11 quiet dependents can be reached by searching the request's own
    words, through ordinary comments and docs prose. They were kept: making them
    quieter would mean hiding things, which the design forbids. The gradebook
    miss came from the one dependent its reviewer rated hard to find. The
    parcelpost miss came from one rated only mildly weak: a search for "manifest"
    reaches it among 11 files.
- **Agent's instructions:** the user's own `~/.claude/CLAUDE.md` is excluded, and
  the Skill tool is allowed in both arms.

## Twelve cases, frozen

Ten more fresh authors wrote the remaining cases from the same brief, with
domains: clinic booking, recipes, library loans, fleet maintenance, payroll,
theatre tickets, greenhouse monitoring, surveys, household budgets and a
hotel desk. The two pilot cases are unchanged.
- **Review:** each case had one fresh reviewer. Their 10 blocking findings,
  all correct work that would have been graded wrong, went back to the authors
  and were fixed. Typical ones:
  - a fact whose old value named a unit;
  - a field list an agent could accurately extend;
  - a check that only one of two reasonable designs passes.
- **Disclosed:** 55 of 68 quiet dependents can be reached by searching the
  request's own words ([`review.json`](review.json)).
- **Rehearsal:** all twelve rehearse usable from a fresh CRLF clone
  ([`rehearsal.json`](rehearsal.json)).
- **Freeze:** [`manifest.json`](manifest.json) was taken at `8c3d7b1`, with
  1,220 case files. [`pilot-manifest.json`](pilot-manifest.json) keeps the
  pilot's freeze.
- **Published:** the cases are in the `v3/` folder of
  <https://github.com/SatyamSingh-Git/elevenpowers-multistage-cases>.

## The full run, started 2026-10-30

The user said go on five replicates. 120 slots were sealed in
`E:/ep-runs/multistage-v3-full-2026-10-30` (outside the repository), run four
at a time and never retried. The first stage of all four lanes qualified:
superpowers loaded in both arms, ElevenPowers' marker only in its own, and no
closed-book breaches. A one-turn probe first confirmed authentication and
Sonnet 5.5 on `claude` 2.1.292, for $0.15.

Before sealing, two frozen modules (`eval/multistage_quiet.py`,
`eval/multistage_run.py`) hashed differently from [`manifest.json`](manifest.json).
The cause was newline conversion: `core.autocrlf` is true on this machine and
the working copies had been rewritten with CRLF after the freeze hashed them.
All ten frozen modules equal the blobs at `8c3d7b1` byte for byte, and equal
the working copies once CRLF is read as LF. The run uses the frozen code.

### As proposed

[`power.json`](power.json) covers twelve cases at the pilot rate of 1.5 lost
groups per superpowers-only conversation, ratio 0.5. With no effect, the test
rejects falsely 1.5–2.3% of the time.

| layout | conversations | power | estimated cost | wall time, four at a time |
|---|---|---|---|---|
| 12 × 2 arms × 4 replicates | 96 | 0.78–0.79 | about $98 | about 2.5–3 h |
| 12 × 2 arms × 5 replicates | 120 | 0.88 | about $123 | about 3–3.5 h |

The cost rests on the pilot's $0.91 per conversation without ElevenPowers and
$1.14 with it, at about 5.4 minutes of model time each. The frozen layout rule
takes the largest affordable layout with power of at least 0.8, which is five
replicates.
