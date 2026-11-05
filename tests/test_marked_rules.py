"""Rules a person marked in the code with LINT.IfChange / LINT.ThenChange.

Design: docs/superpowers/specs/2026-11-05-marked-rules-design.md.
"""
import json
import subprocess

UPLOAD = '''import os

# LINT.IfChange(upload_limit)
MAX_UPLOAD_SIZE_MB = 50
# LINT.ThenChange(//docs/api.md:upload_limit)


def size(path):
    return os.path.getsize(path)
'''
API = '''# API

<!-- LINT.IfChange(upload_limit) -->
Files up to 50 MB are accepted.
<!-- LINT.ThenChange(//config/upload.py:upload_limit) -->

Other notes.
'''


def write(root, files):
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding='utf-8')
    return root


def read(root, path):
    from core.milestones.marked import read
    return read(root, path)


# --- reading the directives ---

def test_a_labelled_block_is_read_with_its_lines_and_its_root_relative_target(tmp_path):
    write(tmp_path, {'config/upload.py': UPLOAD, 'docs/api.md': API})
    blocks, issues = read(tmp_path, 'config/upload.py')
    assert issues == []
    assert blocks == [{'path': 'config/upload.py', 'label': 'upload_limit', 'start': 3, 'then': 5, 'end': 5,
                       'targets': [{'spec': '//docs/api.md:upload_limit', 'path': 'docs/api.md',
                                    'label': 'upload_limit', 'found': True}]}]


def test_a_bare_target_is_found_beside_the_file_first_and_then_from_the_root(tmp_path):
    # abseil writes `../testing/flagsaver.py`; TFX writes `tfx/workspace.bzl` from inside tfx/.
    source = ('# LINT.IfChange\nx = 1\n# LINT.ThenChange(../testing/flagsaver.py:flag_override_parsing)\n'
              '# LINT.IfChange\ny = 2\n# LINT.ThenChange(lib/workspace.bzl)\n')
    write(tmp_path, {'lib/flags/values.py': source, 'lib/testing/flagsaver.py': '', 'lib/workspace.bzl': ''})
    blocks, _ = read(tmp_path, 'lib/flags/values.py')
    assert [(t['path'], t['label'], t['found']) for b in blocks for t in b['targets']] == [
        ('lib/testing/flagsaver.py', 'flag_override_parsing', True), ('lib/workspace.bzl', None, True)]


def test_a_bare_file_name_is_a_file_beside_this_one_not_a_label(tmp_path):
    # LIT writes `# LINT.ThenChange(server_flags.py)` for the file in the same folder.
    write(tmp_path, {'lit/server_config.py': '# LINT.IfChange\nport = 5432\n# LINT.ThenChange(server_flags.py)\n',
                     'lit/server_flags.py': ''})
    blocks, _ = read(tmp_path, 'lit/server_config.py')
    assert blocks[0]['targets'] == [{'spec': 'server_flags.py', 'path': 'lit/server_flags.py', 'label': None, 'found': True}]


def test_line_numbers_are_git_s_whatever_else_breaks_a_line(tmp_path):
    # A form feed or a lone carriage return is a line break to str.splitlines, not to git.
    (tmp_path / 'a.py').write_bytes(b'\xef\xbb\xbf# LINT.IfChange\nA = 1\n# LINT.ThenChange(//b.py)\n'
                                    b'x = 1\n\x0c\ny = "\r"\n# LINT.IfChange\nB = 1\n# LINT.ThenChange(//b.py)\n')
    write(tmp_path, {'b.py': ''})
    blocks, issues = read(tmp_path, 'a.py')
    assert issues == [] and [(b['start'], b['end']) for b in blocks] == [(1, 3), (7, 9)], (blocks, issues)


def test_a_target_list_may_run_over_several_comment_lines(tmp_path):
    source = ('# LINT.IfChange\nRATE_LIMIT_RPS = 100\n# LINT.ThenChange(\n#     //db/limits.sql,\n#\n'
              '#     //docs/api.md:rate_limits,\n#     :alert_threshold,\n# )\n'
              '# LINT.IfChange(alert_threshold)\nALERT = 90\n# LINT.ThenChange(:rate)\n')
    write(tmp_path, {'app/limits.py': source, 'db/limits.sql': '', 'docs/api.md': ''})
    blocks, issues = read(tmp_path, 'app/limits.py')
    assert issues == []
    assert [(b['start'], b['then'], b['end']) for b in blocks] == [(1, 3, 8), (9, 11, 11)]
    assert [(t['path'], t['label'], t['found']) for t in blocks[0]['targets']] == [
        ('db/limits.sql', None, True), ('docs/api.md', 'rate_limits', True), ('app/limits.py', 'alert_threshold', True)]
    assert blocks[1]['targets'] == [{'spec': ':rate', 'path': 'app/limits.py', 'label': 'rate', 'found': False}]


