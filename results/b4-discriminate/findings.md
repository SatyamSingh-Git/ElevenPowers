# B4: the discrimination measurement, taken at last

`claude-opus-5`, effort high, gate arm, 1 replicate, 16 tasks, corpus
`e2d721482fbdd2a5` — the same fingerprint as B3, so the two are one-for-one
comparable. Run 2026-09-17 across four parallel shards. **$40.84**, 110 minutes
of agent time.

Parallelism was verified before use, not after: four concurrent rehearsals
reproduced the sequential answer exactly — same verdict, same `red_before`
count, same reproduction grain on all 16 tasks.

---

## 1. The headline: no vacuous evidence was found

| | B3 (sonnet) | B4 (opus) |
|---|---|---|
| runs where the check was asked | 8 of 16 | **14 of 16** |
| `DISCRIMINATES` | 7 | **14** |
| **`VACUOUS`** | 1 | **0** |

**The rate this project exists to measure is not detectable at this sample
size.** Point estimate 0 of 14. By the rule of three the 95% upper bound is
about **21%**; pooled with B3 it is 1 in 22, about 4.5%, one-sided 95% upper
bound **19.8%**.

> **Corrected 2026-09-19.** That last figure read *~13%* and was wrong. 13.6% is
> `3/22`, the rule of three — which is an approximation for **zero** events and
> does not apply to one. The exact binomial bound solving `P(X ≤ 1 | p) = 0.05`
> is **19.81%** one-sided, and the upper end of the two-sided 95% interval is
> **22.84%**. An external audit found it; the arithmetic was re-run here before
> the correction was written. The error made the result look tighter than it is,
> which is the direction that matters.
>
> The *first* figure is not affected: 0 events of 14 is exactly where the rule
> of three applies. And pooling B3 with B4 still mixes two models over shared
> tasks, so neither bound is an independent-trial estimate — the arithmetic is
> corrected, the pooling assumption is not defended.

That is a negative result about the headline claim, and it is recorded as one.
The premise was that agents routinely finish on evidence that could not have
failed. On this corpus, with these two models, that is either rare or absent.

**And the measurement is weaker than 0-of-14 sounds.** Six of the fourteen had
**more than 20 tests already red** on their base tree (max 48). Where the base
tree is broadly broken, "this check could have failed there" is true no matter
what the agent did, so `VACUOUS` was close to unreachable by construction. The
clean sub-sample is about eight runs, where the upper bound is nearer **31%**.

**The one case that did fire, did not replicate.** `itsdangerous-6c58e969` was
B3's single `VACUOUS`: sonnet called it resolved in 9 turns and 56 seconds on
evidence that would have passed anyway. Opus, same task, took 17 turns and
produced evidence that discriminates, with a real red-then-green test behind it.
That is the mechanism behaving correctly — `VACUOUS` is a property of the
agent's evidence, not of the task — but it is n=1 per arm, an anecdote rather
than a rate.

## 2. The three gates closed today all held

Coverage went from 8 of 16 to 14 of 16, and the two runs B3 lost to the
staleness gate were individually recovered:

| task | B3 | B4 |
|---|---|---|
| `click-9f9b149e` | `discrimination={}` — skipped | `{'tests': 'yes'}`, 30 red on base |
| `click-051bb0f3` | `discrimination={}` — skipped | `{'tests': 'yes'}`, 31 red on base |

`config` is now in every bundle, so each one can say which gate closed. That is
how the remaining two were diagnosed at all.

Targeted reproductions: **5 of 14**, against **0 of 8** in B3.

## 3. The finding that matters more than the rate

**Two of sixteen runs bypassed the gate completely, and not through any gate.**

- `jinja2-0cd69481` — a **5,396-line patch** touching `src/jinja2/utils.py` and
  `tests/test_filters.py`, graded **resolved**, and `ledger.touched` is
  **empty**. The runtime observed none of it. No claim opened, so `on_stop`
  returned at its first line and nothing was ever asked.
- `attrs-5d6d21aa` — the only edit observed was `changelog.d/1331.change.md`,
  which is prose, and prose does not open a claim. The source changes were
  invisible.

This is not the base gate, the staleness gate or the config gate. The agent
changed code, the task graded as resolved, and **the ledger never saw it**. A
completion gate that silently observes nothing is the exact failure shape this
project names as worse than none — and it is at **12.5%** of runs.

That is now the most important open defect, and it outranks the discrimination
rate: a rate measured only over runs the gate could see is conditioned on the
gate working.

## 4. Opus against sonnet, same 16 tasks

| | sonnet (B3) | opus (B4) |
|---|---|---|
| resolved | 10 of 16 | **12 of 16** |
| regressed | 0 | 1 |
| total cost | $24.97 | $40.84 |
| agent time | 127 min | 110 min |

The single regression, `attrs-6fda0a4e`, is **genuine and not the withdrawn
false positive**. PLAN §10 records two earlier `regressed` runs that were an
attrs version string clobbered by a concurrent agent's editable install. This
one broke `TestAnnotations::test_pipe`, `test_pipe_empty` and
`test_pipe_non_introspectable`, and the agent's own patch edits
`src/attr/setters.py` and mentions `pipe` 37 times. It broke code it was
working on.

That is also the first real evidence that running agents concurrently no longer
contaminates results — the per-workspace virtualenv closed that door, and the
rehearsal check could not have proved it, because rehearsals run no agent and so
run no `pip`.

## 5. What this does not support

- No claim about the vacuous rate in general. One corpus, five repositories,
  two models, 22 pooled observations.
- No claim that the gate improves outcomes. This was a single-arm run; there is
  no vanilla arm here to compare against.
- Nothing about `red_before` being clean. Its median is 12 and its max is 48,
  and where it is large it is mostly pre-existing breakage.
