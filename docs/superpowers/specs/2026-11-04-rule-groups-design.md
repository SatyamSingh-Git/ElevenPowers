# Rule groups: discover, certify, ground

2026-11-04. PLAN §13 B, open problem 1, left-behind dependents. The user
asked for the design to be built and delegated every decision. The calls
below are the builder's, marked as such.

## Why

20 of the 31 v3 losses were one rule kept in two files, with the agent
changing one. Detectors that warn on every edit are noise: shared tokens
warn on 73–88% of stages that need nothing. NVIDIA Auto-Ontology's loop
avoids that noise:

- a machine **discovers** candidates;
- a person **certifies** them once;
- agents are **grounded** only in what was certified.

The [$0 spike](../../../results/multistage-v3/discover/README.md) found that
50 proposals per project, made before any change, cover 20 of 51 never-read
dependents. The control covers 11, and random 3.9.

## What gets built

1. **Discover**: `ep_milestones.py --propose [--limit N] [--json]`.
   - Ranks pairs of files that carry the same rule: functions in different
     non-test source files, scored by the rarity-weighted tokens they share,
     normalised by size. This is the spike's measured method, moved into
     `core/milestones/propose.py`.
   - Each proposal shows the two files, the two functions and the shared
     tokens as its reason, plus a ready-to-edit milestone entry.
   - It never writes the declaration file; certifying is the person's step.
   - Pairs already declared together in one milestone are not proposed
     again.
2. **Certify**: the person copies the entries they accept into
   `elevenpowers.milestones.json`. The file and its schema already exist,
   so nothing is built for this step.
3. **Ground, before an edit:** the once-per-file brief before an agent
   edits a file (PreToolUse) adds the declared rules naming that file, if
   they name other files too. For each, it gives the rule's id and
   description and the other files, with the instruction to keep them
   consistent.
4. **Ground, at completion:** the end report (to the person) names each
   declared rule whose files this task changed only partly.

## Decided by the builder

- **Python only in this version** (the spike measured Python). Other source
  files are counted and reported as not examined, never silently skipped.
- **Bounded.** The project's source scan sets the file budget, and
  `--seconds` sets the time. A token held by more than 200 functions is
  skipped and reported, because such tokens weigh little and cost
  quadratic time. Any bound reached marks the result incomplete.
- **The agent never sees a proposal.** Only declared rules reach it, so
  their precision is a person's.
- **Nothing blocks.** Both groundings inform. PLAN §10 and B8 record what
  blocking on an unmeasured signal cost.
- **Proposed entries need a check,** because the schema requires one. The
  project's declared `tests` command is filled in when there is one.
  Otherwise the entry says so and is left for the person to complete.
- **No memory of rejected pairs in this version.** A review is cheap and
  rare: one review at stage 0 matched reviewing before every stage.

## Not claimed

That an agent acts on the brief: delivered briefs were ignored in v3. That
needs a paid, pre-registered run (PLAN §13 B, open problem 2). This version
makes the certified signal exist and reach both the agent and the person.
