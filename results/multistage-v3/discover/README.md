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
