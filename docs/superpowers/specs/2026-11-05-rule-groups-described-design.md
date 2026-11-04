# Does a reviewer's description close the gap the template left? (PLAN §13 B)

**Status: stopped before sealing, 2026-11-05.** The describer ran as
fixed below. It described the certified pair's filename rule, the same
coupling as the template. Stage 5 breaks a different coupling between the
same files: billing's `groupby` relies on the manifest's line order. So the
described arm could not test what the question asks. No run was made
([record](../../../results/rule-groups-described/README.md)). The text
below is the design as written before any description was generated.

## Question

In the acted-on run ([results](../../../results/rule-groups-acted-on/README.md)),
3 of the 4 rules-arm losses were on `parcelpost` stage 5. Its certified
rule's description was the neutral template, which named only the shared
words: "These files keep the same rule (they share manifest_filename, day,
isoformat)." Two of those agents reasoned from the word "filename" and left
`billing.py` alone. The guide now tells people to write the rule itself.
**Does a sentence a reviewer writes from the two files do better than the
template?**

## The describer, fixed in advance

[`describe.py`](../../../results/rule-groups-described/describe.py) stands in
for the person who certifies. For each of the case's certified rules it
runs one Sonnet 5.5 turn, at medium effort, in a folder holding only the
two files. The turn has **no tools**, which the session's init event must
confirm. It sees:

- the proposal: the two files, the two functions and the shared words;
- both files as they stand at stage 0.

It sees no stage request, oracle, result or other file. It is asked for one
sentence of at most 200 characters stating the rule both functions keep.

**Run once, used verbatim.** A reply that is long, wrong or odd is used as
it is, because regenerating would be retrying for a favourable
description. A reply that fails to parse is the only exception. It stops
the experiment and is recorded.

## Design

The acted-on harness, model (Sonnet 5.5, medium), certification, time
limit and sealing are unchanged. Two arms, identical except for the
description text of each certified rule:

- **rules:** the template description, as in the acted-on run;
- **described:** the describer's sentence.

There is no control arm. The acted-on run already measured the note
against none.

**Stage:** `parcelpost` 5 only, the one stage where the template left room.
The template lost 3 of 10 there, and the other primary stages lost 0 or 1
of 10.

**Primary:** the dependent lost, described against rules. The runner's
exact one-sided test with one stratum, which is Fisher's, at α = 0.05. The
pre-registered direction is that described loses fewer.

**Secondary:**

- the run regressed anything other than the dependent;
- the agent named the dependent in its final message;
- cost and model time;
- delivery, from `briefed`.

**Size** ([`power.py`](../../../results/rule-groups-described/power.py),
[output](../../../results/rule-groups-described/power.txt), exact): 30
runs per arm, 60 runs, about $10 and about 25 minutes. With the template
at 30%:

| described loss rate | power |
|---|---|
| 30% (no effect) | 3% (false positive) |
| 10% | 49% |
| 5% | 75% |
| 0% | 97% |

This tests whether a reviewer's sentence **closes most of the gap**. It
cannot see a modest improvement. The template's 30% rests on 3 of 10 runs,
so if its true rate is lower, so is the power. A null here does not show
that descriptions do not matter.

## Gates

1. **$0 rehearsal.**
   - Both arms' declarations load.
   - They differ only in the description text.
   - A replayed Edit and a replayed shell write each bring the note,
     naming the dependent, in the described arm with the describer's text.
2. **No pilot.** The harness is the one qualified on 206 runs on
   2026-11-04. Only the arm's entries differ, and that is tested, with
   seven mutants killed.
3. **Seal and run** the 60, never retrying.

## Bounds known in advance

- One stage, one describer and one description per rule. This is an
  existence test of a mechanism, not a rate for descriptions in general.
- The describer is a model, not a person who knows the project.
