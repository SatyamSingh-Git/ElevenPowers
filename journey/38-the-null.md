# 38 — The measurement came back null

*2026-09-17. B4: 16 tasks, opus 5 at effort high, $40.84, 110 minutes.*

The instrument was repaired all day so that this number would mean something.
It means something. It is **zero**.

---

## What was asked, and what came back

`VACUOUS` — a declared check that would have passed without the change — came
back **0 times in 14 asked runs**. B3 had found 1 in 8. Pooled across both
sweeps: **1 in 22**.

And the one case did not survive contact with a second model. B3's
`itsdangerous-6c58e969` was sonnet calling a task resolved in **9 turns and 56
seconds** on evidence that would have passed anyway. Opus, handed the identical
task, took 17 turns and produced evidence that discriminates, with a real
red-then-green test behind it.

That is the mechanism behaving exactly as designed — `VACUOUS` is a property of
*the agent's evidence*, not of the task — and it is also n=1 per arm, which is
an anecdote.

## The premise this bears on

PLAN §5.10 exists because of an external result: **46% of agent validation
evidence carries no bug-discriminating information** (arXiv 2607.28871, 3,730
validation events). That study is not in doubt and it is cited, not claimed.
What is now on the record is that **this corpus does not reproduce it**.

The honest reading is that the effect is rare *here* rather than that the
literature is wrong. These are well-specified tasks mined from real commits in
five well-maintained Python repositories. It is not where sloppy evidence would
be expected to live. But that reading is a hypothesis about why the null
happened, and hypotheses do not get to cancel measurements — so the frequency
claim is withdrawn in §10 until a corpus or an n exists that supports it.

**And the null is weaker than 0-of-14 sounds**, in the direction that makes it
less damning rather than more: six of the fourteen had **more than twenty tests
already red** on their base tree, up to 48. Against a base that broken, "this
check could have failed there" is true whatever the agent did, so `VACUOUS` was
close to unreachable by construction. The clean sub-sample is about eight, where
the 95% upper bound is nearer 31% than 21%.

## What the day's repairs bought

They bought the right to read the number at all.

| | B3, this morning | B4, tonight |
|---|---|---|
| runs where the check was asked | 8 of 16 | 14 of 16 |
| reproduction established by name | 0 of 8 | 5 of 14 |
| bundles that can explain their own result | no | yes |

Both runs B3 lost to the staleness gate came back individually: `click-9f9b149e`
and `click-051bb0f3` each recorded `discrimination={}` before and
`{'tests': 'yes'}` now, with 30 and 31 tests red on base. Before today a null
would have been noise from a half-blind instrument reporting one fact twice.

## The finding that outranks the rate

**Two of sixteen runs bypassed the gate completely**, and through none of the
three gates closed that morning.

`jinja2-0cd69481` produced a **5,396-line patch** touching `src/jinja2/utils.py`
and `tests/test_filters.py`, graded **resolved** — and `ledger.touched` is
**empty**. The runtime observed none of it. No claim opened, so `on_stop`
returned at its first line and nothing was ever asked of it.
`attrs-5d6d21aa` had exactly one edit observed, `changelog.d/1331.change.md`,
and prose does not open a claim.

A completion gate that silently observes nothing is the failure shape this
project names as worse than none, and it is at **12.5%** of runs. It also
conditions every rate here: a frequency measured over runs the gate could see
says nothing about the runs it could not.

That is the next thing to fix, and it outranks the measurement it undermined.

## One more thing, recorded because it is easy to misread

`attrs-6fda0a4e` came back **`regressed`**. PLAN §10 already withdraws two
earlier `regressed` runs that were an attrs version string clobbered by a
concurrent agent's editable install, so an attrs regression during a **parallel**
sweep is exactly the shape of that false positive.

It is not one. The three broken tests are
`TestAnnotations::test_pipe`, `test_pipe_empty` and
`test_pipe_non_introspectable`, and the agent's own patch edits
`src/attr/setters.py` and says `pipe` **37 times**. It broke code it was working
on.

Which makes it the first real evidence that running agents concurrently no
longer contaminates results — the per-workspace virtualenv closed that door. The
rehearsal check run beforehand could not have proved it, because rehearsals run
no agent and therefore run no `pip`. Four concurrent rehearsals did reproduce
the sequential answer exactly, which is why the parallel sweep was allowed to
start at all.
