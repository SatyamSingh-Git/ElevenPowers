# The assumption nobody ran

**Status:** design, 2026-09-18. Written before the code, after a day in which
almost every defect had the same shape.

> *"I write plausible code fast, and plausible isn't correct. Nearly every defect
> came from writing against an assumed format instead of looking at the real
> one."*

That is not a confession peculiar to one model. It is the most-studied failure
in LLM code generation, and the fix that everyone reaches for first is measured
to barely work.

---

## 1. The shape, from one day's record

Every one of these was written, reviewed, tested and *believed* before anybody
ran the thing it described:

| assumption | how it was found |
|---|---|
| TAP counter format | ran `node --test`, looked |
| turbo's line prefix `@pkg:task:` | ran `turbo test`, looked |
| Go methods nest inside their type | ran the parser, looked |
| Rust `impl Trait for Type` names the type first | ran the parser, looked |
| the C# grammar is called `c_sharp` | ran the parser, looked |
| a module costs ~6ms to parse | measured, it was 3.8ms |
| turbo is the only monorepo prefix shape | looked at a second runner |

Seven defects, one cause, **zero** found by reasoning. Every one surfaced the
moment the real producer was executed and its real output read.

## 2. What the literature says, including the part that hurts

This is **API Knowledge Conflict**, and it is 20.41% of all hallucinations in
the largest taxonomy of the phenomenon:

