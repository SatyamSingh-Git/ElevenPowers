"""Real prepared projects/grades with only the external model process substituted."""
import json
from pathlib import Path
from types import SimpleNamespace
import subprocess
import time

import pytest

from eval import preservation as p
from eval.workflow_cases import case


def prepare(tmp_path,name='workflow-queue-py'):
    return p.prepare(tmp_path/'batch',names=(name,),seconds=720,model='claude-sonnet-5-5')


def test_frozen_equal_inputs_and_four_stage_oracles(tmp_path):
    protocol=prepare(tmp_path)
    assert protocol['schema']==2 and protocol['stage_count']==4
    assert protocol['model']=='claude-sonnet-5-5'
    roots=[tmp_path/'batch'/s/'candidate' for s in protocol['slots']]
    for name in case('workflow-queue-py')['files']:
        assert (roots[0]/name).read_bytes()==(roots[1]/name).read_bytes()
    assert len(protocol['seals'][protocol['slots'][0]]['oracles'])==5
    (roots[0]/'tests/test_agent_extra.py').write_text('import unittest\n')
    with pytest.raises(ValueError):p.verify(tmp_path/'batch',protocol['slots'][0],initial=True)
    p.verify(tmp_path/'batch',protocol['slots'][0])
    (roots[0]/'tests/test_core.py').write_text('pass\n')
    with pytest.raises(ValueError):p.verify(tmp_path/'batch',protocol['slots'][0])


def test_case_and_runtime_changes_cannot_reuse_frozen_protocol(tmp_path,monkeypatch):
    protocol=prepare(tmp_path);slot=protocol['slots'][0]
    original=p.case
    def changed(name):
        value=original(name);value['requests'][0]+=' changed';return value
    monkeypatch.setattr(p,'case',changed)
    with pytest.raises(ValueError):p.verify(tmp_path/'batch',slot)
    monkeypatch.setattr(p,'case',original)
    monkeypatch.setattr(p,'fingerprint',lambda:'0'*64)
    with pytest.raises(ValueError):p.verify(tmp_path/'batch',slot)


@pytest.mark.parametrize('name',['workflow-queue-py','workflow-orders-js'])
def test_comparison_reserves_later_turn_allowances(tmp_path,monkeypatch,name):
    if name.endswith('js'):
        import shutil
        if not shutil.which('node'):pytest.skip('Node unavailable')
    protocol=prepare(tmp_path,name);slot=protocol['slots'][0];caps=[]
    actual=p.run
    def external(command,**kwargs):
        if isinstance(command,list) and command[0]=='fake-host':
            if command[-1]=='--version':return SimpleNamespace(returncode=0,stdout='fake test host',stderr='')
            root=Path(kwargs['cwd']);value=case(name)
            (root/value['production'][0]).write_text(value['gold'][3],encoding='utf8')
            caps.append(kwargs['timeout'])
            # The host's auxiliary small model would otherwise make every turn model-unqualified.
            assert kwargs['env']['ANTHROPIC_DEFAULT_HAIKU_MODEL']==protocol['model']
            identity=protocol['seals'][slot]['session']
            event={'type':'result','session_id':identity,'is_error':False,'modelUsage':{'claude-sonnet-5-5':{}}}
            return SimpleNamespace(returncode=0,stdout=json.dumps(event),stderr='')
        return actual(command,**kwargs)
    monkeypatch.setattr(p,'run',external)
    monkeypatch.setattr(p.subscription,'auth',lambda *a:True)
    ticks=iter([0,90,100,190,200,290,300,390])
    monkeypatch.setattr(p,'time',SimpleNamespace(monotonic=lambda:next(ticks),time=time.time))
    result=p.execute(tmp_path/'batch',slot,'fake-host')
    assert caps==[180,210,270,450]
    assert result['state']=='completed' and result['model_seconds']==360
    assert [s['independent_grade']['passed'] for s in result['stages']]==[4,6,8,10]
    assert all(s['native']['state']!='observed' for s in result['stages'])


