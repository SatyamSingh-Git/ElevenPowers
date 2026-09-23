# B7: do the tests pin the changed logic?

**Run 2026-09-24. 1,296 seconds, $0, no agent.** The gate PLAN §5.16 set for
itself before anything was built.

## The question

§5.10's reversion check asks whether *anything* in the evidence could have
failed. One test that was red on the base tree satisfies it however much of the
change goes unexercised. The question raised against it: *if an agent can always
make pytest green, is the changed logic actually tested?*

§5.16 proposed an answer — mutants confined to the changed lines — and gated it
on this measurement, with three outcomes decided in advance:

| survival | outcome |
|---|---|
| near zero | the tests already pin the change; §5.16 is **withdrawn** |
| high, but equivalent mutants | a noise generator; §5.16 is **postponed** |
| high, and the survivors are real gaps | §5.16 earns its place |

## Method

For each of the 16 corpus tasks: seed the workspace at its base commit, apply
the **gold patch**, and generate mutants confined to the source lines that patch
changed. Run the task's own suite against each. A mutant that no test notices
**survives**.

Operators: statement deletion, string mutation, condition negation, comparison
and boolean swaps, arithmetic swaps, integer and boolean constant changes,
`return None`. Eight mutants per task at most, spread evenly across the sites.

**Three traps built in from the start, each learned this week:**

- The task's declared environment is applied. Without `PYTHONPATH=src` the
  suite imports the installed release, nothing runs against the mutant, and
  every mutant "survives" — the failure that corrupted two published figures on
  2026-09-22.
- Node ids are passed as an argument list, never through a shell.
- **A baseline first.** Tests already failing on the patched tree are
  deselected, so a mutant is only killed by a *new* failure.

**And two controls per task, so the probe is seen to flip.** Reverting the gold
patch must be **killed** — that is `stress.py`'s own mutant, and if it survives
the suite is not reading this source. A harmless no-op must **survive** — if it
is killed, the suite is flaky or the harness over-reports kills. **Both controls
passed on all 16 tasks.**

## Result

| task | survived | sites |
|---|---|---|
| attrs-97f8d175 | 0 / 2 | 2 |
| attrs-6e3786c5 | 0 / 7 | 7 |
| attrs-577c782c | 0 / 2 | 2 |
| attrs-1e07f468 | 0 / 8 | 20 |
| attrs-5d6d21aa | 1 / 8 | 33 |
| attrs-6fda0a4e | 0 / 8 | 25 |
| click-c2ed4149 | 1 / 3 | 3 |
| click-9f9b149e | **4 / 8** | 26 |
| click-051bb0f3 | **4 / 8** | 19 |
| click-ad39d749 | **5 / 8** | 83 |
| click-d946074a | 3 / 8 | 155 |
| click-d340b0c1 | 0 / 4 | 4 |
| click-18d29196 | 2 / 8 | 27 |
| itsdangerous-6c58e969 | 2 / 8 | 15 |
| jinja2-065334d1 | **5 / 7** | 7 |
| jinja2-0cd69481 | 0 / 1 | 1 |

**27 of 98 mutants survived, on 9 of 16 tasks.** Not near zero, so the first
outcome does not apply.

**The repository matters more than anything else in the table.** attrs: **1 of
35**. click: **19 of 47**. Whatever this measures, it is at least as much a
property of a project's testing culture as of any single change.

## Are the survivors real?

Each of the 27 was classified by reading its diff. **This is one reviewer, not
blind, and it is the reviewer who designed the probe** — the bias runs in the
direction of the mechanism looking useful, and that is why the next step below
is an independent classification rather than more mutants.

| judgement | n |
|---|---|
| clearly equivalent — cannot change behaviour | **3** |
| uncertain — defensive initialisers, a trailing `continue` | **3** |
| real but trivial — a warning's `stacklevel` | **1** |
| **real, unpinned behaviour** | **20** |

The three equivalent ones, so the criterion is visible:
`sys.version_info[:2] >= (3, 11)` → `[:3]` gives the same answer for every real
version; a deleted type alias only used in annotations; a changed `assert`
message.

What the twenty look like — every one survived the **maintainer's own tests**
for the change it sits in:

- `ctx.exit()` deleted after printing `--version`. The command carries on
  running after reporting its version.
- `is_eager=True` → `False` on the same option.
- `len(lines) + 1 < self.max_lines` → `+ 2` in `click`'s text wrapper. A
  textbook off-by-one at a boundary — the literal form of *"is it tested on the
  edge case"*.
- `yield rv` deleted inside a context manager, which would raise *"generator
  didn't yield"* the moment that path ran. It survives because nothing runs it.
- In `jinja2-065334d1`, **five of seven mutants survive**: the new branch's
  condition negated, the condition deleted, its return replaced with `None`, its
  return deleted. The maintainer's test exercises the fix without ever entering
  the branch the fix adds.

So the second outcome — *survivors are mostly equivalent* — does not apply
either, on this reviewer's reading.

## What this establishes, and what it does not

**It establishes** that on this corpus, the tests written *with* a change —
by the maintainers of mature, well-tested projects — leave a substantial part of
that change unpinned, and that a diff-scoped mutation probe can find it, cheaply
and without a false kill on any task.

**It does not establish:**

- **Anything about agents.** The gold patch was applied. These are gaps the
  maintainer left; an agent's patch is the untested case. The reasonable
  expectation is that an agent's own tests pin *less*, but that is an
  expectation.
- **That §5.16 has earned its place.** The gate said *survivors a reviewer
  agrees are real gaps*. One unblinded reviewer is not that. It **provisionally
  passes**, pending an independent classification.
- **A rate.** Eight mutants per task, sampled evenly, 98 in total across four
  repositories. `click-d946074a` had 155 sites and 8 were run.
- **Anything about `mutmut` or `cosmic-ray`.** The operators are this probe's
  own. Building §5.16 means borrowing an engine, not promoting `probe.py`.
- **That a surviving mutant is a bug.** It is a line the tests would not notice
  changing. Whether the line is *right* is a separate question nothing here
  answers.

## Next, not run

1. **An independent, blind classification of the 27** — someone who did not
   design the probe, shown each diff without the verdict of the others.
2. **The same probe on an agent's patch** rather than the gold one, which is the
   case §5.16 actually exists for.
3. **Survival by operator.** Statement deletion produced 19 of the 27 survivors
   from 54 attempts; comparison and boolean swaps produced none from 8. Too few
   of the latter to read anything into yet.

Reproduce: `python results/b7-mutants/probe.py` (~22 minutes, $0). Raw
per-mutant results with diffs: `mutants.json`.
