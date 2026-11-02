# Spike: shared rare tokens point at left-behind dependents ($0)

PLAN §13 B, open problem 1. In 22 of the ElevenPowers arm's 31 v3 losses,
the dependent that broke imports nothing the agent edited, so the
import-graph brief (`core/atlas.neighbourhood`) found 4 of 31
([diagnosis](../README.md#why-elevenpowers-did-not-help-diagnosis-of-its-31-losses-0)).
The declared dependents come in three kinds:
- **copy:** another file has its own copy of the rule that changed;
- **contract:** another file relies on an order, format or exception;
- **data:** another file reads the same stored data itself.

**Method.** [`rank.py`](rank.py) runs on the kept snapshots:
1. Take the functions the agent's edit touched, before and after the
   stage.
2. Collect their identifiers, attribute names, string literals and
   numbers.
3. Weight each by its rarity across the project's non-test source files
   (inverse document frequency).
4. Rank every other source file by the weight of the tokens it shares.

This borrows the token weighting behind clone and plagiarism detectors. It
is a spike, not product code.

## Result

| | top 1 | top 3 | top 5 |
|---|---|---|---|
| **the agent's own edit** | **11 of 31** | **17 of 31** | 18 of 31 |
| control: another stage's edit, same conversation | 0 | 5 | 5 |
| expected at random | | 1.8 | |
| import-graph brief | | 4 named (any rank) | |

- **Where it works.** The copies share the rule's own names: `max_fine` and
  `daily_fine`, `daily_threshold`, `is_spending`, and the `"-"`/`split`/
  `lower` of an id rule. The data and order contracts share a stored key or
  an `attrgetter`.
- **Where it fails.** `gradebook` stage 4, all 5 of its losses: the export
  writes a percent with its own fixed format and shares no token with the
  edited configuration. Also `payroll_lite` stage 5 (rank 13) and
  `fleet_service` stage 5 (rank 14).
- **The control holds.** With another stage's edit, no dependent ranks
  first, so the signal comes from the change. Five dependents are central
  enough to reach the top 3 for any edit.

## Held out ([`heldout.py`](heldout.py))

v3 declares only five quiet dependents outside the twelve (case, stage)
pairs read before writing the method. The 120 conversations' own edits rank
them 17 times, in both arms:

| | top 1 | top 3 | control (another stage's edit), top 3 | random, top 3 |
|---|---|---|---|---|
| all 17 | 2 | **4 (24%)** | 0 | 6% |
| copy, 2 | | 2 of 2 | | |
| contract, 14 | | 2 of 14 | | |
| data, 1 | | 0 of 1 | | |

The held-out set agrees with the in-sample pattern but is too small to
settle it. A copy of the changed rule is found; a contract on an order or a
format mostly is not.

## Bounds

- **In-sample, mostly.** The 31 losses were read before the method was
  chosen. The held-out check covers only 5 dependents, 14 of its 17
  rankings being contracts.
- **Recall only.** Top 3 means naming 3 of about 50 files per edited
  function. How often those names are noise has not been measured.
- **Detection is not prevention.** The 4 dependents the import brief did
  name were delivered and not acted on (open problem 2). Finding more of
  them does not show that an agent will act on them.
