# 91 — a fair test is built before it is run

The field report said two things no single-fix sweep can see: with ElevenPowers
the docs stayed current, and a fix stopped breaking the code that depended on
what it changed. The 2026-10-17 multi-stage comparison had already tied. Its
own verdict was that "there was no observed ordinary regression for the
assisted workflow to prevent". So v2 had to be built where something can go
wrong, and checked to be fair before a cent was spent. This entry is that build.
No model has run.

## What was built

- **Case format:** a start tree, one reference diff per stage, a
  "dependent missed" diff for every cross-cutting stage, hidden groups and a
  table of documented facts per stage.
- **Oracles:** earlier behaviour lost, stale facts, and rules kept.
- **Rehearsal:** proves each case catches the three mistakes it exists to
  catch. Those are a missed dependent, forgotten docs, and doing nothing.
- **Power simulation.**
- **Twelve cases,** written by twelve fresh agents who were told nothing about
  ElevenPowers.

## Five things found on the way, none by reading

- **One unimportable group ended the session for all of them.** pytest stops
  collecting at the first import error unless told otherwise, so the other
  groups were silently never run. This was seen in a real pytest run before the
  parser was written.
- **Eight cases cannot win.** With the exact signed-rank test at 0.025, six
  non-tied cases have a minimum p of 0.031. The design's eight cases would need
  seven to differ. So twelve were written.
- **A CRLF checkout breaks every case.** `core.autocrlf` turned the start trees
  into CRLF, and the stage diffs stopped applying. `.gitattributes` now keeps
  case files byte-exact, and this was watched flipping on a clone of the commit
  before.
- **Ten of twelve cases graded wording, not documentation.** Two independent
  reviewers each found facts with invented keys and free-text values, such as
  `heading_id`, "read once" and "most specific first". A careful agent would
  have been scored as forgetting the docs for choosing other words. They also
  found six places where a correct alternative would fail: an unnamed keyword,
  one reading of a request, an unstated lint rule. The brief gained fairness
  rules. A graded fact's key is an existing row or a name the request uses, its
  value is stated in the request, and a group requires only what is stated.
  Every case was rewritten against them, and a second round cleared all twelve.
- **The final code review found three grading defects:**
  - equal means of thirds that differ in the last bit and so broke a tie in the
    frozen test;
  - a candidate printing past the runner's 8 MiB cap, which crashed grading
    instead of being graded;
  - a stale docs row left beside the new one, which passed when it came last.

  Each fix was watched failing first. The first version of the output test
  passed before the fix, because 3 MB is under the cap, and was enlarged until
  it failed.

## Published

The twelve projects are public at
<https://github.com/SatyamSingh-Git/elevenpowers-multistage-cases>, with the
manifest that lets anyone check every file against the frozen commit. A fresh
clone matched all 607 case files.

## What it still cannot say

Nothing about either arm yet. The cases were built to contain dependents and
documented facts, because that is what the claims are about. A result will
show whether the effect appears where it should, not how often such work
occurs. Seven minor review findings are deferred and listed in the plan's
ledger.

*Reproduce: `python -m eval.multistage_rehearse --cases eval/multistage_cases
--out <file>` and `python -m eval.multistage_power`.*
