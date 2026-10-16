"""Owned batches keep independent outcomes under a single actual owner."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from core.config import Config, save
from core.evidence import Result
from core.jobs import Session, read
from core.ledger import Ledger


def project(root, *, failure=False, mutation=''):
    for name in ('tests','build'):
        body=("from pathlib import Path\n"
              f"Path('.elevenpowers/{name}-launched').write_text('yes')\n"
              +(mutation+'\n' if name=='tests' else '')
              +("print('not ok 1 - broken'); raise SystemExit(1)\n" if failure and name=='tests' else "print('ok 1 - works')\n"))
        (root/f'{name}.py').write_text(body)
    commands={p:f'"{sys.executable}" {p}.py' for p in ('tests','build')}
    save(root,Config(profile='guide',auto_detect=False,commands=commands))
    Ledger(root=root,task='batch-subject').save()
    return commands


def execute(root, **kwargs):
    assert importlib.util.find_spec('core.check_batch') is not None, 'Owned batch execution is missing'
    from core.check_batch import execute
    return execute(root,**kwargs)


@pytest.mark.parametrize('failure',[False,True])
def test_real_independent_results_continue_after_failure_under_one_owner(tmp_path,failure):
    project(tmp_path,failure=failure)
    value=execute(tmp_path)
    assert value['schema_version']==2 and value['selected']==['tests','build']
    assert value['state']==('failed' if failure else 'passed')
    assert [r['state'] for r in value['results']]==(['failed','passed'] if failure else ['passed','passed'])
    assert (tmp_path/'.elevenpowers/build-launched').exists()
    data=read(tmp_path)
    rows=[r for r in data['checks'] if r['run']==data['id']]
    assert len(rows)==2 and {r['phase'] for r in rows}=={'declared check tests','declared check build'}
    assert len({r['run'] for r in rows})==1
    evidence=[e for e in Ledger.load(tmp_path).evidence if e.owned_execution]
    assert {e.declaration for e in evidence}=={'tests','build'}
    from core.parsers import DECLARED_KINDS
    for property in ('tests','build'):
        latest=[e for e in evidence if e.declaration==property and e.kind is DECLARED_KINDS[property]][-1]
        assert latest.result is (Result.FAIL if failure and property=='tests' else Result.PASS)


@pytest.mark.parametrize('mutation',[
    "import json; p=Path('.elevenpowers/ledger.json'); v=json.loads(p.read_text()); v['task']='replacement'; p.write_text(json.dumps(v))",
    "import json; p=Path('.elevenpowers/config.json'); v=json.loads(p.read_text()); v['profile']='strict'; p.write_text(json.dumps(v))"
])
def test_actual_identity_movement_refuses_later_property_without_hiding_selection(tmp_path,mutation):
    project(tmp_path,mutation=mutation)
    value=execute(tmp_path)
    assert value['state']=='incomplete' and value['selected']==['tests','build']
    assert [r['state'] for r in value['results']]==['incomplete','incomplete']
    assert value['results'][1]['unrun'] is True
    assert not (tmp_path/'.elevenpowers/build-launched').exists()
    assert len(read(tmp_path)['checks'])==2


def test_producer_change_between_properties_refuses_remaining_execution(tmp_path,monkeypatch):
    import core.checks as checks
    project(tmp_path)
    original_run=checks._run
    original_context=checks.context
    def moving(*args):
        done=original_run(*args)
        monkeypatch.setattr(checks,'context',lambda root:{**original_context(root),'producer':'f'*64})
        return done
    monkeypatch.setattr(checks,'_run',moving)
    value=execute(tmp_path)
    assert value['state']=='incomplete' and value['results'][1]['unrun']
    assert not (tmp_path/'.elevenpowers/build-launched').exists()


@pytest.mark.parametrize('mode',['off','busy','empty'])
def test_refusal_launches_nothing_and_does_not_steal_an_owner(tmp_path,mode):
    commands=project(tmp_path)
    if mode=='off':save(tmp_path,Config(profile='off',auto_detect=False,commands=commands))
    if mode=='empty':save(tmp_path,Config(profile='guide',auto_detect=False))
    if mode=='busy':
        with Session(tmp_path,'batch-subject'):
            before=(tmp_path/'.elevenpowers/verification.json').read_bytes()
            value=execute(tmp_path)
            assert (tmp_path/'.elevenpowers/verification.json').read_bytes()==before
    else:value=execute(tmp_path)
    assert value['state']=='incomplete'
    assert not (tmp_path/'.elevenpowers/tests-launched').exists()
    assert not (tmp_path/'.elevenpowers/build-launched').exists()


@pytest.mark.parametrize('seconds',[0,-1,float('nan'),float('inf'),601,True])
def test_invalid_total_budget_is_refused_before_ownership(tmp_path,seconds):
    project(tmp_path)
    with pytest.raises(ValueError):execute(tmp_path,seconds=seconds)
    assert not (tmp_path/'.elevenpowers/verification.json').exists()


def test_shared_deadline_leaves_later_selection_explicitly_unrun(tmp_path,monkeypatch):
    import core.checks as checks
    from core.jobs import current
    project(tmp_path)
    original=checks._execute
    def exhausted(root,property,session,**kwargs):
        done=original(root,property,session,**kwargs)
        current().budget.deadline=0
        return done
    monkeypatch.setattr(checks,'_execute',exhausted)
    value=execute(tmp_path)
    assert value['state']=='incomplete' and len(value['results'])==2
    assert value['results'][0]['state']=='passed'
    assert value['results'][1]['unrun'] is True and value['results'][1]['attempt'] is None
    assert not (tmp_path/'.elevenpowers/build-launched').exists()
    assert read(tmp_path)['checks'][1]['status']=='deferred'


def test_configuration_moving_after_completed_first_result_cannot_be_adopted_by_next(tmp_path,monkeypatch):
    import core.checks as checks
    project(tmp_path)
    original=checks._execute
    def completed(root,property,session,**kwargs):
        result=original(root,property,session,**kwargs)
        path=root/'.elevenpowers/config.json'
        value=json.loads(path.read_text()); value['profile']='strict'
        path.write_text(json.dumps(value))
        return result
    monkeypatch.setattr(checks,'_execute',completed)
    value=execute(tmp_path)
    assert value['state']=='incomplete' and value['results'][0]['state']=='passed'
    assert value['results'][1]['unrun']
    assert not (tmp_path/'.elevenpowers/build-launched').exists()


def test_identity_movement_after_final_result_does_not_certify_batch(tmp_path,monkeypatch):
    import core.checks as checks
    project(tmp_path)
    original=checks._execute
    def moving(root,property,session,**kwargs):
        result=original(root,property,session,**kwargs)
        if property=='build':
            path=root/'.elevenpowers/config.json'
            value=json.loads(path.read_text()); value['profile']='strict'
            path.write_text(json.dumps(value))
        return result
    monkeypatch.setattr(checks,'_execute',moving)
    value=execute(tmp_path)
    assert [r['state'] for r in value['results']]==['passed','passed']
    assert value['state']=='incomplete' and value['issues']


def test_interrupt_preserves_provisional_receipt_and_whole_queued_denominator(tmp_path,monkeypatch):
    import core.checks as checks
    project(tmp_path)
    def interrupted(*args):raise KeyboardInterrupt()
    monkeypatch.setattr(checks,'_run',interrupted)
    with pytest.raises(KeyboardInterrupt):execute(tmp_path)
    rows=read(tmp_path)['checks']
    assert len(rows)==2 and [r['status'] for r in rows]==['incomplete','deferred']
    records=[e for e in Ledger.load(tmp_path).evidence if e.declaration=='tests']
    assert records and records[-1].execution=='incomplete'
    assert not (tmp_path/'.elevenpowers/build-launched').exists()


def test_actual_incomplete_source_coverage_reports_no_child_execution(tmp_path):
    commands=project(tmp_path)
    save(tmp_path,Config(profile='guide',auto_detect=False,commands=commands,scan={'max_files':1}))
    value=execute(tmp_path)
    assert value['state']=='incomplete' and len(value['results'])==2
    assert all(r['unrun'] for r in value['results'])
    assert not (tmp_path/'.elevenpowers/tests-launched').exists()
    assert not (tmp_path/'.elevenpowers/build-launched').exists()


def test_selection_movement_before_identity_capture_cannot_replace_frozen_commands(tmp_path,monkeypatch):
    import core.checks as checks
    commands=project(tmp_path)
    (tmp_path/'replacement.py').write_text("from pathlib import Path\nPath('.elevenpowers/replacement-launched').write_text('bad')\n")
    original=checks._config
    changed=False
    def selected(root):
        nonlocal changed
        config=original(root)
        if not changed:
            changed=True
            save(root,Config(profile='guide',auto_detect=False,
                commands={**commands,'build':f'"{sys.executable}" replacement.py'}))
        return config
    monkeypatch.setattr(checks,'_config',selected)
    value=execute(tmp_path)
    assert value['state']=='incomplete'
    assert value['selected']==['tests','build'] and len(value['results'])==2
    assert all(r['unrun'] for r in value['results'])
    assert not (tmp_path/'.elevenpowers/replacement-launched').exists()


@pytest.mark.parametrize('change',['command','producer'])
def test_movement_after_outer_guard_is_refused_by_the_child_entry(tmp_path,monkeypatch,change):
    import core.checks as checks
    commands=project(tmp_path)
    (tmp_path/'replacement.py').write_text("from pathlib import Path\nPath('.elevenpowers/replacement-launched').write_text('bad')\n")
    original=checks._execute
    original_context=checks.context
    def interleaved(root,property,session,**kwargs):
        if property=='build':
            if change=='command':
                save(root,Config(profile='guide',auto_detect=False,
                    commands={**commands,'build':f'"{sys.executable}" replacement.py'}))
            else:
                monkeypatch.setattr(checks,'context',lambda root:{**original_context(root),'producer':'f'*64})
        return original(root,property,session,**kwargs)
    monkeypatch.setattr(checks,'_execute',interleaved)
    value=execute(tmp_path)
    assert value['state']=='incomplete' and value['results'][0]['state']=='passed'
    assert value['results'][1]['unrun']
    assert not (tmp_path/'.elevenpowers/build-launched').exists()
    assert not (tmp_path/'.elevenpowers/replacement-launched').exists()
