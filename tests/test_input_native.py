"""Native association uses identified calls and actual observed command results."""
import json
import subprocess
import time

import pytest

from core.ledger import Ledger
from core.parsers import parse
from tests.test_external_input_reuse import dependency_project
from tests.test_input_sessions_gap import session_project


def event(root,command,call='call-one',session='session-one',platform='claude'):
    return {'cwd':str(root),'_ep_platform':platform,'session_id':session,'tool_use_id':call,
            'tool_name':'Bash','tool_input':{'command':command}}


def completed(root,args,command):
    done=subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=20)
    return parse(command,done.stdout+done.stderr,done.returncode,root)


def test_actual_native_pair_qualifies_once(dependency_project):
    from core.inputs.native import before,after
    from core.inputs.receipts import inspect
    root,_,_,_,args,command=session_project(dependency_project)
    payload=event(root,command)
    before(payload,root)
    records=completed(root,args,command)
    assert after(payload,root,records)
    assert inspect(records[-1],root)['state']=='bound'
    replay=[type(r).from_dict(r.to_dict()) for r in records]
    assert not after(payload,root,replay), 'delivery replay cannot create another receipt'
    assert (root/'.elevenpowers/count.txt').read_text()=='1'


@pytest.mark.parametrize('change',['missing','session','call','command','task','duplicate'])
def test_unpaired_or_ambiguous_events_cannot_qualify(dependency_project,change):
    from core.inputs.native import before,after
    from core.inputs.receipts import inspect
    root,_,_,_,args,command=session_project(dependency_project)
    payload=event(root,command)
    if change!='missing': before(payload,root)
    if change=='session': payload['session_id']='other-session'
    if change=='call': payload['tool_use_id']='other-call'
    if change=='command': payload['tool_input']={'command':command+' '}
    if change=='task': Ledger(root=root,task='new-task').save()
    if change=='duplicate': before(payload,root)
    records=completed(root,args,command)
    assert after(payload,root,records)
    assert inspect(records[-1],root)['state']=='incomplete'


def test_concurrent_identified_calls_remain_separate(dependency_project):
    from core.inputs.native import before,after
    from core.inputs.receipts import inspect
    root,_,_,_,args,command=session_project(dependency_project)
    one,two=event(root,command),event(root,command,call='call-two')
    before(one,root); before(two,root)
    two_records=completed(root,args,command);one_records=completed(root,args,command)
    assert after(two,root,two_records) and after(one,root,one_records)
    assert inspect(two_records[-1],root)['state']==inspect(one_records[-1],root)['state']=='bound'


def test_unfinished_callback_does_not_consume_original_before(dependency_project):
    from core.inputs.native import before,after
    from core.inputs.receipts import inspect
    root,_,_,_,args,command=session_project(dependency_project)
    payload=event(root,command); before(payload,root)
    records=parse(command,'command moved to background',None,root)
    assert after(payload,root,records,terminal=False)
    assert inspect(records[-1],root)['state']=='incomplete'
    final=completed(root,args,command)
    assert after(payload,root,final) and inspect(final[-1],root)['state']=='bound'


@pytest.mark.parametrize('mutation',['dependency','source','configuration','expired'])
def test_changes_or_expiry_cannot_qualify_an_observed_pass(dependency_project,mutation):
    from core.inputs.native import before,after
    from core.inputs.receipts import inspect
    root,_,target,language,args,command=session_project(dependency_project)
    payload=event(root,command); before(payload,root)
    records=completed(root,args,command)
    if mutation=='dependency': target.write_bytes(b'value=9\n' if language=='python' else b'module.exports={value:9};\n')
    if mutation=='source': (root/'service.py').write_bytes(b'value=99\n')
    if mutation=='configuration':
        path=root/'.elevenpowers/config.json'; value=json.loads(path.read_text());value['profile']='strict';path.write_text(json.dumps(value))
    if mutation=='expired':
        path=root/'.elevenpowers/input-attempts.json';value=json.loads(path.read_text())
        for row in value['pending'].values(): row['created']=time.time()-3601
        path.write_text(json.dumps(value))
    assert after(payload,root,records)
    assert inspect(records[-1],root)['state'] in {'stale','incomplete'}
    assert records[-1].result.value=='pass'


