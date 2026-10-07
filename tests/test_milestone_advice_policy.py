import json

import pytest


def test_advice_is_explicit_opt_in_and_config_round_trips(tmp_path):
    from core.config import Config, load, save
    from core.milestones.advice import policy
    assert policy({}) is None
    assert policy({'enabled': False}) is None
    save(tmp_path, Config(milestone_advice={'enabled': True, 'seconds': .2}))
    value = load(tmp_path)
    assert policy(value.milestone_advice)['seconds'] == .2
    assert policy(value.milestone_advice)['max_attempts'] == 3


@pytest.mark.parametrize('raw', [True, [], {'enabled': 'true'}, {'enabled': True, 'seconds': True},
    {'enabled': True, 'seconds': float('inf')}, {'enabled': True, 'seconds': 10**400},
    {'enabled': True, 'seconds': 0}, {'enabled': True, 'cooldown': -1},
    {'enabled': True, 'max_attempts': 1.2}, {'enabled': True, 'extra': 4}])
def test_advice_rejects_invalid_limits(raw):
    from core.milestones.advice import policy
    with pytest.raises(ValueError):
        policy(raw)


def test_context_bounds_commands_reasons_and_reports_omissions():
    from core.milestones.advice import render
    commands = [{'command': 'check ' + str(i), 'kind': 'test_suite', 'priority': 'fallback',
                 'milestones': [{'id': 'stage', 'state': 'STALE'}],
                 'reasons': [{'milestone': 'stage', 'input': 'consumer.py', 'category': 'declared'}] * 5,
                 'omitted_reasons': 2} for i in range(9)]
    report = {'state': 'INCOMPLETE', 'coverage': {'complete': False, 'issues': ['graph budget']},
              'rechecks': {'state': 'incomplete', 'commands': commands}}
    value = render(report)
    assert 'INCOMPLETE' in value and 'graph budget' in value
    assert '3 commands omitted' in value and '4 reasons omitted' in value
    assert 'fallback' in value and 'STALE' in value and 'not proof' in value
    assert len(value) <= 6000
    assert 'check 6' not in value


def test_context_never_injects_credentials_or_oversized_fields():
    from core.milestones.advice import render
    value = render({'state': 'ABSENT', 'coverage': {'complete': True, 'issues': []},
        'rechecks': {'commands': [{'command': 'TOKEN=ghp_' + 'a' * 36 + ' x' * 4000,
            'kind': 'test_suite', 'priority': 'direct', 'milestones': [], 'reasons': [], 'omitted_reasons': 0}]}})
    assert 'ghp_' + 'a' * 36 not in value
    assert 'truncated' in value and len(value) <= 6000
