# Rules From Every Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The rule note reaches every host, then also carries Cursor, Copilot, Claude and nested `AGENTS.md` scoped rules, and `ep_milestones --add-rule` declares a rule in one line.

**Architecture:**
- **Part 0** fixes delivery. A brief is marked delivered only when a host can carry it, and hosts that drop pre-tool context get it on the edit's `PostToolUse`.
- **Part 1** adds `core/milestones/scoped.py`, which reads four rule formats. `rules_naming` appends their lines, so both existing delivery paths carry them.
- **Part 2** adds `add_rule` behind a CLI flag.

**Tech Stack:** Python 3.11+, standard library only, pytest.

**Spec:** `docs/superpowers/specs/2026-11-10-rules-from-every-agent-design.md`. Read its "Decided after the builder check" section first.

## Global Constraints

- **Python and dependencies:** Python 3.11 floor, standard library only, no YAML dependency.
- **Read-only:** never write or convert a rule file.
- **Project independence:** nothing names a repository.
- **Limits:** a scoped rule's text is cut to 600 characters and names its source. A file gets at most 3 declared or marked lines plus at most 2 scoped ones.
- **Native skips** apply to the Edit brief only, never to the post-shell note.
- **Order of work:** do not change `core/` or `plugin/bin/` while a sealed batch runs. `E:/ep-runs/rule-mandate-sonnet5-2026-11-10` must have all 80 launched slots finished first.

## Review Focus

1. A Windows path (`src\api\x.ts`) checked against `src/api/**`: it must match. Normalise to `/` before matching. The test belongs to Task 2.
2. A rule file saved with CRLF endings or a UTF-8 BOM: it must parse the same as LF. Task 2.
3. A rule body over 600 characters: it is cut at 600 and ends `… (rest in <source>)`. Task 2.
4. Front matter that does not parse, or a `[` pattern that is not a valid bracket expression: nothing is delivered for that rule, it is listed by `ep_milestones --scoped` with the reason, and no exception escapes the hook. Task 2 and Task 3.
5. A file briefed by the Edit path is not briefed again by the shell path, and the reverse also holds. That keeps the existing `briefed` contract, and it is tested across the new post-edit path. Task 1.

---

### Task 1: The rule note is delivered on every host (Part 0)

**Files:**
- Modify: `core/hook.py`:
  - `on_pre_tool` (lines 215-274);
  - `on_post_tool` (277-301);
  - `_on_post_tool`'s Patch branch (344-361).
- Test: `tests/test_rule_delivery_hosts.py` (new).

**Interfaces:**
- Produces:
  - `PRE_EDIT_CONTEXT: frozenset[str] = frozenset({'claude', 'gemini'})` in `core/hook.py`: the platforms whose adapter delivers `additionalContext` on a pre-tool event.
  - `_brief(root: Path, ledger: Ledger, path: str) -> str`: the rules-plus-neighbourhood text for one file, or `''`. It does not mark anything. It moves the existing expression out of `on_pre_tool`, because two callers now need it.
- Behaviour:
  - In `on_pre_tool`, compute and mark the brief only when `payload.get('_ep_platform', 'claude') in PRE_EDIT_CONTEXT`.
  - In `on_post_tool`, after an edit, brief each edited path not yet in `ledger.briefed` when either the platform is not in `PRE_EDIT_CONTEXT`, or the tool is `Patch`. Mark it, and emit one `PostToolUse` `additionalContext`.
  - For `Patch`, the edited paths are `hosts.edits.after`'s `changed`.

