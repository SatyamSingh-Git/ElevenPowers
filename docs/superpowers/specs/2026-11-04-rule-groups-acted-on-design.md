# Does an agent act on a certified rule? (PLAN §13 B, open problem 2)

**Status: design, 2026-11-04. Gate 1 and the pilot have run; the treatment
was repaired and amended below, before the full run was sealed.**

## Question

Rule groups ([design](2026-11-04-rule-groups-design.md)) put a certified
sentence in the agent's brief before it edits a declared file: *"Declared
rule X (…) is also kept in B. Change them together, or say why one should
differ."* The replay showed the sentence arrives
([results](../../../results/multistage-v3/discover/README.md)). In v3,
delivered import briefs were ignored. **Does this one change what the agent
does?**

## Why it can be measured cheaply

16 of the ElevenPowers arm's 31 v3 losses were on stages whose broken pair a
single review of 50 proposals at stage 0 would have covered:

| stage | ElevenPowers losses in v3, of 5 conversations |
|---|---|
| `household_budget` 7 | 5 |
| `recipe_box` 4 | 4 |
| `library_loans` 1 | 3 |
| `payroll_lite` 2 | 2 |
| `parcelpost` 5 | 2 |

The shipped tool lost the dependent in 16 of 25 conversations on these five
stages (64%), so the baseline leaves room to move.

## Design

**Unit: one stage, not a conversation.** Each run starts from the
reference tree before the stage (`eval/multistage_cases.tree`), sends that
stage's request, and is graded by the case's own oracle groups for the
stage. A one-stage session cost $0.14–0.17 on 2026-11-03, against $1.28 for
an eight-stage conversation, and pairing by stage gives far more power.

**Two arms, identical except for one file.** Both are superpowers plus
ElevenPowers as shipped, with the v3 runner's model (Sonnet 5.5, medium),
time limit, tools and sealing.

- **control:** no `elevenpowers.milestones.json`;
- **rules:** the case's certified rules in `elevenpowers.milestones.json`,
  committed in the start tree.

**Certification, fixed in advance and the same for every case.** A perfect
reviewer is simulated:

- take the top 50 proposals of `ep_milestones --propose` on the stage-0
  tree;
- accept exactly those that pair a file some stage's reference changes with
  that stage's declared dependent.

The description is a neutral template, "These files keep the same rule
(they share A, B, C).", with no word from any stage's request. That is a
lower bound on a person's description. The check is the case's public test
command.

**Primary outcome:** on the five stages above, the share of runs whose
declared dependent's oracle group is lost.

- **Comparison:** rules against control, pooled over stages.
- **Test:** exact one-sided Cochran–Mantel–Haenszel over the five stages,
  α = 0.05.
- **Pre-registered direction:** rules lose fewer.

**Secondary, each reported whatever it shows:**

- the same outcome on every other covered stage;
- **harm:**
  - other groups lost;
  - edits to a declared file on self-contained stages, where nothing needed
    it;
  - wall time and cost;
- **delivery:** the brief was received, from the runtime's own
  `integrations.json` counts and its `briefed` record.

**Size.** Ten runs per arm on each of the five stages: 100 runs, about $16
and about 2.5 hours at four at a time. Simulated with the pre-registered
test ([`power.py`](../../../results/multistage-v3/discover/power.py),
[output](../../../results/multistage-v3/discover/power.txt)):

| loss rate in the rules arm | power at 10 per arm per stage |
|---|---|
| 64%, no effect | 3% (the false-positive rate) |
| 51% | 33% |
| **40%** | **81%** |
| 27% | 98% |

The baselines come from conversations, not single stages. The pilot checks
that the control arm still loses at a similar rate. If it does not, the run
is resized before sealing, never after.

## Gates, in order

1. **$0 rehearsal.**
   - The declarations load without issues for every case.
   - Replaying each covered stage's reference edit through the real hooks
     shows the brief naming the dependent.
   - The control arm's tree has no declaration file.
   - The grader scores the reference as nothing lost, and the `quiet`
     variant as the dependent lost.
2. **Pilot: two of the five stages, three runs per arm (12 runs, about $2).**
   It must show four things:
   - the harness runs;
   - the brief is received in the rules arm;
   - the control arm loses the dependent at least once;
   - no run is lost to infrastructure.
3. **Seal and run** the 100, never retrying for a result. Every attempt is
   kept.

## Amendment after the pilot, before sealing (2026-11-04)

The pilot ([results](../../../results/rule-groups-acted-on/README.md))
qualified the harness. It also showed that the treatment as written, a note
before the agent edits a declared file, reached only edits made with the Edit
tool. Three of six rules-arm runs wrote every file by running Python in Bash
and never saw the note.

- **Treatment, repaired** (`core/hook.py`, d8e31ca). After a shell command,
  each file the task changed that a declared multi-file rule names, and that
  was not briefed yet, gets the same note once. Gate 1 was rerun with a
  shell-write replay: 0 of 5 before the repair, 5 of 5 after, with the
  control arm silent.
- **No resize.** The pilot's control arm lost the dependent in 6 of 6 runs,
  at or above the 64% baseline.
- **The pilot is not pooled** with the full run, because its treatment was
  different. The primary outcome, test, direction and size are unchanged.
- **Delivery** is read from the runtime's `briefed` record, which now holds
  both routes.

## Bounds known in advance

- One stage from the reference tree is not a conversation: the agent has no
  history, and the tree is the reference's, not its own earlier work.
- The certification is perfect by construction. A person may accept fewer
  pairs, or wrong ones.
- The five stages were read when the losses were diagnosed. Their selection
  is by known baseline failure, not at random, so the result says whether
  the brief works where a loss is likely, not how often.
- Through the shell, the note arrives after the command that wrote the file,
  not before it. It can still change the rest of the stage, but not that
  write.