def test_each_language_s_own_comment_marks_a_block(tmp_path):
    write(tmp_path, {'web/types.js': '// LINT.IfChange\nconst A = 1;\n// LINT.ThenChange(//db/schema.sql)\n',
                     'db/schema.sql': '-- LINT.IfChange\nCREATE TABLE a (id INT);\n-- LINT.ThenChange(//web/types.js)\n',
                     'web/style.css': '/* LINT.IfChange */\na { color: red; }\n/* LINT.ThenChange(//web/types.js) */\n'})
    for path, target in (('web/types.js', 'db/schema.sql'), ('db/schema.sql', 'web/types.js'),
                         ('web/style.css', 'web/types.js')):
        blocks, issues = read(tmp_path, path)
        assert issues == [] and [t['path'] for b in blocks for t in b['targets']] == [target], (path, blocks, issues)


def test_a_target_that_is_not_in_the_project_is_kept_and_said_not_found(tmp_path):
    write(tmp_path, {'ops/variables.py': '# LINT.IfChange\nA = 1\n# LINT.ThenChange(//tensorflow/core/variable.proto)\n'})
    blocks, _ = read(tmp_path, 'ops/variables.py')
    assert blocks[0]['targets'] == [{'spec': '//tensorflow/core/variable.proto', 'path': 'tensorflow/core/variable.proto',
                                     'label': None, 'found': False}]


def test_a_bare_target_found_nowhere_is_kept_as_written_not_guessed(tmp_path):
    # TFX writes `# LINT.ThenChange(<Internal source code>)` from inside tfx/types/.
    write(tmp_path, {'tfx/types/artifact.py': '# LINT.IfChange\nA = 1\n# LINT.ThenChange(<Internal source code>)\n'})
    blocks, _ = read(tmp_path, 'tfx/types/artifact.py')
    assert blocks[0]['targets'] == [{'spec': '<Internal source code>', 'path': None, 'label': None, 'found': False}]


def test_a_patch_quotes_other_files_and_is_not_read_for_rules(tmp_path):
    # TFX's patches/tfx.patch carries a context line ` # LINT.ThenChange(` from the file it patches.
    write(tmp_path, {'patches/fix.patch': '@@ -1,2 +1,2 @@\n # LINT.ThenChange(//b.py)\n-x\n+y\n', 'b.diff': '', 'b.py': ''})
    assert read(tmp_path, 'patches/fix.patch') == ([], [])


def test_a_target_outside_the_project_is_never_resolved(tmp_path):
    root = tmp_path / 'project'
    outside = tmp_path / 'outside.py'
    outside.write_text('', encoding='utf-8')
    for spec in ('../../outside.py', '..\\..\\outside.py', outside.as_posix()):
        write(root, {'app/a.py': f'# LINT.IfChange\nA = 1\n# LINT.ThenChange({spec})\n'})
        blocks, _ = read(root, 'app/a.py')
        assert [(t['found'], t['path']) for t in blocks[0]['targets']] == [(False, None)], (spec, blocks)


def test_a_directive_with_text_after_it_is_prose_not_a_block(tmp_path):
    # TF-GNN has `# LINT.ThenChange()../api_def/tfgnn-symbols.txt)`: the block it meant to close stays open.
    source = ('# LINT.IfChange(x) see the docs\nA = 1\n# LINT.ThenChange(//b.py) -->\n'
              '# LINT.IfChange\nB = 2\n# LINT.ThenChange()../api_def/tfgnn-symbols.txt)\n')
    write(tmp_path, {'a.py': source, 'b.py': ''})
    blocks, issues = read(tmp_path, 'a.py')
    assert blocks == []
    assert issues == ['a.py:4: LINT.IfChange is never closed by a LINT.ThenChange'], issues


def test_a_directive_in_code_or_a_markdown_fence_is_not_a_block(tmp_path):
    write(tmp_path, {'a.py': 'TEXT = "# LINT.IfChange"\nA = 1\nPROSE = "# LINT.ThenChange(//b.py)"\n',
                     'guide.md': '```python\n# LINT.IfChange\nA = 1\n# LINT.ThenChange(//b.py)\n```\n', 'b.py': ''})
    assert read(tmp_path, 'a.py') == ([], [])
    assert read(tmp_path, 'guide.md') == ([], [])


