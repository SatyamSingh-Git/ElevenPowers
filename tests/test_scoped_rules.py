"""Rules other agents already have, delivered where the running agent would not see them.

Claude Code loads `.claude/rules` itself on Read/Write/Edit of a matching file, but never a
Cursor rule, a Copilot instruction or a nested AGENTS.md; the other hosts are the mirror image.
docs/superpowers/specs/2026-11-10-rules-from-every-agent-design.md
"""
import re
import subprocess
import sys

import pytest

from core.milestones.scoped import frontmatter, lines_for, read, translate

CASES = {
    '**/*.ts': (['a.ts', 'src/a.ts', 'src/x/y/a.ts'], ['a.tsx', 'src/a.js']),
    'src/**/*.tsx': (['src/a.tsx', 'src/x/a.tsx'], ['a.tsx', 'lib/a.tsx']),
    '*.ts': (['a.ts'], ['src/a.ts']),
    'src/*.py': (['src/a.py'], ['src/x/a.py', 'a.py']),
    '**/subdir/**/*.py': (['subdir/a.py', 'x/subdir/y/a.py'], ['x/a.py']),
    'src/**': (['src/a.py', 'src/x/y.py'], ['lib/a.py']),
}


@pytest.mark.parametrize('pattern', CASES)
def test_translate_matches_the_documented_examples(pattern):
    compiled = translate(pattern, False)
    good, bad = CASES[pattern]
    assert all(compiled.fullmatch(p) for p in good), pattern
    assert not any(compiled.fullmatch(p) for p in bad), pattern


@pytest.mark.skipif(sys.version_info < (3, 13), reason='glob.translate is 3.13+')
@pytest.mark.parametrize('pattern', CASES)
def test_translate_agrees_with_cpython(pattern):
    import glob
    ours, theirs = translate(pattern, False), re.compile(glob.translate(pattern, recursive=True, include_hidden=True))
    for path in sum(CASES[pattern], []):
        assert bool(ours.fullmatch(path)) == bool(theirs.match(path)), (pattern, path)


def test_braces_expand():
    compiled = translate('src/**/*.{ts,tsx}', False)
    assert compiled.fullmatch('src/a/b.ts') and compiled.fullmatch('src/b.tsx') and not compiled.fullmatch('src/b.js')


def test_a_claude_pattern_without_a_slash_matches_at_any_depth():
    assert translate('*.md', True).fullmatch('docs/a.md')
    assert translate('*.md', True).fullmatch('a.md')
    assert not translate('/*.md', True).fullmatch('docs/a.md')
    assert translate('/*.md', True).fullmatch('a.md')
    assert not translate('*.md', False).fullmatch('docs/a.md')


def test_an_invalid_bracket_matches_nothing():
    assert translate('src/[abc.py', False) is None


def test_crlf_and_bom_front_matter_parse_like_lf():
    lf = '---\nglobs: src/api/**\nalwaysApply: false\n---\nUse the client.\n'
    crlf = '﻿' + lf.replace('\n', '\r\n')
    assert frontmatter(lf) == frontmatter(crlf) == ({'globs': 'src/api/**', 'alwaysApply': 'false'}, 'Use the client.')


def test_front_matter_lists_both_ways():
    block = '---\npaths:\n  - "src/**/*.ts"\n  - lib/*.ts\n---\nbody\n'
    inline = "---\npaths: ['src/**/*.ts', lib/*.ts]\n---\nbody\n"
    assert frontmatter(block)[0] == frontmatter(inline)[0] == {'paths': ['src/**/*.ts', 'lib/*.ts']}


def test_unparsable_front_matter_is_none():
    assert frontmatter('---\nglobs src/**\n---\nbody') is None
    assert frontmatter('---\nglobs: src/**\nno end marker') is None


def write(root, files):
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding='utf-8')
    return root


FOUR = {
    '.claude/rules/api.md': '---\npaths:\n  - "src/api/**"\n---\nClaude: validate every request body.\n',
    '.cursor/rules/api.mdc': '---\ndescription: api\nglobs: src/api/**\nalwaysApply: false\n---\nCursor: use the shared client.\n',
    # Cursor ignores globs when alwaysApply is true; the host loads it every session.
    '.cursor/rules/style.mdc': '---\nglobs: src/**\nalwaysApply: true\n---\nAlways: be kind.\n',
    'AGENTS.md': 'Root: hosts load this at start; never re-delivered.\n',
    '.github/instructions/api.instructions.md': '---\napplyTo: "src/api/**/*.ts"\n---\nCopilot: keep handlers pure.\n',
    'src/api/AGENTS.md': 'Agents: never call the database from a handler.\n',
    'src/AGENTS.md': 'Agents (outer): prefer small modules.\n',
    'src/api/handler.ts': 'export {}\n',
    'lib/util.ts': 'export {}\n',
}


def test_each_format_is_read(tmp_path):
    rules, issues = read(write(tmp_path, FOUR))
    by = {r['source']: r for r in rules}
    assert issues == []
    assert by['.claude/rules/api.md']['format'] == 'claude' and by['.claude/rules/api.md']['patterns'] == ['src/api/**']
    assert by['.cursor/rules/api.mdc']['format'] == 'cursor'
    assert by['.github/instructions/api.instructions.md']['patterns'] == ['src/api/**/*.ts']
    assert by['src/api/AGENTS.md']['format'] == 'agents' and by['src/api/AGENTS.md']['patterns'] == ['src/api/**']
    assert '.cursor/rules/style.mdc' not in by, 'always-apply rules are not scoped'
    assert not any('Root:' in r['body'] for r in rules), 'the root AGENTS.md is not scoped'


