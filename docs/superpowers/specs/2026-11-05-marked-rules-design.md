# Rules marked in the code

*2026-11-05. PLAN §13 B, open problem 1, after
[real history](../../../results/rule-groups-history/README.md).*

## Why

The two halves of rule groups were measured separately.

- **Proposals do not find rules in real code.** On 160 quiet co-changes
  from four projects' history, they did no better than a control.
- **Declared rules are acted on.** The dependent was lost in 4 of 50 runs
  against 35 of 50.

So a person has to name the rule, and naming it should cost as little as
possible.

Today it costs a hand-written JSON entry: an id, a description, the files,
and a check whose command must match exactly what the host captures. A
person who knows "this table and that report keep one column order" does
not want to write that.

## Borrowed

Google's IfThisThenThat convention:

```python
# LINT.IfChange(upload_limit)
MAX_UPLOAD_SIZE_MB = 50
# LINT.ThenChange(//docs/api.md:upload_limit)
```

- **Prior art:** Chromium documents it publicly, TensorFlow, TFX, LIT and
  abseil use it, and Chromium's tree carries over a thousand such blocks.
- **Implementation followed:**
  [simonepri/ifttt-lint](https://github.com/simonepri/ifttt-lint) (MIT, Rust,
  an open reimplementation of Google's internal linter). It checks the pairs
  in CI and at commit time.
- **What we add:** we deliver the same pairs to the agent, before its first
  edit of the file and in its end report. No IFTTT tool does that, and it is
  the half measured to work.

A project that already uses the convention gets this with no new
declaration. One that does not can declare a rule with two comments.

## Behaviour

1. **Reading.** A directive is alone on a comment line (`#`, `//`, `--`,
   `;`, `%`, `/* */`, `<!-- -->`), after ifttt-lint's exact-match rule.
   - **Block:** `LINT.IfChange` or `LINT.IfChange(label)` opens one;
     `LINT.ThenChange(targets)` closes it. The target list may continue
     over the comment lines that follow, until `)`.
   - **Targets** are separated by commas:
     - `path` or `path:label`;
     - `:label`, a block in the same file;
     - `//path`, relative to the project root;
     - any other path, relative to the file's folder first, then to the
       root. Real code uses both forms: abseil's `../testing/flagsaver.py`,
       TFX's `tfx/workspace.bzl`.
   - **Ignored:** text after a directive, nested or unclosed blocks and
     directives inside Markdown fences. Each is named as an issue, never
     guessed at.
   - **Bounds:** files over 1 MiB are not read, and at most 64 blocks are
     kept per file.
2. **Before the first edit of a file,** each of its blocks with a target
   that exists adds a line to the existing rule note. It has the same form
   as a declared rule's line:

   > Marked rule upload_limit (config/upload.py lines 1-3) is also kept in
   > docs/api.md:upload_limit. Change them together, or say why one should
   > differ.

   It shares the note's cap of three lines. A block whose targets are all
   missing from the project, such as a Google-internal path, is not said.
3. **After a shell command,** the existing note for files changed through
   the shell covers marked files too. That path used to run only when the
   declarations file exists. Marked files are now also covered when the
   project held a `LINT.ThenChange` when the task opened, which is checked
   once per task. Shell commands in a project with neither still cost
   nothing.
4. **The end report** names a marked rule changed on one side only.
   - **Changed side:** the task's diff from its base has a line inside
     the block, or a deletion there.
   - **Target:**
     - `path:label` counts as changed only if its labelled block changed;
     - a bare `path`, if the file changed at all;
     - `:label`, if that block in the same file changed.
   - **Wording:** "marked rule upload_limit (config/upload.py lines 1-3):
     changed, not docs/api.md:upload_limit".
   - **Without a base,** changed falls back to the file being touched.
5. **Proposals** treat files a block joins as already declared together,
   as they do for JSON declarations.
6. **`ep_milestones --marked`** lists every marked rule in the project,
   with its targets and whether each was found, plus the issues. It is how
   a person sees what is declared and finds a broken target.

## Not in scope

- **No blocking.** As with declared rules, the note informs; it never
  refuses an edit or completion.
- **No `NO_IFTTT` escape hatch,** since nothing blocks.
- **No checks.** A marked rule carries none. Declaring one with checks
  stays in `elevenpowers.milestones.json`.
- **No reverse lookup** when editing a target file. Each side declares its
  own block, as the convention intends.

## Evidence before claims

- **Tests** run every behaviour both ways, with mutants killed.
- **A real project:** abseil-py, which already marks a rule in
  `absl/flags/_flagvalues.py`. It is cloned, a task opened, and the brief
  for that file must name `absl/testing/flagsaver.py:flag_override_parsing`.
  A file without markers must get no marked note.
- **No claim of a new benefit:** the note's delivery is the measured path;
  the inline declaration is a new way into it.
