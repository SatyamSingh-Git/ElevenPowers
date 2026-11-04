# Does an agent act on a certified rule?

PLAN §13 B, open problem 2.
[Design](../../docs/superpowers/specs/2026-11-04-rule-groups-acted-on-design.md),
written before any run. Harness: [`eval/rule_groups_run.py`](../../eval/rule_groups_run.py).

Each run is one v3 stage from its reference tree. The arms are superpowers
plus ElevenPowers as shipped, identical except that `rules` carries the
case's certified rules in `elevenpowers.milestones.json`. Certification is a
simulated perfect reviewer of the stage-0 proposals, fixed in advance and
frozen into the sealed protocol.

## Gate 1: $0 rehearsal, passed 5 of 5 ([`rehearse.py`](rehearse.py), [output](rehearsal.txt))

On each primary stage:

- the stage's pair is certified (2–3 declared rules per case);
- the declarations load, and only the rules arm carries them;
- the reference edit, replayed through the real hooks, brings a brief naming
  the dependent before the rule's other file is edited;
- the grader scores the reference as kept and the left-behind variant as
  lost.

## Gate 2: pilot, launched 2026-11-04

Two stages chosen for their v3 baseline:

- `household_budget` stage 7, lost 5 of 5 in v3;
- `recipe_box` stage 4, lost 4 of 5.

Three runs per arm on each: 12 runs, about $2, Sonnet 5.5 at medium effort,
sealed in `E:/ep-runs/rule-groups-acted-on-pilot-2026-11-04`.

The first slot was the harness check: completed, $0.14, 103 s, and the
control arm lost the dependent. The pilot must show four things:

- the harness runs;
- the brief is received in the rules arm;
- the control arm loses the dependent at least once;
- no run is lost to infrastructure.

It is too small to show an effect and is not read for one.

### Pilot result: the harness qualifies, and delivery has a gap

All 12 runs completed, with nothing lost to infrastructure: $1.63, 43–136
s each ([batch](E:/ep-runs/rule-groups-acted-on-pilot-2026-11-04)).

| stage | control: dependent lost | rules: dependent lost |
|---|---|---|
| `household_budget` 7 | 3 of 3 | 1 of 3 |
| `recipe_box` 4 | 3 of 3 | 0 of 3 |

As pre-registered, this is not read for an effect. Reading the transcripts
shows why it must not be. The note reached the agent in only 3 of 6 rules
runs:

- **Note received:** in both `household_budget` runs that kept the
  dependent, and in `recipe_box` 2, the agent edited a declared file with
  the Edit tool, and the brief named the other file.
- **Note never received:** in `recipe_box` 0 and 1, the agent wrote every
  file by running Python in Bash. No Edit was made, so no brief fired.
  Neither run read `elevenpowers.milestones.json`, and the session-start
  context is the same in both arms. Those agents found the dependent on
  their own, so the arms' difference there is not the note's.
- **Note never received, dependent lost:** `household_budget` rules 1 also
  edited through Bash.

**Decision:** the full run waits for a repair. A rule note has to reach an
agent that edits through the shell as well. It is repaired, rehearsed again
at $0 on the shell path, and only then sealed and run. The pilot batch is
kept as it is.

### Repair: the note now follows a shell write (2026-11-04)

After a Bash or PowerShell command, `core/hook.py` checks what the task
has changed since it opened. Each changed file that a declared multi-file
rule names, and that has not been briefed, gets the rule note once. The
note is the same one an Edit brings.

- Tests are in `tests/test_rule_groups.py`, five new.
  - Forward: a script-written declared file brings the note, once.
  - Adversarial: there is no note for an undeclared file, a file briefed
    earlier, or a file the developer had already changed before the task.
  - A shell change outside any rule leaves that file's own brief for its
    first Edit.
- Mutation check: five of six mutants were killed. The survivor removes the
  shell-only gate. It makes no difference to what is said, because every
  Edit is briefed before it happens. The gate only saves a `git status` on
  every other tool call.
- **Gate 1 rerun** with a shell-write replay ([`rehearse.py`](rehearse.py)):
  before the repair it failed 0 of 5, with the dependent never named. After
  it, it passes 5 of 5, and the control arm is silent both times.
  [`rehearsal.json`](rehearsal.json) is the passing run. It was produced in
  a detached worktree whose `core/hook.py` and `rehearse.py` are
  byte-identical to this commit's.

