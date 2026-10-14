"""Nested reports share external phases, never source qualifications."""
from core.inputs import definition
from core.ledger import Ledger
from core.patchproof.report import build
from tests.test_patchproof_identity import commit
from tests.test_input_scopes import scoped_project, observed_run
from tests.test_external_input_reuse import dependency_project
import time


def saved_consumers(scoped_project):
    root,target,other,commands,*_=scoped_project
    base=commit(root,'two independent consumers')
    (root/'service.py').write_text('value=3\n')
    head=commit(root,'service change')
    ledger=Ledger.load(root)
    for command in commands:
        _,records=observed_run(root,command)
        ledger.add(records)
    ledger.save()
    return root,target,other,commands,base,head


def test_closing_drift_invalidates_only_affected_export_scope(scoped_project,monkeypatch):
    from core.export import build as export
    from core.inputs import collection
    root,target,other,commands,base,head=saved_consumers(scoped_project)
    original=collection.capture
    count=0
    def mutate(root,deadline):
        nonlocal count
        count+=1
        if count==2:
            target.write_text('value=9\n' if target.suffix=='.py' else 'module.exports={value:9};\n')
        return original(root,deadline)
    monkeypatch.setattr(collection,'capture',mutate)
    report=export(root,timeout=120)
    rows={r['declaration']:r for r in report['receipts'] if r['declaration']}
    assert not report['coverage']['complete']
    assert rows['tests']['external_inputs']['state']=='incomplete'
    assert rows['build']['external_inputs']['state']=='bound'
    assert rows['build']['freshness']=='fresh'


def test_shared_collections_do_not_survive_operations_or_hide_closing_drift(scoped_project,monkeypatch):
    root,target,other,commands,base,head=saved_consumers(scoped_project)
    original=definition.raw
    count=0
    def mutate(path,*args,**kwargs):
        nonlocal count
        if path==target:
            count+=1
            if count==2:
                path.write_text('value=9\n' if path.suffix=='.py' else 'module.exports={value:9};\n')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(definition,'raw',mutate)
    report=build(root,base,head,timeout=120)
    assert report['binding']['state']=='unavailable'
    assert count==2
    second=build(root,base,head,timeout=120)
    assert count==4
    rows={r['declaration']:r for r in second['receipts'] if r['declaration']}
    assert rows['tests']['external_inputs']['state']=='stale'
    assert rows['build']['external_inputs']['state']=='bound'


def test_patchproof_nested_reports_read_each_input_only_twice(scoped_project,monkeypatch):
    root,target,other,commands,*_=scoped_project
    base=commit(root,'two independent consumers')
    (root/'service.py').write_text('value=3\n')
    head=commit(root,'service change')
    _,records=observed_run(root,commands[1])
    ledger=Ledger.load(root);ledger.add(records);ledger.save()
    reads=[]
    original=definition.raw
    def count(path,*args,**kwargs):
        if path in (target,other): reads.append(path)
        return original(path,*args,**kwargs)
    monkeypatch.setattr(definition,'raw',count)
    report=build(root,base,head,timeout=120)
    assert report['binding']['state']=='bound',report['binding']
    assert reads.count(target)==reads.count(other)==2,reads