def test_a_wrapped_comment_must_close_on_its_own_line_to_hold_a_directive(tmp_path):
    source = '<!-- LINT.IfChange -->\ntext\n<!-- LINT.ThenChange(//b.py)\ncontinues here -->\n'
    write(tmp_path, {'a.md': source, 'b.py': ''})
    assert read(tmp_path, 'a.md') == ([], ['a.md:1: LINT.IfChange is never closed by a LINT.ThenChange'])


def test_nested_and_unopened_blocks_are_named_not_guessed(tmp_path):
    source = ('# LINT.IfChange(outer)\nA = 1\n# LINT.IfChange(inner)\nB = 2\n# LINT.ThenChange(//b.py)\n'
              '# LINT.ThenChange(//b.py)\n')
    write(tmp_path, {'a.py': source, 'b.py': ''})
    blocks, issues = read(tmp_path, 'a.py')
    assert [b['label'] for b in blocks] == ['inner']
    assert issues == ['a.py:3: LINT.IfChange inside an open block; nesting is not supported',
                      'a.py:6: LINT.ThenChange with no open LINT.IfChange'], issues


def test_a_file_outside_the_project_is_never_read(tmp_path):
    root = tmp_path / 'project'
    write(tmp_path, {'outside.py': '# LINT.IfChange\nA = 1\n# LINT.ThenChange(//project/a.py)\n', 'project/a.py': ''})
    assert read(root, '../outside.py') == ([], [])
    assert read(root, str(tmp_path / 'outside.py')) == ([], [])


def test_a_file_too_large_to_read_is_named(tmp_path):
    write(tmp_path, {'big.py': '# LINT.IfChange\n' + 'x = 1\n' * 200_000 + '# LINT.ThenChange(//b.py)\n', 'b.py': ''})
    assert read(tmp_path, 'big.py') == ([], ['big.py: larger than 1 MiB; its marked rules were not read'])


# --- before the agent's first edit of a marked file ---

def marked(tmp_path, extra=None):
    from tests.test_rule_groups import _hook
    root = write(tmp_path, {'config/upload.py': UPLOAD, 'docs/api.md': API, 'app/names.py': 'def name():\n    return 1\n',
                            **(extra or {})})
    for args in (['init', '-q'], ['add', '-A'], ['-c', 'user.email=e@e', '-c', 'user.name=e', 'commit', '-qm', 'base']):
        subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
    _hook('UserPromptSubmit', {'cwd': str(root), 'prompt': 'raise the upload limit to 100 MB'})
    return root


def test_before_an_edit_a_marked_rule_names_the_other_file_that_keeps_it(tmp_path):
    from tests.test_rule_groups import _brief
    brief = _brief(marked(tmp_path), 'config/upload.py')
    assert ('Marked rule upload_limit (config/upload.py lines 3-5) is also kept in docs/api.md:upload_limit. '
            'Change them together, or say why one should differ.') in brief, brief


def test_a_marked_file_in_a_dot_folder_gets_its_note(tmp_path):
    # CI workflows are a common home for these rules, and `.github` once lost its dot on the way in.
    from tests.test_rule_groups import _brief
    root = marked(tmp_path, {'.github/workflows/ci.yml': '# LINT.IfChange\npython: "3.11"\n# LINT.ThenChange(//config/upload.py)\n'})
    assert 'Marked rule unnamed (.github/workflows/ci.yml lines 1-3)' in _brief(root, '.github/workflows/ci.yml')


def test_a_file_with_no_marked_rule_gets_no_marked_note(tmp_path):
    from tests.test_rule_groups import _brief
    assert 'Marked rule' not in _brief(marked(tmp_path), 'app/names.py')


def test_an_agent_that_edits_a_marked_file_through_the_shell_is_told_too(tmp_path):
    from tests.test_rule_groups import _shell
    root = marked(tmp_path)
    upload = root / 'config/upload.py'
    upload.write_text(upload.read_text(encoding='utf-8').replace('50', '100'), encoding='utf-8')
    note = _shell(root)
    assert 'Marked rule upload_limit' in note and 'docs/api.md:upload_limit' in note, note
    assert 'Marked rule' not in _shell(root), 'said once per file, not after every command'