**Real-host check, both ways** ([`shell_probe.py`](shell_probe.py),
[transcripts](shell-probe/)). The hook emitting the note is not the same as
the model receiving it. So this was run with Claude Code 2.1.292 and Sonnet
5.5, with the runner's own command and sandbox, outside any batch. Each run
was one turn: the agent ran a script with Bash that wrote a declared file,
then quoted any rule note it had received. Total cost $0.11.

- **rules:** the reply quoted the note word for word, including the rule
  id `rule-hours_rows-split_hours`. The agent's only tool call was that one
  Bash command, so it could not have read the declarations itself.
- **control:** the reply was `NONE`, and nothing was briefed.

The design records the repair as an amendment, made before sealing
([spec](../../docs/superpowers/specs/2026-11-04-rule-groups-acted-on-design.md)).

## Gate 3: the full run, sealed and launched 2026-11-04

`E:/ep-runs/rule-groups-acted-on-full-2026-11-04`: five stages, two arms and
ten replicates, which is 100 one-stage runs at Sonnet 5.5, medium effort. The
estimate is about $14–16. [`launch.py`](launch.py) runs them four at a time.
Their order is fixed in `launch-order.json` before the first launch:
replicate blocks in turn, shuffled within each block with a seed. Every
slot runs once and is never retried. The protocol pins the runtime
fingerprint and the harness hash, and every slot checks both before it
starts.

### Result: the certified rule was acted on

All 100 runs completed, and none was lost to infrastructure. The run cost
$16.39 ([analysis](analysis-rule-groups-acted-on-full-2026-11-04.json),
from [`analyse.py`](analyse.py)).

**Primary (pre-registered):** the dependent was lost in **35 of 50 control
runs (70%)** and **4 of 50 rules runs (8%)**. The exact one-sided
stratified test gives **p = 8.6 × 10⁻¹³**.

| stage | control: dependent lost | rules: dependent lost |
|---|---|---|
| `household_budget` 7 | 8 of 10 | 1 of 10 |
| `recipe_box` 4 | 9 of 10 | 0 of 10 |
| `library_loans` 1 | 6 of 10 | 0 of 10 |
| `payroll_lite` 2 | 2 of 10 | 0 of 10 |
| `parcelpost` 5 | 10 of 10 | 3 of 10 |

**Secondary (pre-registered):**

- **Harm.** Other groups were lost in 0 of 50 runs in each arm. Rules runs
  cost $8.53 against $7.86 (+8.5%) and took 89.0 s of model time against
  82.2 s (+8%).
- **Delivery.** All 50 rules runs were briefed on a declared file.
- **Not run in this batch.** The other covered stages and the
  self-contained stages were not part of it, so "the same outcome on every
  other covered stage" and "edits to a declared file where nothing needed
  it" are unmeasured.

**Exploratory, not pre-registered:**

- **The stage's own request was done in all 50 rules runs.** So no rules
  run kept the dependent by doing nothing. This check was confirmed both
  ways at $0 on every stage: an untouched tree fails the request groups,
  and the reference passes them. The control arm's 44 of 50 is not a
  separate finding. All six misses are `library_loans` dependent losses,
  where the request group `grace_report` exercises the dependent report.
- **The shell repair carried the result.** 21 rules runs never used an
  edit tool, and none of them lost the dependent. Without the repair they
  would have received no note at all. In the control arm, 13 of 19 such
  runs lost it.
- **The four rules-arm losses saw the note and left the dependent
  unchanged.** Three named it in the final message and said why they had
  left it, which is the note's own second branch:
  - `household_budget` 1 told the user that netting refunds in
    `reports/month_end.py` "is a small change";
  - `parcelpost` 4 left `billing.py` alone because the change "doesn't
    touch the filename or the day";
  - `parcelpost` 6 left it because it had not touched the manifest
    filename, "so billing and reconcile still read the file as before".

  The `parcelpost` rule's description was the neutral template: "they share
  manifest_filename, day, isoformat". The agents reasoned from exactly
  those words. A person's description of the rule would not point at the
  filename. This is a lead on description quality, not a finding.

**What bounds it** (from the design):

- Certification is perfect by construction. A person may accept fewer
  pairs, or wrong ones.
- Proposals cover 20 of v3's 51 never-read dependents. Where no certified
  rule covers the broken pair, nothing changes.
- The five stages were chosen for their known losses, so the result says
  the note works where a loss is likely, not how often it matters.
- Each run is one stage from the reference tree, not a conversation.
- Both arms ran ElevenPowers. The gain is the certified rules' alone, and
  the shipped tool without them is the 70% control.
