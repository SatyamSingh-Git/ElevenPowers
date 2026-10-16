"""Two installed tasks per subscription conversation, under one shared cap."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
import tempfile

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
    milestones=root/'elevenpowers.milestones.json'
    declaration=json.loads(milestones.read_text())
    for row,command in zip(declaration['milestones'],commands):
        row['inputs']=[production.name]
        row['checks'][0]['command']=command
    milestones.write_text(json.dumps(declaration),encoding='utf-8')
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
    protected=[root/a[-1] for a in args]+[path,milestones,root/'.elevenpowers/config.json',
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


def session_command(executable,root,prompt,identity,*,resume=False):
    command=subscription.command('claude',executable,root,prompt,model='claude-sonnet-5-5')
    command.remove('--no-session-persistence')
    command.extend(['--resume' if resume else '--session-id',identity])
    return command


def snapshot(root):
    current=report(root,timeout=90)
    task=Ledger.load(root).task
    return {'task':hashlib.sha256(task.encode()).hexdigest() if task else None,
            'associations':{r['declaration']:r['external_inputs']['state'] for r in current['receipts'] if r['declaration']},
            'milestones':{m['id']:m['state'] for m in current['milestones']['milestones']},
            'counts':[int(p.read_text()) if p.exists() else 0 for p in
                      (root/'.elevenpowers/count.txt',root/'.elevenpowers/other-count.txt')]}


def pilot(destination,language,source,*,seconds=180,rehearse=False,protocol='exact-command'):
    if protocol == 'declared-runner':
        from .declared_workflow import pilot as declared_pilot
        return declared_pilot(destination,language,source,seconds=seconds,rehearse=rehearse)
    if protocol != 'exact-command':
        raise ValueError('unknown installed protocol')
    if type(seconds) not in (int,float) or not 0<seconds<=180: raise ValueError('pilot cap exceeds approved range')
    destination=Path(destination).absolute()
    if not rehearse and (not destination.is_relative_to(Path(tempfile.gettempdir()).resolve())
            or any((p/'.git').exists() for p in destination.parents)):
        raise ValueError('installed conversations require a new system-temp directory outside Git ancestors')
    if destination.exists() or any(p.is_symlink() for p in (destination,*destination.parents)):
        raise ValueError('pilot destination must be new and unlinked')
    destination.mkdir(parents=True)
    root,base,target,good,bad,args,commands,production,seal=prepare(destination,language,source)
    value={'schema':1,'language':language,'host':'claude','requested_model':'claude-sonnet-5-5',
           'effort':'medium','seconds_cap':seconds,'runtime':fingerprint(),'model_calls':0,
           'api_fallback':False,'state':'rehearsed','continuation':'not_run',
           'turns':[], 'limits':['Two tasks in one persistent conversation per language, sharing one 180-second wall allowance; process cleanup has a separate five-second allowance per call.',
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
        identity=str(uuid.uuid4())
        value['conversation_identity']=identity
        value['host_version']=run([executable,'--version'],cwd=root,timeout=10,shell=False).stdout.strip()
        started=time.monotonic();deadline=started+seconds
        def turn(prompt,resume=False):
            remaining=deadline-time.monotonic()
            if remaining<=0: return False
            row={'resume':resume,'allowance_seconds':round(remaining,3)}
            value['turns'].append(row);value['model_calls']+=1;value['state']='running'
            (destination/'result.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
            began=time.monotonic()
            try:
                done=run(session_command(executable,root,prompt,identity,resume=resume),cwd=root,timeout=remaining,shell=False)
                row.update(exit=done.returncode,observation=subscription.observation('claude',done.stdout,done.stderr))
                # Private disposable diagnostics are not copied into public results.
                (destination/f'turn-{len(value["turns"])}.json').write_text(done.stdout,encoding='utf-8')
                completed=done.returncode==0 and row['observation']['completed']
            except (OSError,subprocess.SubprocessError) as error:
                row['failure']=type(error).__name__;completed=False
            row['wall_seconds']=round(time.monotonic()-began,3)
            return completed
        returned=turn(prompt)
        first=snapshot(root);value['first_task']=first
        if returned and time.monotonic()<deadline:
            target.write_bytes(bad)
            value['before_second_task']=snapshot(root)
            second=f'''Review this as a new task: the first installed SDK input changed after the earlier coding task.
Do not edit any file, SDK, Git state, hook or configuration. Inspect current ElevenPowers evidence first:
"{sys.executable.replace(chr(92),'/')}" "{(source/'plugin/bin/ep_report.py').as_posix()}" --project . --format json
Retain earlier milestone evidence. Run the exact declared command whose evidence needs refresh, using Bash:
{commands[0]}
The other independent declared command is {commands[1]}.
Report the observed failure honestly; do not repair the dependency or claim that all checks pass.
Do not fetch, install, use network tools or delegate to another model.'''
            returned=turn(second,resume=True)
            value['second_task']=snapshot(root)
            value['host_created_distinct_tasks']=bool(first['task'] and value['second_task']['task']
                                                      and first['task']!=value['second_task']['task'])
        value['session_seconds']=round(time.monotonic()-started,3)
        value['model_wall_seconds_including_cleanup']=round(sum(t['wall_seconds'] for t in value['turns']),3)
        value['state']='returned' if returned else 'incomplete'
        value['installed_multitask_observed']=bool(len(value['turns'])==2 and returned
            and value.get('host_created_distinct_tasks') and value['second_task']['associations'].get('tests')=='bound'
            and value['second_task']['milestones'].get('first')=='FAILED'
            and value['second_task']['milestones'].get('second')=='CURRENT')
        target.write_bytes(good)
        value['protected_inputs_unchanged']=all(hashlib.sha256(p.read_bytes()).hexdigest()==seal[p] for p in seal)
        value['independent_correctness_exit']=oracle(root,language)
        if value['state']=='returned' and value['protected_inputs_unchanged'] and value['independent_correctness_exit']==0:
            _git(root,'add',production.name);_git(root,'commit','-qm','installed coding result')
            head=_git(root,'rev-parse','HEAD')
            initial=verify(root,base,head,seconds=180,command_seconds=15)
            before=counts(root)
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
    parser.add_argument('--protocol',choices=('exact-command','declared-runner'),default='exact-command')
    parser.add_argument('--seconds',type=float,default=180)
    options=parser.parse_args(argv)
    print(json.dumps(pilot(options.output,options.language,Path(__file__).resolve().parents[1],
                          seconds=options.seconds,rehearse=options.rehearse,protocol=options.protocol),indent=2))


if __name__=='__main__': main()