- [ ] **Step 1: Write the failing tests.** Each test drives the real adapter through `python plugin/bin/ep_host.py PLATFORM EVENT`, JSON on stdin and stdout, as `tests/test_advice_emission.py` does. Use the platform's native event names: `preToolUse` and `postToolUse` for Cursor and Copilot, and `PreToolUse` and `PostToolUse` for Codex. For Claude, use `plugin/bin/ep_hook.py`, as `tests/test_rule_groups.py::_hook` does. Use that test's `declared(tmp_path)` project, where `app/money.py` is declared with `app/services/pricing.py`.
  - `test_cursor_gets_the_rule_after_the_edit_not_lost_before_it`:
    - the cursor `preToolUse` output has no `additional_context`;
    - the cursor `postToolUse` output for the same edit contains `'app/services/pricing.py'` and `'lodging-tax'`.
  - `test_copilot_gets_the_rule_after_the_edit`: the same, with Copilot's `additionalContext` key.
  - `test_codex_patch_gets_the_rule_after_the_patch`: an `apply_patch` changing `app/money.py`. Its `PostToolUse` `hookSpecificOutput.additionalContext` contains `'lodging-tax'`.
  - `test_claude_still_gets_it_before_the_edit_and_not_again_after`: the pre-tool brief contains `'lodging-tax'`, and the post-tool output does not.
  - `test_a_file_briefed_after_the_edit_is_not_briefed_again_by_the_shell`: run the cursor post-edit, then the shell note after a Bash command, with no second `'lodging-tax'`.
- [ ] **Step 2: Run** `python -m pytest tests/test_rule_delivery_hosts.py -q`. Expected: the four non-Claude tests FAIL, and the Claude one passes. It is the forward control.
- [ ] **Step 3: Implement** the interfaces above in `core/hook.py`.
- [ ] **Step 4: Run** the new file, `tests/test_rule_groups.py`, `tests/test_marked_rules.py` and `tests/test_rule_gate.py`. Expected: all PASS.
- [ ] **Step 5: Mutation check.** Each of these must turn a test red:
  - `PRE_EDIT_CONTEXT` widened to include `cursor`;
  - the post-edit brief removed;
  - the `briefed` mark removed from the post-edit path;
  - the `Patch` brief removed.
- [ ] **Step 6: Commit** `hook: the rule note reaches Cursor, Copilot and Codex - after the edit where a host drops pre-edit text`.

### Task 2: Read scoped rules from four formats

**Files:**
- Create: `core/milestones/scoped.py`.
- Modify: `core/milestones/definition.py`. `rules_naming` gains the parameters below and appends scoped lines.
- Modify: `core/hook.py`. Pass the platform and the kind to `rules_naming` from `_brief` (`'edit'`) and from `_rule_notes_after_shell` (`'shell'`).
- Test: `tests/test_scoped_rules.py` (new).

**Interfaces:**
- Produces, in `core/milestones/scoped.py`:
  - `translate(pattern: str, floating: bool) -> re.Pattern | None`. Glob to a regex over `/`-separated relative paths:
    - `**` is any number of segments, `*` and `?` stay within a segment, and `[...]` is kept;
    - `{a,b}` is expanded first;
    - a leading `/` anchors;
    - without a slash, `floating=True` matches at any depth;
    - it returns `None` for an invalid bracket.

    It follows CPython 3.13 `glob.translate(recursive=True, include_hidden=True)`.
  - `frontmatter(text: str) -> tuple[dict, str] | None`. It returns the fields and the body, or `None` when the block does not parse. It accepts:
    - a BOM;
    - CRLF line endings;
    - `key: value`, with or without quotes;
    - `key: [a, b]`;
    - a YAML block list (`- item`).
  - `read(root: Path) -> tuple[list[dict], list[str]]`. It returns the rules and the issues. Each rule is `{'source': str, 'format': 'claude'|'cursor'|'copilot'|'agents', 'patterns': list[str], 'body': str}`:
    - `claude`: `.claude/rules/**/*.md` with `paths`;
    - `cursor`: `.cursor/rules/**/*.mdc` with `globs`, not `alwaysApply: true`;
    - `copilot`: `.github/instructions/**/*.instructions.md` with `applyTo`;
    - `agents`: every `AGENTS.md` below the root, with `patterns == [<folder>/**]`.

    A comma-separated string is split into its patterns.
  - `lines_for(root: Path, path: str, platform: str, kind: str, cwd: str = '') -> list[str]`. Each line reads ``Project rule from {source} (applies to {', '.join(patterns)}): {body}``, with the body cut to 600 characters and ending `… (rest in {source})` when cut. Order is by source path, with at most 2 lines. Only the closest `AGENTS.md` to `path` is used.
    - **Skips, for `kind == 'edit'` only:**
      - `claude` skips the `claude` format;
      - `cursor` skips `cursor` and `agents`;
      - `copilot` skips `copilot` and `agents`;
      - `codex` skips an `agents` rule whose folder is an ancestor of, or equal to, `cwd`.
