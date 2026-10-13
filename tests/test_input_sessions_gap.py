"""Actual native command checks must expire across dependency and task changes."""
import json
import os
from pathlib import Path
import subprocess

import pytest

from core.ledger import Ledger
from tests.test_external_input_reuse import dependency_project
from tests.test_patchproof_identity import commit,git


def session_project(fixture):
    root,_,_,target,language,args=fixture
    command=Ledger.load(root).config.commands['tests']
    (root/'elevenpowers.milestones.json').write_text(json.dumps({'schema':1,'milestones':[
        {'id':'dependency-behavior','description':'selected dependency still returns two',
         'inputs':['service.py'], 'checks':[{'kind':'test_suite','command':command}]}]}))
    head=commit(root,'retain independently checked behavior')
    Ledger(root=root,task='first',request='build behavior').save()
    return root,head,target,language,args,command


def native_check(root,args,command,call='first-check'):
    from core.hook import dispatch
    payload={'cwd':str(root),'session_id':'actual-local-session','tool_use_id':call,
             'tool_name':'Bash','tool_input':{'command':command}}
    dispatch('PreToolUse',dict(payload))
    done=subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=20)
    dispatch('PostToolUse',{**payload,'tool_response':{'stdout':done.stdout,'stderr':done.stderr,
                                                     'exit_code':done.returncode}})
    return done


def test_native_receipt_expires_on_independently_failed_dependency_drift(dependency_project):
    from core.export import build
    root,head,target,language,args,command=session_project(dependency_project)
    assert native_check(root,args,command).returncode==0
    first=build(root)
    assert first['receipts'][-1]['freshness']=='fresh', first['coverage']
    source={p.name:p.read_bytes() for p in root.iterdir() if p.is_file()}
    environment=dict(os.environ)
    target.write_bytes(b'value=9\n' if language=='python' else b'module.exports={value:9};\n')
    assert subprocess.run(args,cwd=root,capture_output=True,timeout=20).returncode==1
    changed=build(root)
    assert changed['receipts'][-1]['freshness']=='stale'
    assert changed['receipts'][-1]['result']=='pass', 'retain the historical actual outcome'
    assert source=={p.name:p.read_bytes() for p in root.iterdir() if p.is_file()}
    assert git(root,'rev-parse','HEAD').decode().strip()==head and dict(os.environ)==environment
    assert (root/'.elevenpowers/count.txt').read_text()=='2'


def test_milestone_expires_across_tasks_without_source_edits(dependency_project):
    from core.milestones import build
    root,_,target,language,args,command=session_project(dependency_project)
    assert native_check(root,args,command).returncode==0
    Ledger(root=root,task='second',request='continue another behavior').save()
    assert build(root)['state']=='CURRENT'
    target.write_bytes(b'value=9\n' if language=='python' else b'module.exports={value:9};\n')
    assert subprocess.run(args,cwd=root,capture_output=True,timeout=20).returncode==1
    changed=build(root)
    assert changed['state']=='STALE', changed
    assert changed['milestones'][0]['checks'][0]['result']=='pass'
    assert (root/'.elevenpowers/count.txt').read_text()=='2', 'reporting must run no check'
