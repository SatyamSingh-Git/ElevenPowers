# One set of project rules, delivered in every agent

*Written 2026-11-10. A build, not an experiment. Approved in conversation as
"use the instructions people already write, at the moment they apply", then
narrowed by what Claude Code already does (below).*

## Intent

ElevenPowers' measured benefit is a rule shown at the moment it applies,
worded as an instruction:
- 4 of 50 dependents lost with a declared rule, against 35 of 50 without;
- 5 of 60 against 23 of 60 when the rule is an instruction and the request
  pulls the other way.

Today that only works for rules written in ElevenPowers' own
`elevenpowers.milestones.json`, which almost no project has. Projects
already write scoped rules, but in each agent's own format, and each agent
reads only its own. This feature reads the formats a repository already
has, and delivers each rule where the running agent would not otherwise see
it, through the delivery path ElevenPowers already uses for its rule note.

## What already exists (read 2026-11-10, official docs)

| Format | Scoping | Who loads it natively, and when |
|---|---|---|
| `.claude/rules/**/*.md` | `paths:` (YAML list or comma string) | Claude Code: on Read, Write or Edit of a matching file ([memory](https://code.claude.com/docs/en/memory.md)) |
| `.cursor/rules/**/*.mdc` | `globs:` (comma-separated); `alwaysApply`; `description` | Cursor: "auto-attached when a matching file is in context" ([rules](https://cursor.com/docs/context/rules)) |
| `.github/instructions/**/*.instructions.md` | `applyTo:` (comma-separated) | Copilot: requests about matching files; on GitHub.com, cloud agent and code review only ([docs](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions)) |
| `AGENTS.md` in a subfolder | the folder; "the closest AGENTS.md to the edited file wins" | Cursor, Copilot and Codex. Claude Code reads `CLAUDE.md`, not `AGENTS.md` ([agents.md](https://agents.md/)) |

**So the gap is narrower than first pitched.** Claude Code already delivers
its own scoped rules at the point of use. Duplicating that would add noise,
not value. What no host does is read **another** host's rules:
- Claude Code never sees a Cursor rule, a Copilot instruction, or a nested
  `AGENTS.md`.
- Gemini CLI sees none of them unless configured.

A team using two agents writes its rules once, in one of these formats, and
the other agent never sees them.

## Goals

1. **Read four formats** from the project:
   - `.claude/rules/**/*.md` with `paths:`;
   - `.cursor/rules/**/*.mdc` with `globs:`;
   - `.github/instructions/**/*.instructions.md` with `applyTo:`;
   - `AGENTS.md` in any subfolder below the project root.
2. **For a file the agent is about to change** (Edit brief) or has just
   changed through the shell (post-command note), deliver every rule whose
   scope matches it, once per file per task. This is exactly when the
   declared-rule note is delivered today. `rules_naming(root, path)` gains
   the new rules, so both paths and every host adapter get them unchanged.
3. **Skip what the running host loads natively**, so nothing arrives twice:

   | host | skipped |
   |---|---|
   | Claude Code | `.claude/rules` |
   | Cursor | `.cursor/rules` and `AGENTS.md` |
   | Copilot | `.github/instructions` and `AGENTS.md` |
   | Codex | `AGENTS.md` |
   | Gemini CLI | nothing |
4. **Deliver the person's own text,** never rewritten: "Project rule from
   `.cursor/rules/api.mdc` (applies to `src/api/**`): <text>". It is cut to
   600 characters, with the source path named so the agent can read the
   rest. At most 3 rules per file, in a fixed order: the declared rule
   first, then by source path.
5. **One-line rule adding** (item 2 of the plan):
   - `ep_milestones --add-rule A B [--why "..."]` appends a declared rule.
   - Its description is the confirmed instruction form, "`A` and `B` must
     stay consistent: change both in the same task", plus the reason when
     given.
   - It carries the project's declared tests command as its check. It
     refuses a missing file, a repeated pair, and a project with no tests
     command (an entry needs a check).

## Non-goals

- **Root `AGENTS.md` / `CLAUDE.md`.** They are not scoped. Hosts load them
  at start, and re-delivering a whole file at every first edit is the kind
  of note nobody reads.
- **Rules with no path scope:**
  - Cursor `alwaysApply: true` rules;
  - "Apply Intelligently" rules (description only);
  - Copilot's repository-wide `copilot-instructions.md`;
  - `.claude/rules` files without `paths`.

  Hosts load these at start, or by the model's own choice.
- **Checking whether a free-text rule was followed.** It cannot be computed,
  so nothing about free-text rules is said at the end. (An end-report
  listing of delivered rules was considered and dropped: it tells the
  person nothing they can act on.)
- **Writing or converting any rule file.** This is read-only.

## Anti-goals: a failure even if it technically works

- **A rule delivered twice in Claude Code,** once natively and once by us.
- **A Cursor or Copilot file the parser misreads,** so a rule is delivered
  for files outside its scope. An unparsable front matter or glob is
  reported by `ep_doctor` / `ep_milestones --marked`-style listing and the
  rule is not delivered, rather than guessed.
- **A slower edit.** The rule files are read once per task and cached in the
  ledger, like `marked`. Matching is per edited file, against compiled
  patterns.

## Constraints

- **Python 3.11 floor, standard library only.**
  - **Glob semantics:** `**`, `*`, `?`, `[...]`, `{a,b}` braces and a
    leading `/` anchor.
  - **Borrowed:** CPython 3.13's `glob.translate` (PSF licence) defines the
    semantics. 3.11 lacks it, so a minimal translator is vendored, and tests
    check it against `glob.translate` on 3.13 for the documented examples.
  - **Brace expansion:** borrowed from Claude Code's documented behaviour.
- **Front matter:** a minimal reader for `key: value`, `key: [a, b]`, quoted
  values and YAML block lists. Anything else counts as an unparsable rule,
  reported and not delivered. There is no YAML dependency.
- **Project independence.** Nothing names a repository. A project whose rule
  folder is elsewhere is reported as a coverage limit, not searched for.
- **Host identity** comes from the adapter's `_ep_platform`; a direct Claude
  invocation is `claude`.

## Decided here (my calls, made under "decide things yourself")

- 600 characters and 3 rules per file. The note shows the declared rule's
  first 200 characters; a person's rule is longer and denser.
- Nested `AGENTS.md`: only the closest one to the file, below the root,
  matching the format's own rule.
- No rewording of a person's text into the instruction form. The confirmed
  effect is for generated descriptions. Rewriting someone's rule could
  change its meaning.

## Left to the builder

- Where the parsed rules are cached. The ledger, as `marked` is, is the
  obvious place.
- The exact listing command for unparsable rules.

## Decided after the builder check (2026-11-10)

A fresh reader planned from this document and asked five questions. Each was
checked against the code, and settled as follows.

1. **The rule note does not reach three of the five hosts today.** This is
   an existing defect, and it is fixed first, as **Part 0**.
   - Cursor's and Copilot's `render()` drop `additionalContext` on
     `preToolUse` (`core/hosts/cursor.py:62-63`, `copilot.py:45-46`). But
     `on_pre_tool` still adds the file to `ledger.briefed`, so the note is
     lost and recorded as delivered. Even the post-shell note then skips it.
   - Codex's `apply_patch` becomes `Patch`. `on_pre_tool` returns before the
     brief, and the post-tool `Patch` path never asks `rules_naming`.
   - **Fix:** a file is marked briefed only when the brief is actually
     delivered.
     - On a host that drops pre-tool context, the brief rides the
       `PostToolUse` of the edit, which every adapter delivers.
     - Codex's patched files get the same post-edit brief.
     - Tests cover each adapter, both ways.
2. **The skip table is narrowed to what is verified.**
   - **Claude Code skips `.claude/rules`.** This is documented.
   - **Codex skips only `AGENTS.md` files on the chain from the root to its
     working directory.** That is what it collects, by this repository's own
     source-read (`docs/research/hosts/codex-cli.md`). A deeper `AGENTS.md`
     is delivered to Codex.
   - **Cursor and Copilot skip their own formats.** The CLI adapters are not
     verified to load them, so this is a stated coverage limit: a possible
     miss is preferred to a likely duplicate until a probe shows otherwise.
3. **Native skips apply to the Edit brief only, never to the post-shell
   note.** Claude Code loads `paths:` rules on Read, Write or Edit, not for a
   file a script wrote. A guaranteed miss is worse than a possible duplicate.
4. **Anchoring follows each format's own documentation.**
   - **Cursor:** `*.ts` is the root only.
   - **Copilot:** `*.py` is the current directory only. `applyTo` is relative
     to the repository root.
   - **Claude Code:** contrasts `*.md` with "`/*.md` (base directory only)",
     so a pattern without a slash matches at any depth, and a leading `/`
     anchors it.
   - So one translator takes a `floating` flag, set for `.claude/rules` only.
5. **`--add-rule`:**
   - **The file.** It creates `elevenpowers.milestones.json` when missing,
     and says so. Creating it does not switch on automatic advice, which
     still needs `milestone_advice` enabled (`core/milestones/automatic.py`,
     `policy`).
   - **The check.** The tests command is `config.command_for('tests')`,
     discovered or explicit, the same one `--propose` writes into its
     entries.

**The cap.** Declared and marked rules keep their 3 lines. Scoped rules add
at most 2, so a file's brief is at most 5 rules: declared, then marked, then
scoped by source path.

**Order of work.** No code changes until the running Sonnet 5 batch
finishes, because its seal pins `core/` and `plugin/bin/`. Part 0 lands
first, as its own commit. It is a fix to the measured note, on three hosts.

## How it will be checked (not a research programme)

1. **Tests through the real hook,** both directions, for each format:
   - a matching edit gets the rule;
   - a non-matching edit does not;
   - the host-native format is skipped;
   - an unparsable rule is reported, not delivered.

   Mutation-checked.
2. **A $0 rehearsal** on a scratch project carrying all four formats, under
   the Claude and Gemini adapters.
3. **One real-host probe,** a few cents. A Claude Code session edits a file
   covered by a Cursor rule and quotes the rule it received, with a control
   project that has no Cursor rule. This is the same probe shape as the
   shell-path repair.
