"""Real callback producers reproduce boundaries exposed by installed sessions."""
from contextlib import redirect_stdout
import hashlib
import io
import subprocess
import sys

import pytest

from core.claims import infer, opens_new_task
from core.config import Config, save
from core.hook import dispatch
from core.hosts.readiness import ingress, read
from core.ledger import Ledger


@pytest.mark.parametrize('prompt',[
    'This is a new task. The dependency has been restored. Refresh verification.',
    'New task: inspect the current release without edits.',
    'Separate task: inspect deployment receipts.',
    'Next task: inspect the API response.',
])
def test_explicit_subject_boundary_does_not_invent_a_coding_claim(tmp_path,prompt):
    assert infer(prompt)==[]
    assert opens_new_task(prompt)
    save(tmp_path,Config(profile='guide',auto_detect=False))
    dispatch('UserPromptSubmit',{'cwd':str(tmp_path),'prompt':'Fix the existing crash'})
    old=Ledger.load(tmp_path).task
    dispatch('UserPromptSubmit',{'cwd':str(tmp_path),'prompt':prompt})
    ledger=Ledger.load(tmp_path)
    assert ledger.task!=old and ledger.request==prompt and ledger.claims==[]
    dispatch('UserPromptSubmit',{'cwd':str(tmp_path),'prompt':'continue'})
    assert Ledger.load(tmp_path).task==ledger.task


@pytest.mark.parametrize('prompt',['continue the new task','not a new task',
    'The words new task appear in a log.','New task is not needed.'])
def test_mentions_and_continuations_do_not_open_a_subject(prompt):
    assert not opens_new_task(prompt)


def test_native_prompt_and_owned_tool_callbacks_record_the_actual_task(tmp_path):
    from core.checks import execute
    command=f'"{sys.executable}" -c "print(\'1 passed\')"'
    save(tmp_path,Config(profile='guide',auto_detect=False,commands={'tests':command}))
    (tmp_path/'source.py').write_text('value=1\n')
    payload={'cwd':str(tmp_path),'session_id':'synthetic-producer-control'}
    with redirect_stdout(io.StringIO()),ingress('host'):
        dispatch('UserPromptSubmit',{**payload,'prompt':'Fix the existing crash'})
        task=Ledger.load(tmp_path).task
        assert execute(tmp_path,'tests')['state']=='passed'
        before=[e.to_dict() for e in Ledger.load(tmp_path).evidence]
        dispatch('PostToolUse',{**payload,'tool_name':'Bash',
            'tool_input':{'command':'python ep_check.py tests --project .'},
            'tool_response':{'stdout':'Declared check tests: passed','exit_code':0}})
    phases=read(tmp_path)['claude']['phases']
    expected=hashlib.sha256(task.encode()).hexdigest()
    assert phases['UserPromptSubmit']['task']==expected
    assert phases['PostToolUse']['task']==expected
    assert before and [e.to_dict() for e in Ledger.load(tmp_path).evidence]==before


def test_guidance_exposes_each_independent_declared_property(tmp_path):
    from core.checks import guidance
    from core.hosts.setup import invocation_args
    (tmp_path/'test_check.py').write_text("print('1 passed')\n")
    (tmp_path/'build.py').write_text('value=1\n')
    commands={'tests':f'"{sys.executable}" test_check.py','build':f'"{sys.executable}" build.py'}
    save(tmp_path,Config(profile='guide',auto_detect=False,commands=commands))
    lines=guidance(tmp_path).splitlines()
    assert len(lines)==2 and len(guidance(tmp_path))<=2000
    for line in lines:
        args=invocation_args(line.split(': ',1)[1])
        done=subprocess.run(args,cwd=tmp_path,capture_output=True,text=True,timeout=30)
        assert done.returncode==0
    assert {e.declaration for e in Ledger.load(tmp_path).evidence if e.owned_execution}=={'tests','build'}
    selected=guidance(tmp_path,commands=[commands['build']])
    assert len(selected.splitlines())==1
    save(tmp_path,Config(profile='off',auto_detect=False,commands=commands))
    assert guidance(tmp_path)==''


def test_bounded_guidance_names_every_omitted_property(tmp_path,monkeypatch):
    from core.checks import guidance
    import core.hosts.setup as setup
    properties=('tests','build','typecheck','lint','benchmark')
    save(tmp_path,Config(profile='guide',auto_detect=False,commands={p:'echo '+p for p in properties}))
    monkeypatch.setattr(setup,'invocation',lambda args:'x'*1800)
    text=guidance(tmp_path)
    assert len(text)<=2000 and 'instructions not shown' in text
    assert all(p in text for p in properties)


def test_native_tool_callback_without_a_task_cannot_invent_one(tmp_path):
    save(tmp_path,Config(profile='guide',auto_detect=False))
    with redirect_stdout(io.StringIO()),ingress('host'):
        dispatch('PostToolUse',{'cwd':str(tmp_path),'session_id':'synthetic-unbound',
            'tool_name':'Bash','tool_input':{'command':'echo hi'},
            'tool_response':{'stdout':'hi','exit_code':0}})
    assert read(tmp_path)['claude']['phases']['PostToolUse']['task']==''
    assert not (tmp_path/'.elevenpowers/ledger.json').exists()