def test_unparsable_rules_are_issues_not_rules(tmp_path):
    write(tmp_path, {'.cursor/rules/bad.mdc': '---\nglobs src/**\n---\nx\n',
                     '.github/instructions/odd.instructions.md': '---\napplyTo: "src/[x.py"\n---\nx\n'})
    rules, issues = read(tmp_path)
    assert rules == [], 'a rule whose only pattern is invalid scopes nothing'
    assert any('.cursor/rules/bad.mdc' in i for i in issues)
    assert any('src/[x.py' in i for i in issues)


def body(lines):
    return '\n'.join(lines)


def test_claude_is_told_other_agents_rules_and_not_its_own_on_edit(tmp_path):
    root = write(tmp_path, FOUR)
    said = body(lines_for(root, 'src/api/handler.ts', 'claude', 'edit'))
    assert 'Cursor: use the shared client.' in said and 'Copilot: keep handlers pure.' in said
    assert 'Claude: validate' not in said


def test_at_most_two_rules_closest_agents_md_and_order_by_source(tmp_path):
    root = write(tmp_path, {k: v for k, v in FOUR.items() if 'cursor' not in k and 'github' not in k})
    said = lines_for(root, 'src/api/handler.ts', 'claude', 'edit')
    assert len(said) == 1 and 'never call the database' in said[0], 'only the closest AGENTS.md'
    root2 = write(tmp_path / 'b', FOUR)
    assert len(lines_for(root2, 'src/api/handler.ts', 'gemini', 'edit')) == 2


def test_after_the_shell_claude_gets_its_own_rules_too(tmp_path):
    root = write(tmp_path, {'.claude/rules/api.md': FOUR['.claude/rules/api.md'], 'src/api/handler.ts': ''})
    assert lines_for(root, 'src/api/handler.ts', 'claude', 'edit') == []
    assert 'Claude: validate' in body(lines_for(root, 'src/api/handler.ts', 'claude', 'shell'))


def test_cursor_and_copilot_skip_their_own_format_and_agents_md(tmp_path):
    root = write(tmp_path, FOUR)
    cursor = body(lines_for(root, 'src/api/handler.ts', 'cursor', 'edit'))
    assert 'Cursor:' not in cursor and 'Agents:' not in cursor and 'Copilot:' in cursor
    copilot = body(lines_for(root, 'src/api/handler.ts', 'copilot', 'edit'))
    assert 'Copilot:' not in copilot and 'Agents:' not in copilot and 'Cursor:' in copilot


def test_codex_skips_an_agents_md_it_already_loaded_but_not_a_deeper_one(tmp_path):
    root = write(tmp_path, {'src/api/AGENTS.md': FOUR['src/api/AGENTS.md'], 'src/api/handler.ts': ''})
    assert lines_for(root, 'src/api/handler.ts', 'codex', 'edit', cwd='src/api') == []
    assert 'never call the database' in body(lines_for(root, 'src/api/handler.ts', 'codex', 'edit', cwd=''))


def test_a_non_matching_file_gets_nothing(tmp_path):
    root = write(tmp_path, FOUR)
    assert lines_for(root, 'lib/util.ts', 'gemini', 'edit') == []


def test_a_windows_path_matches_a_slash_pattern(tmp_path):
    root = write(tmp_path, FOUR)
    assert 'Cursor:' in body(lines_for(root, 'src\\api\\handler.ts', 'claude', 'edit'))


def test_a_long_rule_is_cut_and_names_its_source(tmp_path):
    root = write(tmp_path, {'.cursor/rules/api.mdc': '---\nglobs: src/**\n---\n' + 'x' * 1000 + '\n',
                            'src/a.py': ''})
    [line] = lines_for(root, 'src/a.py', 'claude', 'edit')
    text = line.split('): ', 1)[1]
    assert text.endswith('… (rest in .cursor/rules/api.mdc)') and text.count('x') == 600


def test_through_the_hook_a_script_written_file_brings_the_rule_in_a_project_with_no_declarations(tmp_path):
    from tests.test_rule_groups import _hook, _shell
    root = write(tmp_path, FOUR)
    for args in (['init', '-q'], ['add', '-A'], ['-c', 'user.email=e@e', '-c', 'user.name=e', 'commit', '-qm', 'base']):
        subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
    _hook('UserPromptSubmit', {'cwd': str(root), 'prompt': 'add a handler for refunds'})
    (root / 'src/api/handler.ts').write_text('export const refund = 1\n', encoding='utf-8')
    note = _shell(root)
    assert 'Claude: validate every request body.' in note, 'after the shell, Claude gets its own rule too'
    assert 'Project rule' not in _shell(root), 'said once per file'


def test_through_the_hook_claude_is_told_a_cursor_rule_before_editing(tmp_path):
    from tests.test_rule_groups import _brief
    root = write(tmp_path, FOUR)
    subprocess.run(['git', 'init', '-q'], cwd=root, check=True)
    assert 'Cursor: use the shared client.' in _brief(root, 'src/api/handler.ts')
    assert 'Project rule' not in _brief(root, 'lib/util.ts')
