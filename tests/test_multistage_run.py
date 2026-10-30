"""The sealed multi-stage runner, with only the external model process substituted.

The fake host plays the agent by applying the case's own stage diffs, so every
grade below comes from the real oracles on real trees.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

import pytest

from eval import multistage_run as m
from eval.bundle import apply_patch
from tests.multistage_fixture import make_case, make_v3_case


def _manifest(cases, path):
    files = {}
    for name in [p.name for p in cases.iterdir()]:
        files[name] = {'file_sha256': {f'eval/multistage_cases/{name}/{p.relative_to(cases / name).as_posix()}':
                                       hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in sorted((cases / name).rglob('*')) if p.is_file()},
                       'sha256': 'frozen-' + name}
    path.write_text(json.dumps({'commit': 'abc', 'cases': files}), encoding='utf-8')
    return path


@pytest.fixture
def setup(tmp_path, monkeypatch):
    cases = tmp_path / 'cases'
    cases.mkdir()
    make_case(tmp_path / 'built')
    shutil.copytree(tmp_path / 'built' / 'fixture', cases / 'fixture')
    (tmp_path / 'frozen').mkdir()
    manifest = _manifest(cases, tmp_path / 'frozen' / 'manifest.json')
    monkeypatch.setattr(m.subscription, 'auth', lambda *a: True)
    protocol = m.prepare(tmp_path / 'batch', ['fixture'], replicates=1, seconds=60, cases=cases, manifest=manifest)
    return SimpleNamespace(root=tmp_path, cases=cases, manifest=manifest, protocol=protocol, batch=tmp_path / 'batch')


def _host(case_root, plan=None, *, model='claude-sonnet-5-5', plugins=True, marker=None, session=None, tools=()):
    """plan maps a stage to 'reference' (default), 'dependent-missed', 'docs-forgotten', 'nothing' or 'timeout'."""
    plan, actual, spent, calls = plan or {}, m.run, {}, []
    case = json.loads((case_root / 'case.json').read_text(encoding='utf-8'))

    def external(command, **kwargs):
        if not (isinstance(command, list) and command[0] == 'fake-host'):
            return actual(command, **kwargs)
        if command[-1] == '--version':
            return SimpleNamespace(returncode=0, stdout='fake test host', stderr='')
        root = Path(kwargs['cwd'])
        prompt = command[2]
        stage = next(n for n, s in enumerate(case['stages'], 1) if s['request'] in prompt)
        sealed = command[command.index('--session-id' if '--session-id' in command else '--resume') + 1]
        calls.append({'stage': stage, 'command': command, 'env': kwargs['env'], 'prompt': prompt})
        what = plan.get(stage, 'reference')
        docs = (root / case['docs']).read_bytes()
        if what != 'nothing' and what != 'timeout':
            diffs = ['reference'] + (['dependent-missed'] if what == 'dependent-missed' else [])
            for name in diffs:
                trouble = apply_patch(root, (case_root / 'stages' / str(stage) / f'{name}.diff').read_text(encoding='utf-8'))
                assert not trouble, trouble
            if what == 'docs-forgotten':
                (root / case['docs']).write_bytes(docs)
        armed = (root / '.claude' / 'settings.local.json').exists()
        shown = armed if marker is None else marker
        spent[sealed] = spent.get(sealed, 0) + 0.25
        events = [
            {'type': 'system', 'subtype': 'hook_response', 'hook_name': 'SessionStart:startup',
             'output': json.dumps({'hookSpecificOutput': {'additionalContext': 'ElevenPowers active (profile: guide).'}})}
            if shown else {'type': 'system', 'subtype': 'hook_started'},
            {'type': 'system', 'subtype': 'init', 'session_id': sealed,
             'plugins': [{'source': 'superpowers@claude-plugins-official'}] if plugins else []},
            {'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'name': name, 'input': value}
                                                          for name, value in tools]}},
            {'type': 'result', 'is_error': False, 'session_id': session or sealed, 'result': 'done',
             'total_cost_usd': spent[sealed], 'modelUsage': {model: {}}},
        ]
        output = '\n'.join(json.dumps(e) for e in events)
        if what == 'timeout':
            raise subprocess.TimeoutExpired(command, kwargs['timeout'], output=output.split('\n')[0])
        return SimpleNamespace(returncode=0, stdout=output, stderr='')
    external.calls = calls
    return external


def _slot(setup, arm):
    return next(s for s in setup.protocol['slots'] if f'--{arm}--' in s)


def test_slots_pair_the_arms_and_the_first_arm_alternates(tmp_path):
    cases = tmp_path / 'cases'
    make_case(tmp_path / 'built')
    for name in ('one', 'two'):
        shutil.copytree(tmp_path / 'built' / 'fixture', cases / name)
    (tmp_path / 'frozen').mkdir()
    manifest = _manifest(cases, tmp_path / 'frozen' / 'manifest.json')
    protocol = m.prepare(tmp_path / 'batch', ['one', 'two'], replicates=2, seconds=60, cases=cases, manifest=manifest)
    assert protocol['slots'][:4] == ['one--superpowers--0', 'one--elevenpowers--0',
                                     'two--elevenpowers--0', 'two--superpowers--0']
    assert protocol['slots'][4:6] == ['one--elevenpowers--1', 'one--superpowers--1']
    assert len(set(protocol['sessions'].values())) == 8


def test_a_case_that_differs_from_the_frozen_manifest_is_refused(setup):
    with pytest.raises(ValueError, match='new batch'):
        m.prepare(setup.batch, ['fixture'], replicates=1, cases=setup.cases, manifest=setup.manifest)
    (setup.cases / 'fixture' / 'oracle' / 'facts.json').write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError, match='frozen'):
        m.prepare(setup.root / 'other', ['fixture'], replicates=1, cases=setup.cases, manifest=setup.manifest)
    with pytest.raises(ValueError, match='frozen'):
        m.verify(setup.batch, _slot(setup, 'superpowers'))


def test_a_batch_under_a_folder_with_instructions_is_refused(setup):
    parent = setup.root / 'project'
    parent.mkdir()
    (parent / 'CLAUDE.md').write_text('# rules\n', encoding='utf-8')
    with pytest.raises(ValueError, match='CLAUDE.md'):
        m.prepare(parent / 'batch', ['fixture'], replicates=1, cases=setup.cases, manifest=setup.manifest)


def test_both_arms_load_superpowers_and_only_one_loads_elevenpowers(setup, monkeypatch):
    host = _host(setup.cases / 'fixture', {n: 'nothing' for n in range(1, 7)})
    monkeypatch.setattr(m, 'run', host)
    for arm in m.ARMS:
        m.execute(setup.batch, _slot(setup, arm), 'fake-host')
        work = setup.batch / _slot(setup, arm) / 'work'
        settings = json.loads((work / '.claude' / 'settings.json').read_text(encoding='utf-8'))
        assert settings['enabledPlugins'] == {m.SUPERPOWERS: True}
        assert (work / '.claude' / 'settings.local.json').exists() == (arm == 'elevenpowers')
        assert (work / '.elevenpowers' / 'config.json').exists() == (arm == 'elevenpowers')
        assert not (work / '.venv').exists()
    first = host.calls[0]['command']
    assert 'Skill' in first[first.index('--tools') + 1].split(',')
    assert 'Agent' in first[first.index('--disallowedTools'):]
    assert '--session-id' in first and '--resume' in host.calls[1]['command']
    assert '--no-session-persistence' not in first
    assert host.calls[0]['env']['ANTHROPIC_DEFAULT_HAIKU_MODEL'] == 'claude-sonnet-5-5'


def test_the_request_reaches_the_agent_verbatim_with_one_fixed_sentence(setup, monkeypatch):
    host = _host(setup.cases / 'fixture')
    monkeypatch.setattr(m, 'run', host)
    m.execute(setup.batch, _slot(setup, 'superpowers'), 'fake-host')
    case = json.loads((setup.cases / 'fixture' / 'case.json').read_text(encoding='utf-8'))
    assert [c['prompt'] for c in host.calls] == [s['request'] + '\n\n' + m.UNATTENDED for s in case['stages']]
    assert not any(word in m.UNATTENDED.lower() for word in ('doc', 'test', 'changelog', 'depend', 'claude.md'))


def test_the_reference_agent_loses_nothing_and_leaves_nothing_stale(setup, monkeypatch):
    monkeypatch.setattr(m, 'run', _host(setup.cases / 'fixture'))
    record = m.execute(setup.batch, _slot(setup, 'superpowers'), 'fake-host')
    assert record['state'] == 'completed' and len(record['stages']) == 6
    assert [s['cost'] for s in record['stages']] == [0.25] * 6
    assert record['grade']['lost'] == 0 and record['grade']['stale'] == 0
    assert all(s['protected'] for s in record['grade']['stages'])


# Later reference diffs do not apply to a broken tree, so the agent does nothing after the mistake.
MISSED = {2: 'dependent-missed', **{n: 'nothing' for n in range(3, 7)}}


def test_a_missed_dependent_is_counted_once_at_the_stage_it_happens(setup, monkeypatch):
    monkeypatch.setattr(m, 'run', _host(setup.cases / 'fixture', MISSED))
    record = m.execute(setup.batch, _slot(setup, 'superpowers'), 'fake-host')
    assert [s['lost'] for s in record['grade']['stages']] == [[], ['use'], [], [], [], []]
    assert record['grade']['lost'] == 1


def test_forgotten_docs_are_stale_from_the_stage_they_were_forgotten(setup, monkeypatch):
    monkeypatch.setattr(m, 'run', _host(setup.cases / 'fixture', {4: 'docs-forgotten', 5: 'nothing', 6: 'nothing'}))
    record = m.execute(setup.batch, _slot(setup, 'superpowers'), 'fake-host')
    stale = [s['stale'] for s in record['grade']['stages']]
    assert stale[:3] == [[], [], []] and stale[3] == ['default']
    assert record['grade']['stale'] == sum(len(s) for s in stale) and record['grade']['lost'] == 0


def test_a_launched_slot_is_never_relaunched(setup, monkeypatch):
    monkeypatch.setattr(m, 'run', _host(setup.cases / 'fixture'))
    slot = _slot(setup, 'superpowers')
    m.execute(setup.batch, slot, 'fake-host')
    with pytest.raises(ValueError, match='never retry'):
        m.execute(setup.batch, slot, 'fake-host')


@pytest.mark.parametrize('trouble, state', [
    ({'marker': True}, 'plugins_unqualified'),
    ({'plugins': False}, 'plugins_unqualified'),
    ({'model': 'claude-opus-5-5'}, 'model_unqualified'),
    ({'session': 'another'}, 'conversation_unqualified'),
    ({'tools': [('Read', {'file_path': '{cases}/fixture/oracle/facts.json'})]}, 'closed_book_breach'),
    ({'tools': [('Bash', {'command': 'curl https://example.invalid'})]}, 'closed_book_breach'),
])
def test_an_unqualified_turn_ends_the_conversation_and_is_not_comparable(setup, monkeypatch, trouble, state):
    if 'tools' in trouble:
        trouble = {'tools': [(n, {k: v.replace('{cases}', str(setup.cases)) for k, v in i.items()})
                             for n, i in trouble['tools']]}
    monkeypatch.setattr(m, 'run', _host(setup.cases / 'fixture', **trouble))
    record = m.execute(setup.batch, _slot(setup, 'superpowers'), 'fake-host')
    assert [s['state'] for s in record['stages']] == [state]
    assert record['state'] == 'incomplete'


def test_a_plain_read_inside_the_project_is_not_a_breach(setup, monkeypatch):
    monkeypatch.setattr(m, 'run', _host(setup.cases / 'fixture', tools=[('Read', {'file_path': 'src/pkg/core.py'})]))
    assert m.execute(setup.batch, _slot(setup, 'superpowers'), 'fake-host')['state'] == 'completed'


def test_only_a_bash_command_is_read_for_network_access(setup):
    described = {'name': 'Bash', 'input': {'command': 'ls', 'description': 'curl the docs page'}}
    reaching = {'name': 'Bash', 'input': {'command': 'curl https://example.invalid', 'description': 'list'}}
    assert m._breaches([described], setup.cases, setup.manifest) == []
    assert len(m._breaches([reaching], setup.cases, setup.manifest)) == 1


def test_a_timeout_is_kept_graded_and_stops_the_conversation(setup, monkeypatch):
    monkeypatch.setattr(m, 'run', _host(setup.cases / 'fixture', {3: 'timeout'}))
    record = m.execute(setup.batch, _slot(setup, 'superpowers'), 'fake-host')
    assert [s['state'] for s in record['stages']] == ['completed', 'completed', 'timeout']
    assert record['state'] == 'incomplete'
    assert len(record['grade']['stages']) == 3 and record['grade']['stages'][2]['stale']


def test_collect_counts_every_slot_and_regrades_from_snapshots(setup, monkeypatch):
    monkeypatch.setattr(m, 'run', _host(setup.cases / 'fixture', MISSED))
    slot = _slot(setup, 'superpowers')
    m.execute(setup.batch, slot, 'fake-host')
    (setup.batch / slot / 'work').rename(setup.root / 'moved-away')
    path = setup.batch / slot / 'result.json'
    stored = json.loads(path.read_text(encoding='utf-8'))
    path.write_text(json.dumps({k: v for k, v in stored.items() if k != 'grade'}), encoding='utf-8')
    rows = {r['slot']: r for r in m.collect(setup.batch, regrade=True)}
    assert rows[slot]['lost'] >= 1 and rows[slot]['comparable']
    assert rows[_slot(setup, 'elevenpowers')]['state'] == 'not_launched'
    assert not rows[_slot(setup, 'elevenpowers')]['comparable']


def test_a_last_stage_timeout_is_graded_but_not_comparable(setup, monkeypatch):
    monkeypatch.setattr(m, 'run', _host(setup.cases / 'fixture', {6: 'timeout'}))
    slot = _slot(setup, 'superpowers')
    m.execute(setup.batch, slot, 'fake-host')
    row = next(r for r in m.collect(setup.batch) if r['slot'] == slot)
    assert len(row['grade']['stages']) == 6 and not row['comparable']


def test_headroom_is_read_from_complete_superpowers_conversations_only():
    rows = [{'arm': 'elevenpowers', 'comparable': True, 'lost': 3, 'stale': 2},
            {'arm': 'superpowers', 'comparable': True, 'lost': 0, 'stale': 0},
            {'arm': 'superpowers', 'comparable': False, 'lost': 2, 'stale': 5}]
    assert m.headroom(rows) is False
    assert m.headroom(rows + [{'arm': 'superpowers', 'comparable': True, 'lost': 0, 'stale': 1}]) is True


def test_a_v3_case_runs_all_eight_stages(tmp_path, monkeypatch):
    cases = tmp_path / 'v3'
    cases.mkdir()
    make_v3_case(tmp_path / 'built')
    shutil.copytree(tmp_path / 'built' / 'fixture3', cases / 'fixture3')
    (tmp_path / 'frozen').mkdir()
    manifest = _manifest(cases, tmp_path / 'frozen' / 'manifest.json')
    monkeypatch.setattr(m.subscription, 'auth', lambda *a: True)
    protocol = m.prepare(tmp_path / 'batch', ['fixture3'], replicates=1, seconds=60, cases=cases, manifest=manifest)
    monkeypatch.setattr(m, 'run', _host(cases / 'fixture3'))
    slot = protocol['slots'][0]
    record = m.execute(tmp_path / 'batch', slot, 'fake-host')
    assert record['state'] == 'completed' and len(record['stages']) == 8
    assert record['grade']['lost'] == 0 and record['grade']['stale'] == 0
    assert next(r for r in m.collect(tmp_path / 'batch') if r['slot'] == slot)['comparable']


def test_reading_the_manifests_folder_is_a_breach(setup, monkeypatch):
    peek = [('Read', {'file_path': str(setup.manifest.parent / 'review.json')})]
    monkeypatch.setattr(m, 'run', _host(setup.cases / 'fixture', tools=peek))
    record = m.execute(setup.batch, _slot(setup, 'superpowers'), 'fake-host')
    assert [s['state'] for s in record['stages']] == ['closed_book_breach']


def test_a_batch_inside_the_withheld_folders_is_refused(setup):
    for inside in (setup.manifest.parent / 'batch', setup.cases / 'batch'):
        with pytest.raises(ValueError, match='withheld'):
            m.prepare(inside, ['fixture'], replicates=1, cases=setup.cases, manifest=setup.manifest)