def test_tracked_native_state_cannot_supply_provenance(dependency_project):
    from core.inputs.native import before,after
    from core.inputs.receipts import inspect
    from tests.test_patchproof_identity import git
    root,_,_,_,args,command=session_project(dependency_project)
    payload=event(root,command); before(payload,root)
    git(root,'add','-f','.elevenpowers/input-attempts.json')
    records=completed(root,args,command)
    assert after(payload,root,records)
    assert inspect(records[-1],root)['state']=='incomplete'


def test_policy_removal_during_call_cannot_drop_required_before(dependency_project):
    from core.inputs.native import before,after
    from core.evidence import Freshness
    from core.inputs.receipts import inspect
    root,_,_,_,args,command=session_project(dependency_project)
    payload=event(root,command);before(payload,root)
    done=subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=20)
    assert done.returncode==0
    (root/'elevenpowers.inputs.json').unlink()
    records=parse(command,done.stdout+done.stderr,done.returncode,root)
    assert after(payload,root,records)
    assert records[-1].source_freshness(root) is Freshness.FRESH
    assert inspect(records[-1],root)['state']=='incomplete'
    assert records[-1].freshness(root) is Freshness.STALE


def test_reused_consumed_call_cannot_leave_previous_pass_current(dependency_project):
    from tests.test_input_sessions_gap import native_check
    from core.milestones import build
    root,_,_,language,args,command=session_project(dependency_project)
    script=root/('check.py' if language=='python' else 'check.cjs')
    with script.open('a') as stream:
        stream.write('assert p.read_text()=="1"\n' if language=='python' else
                     'assert.equal(fs.readFileSync(p,"utf8"),"1");\n')
    assert native_check(root,args,command,call='reused').returncode==0
    assert build(root)['state']=='CURRENT'
    assert native_check(root,args,command,call='reused').returncode==1
    assert build(root)['state'] in {'INCOMPLETE','FAILED'}, 'a consumed-ID pre callback must supersede previous success with an unqualified attempt'


def test_invalid_platform_identity_is_controlled(dependency_project):
    from core.inputs.native import before,after
    from core.inputs.receipts import inspect
    root,_,_,_,args,command=session_project(dependency_project)
    payload=event(root,command,platform=[])
    before(payload,root)
    records=completed(root,args,command)
    assert after(payload,root,records)
    assert inspect(records[-1],root)['state']=='incomplete'


def test_evicted_before_is_unknown_while_retained_pair_works(dependency_project,monkeypatch):
    from core.inputs import native
    from core.inputs.receipts import inspect
    root,_,_,_,args,command=session_project(dependency_project)
    monkeypatch.setattr(native,'MAX_PENDING',2)
    events=[event(root,command,call='call-'+str(i)) for i in range(3)]
    for payload in events: native.before(payload,root)
    missing=completed(root,args,command);kept=completed(root,args,command)
    assert native.after(events[0],root,missing)
    assert inspect(missing[-1],root)['state']=='incomplete'
    assert native.after(events[2],root,kept)
    assert inspect(kept[-1],root)['state']=='bound'


def test_unknown_stale_state_does_not_affect_unconfigured_project(dependency_project):
    from core.inputs.native import before,after
    from core.evidence import Freshness
    root,_,_,_,args,command=session_project(dependency_project)
    payload=event(root,command);before(payload,root)
    (root/'elevenpowers.inputs.json').unlink()
    records=completed(root,args,command)
    assert after(event(root,command,call='new-unconfigured-call'),root,records)
    assert records[-1].freshness(root) is Freshness.FRESH
