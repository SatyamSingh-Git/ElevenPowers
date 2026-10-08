"""Temporal native observations are separate from model comprehension."""
import json
from dataclasses import replace

import pytest

from core.config import load, save
from core.export import build
from core.hosts import readiness, transport
from core.ledger import Ledger
from core.milestones import delivery
from core.milestones.automatic import deliver
from core.parsers import parse
from test_advice_emission import project, attempts

COMMAND = 'python -m pytest test_cli.py -q'


def emitted_project(root):
    project(root)
    config = load(root)
    save(root, replace(config, commands={'tests': COMMAND}, auto_detect=False))
    with readiness.ingress('host'), delivery.collect():
        with readiness.callback('claude', root, 'SessionStart', {'session_id': 'private-session'}):
            pass
        with readiness.callback('claude', root, 'PostToolUse', {'session_id': 'private-session'}):
            context = deliver(Ledger.load(root))
            transport.emit('PostToolUse', {'additionalContext': context})
    return root


def receipt(root, *, code=0, native=True, task='task', session='private-session', earlier=False):
    ledger = Ledger.load(root)
    output = '1 passed in 0.01s' if code == 0 else '1 failed in 0.01s' if code else 'still running'
    records = parse('cd . && ' + COMMAND, output, code, root)
    if earlier:
        for row in records:
            row.at = attempts(root)[0]['emission']['at'] - 1
    ledger.add(records)
    ledger.save()
    if native:
        with readiness.ingress('host'):
            with readiness.callback('claude', root, 'PostToolUse', {'session_id': session}):
                readiness.record_receipts(records, task)
    return records


def inspect(root, task='task'):
    return delivery.inspect(root, 'claude', task, readiness.activation('claude', root), build(root)['receipts'])


@pytest.mark.parametrize('code,state', [(0, 'current'), (1, 'failed'), (None, 'incomplete')])
def test_read_only_view_qualifies_later_wrapped_native_receipt(tmp_path, code, state):
    emitted_project(tmp_path)
    records = receipt(tmp_path, code=code)
    before = {p.name: p.read_bytes() for p in (tmp_path / '.elevenpowers').iterdir() if p.is_file()}
    value = inspect(tmp_path)
    assert value['state'] == 'emitted'
    assert value['matching_native_receipts'] == 1
    found = [r for r in value['checks'] if r['state'] != 'unobserved']
    assert len(found) == 1 and found[0]['state'] == state
    assert found[0]['receipt_key'] == readiness.receipt_key(records[0])
    assert value['model_consumption'] == 'unproven'
    assert before == {p.name: p.read_bytes() for p in (tmp_path / '.elevenpowers').iterdir() if p.is_file()}


@pytest.mark.parametrize('options', [{'native': False}, {'earlier': True}, {'task': 'other'}, {'session': 'other'}])
def test_controller_earlier_and_foreign_receipts_do_not_establish_followup(tmp_path, options):
    emitted_project(tmp_path)
    receipt(tmp_path, **options)
    value = inspect(tmp_path)
    assert value['state'] == 'emitted'
    assert value['matching_native_receipts'] == 0
    assert all(row['state'] == 'unobserved' for row in value['checks'])


def test_later_source_change_keeps_followup_stale(tmp_path):
    emitted_project(tmp_path)
    receipt(tmp_path)
    (tmp_path / 'cli.py').write_text('print(4)\n')
    value = inspect(tmp_path)
    assert any(row['state'] == 'stale' for row in value['checks'])


def test_new_task_does_not_inherit_old_emission(tmp_path):
    emitted_project(tmp_path)
    assert inspect(tmp_path, task='next')['state'] == 'waiting'


@pytest.mark.parametrize('field', ['session', 'runtime', 'generation'])
def test_changed_emission_scope_is_incomplete(tmp_path, field):
    emitted_project(tmp_path)
    path = tmp_path / '.elevenpowers/advice.json'
    value = json.loads(path.read_text())
    value['tasks'][0]['attempts'][0]['emission'][field] = 'd' * (32 if field == 'generation' else 64)
    path.write_text(json.dumps(value))
    result = inspect(tmp_path)
    assert result['state'] == 'incomplete'
    assert result['matching_native_receipts'] == 0


def test_changed_native_wiring_cannot_qualify_old_emission(tmp_path):
    emitted_project(tmp_path)
    (tmp_path / '.claude/settings.local.json').write_text('{}')
    assert inspect(tmp_path)['state'] == 'incomplete'


def test_legacy_worker_record_is_generated_not_retroactive_emission(tmp_path):
    emitted_project(tmp_path)
    path = tmp_path / '.elevenpowers/advice.json'
    value = json.loads(path.read_text())
    for key in ('emission', 'checks', 'context'):
        value['tasks'][0]['attempts'][0].pop(key)
    path.write_text(json.dumps(value))
    assert inspect(tmp_path)['state'] == 'generated'


def test_corrupt_advice_state_does_not_change_receipts(tmp_path):
    emitted_project(tmp_path)
    ledger = (tmp_path / '.elevenpowers/ledger.json').read_bytes()
    (tmp_path / '.elevenpowers/advice.json').write_text('{broken')
    assert inspect(tmp_path)['state'] == 'incomplete'
    assert (tmp_path / '.elevenpowers/ledger.json').read_bytes() == ledger


def test_unconfigured_read_does_not_create_project_state(tmp_path):
    assert delivery.inspect(tmp_path, 'claude', '', {}, [])['state'] == 'unconfigured'
    assert not (tmp_path / '.elevenpowers').exists()


def test_readiness_adds_optional_advice_view_without_a_new_gate(tmp_path):
    from core import health
    emitted_project(tmp_path)
    receipt(tmp_path)
    value = health.inspect('claude', tmp_path)
    assert value['milestone_advice']['state'] == 'emitted'
    assert 'milestone_advice' not in value['health']['stages']
    assert 'Advice delivery: emitted' in health.render(value)
