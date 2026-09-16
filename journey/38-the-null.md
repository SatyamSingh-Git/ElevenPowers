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

---

## The bypass, fixed the same night

The cause was not a missing tool name. `jinja2-0cd69481` recorded `seen=0` and
`touched=0` while running Bash commands, and `attrs-5d6d21aa` shows the method
in its own evidence: a `printf` with a redirect. **The agents write files
through the shell**, and `written_paths()` recognises only some of those shapes.

Enumerating shell write syntax is a race nobody wins - redirection, heredocs,
`sed -i`, `python -c`, a script that writes a script. The working tree already
knows, and `on_stop` was already asking it. One line too late:

    ledger = Ledger.load(root)
    if not ledger.claims:
        return 0
    ledger.touched = ... | set(_changed_paths(root))    # never reached

So the question is asked first, and every changed path goes through
`observe_edit`, which is the same rule that opens a claim from a tool event -
not a second way of opening one.

**And the probe caught a defect in the fix before it shipped.** With git
consulted first, a session that changed *nothing* opened a claim, because
`_changed_paths` returns everything `git status` lists, including
`.elevenpowers/` - the runtime's own ledger. It had been scoring risk as though
the runtime's state were the user's work all along; it only became visible once
that list could open a claim. The state directory is now filtered out for every
caller.

## Three probes in two days have been the bug rather than found one

Worth setting down as a pattern, because the cost is real: each one sent an hour
after the wrong module.

1. A probe spliced `pass` into a multi-line `self.fail(...)` call, the file
   stopped parsing, and `core/radius.py` looked broken when it was fine.
2. A heredoc turned a backslash-b escape into byte 0x08, and a regex
   silently matched nothing.
3. Tonight: `printf ... > file` under `shell=True` on Windows runs under
   cmd.exe, where `printf` does not exist. `git status` came back empty, the
   replay reported the fix had failed, and the fix was correct.

In all three the probe was newer than the code it tested and had no test of its
own. **A probe is code, and it is the code least likely to have been checked.**
The tell each time was the same: a result too clean to be true - nothing
changed, nothing found, nothing matched.

There is a fourth, and it happened while this section was being written: these
paragraphs were appended through a heredoc, which ate the backslashes out of the
very examples describing backslashes being eaten - leaving a literal 0x08 in
the file, inside the sentence about a literal 0x08. Repaired with an editor
rather than a shell, which is what the standing note about this says to do and
what was not done.

---

## B5: the bypass fix, watched working on a live agent

*Four runs, $6.87, about ten minutes.* The fix above was verified by replay, and
a replay cannot reproduce the thing that caused the defect: an agent *choosing*
to write through the shell. Only an agent can do that. So the two tasks that
bypassed were re-run, twice each.

| | B4, before | B5, after |
|---|---|---|
| gate engaged | 0 of 2 | **4 of 4** |
| `touched` | 0 and 1 | 3-4 real source files |
| discrimination | never asked | `yes` on all four |

`src/jinja2/utils.py` and `src/attr/_make.py` are in `touched` now. They are the
files the gate was blind to.

**And the confound is excluded rather than assumed away.** The obvious
alternative explanation is that these agents simply used `Edit` and `Write` this
time, so the fix was never exercised. `ledger.guided` settles it: that flag is
set only by `_guide`, which runs only from the `EDIT_TOOLS` branch of
`on_post_tool`. It is **False on all four runs**. No edit-tool event reached the
runtime in any of them - the agents wrote through the shell again, exactly as
before - and the claim opened solely because `on_stop` now asks the working tree
first.

A fix for a defect found in a paid run, verified in a paid run, with the
alternative explanation ruled out by a flag that could not have been set.
