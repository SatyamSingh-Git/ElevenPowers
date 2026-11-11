# 101 — The agent waited for a report it never read

*2026-11-11. Item 3 of the build list: make the "fix comes with a real test"
check cheaper.*

The held-out sweep's best result had a price on it. Untested fixes fell from
84% to 37% of resolved runs, and assisted runs took about 3.1× as long. The
plan was to profile that time and cut it.

## The time was not the model's

The sweep's transcripts carry both clocks. Model time was 31.5 s against
23.9 s. Wall time was 83.6 s against 25.3 s. So 52 of the 84 seconds were
spent outside the model: in hooks, and in tests.

Each workspace's `verification.json` splits the Stop hook by phase. The
largest phase was not the check that produces the benefit:

- the base-tree suite took 6.9 s;
- the mutation step, "test strength", took **18.3 s at every Stop**.

That step ended incomplete in 110 of 119 runs. Its findings go to a human
report, and by design never to the agent.

## The withdrawal that made this suspicious

On 2026-11-03 the same kind of claim was withdrawn: "the mutation step is
most of the gap." There, the replay had committed each stage first, and the
real runs never did. Every real Stop found its files already dirty and
refused them in 0.6 s.

So this time the number came from the sweep's own records, not a replay,
and it held for a reason that fits: each held-out task opened on a clean
tree. Run alone on four copied final trees, the step took 5.7–60.5 s. Three
of those four never ran a single mutant.

## The change

`strength.at_stop`, off by default. The analysis still runs when asked for
(`ep_strength`, `ep_review --strength`), and a project can put it back at
Stop.

Two things were seen to flip:

- **Tests.** Five mutants of the switch and its validation were all killed.
- **The real hook.** Four sweep runs were replayed from base. The default
  Stop recorded no strength phase; with `at_stop` set, it recorded
  3.8–60.2 s.

## One reading that was wrong on the way

A replay seemed to sit for 9.5 minutes before its Stop. It had not. Its
output was buffered, so the Stop being watched was a later task's. Run
again with flushed output, the whole cachetools replay took 69 s.

## What is left

What remains outside the model is mostly the tests the benefit is made of:

- the agent's own runs, 11.6 s;
- its `ep_check`, 7.1 s;
- the base-tree suite, 6.9 s.

Two cuts from 2026-11-03 postdate the sweep: hooks no longer start through
PowerShell, and `ep_check` no longer hashes the runtime seven times. No new
sweep has measured the total.
