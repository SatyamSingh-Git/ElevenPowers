# Field report — a real project, three setups (2026-10)

**What this is:** the experience of three developers (the project's author and two
friends) using Claude Code on their own real project, first with no plugin, then
with the superpowers plugin, then with superpowers and ElevenPowers together. It
is user experience, recorded as told on 2026-10-23. It is not a measurement: there
was no blind comparison and no counts were kept. The measured results sit
elsewhere (`results/heldout/sweep-2026-10-22/`); this report is kept beside them
because it describes effects that a single-fix sweep cannot see.

## The setting

| | |
|---|---|
| Project | *not yet recorded* |
| Size and language | *not yet recorded* |
| People | three developers |
| Setups, in order | (1) Claude Code alone; (2) with the superpowers plugin; (3) with superpowers and ElevenPowers |
| Time with each setup | *not yet recorded* |
| Project rule in force throughout | `CLAUDE.md` said to update the docs whenever work is done, and never leave them behind |

The setups were used one after another, not side by side, and ElevenPowers was
added on top of superpowers rather than in place of it.

## What changed

### Docs kept up to date

- **No plugin:** docs were updated very rarely, although `CLAUDE.md` required it.
- **superpowers:** better; docs were usually updated, but often still forgotten.
- **superpowers + ElevenPowers:** in their estimate about 95% of the time. When
  they asked "have you updated the docs?", the answer was always yes; they did not
  meet a case where the agent said it had forgotten. This rests on more than the
  agent's word: the author often checked the docs themselves, though not every
  time, and reports that the docs had been updated when checked.

### A fix that causes another bug

- **No plugin:** bug fixing went badly.
- **superpowers:** much better, but once or twice a fix changed something another
  part of the code depended on, the dependent part was not fixed, and a new bug or
  problem followed.
- **superpowers + ElevenPowers:** not met at all so far. They attribute this to
  ElevenPowers working out the blast radius of a change, so the dependent code is
  found before the fix is called done.

### What got worse

- **Speed:** slightly slower than before ElevenPowers, which they put down to it
  running tests and other checks.
- **Tokens:** usage went up very slightly.

### Further observations

*The account ended mid-sentence ("And also, …"); the rest is not yet recorded.*

## How it sits beside the measurements

- The held-out sweep measured one of these effects directly: with ElevenPowers,
  agents backed their fixes with tests far more often (vacuous fixes 84% → 37%).
  Its regression counts point the same way as the second observation but are too
  few to conclude anything (4 ordinary, 2 assisted, of about 120 runs each).
- The sweep also measured the cost they describe, more sharply: about 3.1× the
  model-process time and 1.4× the cost per bug fix. Over a whole working session,
  most of which is not spent on the checks, that plausibly feels "slightly slower".
- Docs upkeep and fixes that miss a dependent change are not measured by any
  experiment here yet. A multi-step build of the same project with and without
  ElevenPowers, with docs freshness and cross-step regressions counted
  mechanically, is the planned test of exactly these two effects:
  [multi-stage v2](../superpowers/specs/2026-10-23-multistage-field-claims-design.md),
  designed 2026-10-23 with superpowers in both arms, as in this report, and not yet run.
- The held-out sweep's launcher loaded no user plugins, so its ordinary arm was
  plain Claude Code, not the superpowers setup this report compares against.

## Still to record

- the project, its size and language, and how long each setup was used;
- one or two concrete incidents for each observation (a fix that would have broken
  something, a doc the agent kept current without being reminded);
- each of the three developers' own view, where it differs;
- the rest of the account that was cut off.
