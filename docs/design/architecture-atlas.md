# The atlas: keeping the map true, and making the agent read it

**Status:** design, 2026-09-16. Written before the code.

> *"Always maintain docs and the architecture map. I want everyone who uses my
> tool to get this. And the coding agent actually uses that architecture for
> reference, and actually makes use of it."*

Two obligations in one sentence, and they are not the same obligation:
**keep the map true** and **put the map in front of the agent**. A true map
nobody reads changes nothing; a map that gets read while it is wrong is worse
than none.

---

## 1. Why this cannot be an instruction

This repository already tried the instruction. `CLAUDE.md` carries a standing
rule — *refresh `architecture/` before finishing* — in a blockquote, at the top,
with a worked example. It is forgotten. That is the user's own report, and it
matches what §2 of [`blast-radius.md`](blast-radius.md) measured: constraint
violation rises **0% to 78% across four compaction rounds**, and soft
organisational policy decays about **8.3x faster** than hard norms. A rule in a
file the agent may or may not still have in context is soft policy.

So the same move as the blast radius: **compute it, do not ask for it.**

## 2. The borrow: reflexion models, 1995

This problem was solved thirty-one years ago and given a name.

> *"Software engineers often use high-level models (for instance, box and arrow
> sketches) to reason and communicate about an existing software system. One
> problem with high-level models is that they are almost always inaccurate with
> respect to the system's source code. [...] An engineer defines a high-level
> model and specifies how the model maps to the source. A tool then computes a
> software reflexion model that shows where the engineer's high-level model
> agrees with and where it differs from a model of the source."*
>
> — Murphy, Notkin & Sullivan, *Software Reflexion Models: Bridging the Gap
> Between Source and High-Level Models*, FSE 1995, pp. 18–28. Applied to NetBSD,
> 250,000 lines of C, in "only a few hours".

That is this feature, exactly. Two models and a comparison:

| | |
|---|---|
| **source model** | computed from the code: modules, and the imports between them |
| **high-level model** | what the repository's committed architecture document says exists |
| **reflexion** | convergence, divergence, absence |

- **Convergence** — the document names it, the code has it. Silent.
- **Divergence** — the code has a module no document names. *The map went stale.*
- **Absence** — a document names a path the code no longer has. *The doc went stale.*

One computation answers both halves of the request. The architecture map and the
documentation are the same artifact class, checked the same way.

**What we add to the borrow.** Murphy's engineer states the high-level model by
hand and maps it to the source by hand. Here the high-level model is *already
written* — it is the committed architecture page — and the mapping is the repo
paths it names. The comparison runs at task completion, attributed to the change
that caused it, and bound to the same ledger as every other obligation.

## 3. The second borrow: outdated references are detectable

The absence half is not speculative either.

