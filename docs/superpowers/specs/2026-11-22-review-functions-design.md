# The reviewer's report names the functions no test checks

*2026-11-22. A small change, under the user's standing "decide things
yourself": every choice below is mine.*

## Why

PLAN §13 makes reviewer evidence the current focus, and `ep_review` is the
reviewer's one-minute report. Its "Lines no test noticed" section samples
line mutations (`--strength`). TestMiner answers the same reviewer question
one level up, with plain verdicts per function the change touched:
`reached, not checked`, `partly checked`, `not reached`. Today a reviewer
has to know it exists and run it separately, with its own flags.

## What it does

`ep_review --base B --functions` runs TestMiner (`mine(..., base=B)`) on
the head worktree the review already creates, with the review's test
command and its base commit. The report gains a section:

```
## Functions no test checks

- svc.py:12 total: partly checked (returning 0 or 1 failed no test)
- svc.py:40 Box.size: reached, not checked (tests: test_svc.test_box)
- svc.py:55 helper: not reached
3 more functions are checked by their tests.
```

- Only the three verdicts above are listed; `checked` is counted.
  `unknown` is counted with its reasons, shortest first, in the section.
- TestMiner's issues go to "Unknown", as strength's do.
- When TestMiner cannot run (a command that is not direct pytest or
  unittest, a project below the repository root, coverage.py missing), the
  section says "Not measured:" with its reason. The review itself is never
  refused for it.
- Without `--functions`, the section says how to ask for it, as
  `--strength` does.
- `--function-seconds` (default 120) and `--function-limit` (default 20)
  pass through. The JSON report gains `functions`: TestMiner's result, or
  `{"state": "not measured: …"}`.

## Approaches

- **Chosen: a separate section, on the same worktree.** It reuses
  TestMiner unchanged and keeps line-level and function-level findings
  apart.
- **Merged into "Lines no test noticed".** Rejected: two granularities in
  one list, and two different notions of a sample.
- **TestMiner's extreme values as strength's engine.** Rejected: loses the
  line-level detail reviewers already use.

## Bounds

- Python only, as TestMiner.
- One more full test run under coverage, plus up to a few runs per examined
  function: opt-in for that reason.
- Equivalent values can still give a false `partly checked`, so the section
  carries that sentence in "Unknown".

## Checks

- A fixture change with an unasserted function: listed `reached, not
  checked`; an asserted one: counted as checked (both directions).
- A non-direct command: "Not measured" with the reason, the review still
  produced.
- Without `--functions`: the hint line, and `functions` is null in JSON.
