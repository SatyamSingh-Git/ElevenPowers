# Other agents' rules, delivered in every agent: checks

A build, not an experiment
([design](../../docs/superpowers/specs/2026-11-10-rules-from-every-agent-design.md),
[plan](../../docs/superpowers/plans/2026-11-10-rules-from-every-agent.md)).
These are the checks that it reaches the agent.

## $0 rehearsal: passed 3 of 3 ([`rehearse.py`](rehearse.py), [output](rehearsal.json))

A scratch project carries all four formats. It is driven through the real
launchers: `plugin/bin/ep_hook.py` for Claude Code, and `plugin/bin/ep_host.py
gemini` for Gemini.

- **Claude Code**, editing `src/api/handler.ts`, gets the Cursor and Copilot
  rules and not its own `.claude/rules`.
- **Gemini** gets the first two by source, the Claude rule included.
- **A non-matching file** gets no project rule on either host.

**The first run failed, and the fault was in the rehearsal.** It called the
hook once per tag it checked for. The first call briefed the file, so every
later call was rightly silent. Read directly, `rules_naming` and the raw hook
output were correct. The script now calls the hook once per file.

## Real-host probe: passed ([`probe.py`](probe.py), [output](probe.json))

One Claude Code turn per arm, Sonnet 5.5 at medium effort, on a v3 workspace
(`payroll_lite` stage 2). **$0.13.**

| arm | the project has | the agent's tools | its reply |
|---|---|---|---|
| `rule` | a `.cursor/rules/overtime.mdc` scoped to the edited file, carrying the marker `PROBE-4417` | Read, Edit; it never opened `.cursor` | quoted the rule word for word, marker included |
| `control` | no rule | Read, Edit | `NONE` |

Claude Code does not read Cursor rules itself. So the marker reached the
model only through ElevenPowers' note.

## Tests

- **`tests/test_scoped_rules.py`, 31 tests:**
  - the glob translator against CPython 3.13's `glob.translate`;
  - each format read;
  - native skips on edit, and none after the shell;
  - only the closest `AGENTS.md`;
  - the 600-character cut;
  - Windows paths;
  - unreadable rules listed and not delivered;
  - the `--scoped` listing;
  - through the hook.

  Mutation check: 13 of 13 killed.
- **`tests/test_rule_delivery_hosts.py`, 6 tests:** the note reaching Cursor,
  Copilot and Codex. Mutation check: 5 of 6 killed, and the survivor is
  equivalent.
- **`--add-rule`, 5 tests in `tests/test_rule_groups.py`.** Mutation check,
  with the listing: 8 of 8 killed.

## Bounds

- **Cursor and Copilot CLIs are assumed to load their own formats,** so those
  are skipped on edit. This is from their IDE and GitHub.com docs, not
  checked on the CLIs.
- **Codex is assumed to load `AGENTS.md` from the root to its working
  directory only.** That is from this repository's source-read of Codex.
- **Only the Claude Code path was probed on a real host.**