- Changes `rules_naming(root, path, platform='claude', kind='edit', cwd='') -> str`. It returns the existing lines, cut to 3, followed by `lines_for(...)`.

- [ ] **Step 1: Write the failing tests** in `tests/test_scoped_rules.py`:
  - `test_translate_matches_cpython_on_the_documented_examples`, for `**/*.ts`, `src/**/*.tsx`, `*.ts`, `src/*.py`, `**/subdir/**/*.py` and `src/**/*.{ts,tsx}`:
    - with `floating=False`, it agrees with `glob.translate` on Python 3.13, using `pytest.importorskip`-style skipping below 3.13;
    - on 3.11 it holds the expected matches as literals, for example `translate('*.ts', False)` matches `a.ts` and not `src/a.ts`.
  - `test_a_claude_pattern_without_a_slash_matches_at_any_depth`: `translate('*.md', True)` matches `docs/a.md`, and `translate('/*.md', True)` does not.
  - `test_an_invalid_bracket_matches_nothing_and_is_reported`.
  - `test_crlf_and_bom_front_matter_parse_like_lf`.
  - `test_unparsable_front_matter_is_an_issue_not_a_rule`.
  - `test_each_format_is_read`: one fixture project with all four formats, and the 4 rules come back with the right `format` and `patterns`.
  - `test_a_cursor_always_apply_rule_is_not_scoped`.
  - `test_a_windows_path_matches_a_slash_pattern`: `lines_for(root, 'src\\api\\x.ts', 'claude', 'edit')` returns the Cursor rule for `src/api/**`.
  - `test_a_long_rule_is_cut_and_names_its_source`: a 1,000-character body gives a line whose body part is ≤600 characters and ends `(rest in .cursor/rules/api.mdc)`.
  - `test_only_the_closest_agents_md_is_used`.
  - `test_claude_skips_its_own_rules_on_edit_but_not_after_the_shell`.
  - `test_codex_skips_an_agents_md_it_already_loaded`, with `cwd` equal to that folder, but not a deeper one.
  - `test_through_the_hook_claude_is_told_a_cursor_rule_before_editing`, end to end with `ep_hook.py PreToolUse`. A non-matching file gets no rule. This is the adversarial row.
- [ ] **Step 2: Run** `python -m pytest tests/test_scoped_rules.py -q`. Expected: FAIL on import.
- [ ] **Step 3: Implement** `core/milestones/scoped.py` and the `rules_naming` change. Pass the platform and `kind` through from `core/hook.py`. `cwd` is the payload's `cwd`, relative to the root.
- [ ] **Step 4: Run** the new file and every `tests/test_rule*.py` and `tests/test_marked_rules.py`. Also run it under `py -3.11`. Expected: all PASS.
- [ ] **Step 5: Mutation check.** Each must go red:
  - `floating` ignored;
  - the BOM strip removed;
  - the 600-character cut removed;
  - the Claude edit skip removed;
  - the shell exception removed, so the skip applies on `shell`;
  - the closest-`AGENTS.md` choice changed to the farthest.
- [ ] **Step 6: Commit** `milestones: deliver Cursor, Copilot, Claude and nested AGENTS.md rules where the host would not`.

