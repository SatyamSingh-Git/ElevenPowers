"""Qualified identity must survive capture, reuse, task replacement and exports."""
import json
from types import SimpleNamespace

import pytest

from core.config import Config, save
from core.evidence import Freshness, Result
from core.hook import on_post_tool
from core.ledger import Ledger
from core.milestones import build
from core.parsers import parse


@pytest.fixture
def project(tmp_path):
    (tmp_path / 'app.py').write_text('value = 1\n')
    value = {'schema': 1, 'milestones': [{'id': 'behavior', 'description': 'Behavior remains checked.',
        'inputs': ['app.py'], 'checks': [{'kind': 'test_suite', 'command': 'npm run ci'}]}]}
    (tmp_path / 'elevenpowers.milestones.json').write_text(json.dumps(value))
    save(tmp_path, Config(commands={'tests': 'npm run ci'}))
    return tmp_path


@pytest.mark.parametrize('code,state', [(0, 'CURRENT'), (1, 'FAILED'), (None, 'INCOMPLETE')])
def test_wrapper_latest_receipt_survives_history_and_task_replacement(project, code, state):
    ledger = Ledger(root=project, task='first')
    ledger.add(parse('npm run ci', '', 0, project)); ledger.save()
    ledger.add(parse('cd . && npm run ci', '', code, project)); ledger.save()
    assert build(project)['state'] == state
    Ledger(root=project, task='second').save()
    assert build(project)['state'] == state
    saved = Ledger.load(project).milestone_history['receipts']
    assert len(saved) == 1 and saved[0]['command'] == 'cd . && npm run ci'


@pytest.mark.parametrize('code,expected', [(0, []), (1, ['tests']), (None, ['tests'])])
def test_reuse_requires_fresh_success_for_qualified_declared_identity(project, code, expected):
    from core.verify import dischargeable
    ledger = Ledger(root=project)
    ledger.add(parse('cd . && npm run ci', '', code, project))
    ledger.verdicts = lambda: [SimpleNamespace(stale=[], missing=[
        SimpleNamespace(obligation=SimpleNamespace(needs='tests'))])]
    assert dischargeable(ledger) == expected


def test_declaration_change_stales_qualified_wrapper(project):
    row = parse('cd . && npm run ci', '', 0, project)[0]
    save(project, Config(commands={'tests': 'npm run check'}))
    assert row.freshness(project) is Freshness.STALE


@pytest.mark.parametrize('key', ['workdir', 'cwd', 'working_directory'])
@pytest.mark.parametrize('wrapped', [False, True])
def test_claude_tool_directory_mismatch_is_incomplete(project, key, wrapped):
    other = project / 'other'; other.mkdir()
    command = 'cd . && npm run ci' if wrapped else 'npm run ci'
    on_post_tool({'tool_name': 'Bash', 'tool_input': {'command': command, key: str(other)},
                  'tool_response': {'exit_code': 0, 'stdout': 'checks complete'}}, project)
    row = Ledger.load(project).evidence[-1]
    assert row.execution == 'incomplete' and row.result is Result.ERROR
    assert row.coverage_issues


def test_conflicting_tool_directory_aliases_cannot_credit_success(project):
    other = project / 'other'; other.mkdir()
    on_post_tool({'tool_name': 'Bash', 'tool_input': {'command': 'npm run ci',
                  'workdir': str(project), 'cwd': str(other)},
                  'tool_response': {'exit_code': 0, 'stdout': 'checks complete'}}, project)
    assert Ledger.load(project).evidence[-1].execution == 'incomplete'


@pytest.mark.parametrize('directory', [None, '', False, 0, []])
def test_present_invalid_directory_metadata_is_not_absent(project, directory):
    on_post_tool({'tool_name': 'Bash', 'tool_input': {'command': 'npm run ci', 'cwd': directory},
                  'tool_response': {'exit_code': 0, 'stdout': 'checks complete'}}, project)
    assert Ledger.load(project).evidence[-1].execution == 'incomplete'


@pytest.mark.parametrize('response', [{'interrupted': True}, {'timed_out': True}, {},
    {'session_id': 42, 'stdout': 'still running'}])
def test_wrapped_incomplete_native_attempt_supersedes_previous_success(project, response):
    ledger = Ledger(root=project, task='one')
    ledger.add(parse('npm run ci', '', 0, project)); ledger.save()
    on_post_tool({'tool_name': 'Bash', 'tool_input': {'command': 'cd . && npm run ci'},
                  'tool_response': response}, project)
    assert build(project)['state'] == 'INCOMPLETE'


def test_portable_report_explains_raw_and_declared_command(project):
    from core.export import build as report
    ledger = Ledger(root=project)
    ledger.add(parse('cd . && npm run ci', '', 0, project)); ledger.save()
    row = report(project)['receipts'][0]
    assert row['command'] == 'cd . && npm run ci'
    assert row['declared_command'] == 'npm run ci'


@pytest.mark.parametrize('host', ['codex', 'gemini', 'cursor', 'copilot'])
def test_all_added_host_contracts_share_qualified_capture(project, host):
    import importlib
    adapter = importlib.import_module('core.hosts.' + host)
    inputs = {'command': 'cd . && npm run ci'}
    payload = {'cwd': str(project), 'tool_name': 'Bash', 'tool_input': inputs,
               'tool_response': {'exit_code': 0, 'stdout': 'checks complete'}}
    phase = 'PostToolUse'
    if host == 'gemini':
        phase = 'AfterTool'; payload['tool_name'] = 'run_shell_command'
        payload['tool_response'] = {'llmContent': 'checks complete', 'data': {'exitCode': 0}}
    if host == 'cursor':
        phase = 'postToolUse'; payload['tool_name'] = 'Shell'
        payload['tool_output'] = payload['tool_response']
    if host == 'copilot':
        phase = 'postToolUse'; payload.update(toolName='bash', toolArgs=inputs,
                                             toolResult={'exitCode': 0, 'textResultForLlm': 'checks complete'})
    event = adapter.normalize(phase, payload)
    on_post_tool(event.payload, event.root)
    row = Ledger.load(project).evidence[-1]
    assert row.result is Result.PASS and row.declaration == 'tests'
    assert build(project)['state'] == 'CURRENT'
