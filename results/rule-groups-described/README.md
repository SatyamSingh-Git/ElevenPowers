# Does a reviewer's description close the gap the template left? Stopped before sealing

[Design](../../docs/superpowers/specs/2026-11-05-rule-groups-described-design.md),
written before any description or run. **Not run.** The description
step, which the design fixed in advance, showed at $0.07 that the
experiment could not test what it asked.

## What ran

- **A launcher check, twice.** The first call of
  [`describe.py`](describe.py) failed before any model call. It left
  `--output-format` without its value, and `claude` refused the arguments.
  That cost $0 and produced no description. Fixed, a trivial one-turn check
  confirmed the init event lists **no tools** and the model is Sonnet 5.5.
  It cost $0.03.
- **The describer, once** ([output](descriptions.json),
  [prompts and replies](describer.jsonl)). It wrote one tool-free Sonnet 5.5
  turn per certified `parcelpost` rule, given only the proposal and its two
  files at stage 0. It cost $0.04. The replies, verbatim:
  - `rule-_check_digit-_plausible_number`: "The check digit of a tracking
    number (PP + 8-digit serial + digit + GB) is (10 − weighted sum % 10) %
    10 over the serial's digits with weights alternating 3,1 starting at 3;
    `_plausible_number` must validate exactly what `_check_digit` issues."
  - `rule-manifest_filename-bill_day`: "Billing finds a day's manifest by
    calling `manifest_filename(day)` (`manifest-<day.isoformat()>.csv`) in
    `settings.manifest_dir`, so the manifest writer and `bill_day` must keep
    deriving the filename from that one function."

## Why it stopped

The reviewer described the **filename** rule, the same coupling as the
template's shared words. That is what the two proposed functions share.

Stage 5 breaks a different coupling between the same two files. Its
declared dependent's note says billing "groups the manifest's charges by
account with itertools.groupby and so relies on lines of one account being
adjacent". That `groupby` is in `make_invoices`, not in `bill_day`, and
the line order comes from `_manifest_order`, not `manifest_filename`.

So any description of the certified pair, template or reviewer's, names a
rule the stage does not touch. The agents who left `billing.py` alone
reasoned correctly from that rule: the change "doesn't touch the filename".
The described arm would have tested a description that gives the agent
nothing more than the template did. A null from it would then have been
misread as "descriptions do not matter".

Stopping was decided on this input, before sealing and before any run
outcome existed.

## What it corrects

- **The acted-on lead is withdrawn** (PLAN §10). It said "a person's
  description of the rule would not point at the filename". It did. The
  `parcelpost` losses are a pair of files tied in two ways, with the note
  naming one. They are not a weak description.
- **The guide's advice is rewritten** from the same evidence. An agent
  takes the declared rule as the whole contract between the files. When
  files are tied in more than one way, the description has to say so.

## What it leaves open

- A note that names one rule invites the agent to check only that rule. It
  is untested whether wording that declares the files coupled as a whole,
  or a description of every tie between them, would have kept the
  dependent.
- A test of that would need stages where the broken coupling is not the
  proposed one, chosen in advance and not only this one.

## How often a certified pair names the wrong tie ([`coupling_scan.py`](coupling_scan.py), [output](coupling-scan.json), $0)

The scan looked at each of the 25 covered v3 stages. For each, it asked
whether the reference changes a function the certifying proposal named, or
another function in the same two files. Functions were read with `ast`,
and changed lines with `difflib`. Read by hand, `parcelpost` 5 changes
`_manifest_order` and `make_invoices`, and `household_budget` 7 changes
exactly the two proposed functions.

- **16 stages:** the stage changes a proposed function, so the note names
  the tie that breaks.
- **9 stages:** the stage breaks another tie between the same files.
  - `clinic_booking` 7, `gradebook` 3, `hotel_desk` 7;
  - `parcelpost` 1, `parcelpost` 5;
  - `payroll_lite` 4, `recipe_box` 1, `recipe_box` 8, `survey_tally` 4.

Joined with the acted-on and harm runs' covered stages, the dependent was
lost as follows:

| the stage breaks… | control | rules |
|---|---|---|
| the tie the note names (16 stages) | 26 of 52 (50%) | 2 of 52 (4%) |
| another tie (9 stages) | 11 of 18 (61%) | 4 of 18 (22%) |

**Exploratory and after the fact.** The cells are small and unbalanced:
10 of the 18 runs in the second row are `parcelpost` 5. The note helps in
both rows, because it puts the other file in front of the agent. Where it
names the wrong tie, it leaves more behind.

A note that declares the files coupled as a whole, rather than by one
rule, could close that residue. It could also invite edits nothing needed.
These 9 stages are where it would have to be tested, chosen now, before
any such wording exists.
