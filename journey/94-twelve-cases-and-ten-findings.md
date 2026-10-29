# 94 — twelve cases and ten findings

After the v3 pilot came back a go, the remaining ten cases were written the
same way as the first two. Ten fresh authors worked in parallel from the same
brief and prompt, told nothing about ElevenPowers, each in its own domain. All
ten rehearsed usable on their first report, and each was re-rehearsed here
independently before it was committed.

## Reviews still found correct work graded wrong

One fresh reviewer per case found ten blocking problems, in five shapes. None
of them was visible to the rehearsal: it proves the reference passes and that
broken variants fail, so it cannot see a correct alternative the oracle refuses.

- **A fact whose old value named a unit or a vocabulary.** Examples: occupancy
  as `percent`, the bookings order as `booking reference` when the old value
  named columns. An agent's equally accurate wording would have been stale.
  The fix, as for parcelpost: make the row a format example stated in the
  request, such as `0.4` becoming `40.0`, or one marked literal.
- **A fact an agent could accurately change although the reference kept it.**
  A field list that a reasonable design extends (`workorders.json`), or a rule
  whose meaning shifted (`duplicate rule`). These are now never graded.
- **A version the request did not pin.** Bumping a file version is the standard
  way to keep old files opening, so the request now says the version stays 1,
  and the old-file check writes a real old file.
- **A check only one of two reasonable designs passes:**
  - a fractional setting the request never allowed;
  - an id allocator that a correct prune could reset;
  - a waived fee recorded as a zero charge;
  - a sort located in one particular helper;
  - markdown tables required to have outer pipes.
- **A "quiet dependent" that was the requested site itself.** A layout table
  every report reads was declared as a dependent. Leaving it behind failed the
  stage's own feature, so it measured nothing. It was replaced by a genuine
  consumer that reads the rows by position.

Two contrivances were also fixed: a module importing from the very module
whose rule it re-implemented, and a reference that weakened an exact public
test so the quiet check would pass.

## What stayed, disclosed

55 of 68 quiet dependents can be reached by searching for the request's own
words, nearly always through an ordinary docstring or docs sentence. They
stay: stripping natural prose would be hiding. The v3 pilot's two genuine
misses came from one such weak dependent and one strong one, so weak does not
mean free. The name check reads changed docstring lines word by word, and two
authors kept old docstring wording to satisfy it. That is recorded as a check
weakness, not changed mid-build.

## Frozen

- **Rehearsal:** all twelve rehearse usable from a fresh CRLF clone.
- **Manifest:** frozen at `8c3d7b1` with 1,220 case files. The two pilot cases
  are byte-identical to their pilot freeze.
- **Published:** the `v3/` folder of the public cases repository, checked file
  by file against the manifest.
- **Full run:** proposed at five replicates (120 conversations, about $123,
  power 0.88 at the pilot rate), and it waits for the user's go.
