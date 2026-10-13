"""Actual commands across synthetic existing host envelopes, not installed sessions."""
import subprocess

import pytest

from core.ledger import Ledger
from tests.test_external_input_reuse import dependency_project
from tests.test_input_sessions_gap import session_project


@pytest.mark.parametrize('host,directory',[(host,None) for host in ['claude','codex','gemini','cursor','copilot']]+[('gemini','.'),('gemini','./')])
def test_normalized_host_pair_observes_actual_command(dependency_project,host,directory):
    from core.inputs.receipts import inspect
    from core.hook import dispatch
    from core.hosts.bridge import run
    root,_,_,_,args,command=session_project(dependency_project)
    payload={'cwd':str(root),'session_id':'synthetic-session','tool_use_id':'actual-check-call',
             'tool_name':'Bash','tool_input':{'command':command}}
    pre,post='PreToolUse','PostToolUse'
    if host=='gemini':
        pre,post='BeforeTool','AfterTool';payload['tool_name']='run_shell_command'
        payload['tool_input']['dir_path']=directory or str(root)
    elif host=='cursor':
        pre,post='preToolUse','postToolUse';payload['tool_name']='Shell'
        payload['conversation_id']='synthetic-session'
    elif host=='copilot':
        pre,post='preToolUse','postToolUse';payload.update(sessionId='synthetic-session',toolName='bash',toolArgs={'command':command})
    if host=='claude': dispatch(pre,dict(payload))
    else: run(host,pre,dict(payload))
    done=subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=20)
    assert done.returncode==0
    completed={**payload,'tool_response':{'stdout':done.stdout,'stderr':done.stderr,'exit_code':done.returncode}}
    if host=='gemini': completed['tool_response']={'llmContent':done.stdout,'data':{'exit_code':done.returncode}}
    if host=='cursor': completed['tool_output']={'stdout':done.stdout,'stderr':done.stderr,'exit_code':done.returncode}
    if host=='copilot': completed['toolResult']={'textResultForLlm':done.stdout,'exit_code':done.returncode}
    if host=='claude': dispatch(post,completed)
    else: run(host,post,completed)
    records=Ledger.load(root).evidence
    assert inspect(records[-1],root)['state']=='bound'
    assert (root/'.elevenpowers/count.txt').read_text()=='1'
