# Data flow: does following what the changed code returns find what was left behind? ($0)

PLAN §13 B, open problem 1. The lead came from the
[same-state spike](../cowriters/README.md). Its held-out contract dependents
were assumptions about the data the changed code produces ("rows arrive
sorted", "the list only grows"), and their recorded paths follow that data
to the code that uses it.

## A fresh test set

Every detector so far was designed or judged on the 17 stages behind the
losses and the earlier held-out set, and all 17 have now been read. This
spike uses the **51 declared dependents of the other stages**, which have
never been read: data 17, key 16, copy 13, contract 5.

These stages had no loss because the agents updated the dependent, so there
is no agent edit that leaves it behind. Each is built from the case's own
reference instead (`eval/multistage_cases.tree`):

- **before:** the reference tree at stage n − 1;
- **after:** the `quiet` variant at stage n, which is the reference change
  with that dependent left behind;
- **edited:** the files that differ between the two;
- **control:** the same dependent, ranked from another stage's reference
  change.

## Plan, written before `dataflow.py` exists

**Detector.** Find the functions the change touched, before and after. A
file scores by how much it uses them:

- calls to a touched function, by name, weighted by that name's rarity
  across the project;
- callers of those callers, one more hop, at half weight.

Calls are resolved by name only, with no types. Unrelated functions that
share a name will collide; rarity weighting is the only defence.

**Compared on the same 51,** with the same trees and controls, against the
two earlier scorers: shared rare tokens and co-readers.

**Decided in advance.** Data flow is worth building as an on-demand question
("what uses what this change returns?") only if all three hold:

- it puts at least 17 of 51 (a third) in the top 3;
- that is at least 5 more than the better of the other two;
- its control finds at most half as many.

Otherwise it is recorded as tried. The two earlier detectors' fresh results
are recorded either way, because they are their first test on unread
stages.

**Bounds known in advance:**

- A reference change is cleaner than an agent's, so these ranks may be
  better than an agent's edit would give.
- Contracts, the kind that motivated this, are only 5 of the 51.