def test_a_project_with_no_marked_or_declared_rule_never_looks_for_them_after_a_shell_command(tmp_path):
    from core.ledger import Ledger
    from tests.test_rule_groups import _shell
    root = marked(tmp_path)
    for path in ('config/upload.py', 'docs/api.md'):
        (root / path).write_text('plain\n', encoding='utf-8')
    subprocess.run(['git', '-c', 'user.email=e@e', '-c', 'user.name=e', 'commit', '-qam', 'unmark'], cwd=root, check=True)
    from tests.test_rule_groups import _hook
    _hook('UserPromptSubmit', {'cwd': str(root), 'prompt': 'add a names page'})
    (root / 'app/names.py').write_text('def name():\n    return 2\n', encoding='utf-8')
    assert _shell(root) == ''
    assert Ledger.load(root).marked is False
    # Asked once per task: a rule marked mid-task is found from the next task on.
    (root / 'app/names.py').write_text('# LINT.IfChange\nA = 1\n# LINT.ThenChange(//config/upload.py)\n', encoding='utf-8')
    assert _shell(root) == ''
    subprocess.run(['git', '-c', 'user.email=e@e', '-c', 'user.name=e', 'commit', '-qam', 'mark'], cwd=root, check=True)
    task = Ledger.load(root).task
    _hook('UserPromptSubmit', {'cwd': str(root), 'prompt': 'fix the bug in the names page'})
    assert Ledger.load(root).task != task
    (root / 'app/names.py').write_text('# LINT.IfChange\nA = 2\n# LINT.ThenChange(//config/upload.py)\n', encoding='utf-8')
    assert 'Marked rule unnamed' in _shell(root)


def edit(root, path, old, new):
    text = (root / path).read_text(encoding='utf-8')
    assert old in text
    (root / path).write_text(text.replace(old, new), encoding='utf-8')


def report(root, touched):
    from tests.test_rule_groups import _report
    return _report(root, touched)


LEFT = 'marked rule upload_limit (config/upload.py lines 3-5): changed, not docs/api.md:upload_limit'


def test_the_end_report_names_a_marked_rule_changed_on_one_side_only(tmp_path):
    root = marked(tmp_path)
    edit(root, 'config/upload.py', 'MAX_UPLOAD_SIZE_MB = 50', 'MAX_UPLOAD_SIZE_MB = 100')
    assert LEFT in report(root, ['config/upload.py'])


def test_a_change_outside_the_marked_block_is_not_the_rule_changing(tmp_path):
    root = marked(tmp_path)
    edit(root, 'config/upload.py', 'return os.path.getsize(path)', 'return os.stat(path).st_size')
    assert 'marked rule' not in report(root, ['config/upload.py'])


def test_a_line_deleted_inside_the_block_is_the_rule_changing(tmp_path):
    root = marked(tmp_path)
    edit(root, 'config/upload.py', 'MAX_UPLOAD_SIZE_MB = 50\n', '')
    assert 'marked rule upload_limit (config/upload.py lines 3-4): changed, not docs/api.md:upload_limit' in report(
        root, ['config/upload.py'])


def test_the_report_is_quiet_when_the_labelled_block_on_the_other_side_changed_too(tmp_path):
    root = marked(tmp_path)
    edit(root, 'config/upload.py', 'MAX_UPLOAD_SIZE_MB = 50', 'MAX_UPLOAD_SIZE_MB = 100')
    edit(root, 'docs/api.md', 'up to 50 MB', 'up to 100 MB')
    assert 'marked rule' not in report(root, ['config/upload.py', 'docs/api.md'])


def test_the_other_file_changed_outside_its_labelled_block_does_not_count(tmp_path):
    root = marked(tmp_path)
    edit(root, 'config/upload.py', 'MAX_UPLOAD_SIZE_MB = 50', 'MAX_UPLOAD_SIZE_MB = 100')
    edit(root, 'docs/api.md', 'Other notes.', 'Other notes, revised.')
    assert LEFT in report(root, ['config/upload.py', 'docs/api.md'])


def test_a_target_named_without_a_label_counts_as_changed_by_any_change_to_its_file(tmp_path):
    root = marked(tmp_path, {'app/rate.py': '# LINT.IfChange\nRATE = 1\n# LINT.ThenChange(//app/names.py)\n'})
    edit(root, 'app/rate.py', 'RATE = 1', 'RATE = 2')
    assert 'marked rule unnamed (app/rate.py lines 1-3): changed, not app/names.py' in report(root, ['app/rate.py'])
    edit(root, 'app/names.py', 'return 1', 'return 2')
    assert 'marked rule' not in report(root, ['app/rate.py', 'app/names.py'])