> Zhang, Wang, Wang, Chen & Zheng, *LLM Hallucinations in Practical Code
> Generation: Phenomena, Mechanism, and Mitigation*
> ([arXiv:2409.20550](https://arxiv.org/abs/2409.20550), 2024). 1,380 annotated
> snippets. Three categories: **Task Requirement Conflicts 43.53%**, **Factual
> Knowledge Conflicts 31.91%** — of which **API Knowledge Conflicts 20.41%** —
> and **Project Context Conflicts 24.56%**.

**And the obvious remedy is measured to be nearly useless.** Their own
retrieval-augmented mitigation improved Pass@1 by **+0.87% to +3.05%**. Other
work is blunter:

> *"Documentation mainly helps models identify **what** APIs to use and remains
> insufficient for teaching **how** to use them correctly. Even with **oracle**
> API-document retrieval, LLMs still make recurring errors at the API,
> cross-API, and task levels."*
> — *Learning from Execution: Self-Evolving Memory for Private-Library Code
> Generation* ([arXiv:2604.24222](https://arxiv.org/html/2604.24222))

So "read the documentation first" is not the fix. Neither is "be more careful",
which is the same instruction addressed to a model instead of a retriever.
Constraint violation rises **0% to 78% across four compaction rounds** — an
instruction to check is gone by the time it matters.

**What does work is execution.** Grounding generation in execution feedback
moved pass@1 from ~70% to 89% in one study
([RLEF, arXiv:2410.02089](https://arxiv.org/abs/2410.02089)). That is this
project's entire thesis, pointed at a new target: *a claim is not evidence until
something ran*.

## 3. The computable rule

The runtime already watches every command an agent runs and keeps its output.
So the question "did you look?" is not a matter of trust — it is a lookup.

> **A pattern this task introduced, which never matched any output this task
> captured, is an assumption nobody verified.**

That is exactly the defect. `TAP_COUNT` was written and no `node --test` output
existed in the ledger to match it against. The turbo prefix was written and no
turbo output existed. In each case the runtime *knew* nothing had been run, and
nobody asked it.

And a second rule falls out of machinery that already exists. `core/stress.py`
runs the declared check against the base commit and records which tests were red
there. Therefore:

> **A test this task added, which passes on the tree as it was, did not test
> this change.**

That is the vacuous probe, computed. Four of them shipped today and only
hand-flipping caught them.

## 4. Why a pattern, specifically

Because it is the one assumption that is **machine-checkable without
understanding the code**. A regex is a falsifiable claim about text. Either some
text the task actually saw matches it, or none did — and "none did" is precisely
the state every one of those seven defects was in.

It does not catch everything, and §6 says what it misses. It catches the
majority of what went wrong here, and it catches it *before* the agent says
done rather than after a user asks.

## 5. What it will not do

- **It will not block.** Report-only, like every other check here. This gate
  blocked 75% of runs once on a signal nobody had measured.
- **It will not demand a test.** A pattern with no evidence is *named*; nothing
  is required of it. `core/surface.py` exists because an obligation nothing can
  discharge is a design error.
- **It will not read patterns it cannot parse.** A malformed or dynamic regex is
  skipped in silence rather than guessed at.

## 6. What it misses, stated now rather than discovered later

- **Non-regex assumptions.** `"c_sharp"` was a plain string in a lookup table,
  and this would not have caught it. Node-type tables likewise.
- **A pattern verified in a different session.** The ledger is per task, so a
  pattern confirmed last week reads as unverified today. That is the safe
  direction, but it is noise.
- **A pattern matched by output the agent never actually inspected.** Running
  the command is necessary, not sufficient - though it is the step that was
  skipped every time here.

## 7. Both ways, before it is believed

- **forward** — a task adds a regex and runs a command whose output matches it;
  **silent**.
- **adversarial** — a task adds a regex and runs nothing that matches; reported.
- **adversarial** — a task adds a regex and runs a command whose output does
  *not* match it; reported, because that is the same state.
- **adversarial** — a task that adds no patterns at all; silent.
- **adversarial** — an unparseable or dynamically built pattern; skipped, not
  guessed.
- **forward** — a new test that fails on the base tree; **silent**, it
  discriminates.
- **adversarial** — a new test that passes on the base tree; reported as having
  tested nothing about this change.
- **adversarial** — no base commit, or no base-tree run; says nothing rather
  than accusing.

## 7b. Where it speaks, and the intervention that was researched and refused

The obvious improvement is placement. This project's own numbers say so: the
**median decisive error lands at step 7 of 27**, the recovery window is **one
step**, observable signals appear about **ten steps later**, and **82% of doomed
runs keep executing** after recovery is impossible. A fact delivered at the
proposed stop arrives long after the work was built on it - which is exactly why
`report.guidance` exists.

So the plan was to inject it into the loop: the moment a command runs, if a
pattern the task wrote still matches nothing, say so then.

**The evidence says do not.** *Accurate Failure Prediction in Agents Does Not
Imply Effective Failure Prevention*
([arXiv:2602.03338](https://arxiv.org/abs/2602.03338)) measures precisely this
move. A critic with **AUROC 0.94** - detection good enough that nobody would
question shipping it - caused a **26 percentage point collapse** when allowed to
intervene. It helped only where runs were already failing (+2.8pp on ALFWorld,
p=0.014) and harmed ones that were succeeding (0 to -26pp). The authors' own
conclusion is that the value of such a framework is *"identifying when **not**
to intervene"*, and that a **50-task pilot** is needed before trusting one in
deployment.

Related work finds the same shape: richer, context-aware feedback "slightly
improves" outcomes for some models and "substantially worsens" them for others.

That maps exactly onto this repository's history. It blocked **75% of runs**
once on a signal nobody had measured, and its own live figure is that **80% of
first proposals are already right** - which is the population the paper says
intervention damages most.

**So: pulled, never pushed.** The same computation is reachable from
`ep_status` at step 7 by an agent or a person who asks, and reported at the
stop. Nothing is injected into a trajectory that may be going perfectly well.
`core/status.py` already exists for this reason - *"a verification layer whose
state can only be observed by tripping over it is one the user cannot reason
about"*.

A test enforces it rather than a comment: `test_nothing_is_ever_injected_into_
the_loop` reads `core/hook.py` and fails if either check is called there. §5.12,
in a form that cannot drift.

**What would license the push:** the 50-task pilot that paper prescribes,
comparing arms with and without injection. That is the same shape as the unrun
B6 experiment, and it costs the same kind of money.

## 8. Phasing

1. `core/assumptions.py` — both rules, with the tests above. No wiring.
2. Report-only lines in `end_report`.
3. Measure the firing rate on real commits before it is anything more.

Stopping after (2) is an acceptable outcome. A line that says *you wrote a
pattern nothing you ran produced* is worth having even if it never refuses
anything — because on the day it was needed, seven separate times, nobody said
it.
