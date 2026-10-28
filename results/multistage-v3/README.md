# Multi-stage v3: pilot is a go

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
([`manifest.json`](manifest.json), [`pilot-protocol.json`](pilot-protocol.json)).
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
  superpowers-only conversation, twelve cases give roughly 0.45–0.6 power at
  ratio 0.5 ([power table](../multistage/power.json): 0.44–0.48 at rate 1 and
  0.78–0.80 at rate 2, three replicates). The full-run proposal must either add
  replicates or say it is descriptive, as the frozen layout rule requires.

## How the cases were checked

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

## Next

Under the design, ten more fresh authors write the remaining cases from the same
[brief](../../eval/multistage_v3/AUTHORING.md). The two pilot cases stay
unchanged. Then come review, rehearsal and freeze. The full run is proposed with
its measured cost and waits for the user's go.
