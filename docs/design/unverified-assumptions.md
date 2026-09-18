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
- **A pattern whose producer the code never names.** The §7c narrowing trades
  this away deliberately: a regex for `ruff`'s output in a file that never
  writes the word `ruff` is not reported. Silence is the safe direction, and the
  alternative was firing on every validation regex in the repository.
- **A credential with no recognisable shape.** `core/redact.py` matches issuer
  prefixes and named values, not randomness. A bare high-entropy string that
  nothing labels survives - and the alternative, an entropy threshold, eats
  every git sha in the ledger.

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

Added with the narrowing and the redaction (§7c):

- **forward** — the TAP case survives the narrowing: `parsers.py` names
  `node --test`, node was run, the counter matched nothing; **reported**.
- **adversarial** — an email and a phone validator in a file naming no tool;
  **silent** - and the same file with the narrowing removed is loud, or the
  silence proves nothing.
- **adversarial** — a runner named in one file does not vouch for a regex in
  another.
- **forward** — a pattern in a file the task *created*; reported, because the
  whole new file is what was added.
- **forward** — fifteen documented example credentials; none survives `scrub`.
- **adversarial** — eight real producers, 27,700 characters of this project's
  own output; **not one character changed**. This is the requirement that
  rules entropy out.
- **adversarial** — a lowercase English word after `token:` is not a
  credential, and `token=\w+` still matches its own redacted output.

### And every one of them was watched flipping

A regression test is not evidence until it has been seen failing before the fix
and passing after. Three of the tests here were written *after* their fix and so
had never been seen to fail — which is exactly the vacuous probe this module
computes for everyone else. Each fix was therefore broken in turn and the test
guarding it re-run:

| fix removed | guard |
|---|---|
| the strong-construct rule | `test_source_code_in_a_string_is_not_a_pattern` |
| escapes blanked before the tool name | `test_an_escape_does_not_hide_the_tool_name` |
| the tool is the first real token | `test_the_tool_is_the_first_real_token` |
| `scrub` on the way into the ledger | `test_the_ledger_scrubs_on_the_way_in` |
| the self-ignoring state directory | `test_state_directory_ignores_itself` |
| the quote before the separator | the JSON-key case of `test_an_issued_credential...` |

**Six broken, six red, and green again on restore.** A seventh control is built
into the narrowing tests themselves: the file that must be silent is asserted
*loud* with the narrowing switched off, in the same run, so the silence can
never be mistaken for the feature working.

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

## 7c. Two costs this introduced, and what they are worth

Asked plainly whether the check would *hurt*, and the honest answer was yes,
twice. Both are recorded here because both were created by the fix rather than
found in the code it checks. Both are now closed; what closing them cost, and
the three defects that closing them turned up, are below.

### The state directory was never protected, and this widened what is in it

To answer "did anything you ran look like this", the ledger began keeping
**12 commands x 8KB** of output. Before that it kept `_tail(output)` - three
lines. That is a real increase in what sits on disk, and if a command prints a
token it is now written down.

**And the exposure predates the change.** `.elevenpowers/ledger.json` already
held the user's prompt, every command string, and three lines of every output.
This repository gitignores `.elevenpowers/`; **a user's repository does not**,
and the plugin never wrote that line for them. A `git add -A` commits the lot.

**Shipped: the state directory ignores itself.** `Ledger._keep_out_of_git`
writes `.elevenpowers/.gitignore` containing `*` on every save, which makes git
ignore everything in that directory regardless of what the repository's own
ignore file says. It needs no edit to a file the user owns, it protects the
whole directory rather than the one field that prompted it, and the uninstall
story is unchanged - the directory is still the only thing to delete. An ignore
file already there is never overwritten.

Measured both ways on a fresh `git init` that has never heard of this plugin:
with the marker, `git status --porcelain` is empty; with it removed,
`?? .elevenpowers/`.

