"""Explicit one-session subscription pilot plus model-free scope continuation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from core.config import Config, save
from core.hosts.setup import install
from core.hosts.provenance import fingerprint
from core.ledger import Ledger
from core.export import build as report
from core.patchproof.execution import verify
from . import subscription
from .input_scopes import project, counts
from .github_presentation import _git
from core.process import run


def prepare(directory,language,source):
    root,base,head,target,other,good,bad,args,commands=project(directory,language)
    production=root/('service.py' if language=='python' else 'service.cjs')
    broken=('def charge(cents,bps):\n    return cents*bps//10000\n' if language=='python'
            else 'exports.charge=(cents,bps)=>Math.floor(cents*bps/10000);\n')
    reference=('def charge(cents,bps):\n    return (cents*bps+5000)//10000\n' if language=='python'
               else 'exports.charge=(cents,bps)=>Number((BigInt(cents)*BigInt(bps)+5000n)/10000n);\n')
    production.write_text(broken,encoding='utf-8')
    for command_args in args:
        check=root/command_args[-1]
        with check.open('a',encoding='utf-8') as stream:
            stream.write(('from service import charge\nassert charge(50,100)==1\nassert charge(1,10000)==1\n'
                         if language=='python' else
                         "const charge=require('./service.cjs').charge;\nassert.equal(charge(50,100),1);\nassert.equal(charge(1,10000),1);\n"))
    # One literal spelling accepted by both Windows cmd and the host Bash tool.
    if os.name=='nt': commands=[' '.join('"'+a.replace('\\','/')+'"' for a in command_args) for command_args in args]
    config=Config(auto_detect=False,commands={'tests':commands[0],'build':commands[1]})
    save(root,config)
    path=root/'elevenpowers.inputs.json';policy=json.loads(path.read_text())
    for row,command in zip(policy['commands'],commands): row['command']=command
    path.write_text(json.dumps(policy),encoding='utf-8')
    install('claude',root,sys.executable,source)
    with (root/'.gitignore').open('a',encoding='utf-8') as stream: stream.write('\n.claude/settings.local.json\n')
    _git(root,'add','.');_git(root,'commit','-qm','installed scoped consumer exercise')
    base=_git(root,'rev-parse','HEAD')
    # Real producer rehearsal: broken rounding fails; correct integer arithmetic passes.
    wrong=run(args[0],cwd=root,timeout=15,shell=False).returncode
    production.write_text(reference,encoding='utf-8')
    right=run(args[0],cwd=root,timeout=15,shell=False).returncode
    independent=oracle(root,language)
    production.write_text(broken,encoding='utf-8')
    if wrong==0 or right!=0 or independent!=0: raise ValueError('actual contract rehearsal did not flip')
    protected=[root/a[-1] for a in args]+[path,root/'.elevenpowers/config.json',
        root/'.elevenpowers/input-roots.json',root/'.claude/settings.local.json']
    seal={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    return root,base,target,good,bad,args,commands,production,seal


def oracle(root,language):
    # Literal independently calculated results include a half-cent and a large integer.
    values=[[50,100,1],[5051,750,379],[0,10000,0],[9007199254740991,9999,9006298534815517]]
    if language=='python':
        code='from service import charge\n'+'\n'.join(f'assert charge({c},{b})=={v}' for c,b,v in values)
        command=[sys.executable,'-B','-c',code]
    else:
        code="const assert=require('node:assert/strict'),charge=require('./service.cjs').charge;"+''.join(
            f'assert.equal(charge({c},{b}),{v});' for c,b,v in values)
        command=[shutil.which('node'),'-e',code]
    return run(command,cwd=root,timeout=15,shell=False).returncode


def pilot(destination,language,source,*,seconds=180,rehearse=False):
    if type(seconds) not in (int,float) or not 0<seconds<=180: raise ValueError('pilot cap exceeds approved range')
    destination=Path(destination).absolute()
    if destination.exists() or any(p.is_symlink() for p in (destination,*destination.parents)):
        raise ValueError('pilot destination must be new and unlinked')
    destination.mkdir(parents=True)
    root,base,target,good,bad,args,commands,production,seal=prepare(destination,language,source)
    value={'schema':1,'language':language,'host':'claude','requested_model':'claude-sonnet-5-5',
           'effort':'medium','seconds_cap':seconds,'runtime':fingerprint(),'model_calls':0,
           'api_fallback':False,'state':'rehearsed','continuation':'not_run',
           'limits':['One installed initial coding session; subsequent cross-task drift/reuse is controller-driven and model-free.',
                     'No causal coding-quality or population benefit claim; no OS closed-book boundary.']}
    if not rehearse:
        executable=shutil.which('claude')
        if not executable or not subscription.auth('claude',executable,root): raise ValueError('subscription authentication unavailable')
        prompt=f'''Fix {production.name}: charge(cents,bps) takes nonnegative safe integers, bps 0..10000,
and returns cents*bps/10000 rounded half up using exact integer arithmetic. Keep the existing API.
Edit only {production.name}. Do not alter checks, dependencies, configuration, hooks, Git state or documentation.
Run these exact declared commands separately with Bash, then report the result:
{commands[0]}
{commands[1]}
Do not fetch, install, use network tools or delegate to another model. Work in this project only.'''
        command=subscription.command('claude',executable,root,prompt,model='claude-sonnet-5-5')
        started=time.monotonic();value['model_calls']=1;value['state']='running'
        (destination/'result.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
        try:
            done=run(command,cwd=root,timeout=seconds,shell=False)
            value.update(state='returned' if done.returncode==0 else 'host_failed',exit=done.returncode,
                         host_observation=subscription.observation('claude',done.stdout,done.stderr))
        except (OSError,subprocess.SubprocessError) as error:
            value.update(state='incomplete',failure=type(error).__name__)
        value['session_seconds']=round(time.monotonic()-started,3)
        value['protected_inputs_unchanged']=all(hashlib.sha256(p.read_bytes()).hexdigest()==seal[p] for p in seal)
        value['independent_correctness_exit']=oracle(root,language)
        current=report(root,timeout=120)
        value['installed_associations']={r['declaration']:r['external_inputs']['state'] for r in current['receipts'] if r['declaration']}
        value['task_created_by_host']=bool(Ledger.load(root).task)
        if value['state']=='returned' and value['protected_inputs_unchanged'] and value['independent_correctness_exit']==0:
            _git(root,'add',production.name);_git(root,'commit','-qm','installed coding result')
            head=_git(root,'rev-parse','HEAD')
            initial=verify(root,base,head,seconds=180,command_seconds=15)
            before=counts(root)
            Ledger(root=root,task='controlled next task').save()
            target.write_bytes(bad)
            value['controlled_milestone_drift']={m['id']:m['state'] for m in report(root,timeout=120)['milestones']['milestones']}
            failed=verify(root,base,head,seconds=180,command_seconds=15);after=counts(root)
            target.write_bytes(good)
            value.update(continuation=failed['state'],controlled_initial=initial['state'],
                         controlled_count_delta=[b-a for a,b in zip(before,after)])
    (destination/'result.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
    return value


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--language',choices=('python','javascript'),required=True)
    parser.add_argument('--rehearse',action='store_true')
    options=parser.parse_args(argv)
    print(json.dumps(pilot(options.output,options.language,Path(__file__).resolve().parents[1],rehearse=options.rehearse),indent=2))


if __name__=='__main__': main()