def test_timeout_retains_attempt_and_stops_later_stages(tmp_path,monkeypatch):
    protocol=prepare(tmp_path);slot=protocol['slots'][0];actual=p.run
    def external(command,**kwargs):
        if isinstance(command,list) and command[0]=='fake-host':
            if command[-1]=='--version':return SimpleNamespace(returncode=0,stdout='fake test host',stderr='')
            raise subprocess.TimeoutExpired(command,kwargs['timeout'])
        return actual(command,**kwargs)
    monkeypatch.setattr(p,'run',external);monkeypatch.setattr(p.subscription,'auth',lambda *a:True)
    result=p.execute(tmp_path/'batch',slot,'fake-host')
    assert result['state']=='incomplete' and len(result['stages'])==1
    assert result['stages'][0]['state']=='timeout'
    assert (tmp_path/'batch'/slot/'result.json').exists()
    with pytest.raises(ValueError,match='retry'):p.execute(tmp_path/'batch',slot,'fake-host')


def test_mixed_protocols_and_unsupported_models_cannot_prepare(tmp_path):
    with pytest.raises(ValueError):p.prepare(tmp_path/'mixed',names=('queue','workflow-orders-js'),seconds=720)
    with pytest.raises(ValueError):p.prepare(tmp_path/'model',names=('workflow-orders-js',),model='other')
    assert not (tmp_path/'model').exists()


def test_agent_cannot_replace_the_frozen_git_head(tmp_path):
    protocol=prepare(tmp_path);slot=protocol['slots'][0];candidate=tmp_path/'batch'/slot/'candidate'
    subprocess.run(['git','-c','user.name=control','-c','user.email=control@example.invalid',
                    'commit','--allow-empty','-qm','unexpected commit'],cwd=candidate,check=True)
    with pytest.raises(ValueError,match='Git'):p.verify(tmp_path/'batch',slot)


@pytest.mark.parametrize('owned',[True,False],ids=['owned-followup','generic-only'])
def test_each_stage_reads_out_declared_rows_and_feedback_delivery(tmp_path,monkeypatch,owned):
    import shutil,sys
    if not shutil.which('node'):pytest.skip('Node unavailable')
    name='workflow-orders-js';protocol=prepare(tmp_path,name)
    slot=next(s for s in protocol['slots'] if s.endswith('assisted'));actual=p.run
    source=Path(p.__file__).resolve().parents[1]
    def hook(root,event,payload):
        payload={'cwd':str(root),'session_id':protocol['seals'][slot]['session'],**payload}
        done=subprocess.run([sys.executable,str(source/'plugin/bin/ep_hook.py'),event],input=json.dumps(payload),
                            capture_output=True,text=True,timeout=120)
        assert done.returncode==0,done.stderr
        return done.stdout
    def bash(root,command,shown,index):
        done=subprocess.run(command,cwd=root,shell=True,capture_output=True,text=True,timeout=120)
        return hook(root,'PostToolUse',{'tool_name':'Bash','tool_use_id':f'call-{index}','tool_input':{'command':shown},
                    'tool_response':{'stdout':done.stdout+done.stderr,'exit_code':done.returncode}})
    def external(command,**kwargs):
        if isinstance(command,list) and command[0]=='fake-host':
            if command[-1]=='--version':return SimpleNamespace(returncode=0,stdout='fake test host',stderr='')
            root=Path(kwargs['cwd']);value=case(name)
            hook(root,'SessionStart',{});hook(root,'UserPromptSubmit',{'prompt':'continue the stage'})
            (root/value['production'][0]).write_text(value['gold'][3],encoding='utf8')
            hook(root,'PostToolUse',{'tool_name':'Write','tool_input':{'file_path':str(root/value['production'][0])},
                                     'tool_response':{}})
            reply=bash(root,value['public_command'],value['public_command']+' 2>&1 | tail -15',1)
            stages.append(reply)
            if owned:
                runner=f'"{sys.executable}" "{source/"plugin/bin/ep_check.py"}" tests --project "{root}"'
                bash(root,runner,runner,2)
            identity=protocol['seals'][slot]['session']
            event={'type':'result','session_id':identity,'is_error':False,'modelUsage':{'claude-sonnet-5-5':{}}}
            return SimpleNamespace(returncode=0,stdout=json.dumps(event),stderr='')
        return actual(command,**kwargs)
    stages=[]
    monkeypatch.setattr(p,'run',external);monkeypatch.setattr(p.subscription,'auth',lambda *a:True)
    result=p.execute(tmp_path/'batch',slot,'fake-host')
    assert 'Owned check arguments' in stages[0]
    first=result['stages'][0]['declared_closure']
    assert first['delivery']['state']=='emitted' and first['delivery']['model_consumption']=='unproven'
    assert first['declared']=={'tests':'CURRENT' if owned else 'STALE'}
    assert first['delivery']['followups']==[{'declaration':'tests','state':'current' if owned else 'unobserved'}]
