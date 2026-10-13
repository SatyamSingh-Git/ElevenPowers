"""Witnessed whole-branch review boundaries using real commands and state."""
from contextlib import contextmanager
import json

import pytest

from core.evidence import Freshness
from core.ledger import Ledger
from core.obligations import Claim
from tests.test_external_input_reuse import dependency_project
from tests.test_input_native import event,completed
from tests.test_input_sessions_gap import session_project,native_check


@pytest.mark.parametrize('mode',['post-only','pending-eviction','completed-eviction'])
def test_forgotten_identity_never_pairs_a_delayed_result(dependency_project,monkeypatch,mode):
    from core.inputs import native
    from core.inputs.receipts import inspect
    root,_,_,_,args,command=session_project(dependency_project)
    one,two=event(root,command),event(root,command,call='other-call')
    if mode!='post-only': native.before(one,root)
    old=completed(root,args,command)
    if mode=='post-only':
        assert native.after(one,root,old)
        assert inspect(old[-1],root)['state']=='incomplete'
    elif mode=='pending-eviction':
        monkeypatch.setattr(native,'MAX_PENDING',1)
        native.before(two,root)
    else:
        monkeypatch.setattr(native,'MAX_COMPLETED',1)
        assert native.after(one,root,old)
        assert inspect(old[-1],root)['state']=='bound'
        native.before(two,root)
        legitimate=completed(root,args,command)
        assert native.after(two,root,legitimate)
        assert inspect(legitimate[-1],root)['state']=='bound'
    count=(root/'.elevenpowers/count.txt').read_text()
    native.before(one,root)
    replay=[type(r).from_dict(r.to_dict()) for r in old]
    accepted=native.after(one,root,replay)
    assert not accepted or inspect(replay[-1],root)['state']=='incomplete'
    assert (root/'.elevenpowers/count.txt').read_text()==count


@pytest.mark.parametrize('phase',['capture','save-lock'])
def test_native_pre_cannot_replace_a_successor_task(dependency_project,monkeypatch,phase):
    from core.inputs import native
    from core import jobs
    root,_,_,_,args,command=session_project(dependency_project)
    def replacement():
        return Ledger(root=root,task='replacement',request='replacement work',claims=[Claim.FEATURE_ADDED])
    if phase=='capture':
        original=native.capture
        def changed(path,deadline):
            value=original(path,deadline);replacement().save();return value
        monkeypatch.setattr(native,'capture',changed)
    else:
        original=native.ledger_write
        @contextmanager
        def changed(path,**kwargs):
            with original(path,**kwargs):
                replacement()._save_locked()
                yield
        monkeypatch.setattr(native,'ledger_write',changed)
    native.before(event(root,command),root)
    saved=Ledger.load(root)
    assert (saved.task,saved.request,saved.claims)==('replacement','replacement work',[Claim.FEATURE_ADDED])
    if phase=='save-lock': monkeypatch.setattr(native,'ledger_write',original)
    records=completed(root,args,command)
    native.after(event(root,command),root,records)
    from core.inputs.receipts import inspect
    assert inspect(records[-1],root)['state']=='incomplete'
    assert Ledger.load(root).task=='replacement'


def test_unidentified_pre_cannot_lose_required_scope_when_policy_removed(dependency_project):
    from core.inputs import native
    from core.inputs.receipts import inspect
    root,_,_,_,args,command=session_project(dependency_project)
    payload=event(root,command);payload.pop('tool_use_id')
    native.before(payload,root)
    (root/'elevenpowers.inputs.json').unlink()
    records=completed(root,args,command)
    assert records[-1].source_freshness(root) is Freshness.FRESH
    assert native.after(payload,root,records)
    assert inspect(records[-1],root)['state']=='incomplete'
    assert records[-1].freshness(root) is Freshness.STALE


@pytest.mark.parametrize('moving',['source','configuration','external'])
def test_closing_changes_invalidate_all_public_claims(dependency_project,monkeypatch,moving):
    from core.inputs import definition
    from core.export import build
    root,_,target,language,args,command=session_project(dependency_project)
    ledger=Ledger.load(root);ledger.claims=[Claim.REFACTOR_SAFE];ledger.save()
    assert native_check(root,args,command).returncode==0
    initial=build(root)
    assert initial['state']=='VERIFIED'
    assert initial['task']['claims'][0]['state']=='VERIFIED'
    original=definition.raw;reads=[]
    def changed(path,*a,**kwargs):
        if path==target:
            reads.append(path)
            if len(reads)==2:
                if moving=='external': target.write_bytes(b'value=9\n' if language=='python' else b'module.exports={value:9};\n')
                elif moving=='source': (root/'service.py').write_bytes(b'value=9\n')
                else:
                    config=root/'.elevenpowers/config.json';value=json.loads(config.read_text())
                    value['commands']['tests']=command+' --changed';config.write_text(json.dumps(value))
        return original(path,*a,**kwargs)
    monkeypatch.setattr(definition,'raw',changed)
    value=build(root)
    assert not value['coverage']['complete']
    assert value['state']!='VERIFIED'
    assert value['receipts'][-1]['freshness']!='fresh'
    assert value['task']['claims'][0]['state']!='VERIFIED'
    assert value['task']['claims'][0]['checks'][0]['freshness']!='fresh'
    assert value['milestones']['state']!='CURRENT'
    assert value['milestones']['milestones'][0]['checks'][0]['state']!='CURRENT'
    assert value['receipts'][-1]['result']=='pass', 'original actual outcome stays visible'