> Tan, Wagner & Treude, *Detecting Outdated Code Element References in Software
> Repository Documentation*, Empirical Software Engineering 29(1):5, 2023
> ([arXiv:2212.01479](https://arxiv.org/abs/2212.01479)). Over **3,000 GitHub
> projects**; *"most projects contain at least one outdated code element
> reference at some point in their history."* Their mechanism: detect references
> that **survive in the documentation after all source code instances have been
> deleted**.

That mechanism is taken verbatim. A document naming `core/verify.py` after
`core/verify.py` is gone is an outdated reference, and it is cheap and exact to
detect — no model, no heuristic, a path lookup.

## 4. The tension worth stating out loud

matklad's [*ARCHITECTURE.md*](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html)
(Feb 2021) is the convention most repositories that have such a file are
following, and its advice is the opposite of what this feature wants:

> *"Do name important files, modules, and types. Do not directly link them
> (links go stale)."*
>
> *"This is the main rule of thumb for ARCHITECTURE — only specify things that
> are unlikely to frequently change."*

That advice is right about the trade-off, and right about the remedy *given no
tooling*: if staleness cannot be detected, avoid the things that go stale. This
feature changes the premise. **When staleness is detected automatically,
precision becomes affordable** — a document can name modules, because being
wrong about one is now caught in the run that made it wrong rather than by a
confused reader a year later. That is the whole of what is added, and it is
worth one sentence because it is also the risk: if the detection is noisy, the
advice to stay vague was better.

## 5. What it computes

**Source model** — `ast`, stdlib only, per `core/`'s zero-dependency rule.
Nodes are modules; edges are intra-repository imports resolved from `import` and
`from ... import` against the repo's own files. Third-party and stdlib imports
are dropped: they are not this repository's architecture.

**High-level model** — the repo paths named in the architecture documents. A
document is discovered, not configured, in this order:

1. an `architecture/` directory, any file in it
2. `ARCHITECTURE.md`
3. `docs/architecture*`, `docs/design/*`
4. `README.md`

Paths are read out of backticks, markdown links and plain text that looks like a
repo path. Prose is not searched for symbol names: the false-positive cost is
too high, and this project has already paid four rounds of it on the exposure
canary.

**Reflexion**, scoped to the task:

- **divergence** — a module **this task added** that no document names
- **absence** — a path **this task deleted or renamed** that a document still names

Pre-existing drift is counted and reported as a single number, never as an
obligation. A first run that dumps two hundred findings is a first run that gets
switched off, and this gate has already blocked 75% of runs once on a signal
nobody had measured.

## 6. Making the agent actually use it

Computing a true map is half the request. The other half is that the map must
reach the agent at the moment it is deciding something.

| When | What it gets | Why there |
|---|---|---|
| `SessionStart` | one line: where the architecture document is, and whether it is currently in drift | so the agent knows the artifact exists at all |
| `PreToolUse` on the **first** edit of a file | that file's neighbourhood: what imports it, what it imports, which document describes it | the moment before it changes something is the only moment the information can change the change |
| `Stop` / `end_report` | divergence and absence this task caused | the obligation, attributed |

First-touch only, per file, per session. An architecture note on every edit is
an architecture note nobody reads.

> **The first version of "first touch" meant the wrong thing, and it cost the
> whole feature.** It was gated on `ledger.seen`, which records *reads* as well
> as edits — and in this host the edit tool requires the file to have been read
> first. So the note intended for the first edit was consumed by the read that
> preceded it, every time. Only a blind `Write` to an unread path ever produced
> one, and on an unread path there is usually nothing to say.
>
> An external audit measured it on 2026-09-19: emitted on a direct edit, silent
> after `Read` → `Edit`. Delivery is now tracked in its own list, `ledger.briefed`,
> because observing a file and telling someone about it are different events.
>
> **This changes what the published measurement meant.** *"The neighbourhood
> brief fires on 47% of files a real commit touched"* was computed by calling
> `atlas.neighbourhood` over real commits — it is what the function can *say*,
> not what an agent *received*, and the received rate was near zero until that
> fix. PLAN §10 records the correction. The general lesson is worth more than
> the fix: **a detector measured by calling it is not a feature measured by
> using it.**

This composes with `core/radius.py` rather than duplicating it: **radius is
symbol-level and runs at completion** — the siblings and callers of what
changed. **Atlas is module-level and runs before the edit** — the neighbourhood
of where you are about to work.

## 7. For repositories that have no map at all

Most will not have one. Divergence is unreportable when there is no document to
diverge from, and `core/surface.py` exists because an obligation nothing can
discharge is a design error rather than a finding.

So the tool writes the first one: `ARCHITECTURE.md`, generated from the source
model — the module list, grouped by directory, with each module's in-edges and
out-edges. It is a starting point a human is expected to rewrite, and it is
honest from the moment it is written because the code produced it. After that,
the reflexion check keeps it honest.

That is what "everyone who uses my tool gets this" means concretely: not a
convention they must adopt, a file the tool can produce and then defend.

## 8. Both ways, before it is believed

Per §5.0, and because a drift check that fires on everything and one that fires
on nothing are both indistinguishable from the feature being absent:

- **forward** — add a module no document names; divergence is reported.
- **forward** — delete a file `README.md` links to; absence is reported.
- **forward control** — name the new module in the document; the report is silent.
- **adversarial** — a repository with no architecture document at all; **silent**,
  and nothing is demanded.
- **adversarial** — pre-existing drift the task did not cause; counted, **not**
  obligated.
- **adversarial** — a document naming a path that still exists; **silent**.
- **adversarial** — a third-party import (`import os`, `import pytest`); **not**
  an architecture edge, so not a module the map must name.
- **adversarial** — a design note naming a module; documentation for the absence
  check, but **not** the map, so it cannot discharge divergence.

*Corrected while building.* An earlier draft of this list promised that a path
inside a fenced code block showing example output would be ignored. The built
check does something stronger and simpler: absence only ever considers paths
**this task removed**, so a path that never existed in the repository is never
examined at all, fenced or not. Stripping fences was rejected because a fenced
directory tree is the commonest way a repository documents its own structure,
and dropping it would have missed the main case.

## 9. Phasing

1. `core/atlas.py` — source model, document model, reflexion. Tests above. No wiring.
2. `ARCHITECTURE.md` generation, and the drift lines in `end_report`, report-only.
3. The edit-time neighbourhood brief through `PreToolUse`, first-touch only.
4. Measure the rate on the corpus before any of it becomes a discharging obligation.

Stopping after (3) is an acceptable outcome. A map that is true, and that the
agent reads before it edits, is worth having even if it never refuses anything.