def test_adding_or_removing_a_target_in_a_list_is_not_the_rule_changing(tmp_path):
    source = '# LINT.IfChange\nRATE = 1\n# LINT.ThenChange(\n#     //docs/api.md,\n#     //app/old.py,\n# )\n'
    root = marked(tmp_path, {'app/rate.py': source, 'app/old.py': ''})
    edit(root, 'app/rate.py', '#     //app/old.py,\n', '')
    assert 'marked rule' not in report(root, ['app/rate.py'])
    edit(root, 'app/rate.py', '#     //docs/api.md,\n', '#     //docs/api.md,\n#     //app/names.py,\n')
    assert 'marked rule' not in report(root, ['app/rate.py'])
    edit(root, 'app/rate.py', 'RATE = 1', 'RATE = 2')
    assert 'marked rule unnamed (app/rate.py lines 1-6): changed, not docs/api.md' in report(root, ['app/rate.py'])


def test_the_report_reads_git_s_hunks_whatever_the_user_s_diff_settings(tmp_path):
    root = marked(tmp_path)
    for key, value in (('color.diff', 'always'), ('color.ui', 'always')):
        subprocess.run(['git', 'config', key, value], cwd=root, check=True)
    edit(root, 'config/upload.py', 'MAX_UPLOAD_SIZE_MB = 50', 'MAX_UPLOAD_SIZE_MB = 100')
    assert LEFT in report(root, ['config/upload.py'])


def test_a_target_git_treats_as_binary_still_counts_as_changed(tmp_path):
    root = marked(tmp_path, {'.gitattributes': 'gen/* -diff\n', 'gen/lock.json': '{"a": 1}\n',
                             'app/rate.py': '# LINT.IfChange\nRATE = 1\n# LINT.ThenChange(//gen/lock.json)\n'})
    edit(root, 'app/rate.py', 'RATE = 1', 'RATE = 2')
    edit(root, 'gen/lock.json', '1', '2')
    assert 'marked rule' not in report(root, ['app/rate.py', 'gen/lock.json'])


def test_a_target_changed_before_the_task_opened_is_not_this_task_keeping_it_in_step(tmp_path):
    root = marked(tmp_path)
    edit(root, 'docs/api.md', 'up to 50 MB', 'up to 60 MB')   # the developer, mid-change, before the task
    edit(root, 'config/upload.py', 'MAX_UPLOAD_SIZE_MB = 50', 'MAX_UPLOAD_SIZE_MB = 100')
    assert LEFT in report(root, ['config/upload.py'])


def test_a_changed_block_whose_only_target_is_outside_the_project_is_not_reported(tmp_path):
    root = marked(tmp_path, {'ops/variables.py': '# LINT.IfChange\nA = 1\n# LINT.ThenChange(//internal/variable.proto)\n'})
    edit(root, 'ops/variables.py', 'A = 1', 'A = 2')
    assert 'marked rule' not in report(root, ['ops/variables.py'])


def test_a_new_file_the_task_marked_is_changed_throughout(tmp_path):
    root = marked(tmp_path)
    write(root, {'app/rate.py': '# LINT.IfChange\nRATE = 1\n# LINT.ThenChange(//app/names.py)\n'})
    assert 'marked rule unnamed (app/rate.py lines 1-3): changed, not app/names.py' in report(root, ['app/rate.py'])


def test_renaming_a_block_s_label_is_not_the_rule_changing(tmp_path):
    root = marked(tmp_path)
    edit(root, 'config/upload.py', '# LINT.IfChange(upload_limit)', '# LINT.IfChange(upload_size)')
    assert 'marked rule' not in report(root, ['config/upload.py'])


def test_without_a_base_commit_a_touched_file_stands_for_its_blocks(tmp_path):
    from core.milestones.definition import partly_changed
    root = write(tmp_path, {'config/upload.py': UPLOAD, 'docs/api.md': API})
    assert partly_changed(root, ['config/upload.py'], '') == [LEFT]
    assert partly_changed(root, ['config/upload.py', 'docs/api.md'], '') == []


