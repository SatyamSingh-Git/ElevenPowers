# Would a reviewer keep the pairs that matter? Yes, 16 of 27

[Design](../../docs/superpowers/specs/2026-11-05-rule-groups-reviewed-design.md),
written before any call. Script: [`review.py`](review.py).

One Sonnet 5.5 turn per case, at medium effort, with **no tools** (each
init event lists none). Blind to every stage, it read the case's 50
proposals at stage 0, with both functions' source, and replied with the
numbers it would certify. All 12 replies parsed. The cost was $1.44
([summary](review.txt), [kept and certified](reviewed.json),
[prompts and replies](reviewer.jsonl)).

## Result

- **Recall: 16 of 27** certified pairs kept (59%). That passes the
  pre-set half, so the decision fixed in advance applies: the acted-on
  design reruns with this certification.
- **Burden:** 3–11 proposals kept per case, 73 in total over 12 cases.
  This is not precision, which needs a person's labels: a kept pair no
  stage breaks may still be a true rule.
- **Covered stages:** the reviewer kept the pair on 15 of 25, and on 4 of
  the 5 acted-on primary stages. It dropped `parcelpost` 5's
  `manifest_filename` and `bill_day` pair.
- **Read with the [coupling scan](../rule-groups-described/README.md)**
  (exploratory): it kept 12 of the 16 pairs whose proposed functions are
  the tie the stage breaks, and 3 of the 9 whose are not. Where the
  proposed functions really share a rule, a reader sees it.

| case | kept | certified kept |
|---|---|---|
| clinic_booking | 3 | 2 of 3 |
| fleet_service | 6 | 2 of 3 |
| gradebook | 8 | 1 of 1 |
| greenhouse_monitor | 5 | 2 of 2 |
| hotel_desk | 5 | 0 of 1 |
| household_budget | 11 | 2 of 3 |
| library_loans | 6 | 2 of 2 |
| parcelpost | 4 | 1 of 2 |
| payroll_lite | 4 | 1 of 2 |
| recipe_box | 9 | 2 of 3 |
| survey_tally | 5 | 0 of 3 |
| ticket_office | 7 | 1 of 2 |

## Attempts

- **Attempt 1** ([log](review-attempt-1-winerror206.txt)) failed at
  process creation before any model call, at $0. The about 53k-character
  prompt was passed on the command line, past Windows' 32,767 characters
  (`WinError 206`), and no case got a reply.
- **Fixed:** the prompt now goes on stdin. A check with a 40,000-character
  prompt and no tools replied as asked, at $0.19 including the session's
  cache write. That put the estimate at about $2.50–3, against the
  design's $1–2. The run itself cost $1.44.

## Bounds

- A model stands in for a person who knows the project.
- Truth is what the v3 stages break, so recall is measured and precision
  is not.