### Task 3: List scoped rules and add a rule in one line

**Files:**
- Modify: `plugin/bin/ep_milestones.py`. Add the flags `--scoped` and `--add-rule A B` with `--why TEXT`.
- Modify: `core/milestones/definition.py`. Add `add_rule`.
- Test: `tests/test_scoped_rules.py` (listing), `tests/test_rule_groups.py` (`add_rule`).

**Interfaces:**
- Consumes: `scoped.read(root)` from Task 2.
- Produces: `add_rule(root: Path, a: str, b: str, why: str = '') -> dict`. It returns the entry it wrote:
  - `id` is `rule-{stem a}-{stem b}`, made unique the way `propose` does;
  - `description` is ``"`{a}` and `{b}` must stay consistent: change both in the same task."``, followed by `" " + why` when given;
  - `inputs` is `[a, b]`;
  - `checks` is the test suite from `load_config(root).command_for('tests')`.

  It creates `elevenpowers.milestones.json` (`{'schema': 1, 'milestones': [...]}`) when the file is missing. It raises `ValueError` for:
  - a missing file;
  - `a == b`;
  - a pair already declared together;
  - no tests command.

- [ ] **Step 1: Write the failing tests:**
  - `test_add_rule_writes_the_instruction_with_the_tests_command`;
  - `test_add_rule_creates_the_declarations_when_missing`;
  - `test_add_rule_refuses_a_missing_file_a_repeat_and_no_tests_command` (three asserts with `pytest.raises(ValueError)`);
  - `test_the_added_rule_reaches_the_brief`: after `add_rule`, `rules_naming(root, a)` names `b`;
  - `test_scoped_listing_names_rules_and_unparsable_files`: the CLI `--scoped --json` lists each rule's source and patterns, and the issues.
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Implement** `add_rule` and both flags. `--add-rule` prints the entry and the file path. On `ValueError` it prints the reason and exits 2.
- [ ] **Step 4: Run** the files from Step 1 and `tests/test_rule_groups.py`. Expected: PASS.
- [ ] **Step 5: Mutation check.** Each must go red:
  - the repeat check removed;
  - the tests-command check removed;
  - `description` reverted to the template.
- [ ] **Step 6: Commit** `ep_milestones: --add-rule in one line, --scoped lists other agents' rules`.

### Task 4: Docs, map, rehearsal, probe and full suite

**Files:**
- Modify:
  - `the-guide/milestones.md`, a section "Rules other agents already have";
  - `README.md`, item 9 of what it does today: one sentence on reading other agents' rule files;
  - `docs/status.md`;
  - `architecture/index.html`, the milestones node, and a new `scoped` node with edges `hook→milestones` (already present) and `milestones→scoped`, plus `meta.updated` and the changelog.
- Create: `results/scoped-rules/rehearse.py` and `results/scoped-rules/probe.py`, with their outputs.

- [ ] **Step 1: $0 rehearsal.** In a scratch project holding all four formats, through `plugin/bin/ep_hook.py` under the `claude` and `gemini` platforms:
  - each matching edit is briefed with the expected sources;
  - Claude does not get `.claude/rules` on edit;
  - a non-matching file gets nothing.

  Save the result to `rehearsal.json`.
- [ ] **Step 2: Real-host probe,** a few cents, with Sonnet 5.5 at medium effort, the same command shape as `results/rule-groups-acted-on/shell_probe.py`. One Claude Code turn edits a file covered only by a `.cursor/rules` rule, then quotes any project rule it received.
  - **Control:** the same project without the rule must answer `NONE`.
  - Save both transcripts.
- [ ] **Step 3: Run** `python architecture/check.py --render`. Expected: `OK`.
- [ ] **Step 4: Run the full suite** with `python -m pytest -q`. Expected: 0 failed.
- [ ] **Step 5: Commit and push.** Then watch hosted CI on Linux and Windows, Python 3.11 and 3.13.
