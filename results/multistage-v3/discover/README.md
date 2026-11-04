# Discover, then certify: would one review of proposed rule groups have covered the dependents? ($0)

PLAN §13 B, open problem 1. The loop is borrowed from NVIDIA Auto-Ontology
([reading list](../../../docs/research/reading-list.md)): *discover* a map
automatically, have a person *certify* it once, and *ground* agents in the
certified map only.

Here the map is groups of files that carry the same rule. ElevenPowers
already has the certified half: a milestone in `elevenpowers.milestones.json`
lists input files and checks. The question is the discover half. Before any
change is made, would a short list of proposed pairs, read once by a person,
have contained the pairs that later broke?

Per-edit ranking is a different question, already measured (16 of 51 in the
top 3, [data flow](../dataflow/README.md)). This one sees no edit. It
proposes from the project alone, so its errors are paid once, at review, and
never on an edit.

## Plan, written before `discover.py` exists

**Proposal.** For the project tree just before a stage:

- every pair of functions in different non-test source files;
- scored by the rarity-weighted (IDF) identifiers, literals and numbers they
  share (the token spike's weighting), normalised by the square root of the
  product of each function's own total weight, so large functions do not win
  by size;
- a file pair takes its best function pair's score;
- the proposal is the top K file pairs, each shown with its shared tokens as
  the reason.

**Truth.** A stage's pair is (a file the stage's reference changes, the
stage's declared dependent). It counts as covered if that pair is in the
top K proposed for the tree before the stage. The stage's files are taken
from `reference.diff` without the dependent's own fix: the `quiet` variant
against the stage before.

**Two sets:**

- the **51 never-read dependents** (the [data-flow](../dataflow/README.md)
  set), which decide;
- the 17 read stages, reported for completeness only.

**Decided in advance.** Worth building only if, on the 51, a review of
**K = 50** pairs per project covers **at least 17** (a third). Recall at
K = 10, 20, 50 and 100 is reported either way. K = 50 is about the number a
person can read in one sitting, with reasons.

**Bounds known in advance:**

- Proposals come from the tree before each stage, which assumes the person
  reviews again as the project grows. A single review at stage 0 is
  reported too.
- Coverage is a ceiling: a person may reject a true pair.
- Precision cannot be judged without human labels. The declared
  dependents give a lower bound only.

## Result: passes its bar ([`discover.py`](discover.py), [rows](discover.json), [summary](discover.txt))

| 51 never-read dependents, covered within K proposals per project | K = 10 | 20 | **50** | 100 |
|---|---|---|---|---|
| proposals from the tree before each stage | 8 | 11 | **20** | 32 |
| one review at stage 0 | 8 | 10 | 20 | 32 |
| control: the dependent joined to another stage's changed files | 3 | 5 | 11 | 18 |
| random, expected | 0.8 | 1.6 | 3.9 | 7.8 |

- **At K = 50 it covers 20 of 51,** against a bar of 17. That is about
  twice the control and five times random.
- **One review at the start does as well** as reviewing again before every
  stage, so a project need not re-run it on every change.
- **By kind, at K = 50:** copy 8 of 13, data 9 of 17, key 2 of 16,
  contract 1 of 5.
- **The control is not small** (11): files in these small projects are
  related, and a dependent often shares rules with more than one change. The
  margin over it is what supports the claim.

A proposal reads as a reason a person can judge. From the covered rows:

- `reports/statement.py` and `services/fees.py`: `total` and `total`
  sharing `"0.00"`, `Decimal`, `amount`;
- `model/money.py` and `reports/costs.py`: `ROUND_HALF_UP`, `quantize`,
  `cents`;
- `services/ingest.py` and `services/manual.py`: `"missing sensor"`,
  `check_range`, `canonical_unit`.

Some are generic, such as two CSV writers sharing `newline`, `writer` and
`"w"`. Rejecting those is the point of the certify step.

**Decision:** build it. Proposals go to a person, never to the agent, and
only pairs a person declares reach the agent.

## Built, and the whole loop replayed on a real loss ([`replay_loop.py`](replay_loop.py), [output](replay_loop.txt))

The runtime's `propose()` gives the spike's place for all 51 never-read
dependents ([`product.py`](product.py), [output](product.txt)).

`payroll_lite` stage 2 is one of the 31 v3 losses: the agent changed the
overtime rule and left `reports/hours.py`, which keeps its own copy. On
that conversation's kept snapshot, at $0:

1. **Discover.** The top proposal for the project is
   `rules/overtime.py` with `reports/hours.py`, sharing `daily_threshold`
   and `holiday`.
2. **Certify.** The replay accepts it as a person would. The rule's
   description is the replay's own words, not the case's.
3. **Ground, for the agent.** The agent's real edits are replayed through
   the real hooks. Before it edits `rules/overtime.py`, its brief says:
   "Declared rule overtime-split (How ordinary and overtime hours are split
   for pay.) is also kept in src/payroll/reports/hours.py. Change them
   together, or say why one should differ."
4. **Ground, for the reviewer.** At Stop, the end report says: "declared
   rule overtime-split: changed src/payroll/rules/overtime.py, not
   src/payroll/reports/hours.py". That is the file this agent left behind.

**Not shown:**

- whether an agent acts on the brief: briefs were ignored in v3, and this
  needs a paid, pre-registered run;
- whether a person accepts the right pairs: the replay accepted the top one.

`hotel_desk` stage 3 is not covered. Its edited helper reads no rule input
of its own, the same case co-readers missed.
