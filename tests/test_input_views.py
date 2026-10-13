"""Public consumers separate source facts from qualified external execution."""
import json

import pytest

from core.ledger import Ledger
from tests.test_external_input_reuse import dependency_project
from tests.test_input_sessions_gap import session_project,native_check


@pytest.mark.parametrize('mode',['unchanged','drift','missing','legacy'])
def test_reports_and_milestones_explain_external_qualification(dependency_project,mode):
    from core.export import build,markdown
    from core.milestones import build as milestones
    from core.patchproof.report import build as patchproof
    root,head,target,language,args,command=session_project(dependency_project)
    assert native_check(root,args,command).returncode==0
    if mode=='drift': target.write_bytes(b'value=9\n' if language=='python' else b'module.exports={value:9};\n')
    elif mode=='missing': target.unlink()
    elif mode=='legacy':
        # Remove metadata from preserved history too; current reads cannot invent it.
        path=root/'.elevenpowers/ledger.json'
        value=json.loads(path.read_text())
        for row in value['evidence']+value.get('milestone_history',{}).get('receipts',[]):
            row.pop('external_inputs',None)
        path.write_text(json.dumps(value))
    report=build(root)
    expected={'unchanged':'bound','drift':'stale','missing':'incomplete','legacy':'incomplete'}[mode]
    receipt=report['receipts'][-1]
    assert receipt['result']=='pass'
    assert receipt['source_freshness']=='fresh'
    assert receipt['external_inputs']['state']==expected
    assert 'External inputs' in markdown(report)
    retained=milestones(root)
    check=retained['milestones'][0]['checks'][0]
    assert check['source_freshness']=='fresh'
    assert check['external_inputs']['state']==expected
    assert check['state']=={'bound':'CURRENT','stale':'STALE','incomplete':'INCOMPLETE'}[expected]
    if mode!='unchanged': assert retained['next_actions']
    bundle=patchproof(root,'HEAD~1',head,timeout=120)
    assert bundle['receipts'][-1]['source_freshness']=='fresh'
    assert bundle['receipts'][-1]['external_inputs']['state']==expected
    assert str(target.parent) not in json.dumps([report,retained,bundle])
    assert (root/'.elevenpowers/count.txt').read_text()=='1','views must launch no checks'


def test_closing_external_drift_cannot_leave_bound_export_rows(dependency_project,monkeypatch):
    from core.inputs import collection
    from core.export import build
    root,_,target,language,args,command=session_project(dependency_project)
    assert native_check(root,args,command).returncode==0
    original=collection.capture;calls=[]
    def moving(path,deadline):
        calls.append(path)
        if len(calls)==2:
            target.write_bytes(b'value=9\n' if language=='python' else b'module.exports={value:9};\n')
        return original(path,deadline)
    monkeypatch.setattr(collection,'capture',moving)
    report=build(root)
    assert not report['coverage']['complete']
    assert report['receipts'][-1]['external_inputs']['state']=='incomplete'
    assert report['receipts'][-1]['freshness']=='stale'
    assert report['milestones']['state']=='INCOMPLETE'
    assert report['milestones']['milestones'][0]['checks'][0]['state']=='INCOMPLETE'
    assert len(calls)==2, 'one bounded shared view, not a separate collection per receipt'
