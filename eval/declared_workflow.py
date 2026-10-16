"""Opt-in three-task adapter over the existing installed consumer pilot."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import math
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

from core.commands import owned_check_envelope
from core.hosts.provenance import fingerprint
from core.hosts.readiness import read as diagnostics
from core.hook import dispatch
from core.ledger import Ledger
from core.process import run
from . import subscription, transcript
from .input_scope_pilot import prepare, oracle, session_command, snapshot
from .preservation import _manifest, _write


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def allowance(total, spent, turns):
    if (type(turns) is not int or turns < 1 or type(total) not in (int,float)
            or type(spent) not in (int,float) or not math.isfinite(total)
            or not math.isfinite(spent) or total <= 0 or spent < 0):
        raise ValueError('invalid turn allowance')
    return max(0,total-spent)/turns


def _reported(output):
    if isinstance(output,dict):
        values=[output[k] for k in ('stdout','content','text','output') if k in output]
        if output.get('schema_version')==1:values.append(json.dumps(output))
        return [row for value in values for row in _reported(value)]
    if isinstance(output,list):return [row for value in output for row in _reported(value)]
    if not isinstance(output,str) or len(output)>256*1024:return []
    rows=[(m[0],m[1],None) for m in re.findall(r'(?m)^Declared check (tests|build|typecheck|lint|benchmark): (passed|failed|incomplete)\s*$',output)]
    decoder=json.JSONDecoder()
    for match in list(re.finditer(r'(?m)^\s*\{',output))[:32]:
        try:
            data,_=decoder.raw_decode(output[match.start():].lstrip())
            if (isinstance(data,dict) and data.get('schema_version')==1
                    and data.get('property') in ('tests','build','typecheck','lint','benchmark')
                    and data.get('state') in ('passed','failed','incomplete') and isinstance(data.get('attempt'),str)):
                rows.append((data['property'],data['state'],data['attempt']))
        except (ValueError,TypeError):pass
    return rows


def observe(root, log, *, since, session, runtime):
    """Join completed native calls, current task callbacks and fresh owned receipts."""
    value={'native_runner_adoption':False,'task':'','owned_receipts':0,'completed_runner_calls':0}
    try:
        rows=[json.loads(line) for line in Path(log).read_text(encoding='utf8').splitlines() if line.strip()]
        result=next((r for r in reversed(rows) if r.get('type')=='result'),{})
        if result.get('session_id')!=session: return value
        candidates=[c for turn in transcript.load(Path(log)) for c in turn.calls
               if c.name in ('Bash','Shell') and c.result is not None
               and owned_check_envelope(c.args.get('command',''))]
        ledger=Ledger.load(root); task=digest(ledger.task) if ledger.task else ''
        receipts=[e for e in ledger.evidence if e.owned_execution and e.at>=since and e.execution=='complete']
        calls=[c for c in candidates if any(e.declaration==prop
               and e.result.value=={'passed':'pass','failed':'fail','incomplete':'unknown'}[state]
               and (attempt is None or e.owned_execution.get('attempt')==attempt)
               for prop,state,attempt in _reported(c.result) for e in receipts)]
        host=diagnostics(root).get('claude',{}); phases=host.get('phases',{})
        native=bool(task and not host.get('errors') and all(
            phases.get(p,{}).get('processed',0)>0 and phases[p].get('last_at',0)>=since
            and phases[p].get('session')==digest(session) and phases[p].get('task')==task
            for p in ('UserPromptSubmit','PostToolUse','Stop'))
            and phases.get('SessionStart',{}).get('session')==digest(session)
            and phases.get('SessionStart',{}).get('runtime_fingerprint')==runtime)
        value.update(task=task,owned_receipts=len(receipts),completed_runner_calls=len(calls),
                     native_runner_adoption=bool(calls and receipts and native))
    except (OSError,ValueError,TypeError,KeyError,AttributeError):
        pass
    return value


def _command(executable,root,prompt,identity,stage):
    args=session_command(executable,root,prompt,identity,resume=stage>1)
    args[args.index('--output-format')+1]='stream-json'
    return args+['--verbose','--disable-slash-commands','--disallowedTools','WebFetch','WebSearch','Agent']


def _reference(language):
    return ('def charge(cents,bps):\n    return (cents*bps+5000)//10000\n' if language=='python' else
            'exports.charge=(cents,bps)=>Number((BigInt(cents)*BigInt(bps)+5000n)/10000n);\n')


def pilot(destination,language,source,*,seconds=180,rehearse=False):
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<seconds<=240:
        raise ValueError('invalid declared workflow allowance')
    if language not in ('python','javascript'): raise ValueError('unknown language')
    destination=Path(destination).absolute()
    if (destination.exists() or any(p.is_symlink() or getattr(p,'is_junction',lambda:False)()
                                   for p in (destination,*destination.parents))):
        raise ValueError('new unlinked destination required')
    if not rehearse and (not destination.is_relative_to(Path(tempfile.gettempdir()).resolve())
                         or any((p/'.git').exists() for p in destination.parents)):
        raise ValueError('installed conversations require system temp outside Git ancestors')
    destination.mkdir(parents=True)
    root,base,target,good,bad,args,commands,production,seal=prepare(destination,language,Path(source))
    initial=_manifest(root); other=target.with_name('other'+target.suffix); other_bytes=other.read_bytes()
    value={'schema':2,'protocol':'declared-runner','host':'claude','language':language,
           'requested_model':'claude-sonnet-5-5','effort':'medium','runtime':fingerprint(),
           'seconds_cap':seconds,'model_calls':0,'model_seconds':0,'turns':[],'snapshots':[],
           'qualified':False,'native_runner_adoption':False,'task_boundaries':False,
           'state':'prepared','installed_acceptance':False,'api_fallback':False,
           'limits':['Synthetic rehearsal is not installed acceptance.',
                     'Native local observations are unsigned; no OS closed-book or causal coding benefit claim.']}
    path=destination/'result.json'
    _write(path,value)
    def protected(expected):
        current=_manifest(root)
        return (target.read_bytes()==expected and other.read_bytes()==other_bytes
                and all(p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in seal.items())
                and current.keys()==initial.keys()
                and all(current[n]==h for n,h in initial.items() if n!=production.name))
    def control(stage,properties):
        with redirect_stdout(io.StringIO()):
            dispatch('UserPromptSubmit',{'cwd':str(root),'session_id':'synthetic-rehearsal','prompt':f'controlled task {stage}'})
        outcomes=[]
        for prop in properties:
            cmd=[sys.executable,str(Path(source)/'plugin/bin/ep_check.py'),prop,'--project',str(root),'--json']
            done=run(cmd,cwd=root,timeout=45,shell=False)
            outcomes.append(json.loads(done.stdout)['state'])
        return outcomes
    try:
        if rehearse:
            production.write_text(_reference(language),encoding='utf8')
            value['controlled_outcomes']=control(1,('tests','build'))
            value['snapshots'].append(snapshot(root))
            target.write_bytes(bad);value['snapshots'].append(snapshot(root))
            value['controlled_outcomes']+=control(2,('tests',));value['snapshots'].append(snapshot(root))
            target.write_bytes(good)
            value['controlled_outcomes']+=control(3,('tests',));value['snapshots'].append(snapshot(root))
            value['state']='rehearsed'
        else:
            executable=shutil.which('claude')
            if not executable or not subscription.auth('claude',executable,root):
                raise ValueError('subscription authentication unavailable')
            identity=str(uuid.uuid4());value['conversation_identity']=identity
            value['host_version']=run([executable,'--version'],cwd=root,timeout=10,shell=False).stdout.strip()
            prompts=[f'''Fix {production.name}: charge(cents,bps) takes nonnegative safe integers and bps 0..10000.
Return cents*bps/10000 rounded half up using exact integer arithmetic; preserve the API.
Edit only {production.name}. Use installed project guidance to verify both declared properties tests and build.
Do not change tests, dependencies, settings, hooks, Git state or documentation.''',
                '''This is a new task. The first external SDK input changed after earlier verification.
Inspect current project evidence and verify the affected behavior. Retain the independent consumer's evidence.
Do not repair the SDK or edit any file; report observed failure honestly.''',
                '''This is a new task. The first external SDK input has been restored.
Refresh affected verification and inspect the retained independent consumer. Do not edit any file.''']
            for stage,prompt in enumerate(prompts,1):
                if stage==2:
                    target.write_bytes(bad);value['snapshots'].append(snapshot(root))
                if stage==3: target.write_bytes(good)
                expected=bad if stage==2 else good
                if not protected(expected) or fingerprint()!=value['runtime']:
                    value['state']='scope_or_runtime_changed';break
                cap=allowance(seconds,value['model_seconds'],4-stage)
                if cap<=0: value['state']='incomplete';break
                row={'stage':stage,'allowance_seconds':cap,'state':'running','started_at':time.time()}
                value['turns'].append(row);value['model_calls']+=1;_write(path,value)
                started=time.monotonic();output=''
                try:
                    done=run(_command(executable,root,prompt+'\nWork only in this project; do not fetch, install, use network tools or delegate.',identity,stage),
                             cwd=root,timeout=cap,shell=False)
                    output=done.stdout
                    event=next((json.loads(line) for line in reversed(output.splitlines()) if json.loads(line).get('type')=='result'),{})
                    obs=subscription.observation('claude',json.dumps(event),done.stderr)
                    row.update(state='completed' if done.returncode==0 and obs['completed'] and obs['models']==['claude-sonnet-5-5'] else 'incomplete',observation=obs)
                except (OSError,ValueError,subprocess.SubprocessError) as error:
                    row.update(state='incomplete',error=type(error).__name__)
                finally:
                    row['wall_seconds']=round(time.monotonic()-started,3)
                    value['model_seconds']+=row['wall_seconds']
                    log=destination/f'native-{stage}.jsonl';log.write_text(output,encoding='utf8')
                    row['native']=observe(root,log,since=row['started_at'],session=identity,runtime=value['runtime'])
                    row['scope_preserved']=protected(expected)
                    value['snapshots'].append(snapshot(root));_write(path,value)
                if row['state']!='completed' or not row['scope_preserved']: break
            value['state']='returned' if len(value['turns'])==3 and all(t['state']=='completed' for t in value['turns']) else 'incomplete'
            value['native_runner_adoption']=len(value['turns'])==3 and all(t['native']['native_runner_adoption'] for t in value['turns'])
            tasks=[s['task'] for i,s in enumerate(value['snapshots']) if i!=1]
            value['task_boundaries']=len(tasks)==3 and all(tasks) and len(set(tasks))==3
        value['protected_inputs_unchanged']=protected(good)
        value['independent_correctness_exit']=oracle(root,language)
        expected=[{'first':'CURRENT','second':'CURRENT'},{'first':'STALE','second':'CURRENT'},
                  {'first':'FAILED','second':'CURRENT'},{'first':'CURRENT','second':'CURRENT'}]
        value['behavior_qualified']=([s['milestones'] for s in value['snapshots']]==expected
                                     and value['protected_inputs_unchanged'] and value['independent_correctness_exit']==0
                                     and fingerprint()==value['runtime'])
        value['rehearsal_qualified']=rehearse and value['behavior_qualified']
        value['qualified']=bool(not rehearse and value['behavior_qualified'] and value['native_runner_adoption']
                                and value['task_boundaries'] and value['state']=='returned')
        value['installed_acceptance']=value['qualified']
    except BaseException as error:
        value.update(state='interrupted' if isinstance(error,KeyboardInterrupt) else 'incomplete',error=type(error).__name__)
        _write(path,value)
        raise
    finally:
        _write(path,value)
    return value
