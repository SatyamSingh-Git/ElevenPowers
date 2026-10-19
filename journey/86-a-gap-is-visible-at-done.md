# 86 — a gap is visible at done

Journey 85 ended with a JavaScript conversation whose task was `VERIFIED` while
both exact declared milestones sat stale for a turn. The receipts already knew
the difference. The completion report did not say it. And when the runtime
offered feedback about that gap, nothing could tell whether the host ever
returned it to the agent, let alone whether anything followed.

## Show the exact state at done

The completion report now lists each configured declaration under its newest
exact receipt: `CURRENT`, `FAILED`, `STALE`, `ABSENT` or `INCOMPLETE`. Only the
configured command for that property counts; a passing `node --test | tail -15`
leaves the declaration `ABSENT` even though the task is verified. The section
changes no verdict and runs nothing.

Its first version printed `INCOMPLETEtests`. The state column was ten wide and
`INCOMPLETE` is ten letters. The test asserted only the `STALE` line.

## Separate three facts

Feedback now leaves up to three observations, each a hash or bounded metadata:
the runtime meant to say it (intent), a launcher flushed it in a supported
context field under the same installation (emitted), and the same host session
later returned an exact receipt newer than that emission (follow-up). The report
calls the whole section *model consumption unproven*, because that is all it is.

The observer was borrowed from the milestone-advice one and arrived with a
single forward test. Adversarial controls followed: replay, other
fields, truncated text, nested-too-deep responses, a removed, reconfigured or
reinstalled integration, failed, incomplete and earlier receipts, malformed notes.
Watching each guard flip took eighteen mutations. Two of them first survived.
Reinstallation changes only the generation, which no control exercised. And
the privacy assertion could not fail: feedback contains newlines, the stored
JSON escapes them, and `text not in stored` was true of any file. A malformed
intent note also crashed the whole completion report.

## The recommended path was invisible

Then the real launcher ran. A JavaScript project took the generic pass, the
feedback was emitted, the owned runner made `tests` current — and the follow-up
said `unobserved`. Owned output is deliberately never parsed by the host
callback, so the receipt the feedback asks for was the one receipt no callback
could link. Every unit control had passed, because each one built its exact
receipt by parsing a direct command.

The runner already bound a random attempt digest to its receipts. It now prints
it, and a host callback for an owned envelope links only ledger receipts that
carry a printed attempt. Output still creates no evidence. An attempt echoed
from before the emission links an old receipt, so a follow-up also requires the
receipt itself to postdate the emission. The same links reach the milestone
observer.

## What ran

`python -m eval.declared_closure` drives actual pytest and `node --test`
projects through all five adapters, replay and native: 20 of 20 cases record
`ABSENT → ABSENT → CURRENT → STALE → FAILED → INCOMPLETE`, emitted follow-ups
`current / failed / incomplete` natively and no emission under replay. The
Python acceptance fixture from earlier work could not be reused: it is a bespoke
TAP script, which the generic predicate does not claim, so it never produces
feedback. That limit is general and stays.

No model was run. The open question is unchanged and now measurable: in an
installed session, does the agent take the owned path after the feedback
arrives?