def test_a_pair_already_marked_together_is_not_proposed_again(tmp_path):
    from core.milestones.propose import propose
    from tests.test_rule_groups import TAX, project
    first = propose(project(tmp_path / 'plain'))['proposals'][0]['files']
    assert first == ['app/money.py', 'app/services/pricing.py']
    root = project(tmp_path / 'marked', {
        'app/money.py': TAX.replace('\n\ndef lodging_tax', '\n# LINT.IfChange\ndef lodging_tax')
        + '# LINT.ThenChange(//app/services/pricing.py)\n'})
    assert ['app/money.py', 'app/services/pricing.py'] not in [p['files'] for p in propose(root)['proposals']]


def test_the_command_lists_every_marked_rule_and_what_is_broken(tmp_path):
    from tests.test_rule_groups import _cli
    root = marked(tmp_path, {'ops/variables.py': '# LINT.IfChange\nA = 1\n# LINT.ThenChange(//internal/variable.proto)\n',
                             'app/rate.py': '# LINT.IfChange\nRATE = 1\n# LINT.ThenChange(//docs/api.md:renamed)\n',
                             'app/open.py': '# LINT.IfChange\nB = 1\n',
                             'app/anchor.py': '# LINT.IfChange(flag_parsing)\nC = 1\n# LINT.ThenChange()\n',
                             'tfx/types/artifact.py': '# LINT.IfChange\nD = 1\n# LINT.ThenChange(<Internal source code>)\n'})
    done = _cli('--project', str(root), '--marked', '--json')
    assert done.returncode == 0, done.stderr
    value = json.loads(done.stdout)
    shown = {(r['path'], r['start']): [(t['spec'], t['found']) for t in r['targets']] for r in value['rules']}
    assert shown == {('app/anchor.py', 1): [], ('app/rate.py', 1): [('//docs/api.md:renamed', False)],
                     ('tfx/types/artifact.py', 1): [('<Internal source code>', False)],
                     ('config/upload.py', 3): [('//docs/api.md:upload_limit', True)],
                     ('docs/api.md', 3): [('//config/upload.py:upload_limit', True)],
                     ('ops/variables.py', 1): [('//internal/variable.proto', False)]}, shown
    assert value['issues'] == ['app/open.py:1: LINT.IfChange is never closed by a LINT.ThenChange']
    text = _cli('--project', str(root), '--marked').stdout
    assert 'config/upload.py lines 3-5 -> docs/api.md:upload_limit' in text, text
    assert 'app/rate.py lines 1-3 -> docs/api.md:renamed (label not found)' in text, text
    assert 'ops/variables.py lines 1-3 -> //internal/variable.proto (not found)' in text, text
    assert 'tfx/types/artifact.py lines 1-3 -> <Internal source code> (not found)' in text, text
    assert 'app/anchor.py lines 1-3 -> no targets: a label other rules name' in text, text


def test_a_file_already_looked_at_after_one_command_is_not_read_again_after_the_next(tmp_path):
    # A formatter can change thousands of files; each later command must not read them all again.
    import os
    from tests.test_rule_groups import _shell
    root = marked(tmp_path)
    names = root / 'app/names.py'
    names.write_text('def name():\n    return 2\n', encoding='utf-8')
    assert _shell(root) == ''
    before = os.stat(names).st_mtime
    names.write_text('# LINT.IfChange\nA = 1\n# LINT.ThenChange(//config/upload.py)\n', encoding='utf-8')
    os.utime(names, (before, before))
    assert _shell(root) == '', 'unchanged since the last command, so not read again'
    os.utime(names)
    assert 'Marked rule unnamed' in _shell(root)


def test_a_search_that_failed_is_not_taken_for_an_answer(tmp_path, monkeypatch):
    import subprocess as sp
    from core import process
    from core.milestones.marked import present
    write(tmp_path, {'a.py': '# LINT.IfChange\nA = 1\n# LINT.ThenChange(//b.py)\n', 'b.py': ''})
    subprocess.run(['git', 'init', '-q'], cwd=tmp_path, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=tmp_path, check=True)
    assert present(tmp_path) is True

    def slow(*args, **kwargs):
        raise sp.TimeoutExpired(args[0], 10)
    monkeypatch.setattr(process, 'run', slow)
    assert present(tmp_path) is None


def test_a_rule_whose_targets_are_all_outside_the_project_is_not_put_on_the_agent(tmp_path):
    # TensorFlow's exported files name Google-internal paths the agent cannot change.
    from tests.test_rule_groups import _brief
    root = marked(tmp_path, {'ops/variables.py': '# LINT.IfChange\nA = 1\n# LINT.ThenChange(//internal/variable.proto)\n'})
    assert 'Marked rule' not in _brief(root, 'ops/variables.py')
