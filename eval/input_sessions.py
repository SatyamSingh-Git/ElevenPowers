"""Actual ordinary/owned input drift and recovery across tasks; no model calls."""
import argparse
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import time

from core.export import build as report
from core.hosts.bridge import run as bridge
from core.hosts.provenance import fingerprint
from core.hook import dispatch
from core.inputs import definition
from core.ledger import Ledger
from core.milestones import build as milestones
from core.obligations import Claim
from core.process import run
from core.verify import discharge
from eval.external_inputs import project
from eval.github_presentation import _git,_snapshot

HOSTS=['claude','codex','gemini','cursor','copilot']


def native(root,args,command,host,call,*,pre=True):
    """Explicitly synthetic host envelopes around one actual local command."""
    payload={'cwd':str(root),'session_id':'synthetic-session','tool_use_id':call,
             'tool_name':'Bash','tool_input':{'command':command}}
    before,after='PreToolUse','PostToolUse'
    if host=='gemini':
        before,after='BeforeTool','AfterTool';payload['tool_name']='run_shell_command'
        payload['tool_input']['dir_path']=str(root)
    elif host=='cursor':
        before,after='preToolUse','postToolUse';payload['tool_name']='Shell'
        payload['conversation_id']='synthetic-session'
    elif host=='copilot':
        before,after='preToolUse','postToolUse'
        payload.update(sessionId='synthetic-session',toolName='bash',toolArgs={'command':command})
    def emit(event,value):
        with redirect_stdout(io.StringIO()):
            if host=='claude': dispatch(event,value)
            else: bridge(host,event,value)
    if pre: emit(before,dict(payload))
    done=run(args,cwd=root,shell=False,timeout=15)
    completed={**payload,'tool_response':{'stdout':done.stdout,'stderr':done.stderr,'exit_code':done.returncode}}
    if host=='gemini': completed['tool_response']={'llmContent':done.stdout,'data':{'exit_code':done.returncode}}
    if host=='cursor': completed['tool_output']={'stdout':done.stdout,'stderr':done.stderr,'exit_code':done.returncode}
    if host=='copilot': completed['toolResult']={'textResultForLlm':done.stdout,'exit_code':done.returncode}
    emit(after,completed)
    if done.returncode: raise ValueError('independent ordinary producer did not pass')


def case(directory,language):
    root,base,head,target,good,bad,args,command=project(directory,language)
    (root/'elevenpowers.milestones.json').write_text(json.dumps({'schema':1,'milestones':[
        {'id':'dependency-behavior','description':'selected dependency returns two','inputs':['service.py'],
         'checks':[{'kind':'test_suite','command':command}]}]}),encoding='utf-8')
    _git(root,'add','.');_git(root,'commit','-qm','retain independently checked behavior')
    head=_git(root,'rev-parse','HEAD')
    Ledger(root=root,task='first',request='retain behavior').save()
    counts=[];states=[]
    def count(): counts.append(int((root/'.elevenpowers/count.txt').read_text()))
    for host in HOSTS:
        native(root,args,command,host,host+'-check')
        if report(root)['receipts'][-1]['external_inputs']['state']!='bound':
            raise ValueError('synthetic host pair lost external provenance')
    count()
    Ledger(root=root,task='second',request='build another behavior').save()
    states.append(milestones(root)['state']);count()
    source={p.name:p.read_bytes() for p in root.iterdir() if p.is_file()};environment=dict(os.environ)
    target.write_bytes(bad)
    if run(args,cwd=root,shell=False,timeout=15).returncode==0:
        raise ValueError('independent dependency fault was not detected')
    count();states.append(milestones(root)['state']);count()
    if source!={p.name:p.read_bytes() for p in root.iterdir() if p.is_file()} or dict(os.environ)!=environment or _git(root,'rev-parse','HEAD')!=head:
        raise ValueError('dependency fault moved source, HEAD or environment')
    ledger=Ledger.load(root);ledger.claims=[Claim.REFACTOR_SAFE];ledger.save()
    discharge(ledger);states.append(milestones(root)['state']);count()
    target.write_bytes(good)
    discharge(ledger);states.append(milestones(root)['state']);count()
    if discharge(ledger): raise ValueError('unchanged fresh owned result was not reused')
    count()
    target.unlink();discharge(ledger);states.append(milestones(root)['state']);count()
    target.write_bytes(good)
    native(root,args,command,'claude','post-only',pre=False)
    states.append(milestones(root)['state']);count()
    native(root,args,command,'claude','identified-recovery');count()
    Ledger(root=root,task='third',request='continue development').save()
    states.append(milestones(root)['state'])
    before=_snapshot(root);reads=[];original=definition.raw
    def measured(path,*a,**kw):
        if path==target: reads.append(path)
        return original(path,*a,**kw)
    definition.raw=measured
    try: final=report(root)
    finally: definition.raw=original
    count()
    readonly=_snapshot(root)==before
    expected=['CURRENT','STALE','FAILED','CURRENT','INCOMPLETE','INCOMPLETE','CURRENT']
    if states!=expected or counts!=[5,5,6,6,7,8,8,8,9,10,10] or not readonly or len(reads)!=2:
        raise ValueError('ordinary-session independent protocol did not qualify: '+str((states,counts,len(reads))))
    return {'language':language,'hosts':HOSTS,'states':states,'counts':counts,'readonly':readonly,
            'report_reads':len(reads),'final_external_state':final['milestones']['milestones'][0]['checks'][0]['external_inputs']['state']}


def exercise(directory):
    directory=Path(directory).absolute()
    if directory.resolve()!=directory or directory.is_symlink(): raise ValueError('linked exercise directory')
    directory.mkdir();started=time.monotonic()
    result={'schema':1,'kind':'external_input_sessions','cases':[case(directory,l) for l in ('python','javascript')],
            'runtime_fingerprint':fingerprint(),'elapsed_seconds':round(time.monotonic()-started,3),
            'limits':['Authored capability controls and synthetic host callbacks; not installed acceptance, atomic snapshots or population coding benefit.']}
    (directory/'result.json').write_text(json.dumps(result,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    print(json.dumps(exercise(parser.parse_args().output),ensure_ascii=True))


if __name__=='__main__': main()
