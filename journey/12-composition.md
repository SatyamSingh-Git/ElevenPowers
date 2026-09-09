# 12. Building the yardstick, and mismeasuring with it

## The thing that had never existed

The project's first goal, stated before any code, was to combine the strengths
of the systems it studied so that each one's weakness is covered by another's.
`docs/research/complementarity-matrix.md` mapped that across fourteen systems
and ended with an instruction: **the system must beat the composition baseline,
not only vanilla and single frameworks.**

That baseline had never been assembled. So for twelve phases the project's
central claim had no test.

## Assembling it

`eval/stack.py` builds it from local clones, following the matrix's recipe:
superpowers' skills and handoff scripts, ECC's hard blocks and batched stop
check, gstack's evidence ledger and verify gate, Spec Kit's lean commands,
BMAD's blind-then-claims review. All MIT, with a NOTICE recording every licence
and every deliberate exclusion.

The census it prints is the first result, and it needs no agent runs:

```
skills             14
commands            5
agents              1
always-on          ~1,038 tokens every turn
on demand         ~58,862 tokens if everything is read

competing routers   3
review mechanisms   9
state directories   9
```

The matrix predicted three reviewer mechanisms would collide. Counted in the
assembled stack there are nine, and nine state directories appear in a
repository that installed only the recommended pieces.

## A hazard the matrix does not mention

The first build copied superpowers' `skills/` and not its `hooks/`. The plugin
loaded, the descriptions reached the system prompt, and the smoke test came back
in six turns for six cents, which is exactly what vanilla costs.

The habit of checking whether the mechanism fired before believing the number is
the only reason this was caught. The transcript had no `You have superpowers`
in it and no skill had been invoked.

**Superpowers delivers its routing pressure through a SessionStart injection.**
Take its skill bodies without that hook and you buy their entire token cost and
none of their behaviour. With the hook wired: eleven turns, a skill actually
invoked.

That is a real hazard for anyone assembling these systems, and it is only
visible by assembling them.

## The comparison, and why it could not have worked

```
arm                         n  resolved   turns  seconds    cost
vanilla                    16       94%     8.7       39    1.06
superpowers (best part)    16       75%    12.8       61    1.62
composition stack          16       81%    12.1       60    1.49
this project               16       75%     9.8       83    2.23
```

Nothing beats doing nothing, and every arm costs more. That reads like a
finding. It is not, and the reason is worth stating precisely:

```
tasks a plain agent always resolves : 11   (no headroom)
unstable                            : 4
never resolved                      : 1

in the pass used as the baseline, the plain arm failed only: ['merge_busy']
which is the task nothing resolves, so no arm had anything to improve on.
```

**The baseline failed exactly one task, and it is the task nothing ever
resolves.** There was no headroom at all. No arm could have demonstrated a
benefit on this suite, whatever it did.

The plan's own exit criterion for this milestone says the comparison runs "on
the discriminating suite from M5". That suite does not exist yet, and I ran the
comparison on the one already known not to discriminate.

## The distinction I had and then dropped

Phase 10 measured the ceiling and phase 11 used it correctly. M1 succeeded
because **block rate is observed on every run**: sixteen runs give sixteen
observations, and a fall from 75 percent to 12 is far outside the noise.

Resolution is not like that. Only tasks where two arms disagree carry
information, and disagreement is bounded by how often the baseline fails. With
one failure available, the strongest result obtainable was p = 1.000, and
`eval/analyse.py` printed exactly that before printing anything else.

**Per-run metrics are measurable on this suite. Per-discordant-pair metrics are
not.** I applied that in M1 and forgot it one milestone later.

## What M2 did establish

- The baseline exists and rebuilds from one command, so the project's central
  claim is testable for the first time.
- Composition costs 1.4 times vanilla's tokens and 1.5 times its wall clock in
  this configuration. Cost is a per-run measurement, so that part is sound.
- The stack and its strongest single part are indistinguishable here: 81 against
  75 percent, two broken tasks against three, all inside the noise floor.
- No arm damaged anything stable. Across all three, zero of the eleven reliably
  resolved tasks failed.
- Nine review mechanisms and nine state directories, counted rather than
  predicted.

## What it did not

P11 is unanswered. Composition shows measurable extra cost and no measurable
benefit, but a test with no headroom cannot show benefit, so only the cost half
of that sentence is evidence.

**M2 does not exit.** Its exit criterion requires a suite that discriminates,
and building one is now blocking two milestones rather than one.
