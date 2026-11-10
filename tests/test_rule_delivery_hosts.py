"""The rule note reaches the agent on every host, not only the ones that carry pre-edit text.

Cursor's and Copilot's adapters drop `additionalContext` on preToolUse, and Codex edits through
`apply_patch`, which never asked for a brief. The file was still recorded as briefed, so even the
post-shell note skipped it: the measured note reached only Claude Code and Gemini.
"""
import json

from core.hosts.bridge import run
from tests.test_rule_groups import _hook, declared


def _edit(root, platform):
    target = str(root / 'app/money.py')
    if platform == 'copilot':
        return {'cwd': str(root), 'sessionId': 's', 'toolName': 'edit', 'toolArgs': {'file_path': target},
                'toolResult': {'resultType': 'success'}}
    tool = 'replace' if platform == 'gemini' else 'Edit'
    return {'cwd': str(root), 'session_id': 's', 'tool_name': tool,
            'tool_input': {'file_path': target, 'old_string': 'a', 'new_string': 'b'}}


EVENTS = {'cursor': ('preToolUse', 'postToolUse'), 'copilot': ('preToolUse', 'postToolUse'),
          'gemini': ('BeforeTool', 'AfterTool')}


def _said(response):
    return json.dumps(response)


def test_cursor_gets_the_rule_after_the_edit_not_lost_before_it(tmp_path):
    root = declared(tmp_path)
    before, _ = run('cursor', 'preToolUse', _edit(root, 'cursor'))
    assert 'lodging-tax' not in _said(before)
    after, _ = run('cursor', 'postToolUse', _edit(root, 'cursor'))
    assert 'lodging-tax' in after.get('additional_context', '') and 'app/services/pricing.py' in after['additional_context']


def test_copilot_gets_the_rule_after_the_edit(tmp_path):
    root = declared(tmp_path)
    run('copilot', 'preToolUse', _edit(root, 'copilot'))
    after, _ = run('copilot', 'postToolUse', _edit(root, 'copilot'))
    assert 'lodging-tax' in after.get('additionalContext', ''), after


def test_codex_patch_gets_the_rule_after_the_patch(tmp_path):
    root = declared(tmp_path)
    patch = ('*** Begin Patch\n*** Update File: app/money.py\n@@\n-ROUND_HALF_UP)\n+ROUND_HALF_EVEN)\n'
             '*** End Patch')
    payload = {'cwd': str(root), 'session_id': 's', 'tool_use_id': 'call-1', 'tool_name': 'apply_patch',
               'tool_input': {'command': patch}}
    run('codex', 'PreToolUse', payload)
    money = root / 'app/money.py'
    money.write_text(money.read_text(encoding='utf-8').replace('ROUND_HALF_UP)', 'ROUND_HALF_EVEN)'),
                     encoding='utf-8')
    after, _ = run('codex', 'PostToolUse', payload)
    assert 'lodging-tax' in after.get('hookSpecificOutput', {}).get('additionalContext', ''), after


def test_gemini_still_gets_it_before_the_edit_and_not_again_after(tmp_path):
    root = declared(tmp_path)
    before, _ = run('gemini', 'BeforeTool', _edit(root, 'gemini'))
    assert 'lodging-tax' in _said(before)
    after, _ = run('gemini', 'AfterTool', _edit(root, 'gemini'))
    assert 'lodging-tax' not in _said(after)


def test_claude_still_gets_it_before_the_edit_and_not_again_after(tmp_path):
    root = declared(tmp_path)
    before = _hook('PreToolUse', {'cwd': str(root), 'tool_name': 'Edit',
                                  'tool_input': {'file_path': str(root / 'app/money.py')}})
    assert 'lodging-tax' in before.stdout
    after = _hook('PostToolUse', {'cwd': str(root), 'tool_name': 'Edit',
                                  'tool_input': {'file_path': str(root / 'app/money.py')},
                                  'tool_response': {'filePath': str(root / 'app/money.py')}})
    assert 'lodging-tax' not in after.stdout


def test_a_file_briefed_after_the_edit_is_not_briefed_again_by_the_shell(tmp_path):
    root = declared(tmp_path)
    money = root / 'app/money.py'
    money.write_text(money.read_text(encoding='utf-8').replace('ROUND_HALF_UP)', 'ROUND_HALF_EVEN)'),
                     encoding='utf-8')
    run('cursor', 'preToolUse', _edit(root, 'cursor'))
    after, _ = run('cursor', 'postToolUse', _edit(root, 'cursor'))
    assert 'lodging-tax' in after.get('additional_context', '')
    shell, _ = run('cursor', 'postToolUse', {'cwd': str(root), 'session_id': 's', 'tool_name': 'Shell',
                                             'tool_input': {'command': 'python edit.py'},
                                             'tool_output': '', 'exit_code': 0})
    assert 'lodging-tax' not in _said(shell)
