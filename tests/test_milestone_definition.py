import json

import pytest


def declaration(root, **extra):
    value = {'schema': 1, 'milestones': [{'id': 'login', 'description': 'A valid session is accepted.',
             'inputs': ['provider.py', 'tests/test_login.py'],
             'checks': [{'kind': 'test_suite', 'command': 'python -m pytest tests/test_login.py'}]}]}
    value.update(extra)
    (root / 'elevenpowers.milestones.json').write_text(json.dumps(value), encoding='utf-8')
    return value


def test_absent_definition_is_not_configured(tmp_path):
    from core.milestones.definition import load
    assert load(tmp_path) == {'configured': False, 'fingerprint': '', 'milestones': [], 'issues': []}
    assert not (tmp_path / '.elevenpowers').exists()


def test_valid_definition_retains_human_expectation_and_exact_commands(tmp_path):
    from core.milestones.definition import load
    value = declaration(tmp_path)
    result = load(tmp_path)
    assert result['milestones'] == value['milestones']
    assert len(result['fingerprint']) == 64
    assert result['configured'] and not result['issues']
    assert not (tmp_path / '.elevenpowers').exists()


@pytest.mark.parametrize('change', [
    {'schema': 2}, {'schema': True}, {'surprise': 1}, {'milestones': []},
    {'milestones': 'login'}, {'milestones': [None]},
])
def test_invalid_top_level_is_an_explicit_gap(tmp_path, change):
    from core.milestones.definition import load
    declaration(tmp_path, **change)
    result = load(tmp_path)
    assert result['configured'] and result['issues'] and not result['milestones']


@pytest.mark.parametrize('field,value', [
    ('id', ''), ('id', '../login'), ('description', ''), ('inputs', []),
    ('inputs', ['../escape.py']), ('inputs', ['C:/escape.py']), ('inputs', ['src\\file.py']),
    ('inputs', ['./provider.py']), ('inputs', ['.elevenpowers/ledger.json']),
    ('inputs', ['provider.py', 'provider.py']), ('checks', []),
    ('checks', [{'kind': 'test', 'command': 'pytest'}]),
    ('checks', [{'kind': 'test_suite', 'command': ''}]),
    ('checks', [{'kind': 'test_suite', 'command': 'pytest', 'typo': 1}]),
    ('inputs', ['provider.py'] * 129),
])
def test_invalid_milestone_fields_cannot_silently_define_behavior(tmp_path, field, value):
    from core.milestones.definition import load
    document = declaration(tmp_path)
    document['milestones'][0][field] = value
    (tmp_path / 'elevenpowers.milestones.json').write_text(json.dumps(document))
    result = load(tmp_path)
    assert result['issues'] and not result['milestones']


def test_duplicate_ids_and_duplicate_json_keys_are_rejected(tmp_path):
    from core.milestones.definition import load
    value = declaration(tmp_path)
    value['milestones'].append(value['milestones'][0])
    path = tmp_path / 'elevenpowers.milestones.json'
    path.write_text(json.dumps(value))
    assert load(tmp_path)['issues']
    path.write_text('{"schema": 1, "schema": 1, "milestones": []}')
    assert load(tmp_path)['issues']


def test_oversize_and_deadline_are_not_an_empty_project(tmp_path):
    from core.milestones.definition import load
    declaration(tmp_path)
    assert load(tmp_path, deadline=0)['issues']
    (tmp_path / 'elevenpowers.milestones.json').write_bytes(b' ' * (128 * 1024 + 1))
    assert load(tmp_path)['issues']


def test_nested_repository_input_is_rejected(tmp_path):
    from core.milestones.definition import load
    nested = tmp_path / 'nested'
    nested.mkdir(); (nested / '.git').write_text('gitdir: elsewhere')
    value = declaration(tmp_path)
    value['milestones'][0]['inputs'] = ['nested/provider.py']
    (tmp_path / 'elevenpowers.milestones.json').write_text(json.dumps(value))
    assert load(tmp_path)['issues']


def test_symlink_input_cannot_escape_declarations(tmp_path):
    from core.milestones.definition import load
    (tmp_path / 'target.py').write_text('value = 1')
    try:
        (tmp_path / 'provider.py').symlink_to(tmp_path / 'target.py')
    except OSError:
        pytest.skip('symlink privilege unavailable')
    declaration(tmp_path)
    assert load(tmp_path)['issues']