**Shipped: `core/redact.py`, as defence in depth.** Not entropy. Entropy is the
property of a git sha, a UUID, a content hash and a long identifier, all of
which this project's own output is made of - and a redactor that eats test
output breaks the very check the output is kept for. Prefixes are taken from two
sources that agree, [Semgrep's *Secrets Story: The Prefixed Secrets That Tried
to Get Away*](https://semgrep.dev/blog/2025/secrets-story-and-prefixed-secrets/)
and [apikeys.guide, *Key Formats &
Prefixes*](https://apikeys.guide/docs/implementation/key-formats-and-prefixes),
plus the named-value form (`AWS_SECRET_ACCESS_KEY=`, whose value has no prefix
at all), bearer headers, JWTs and PEM blocks.

Measured by running eight real producers in this repository - `git log`,
`git status`, `git diff --stat`, two `pytest` invocations, `architecture/check.py`,
`node --test` and `pip list`, 27,700 characters - and diffing before against
after: **zero characters changed**. Forward, fifteen documented example
credentials: **zero survived**.

**And the prefixes were confirmed by something outside this project.** The first
attempt to push this work was **refused by GitHub's own push protection**, which
named the Slack and Stripe lines in `tests/test_redact.py` — invented values, but
in shapes real enough that a production scanner treats them as live. That is a
better check on the table than any amount of re-reading it, and it cost nothing.
The fixtures are now assembled from a prefix and a body at import time so no
complete token literal sits in the file; the block was **not** bypassed through
the allow-this-secret link, because a fixture shaped exactly like a credential is
one every tool downstream will keep treating as one.

Two things it found by being run rather than reasoned about. A quoted JSON key -
`"refresh_token": "1//0e..."` - walked straight past the first version, which
read only `KEY=value`; that is how every JSON and YAML config on earth spells it.
And the replacement marker is a bare word, not `<redacted>`, because the
redactor runs over the same text §3 searches: `token=\w+` must still match its
own redacted output, or a pattern that *was* confirmed gets reported as
unverified.

### The check assumes every pattern describes command output

It does not. These are all claims about *data*, not about a tool:

```
^[^@]+@[^@]+\.[a-z]{2,}$     email validation
^\+?[0-9]{7,15}$              phone validation
<a href="([^"]+)"             scraping fetched HTML
```

Nothing a command printed will ever match them, so each is reported as
unverified, every time. On a repository that parses formats fetched at runtime -
a scraper, a client library - that is most of the regexes in it, and the feature
becomes noise.

**Shipped: the code must name a tool the task actually ran.** A pattern in file
F is reported only when F's added lines mention the bare name of a command this
task executed. The TAP case qualifies - the same diff added `node --test` to the
dispatch, and `node --test` was run. An email validator in a file that mentions
no command does not. Attribution is **per file**, not pooled across the diff, so
a runner named in `parsers.py` does not vouch for a regex in `validate.py`.

Two refinements, both forced by running it:

- **The launcher is not the tool.** `python -m pytest` is a claim about pytest.
  Keeping `python` would let the word in any docstring vouch for every regex in
  the file containing it, which is the narrowing undone. Task words - `test`,
  `run`, `build` - are dropped for the same reason.
- **Escapes are blanked before the name is looked for.** The first version used
  a plain word boundary and went silent on `core/parsers.py`, the single file
  the whole feature was built for: it names node as `r"\bnode\s+--test\b"`, and
  the character before `node` there is the `b` of `\b`. The forward test caught
  it on its first run.

And the flip control found a third defect that had nothing to do with the
narrowing. `git diff <base> -- <path>` reports **nothing at all** for an
untracked file, so every pattern in every file a task *creates* was exempt -
including `core/redact.py`, added in this same change. A new file is read whole,
because the whole file is what the task added.

This narrows honestly rather than cleverly. It misses a pattern written for a
tool the code never names, which is the safe direction: silence, not a wrong
accusation.

### Then it was pointed at its own diff, and found two more

The cheapest possible test of a noise complaint is to run the check on the
change that fixes it. Eighteen patterns came back. Eleven were real; **seven
were source code**.

```
'def secret_santa(names):'
'self.token_count = len(tokens)'
'import re\nCOUNT = re.compile(r"{body}")\n{dispatch}'
```

Those are test *fixtures* — strings holding code — and code is made of brackets
and parentheses, so a "two or more metacharacters" rule reads them as claims
about some tool's output. A literal must now also contain a construct that only
a regular expression has: an anchor, an escape class, alternation, a quantifier,
a group flag, a real character class.

**Measured before adopting, not after.** Against all **67** pattern literals
`core/` compiles — read out of the AST, so pieces of a concatenated pattern
count — the rule loses **none**, and it drops **all seven** fixtures. A test
re-measures that on every run, so a future pattern shape cannot quietly fall
out.

The same run showed the tool-name set was too generous: it took *every* token,
so `git status` vouched for any file containing the word "status" and
`pytest tests/test_redact.py` vouched for anything containing "test_redact" —
the narrowing widening itself back out. It is now the first token that is
neither a flag nor a launcher. Ten real runner shapes were run through it before
the table was written down, and **two were wrong**: `go test` returned nothing,
because a two-letter name fell below the length floor, and `bundle exec rspec`
returned `bundle` — the same launcher idiom as `npx`.

Which is, once again, the rule this whole feature exists to enforce: the shapes
were written from memory, and running them was what corrected them.

## 8. Phasing

1. `core/assumptions.py` — both rules, with the tests above. No wiring.
2. Report-only lines in `end_report`.
3. Measure the firing rate on real commits before it is anything more.

Stopping after (2) is an acceptable outcome. A line that says *you wrote a
pattern nothing you ran produced* is worth having even if it never refuses
anything — because on the day it was needed, seven separate times, nobody said
it.
