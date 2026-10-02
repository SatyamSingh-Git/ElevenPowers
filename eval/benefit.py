"""Explicit one-host proposal pilot; never run during plugin installation."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from core.config import Config, save
from core.export import write
from core.hosts.provenance import fingerprint
from core.hosts.setup import _write, invocation
from core.hosts.readiness import configured, activation
from core.process import run
from . import benefit_cases as cases, challenge, proposals, subscription


def schedule():
    return [(case,n,arm) for n in range(2) for case in cases.CASES
            for arm in (('baseline','tool') if n == 0 else ('tool','baseline'))]


def grade_snapshot(case, value):
    unavailable = {'state':'unavailable','passed':0,'total':0,'regressions':None,'checks':{}}
    try:
        if value['state'] != 'complete' or set(value['files']) != set(cases.names(case)):
            return unavailable
        digest = hashlib.sha256(json.dumps(value['files'],sort_keys=True).encode()).hexdigest()
        if digest != value['fingerprint']:
            return unavailable
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            total=0
            for name, encoded in value['files'].items():
                if encoded is None:
                    continue
                raw=base64.b64decode(encoded,validate=True); total += len(raw)
                if total > proposals.MAX_BYTES:
                    return unavailable
                path=root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw)
            if not cases.contract(case,root):
                return unavailable
            return challenge.grade(root)
    except (ValueError,KeyError,TypeError,OSError):
        return unavailable


def summarize(records):
    expected=set(schedule())
    keys=[(r['case'],r['replicate'],r['arm']) for r in records]
    complete=len(keys)==8 and set(keys)==expected
    valid=[r for r in records if r['state']=='graded']
    repairs=[]; refreshes=[]
    for r in valid:
        for p in r['proposals']:
            if r['arm']=='tool' and p['decision']=='block' and p['before_grade']['state']=='graded' and r['final_grade']['state']=='graded' and p['before_grade']['passed'] < r['final_grade']['passed']:
                repairs.append([r['case'],r['replicate']])
            if r['arm']=='tool' and p.get('verification_before') in ('missing','stale','fail') and p.get('verification_after')=='fresh_pass':
                refreshes.append([r['case'],r['replicate']])
    return {'schema_version':1,'state':'incomplete' if not complete else 'qualified' if len(valid)==8 else 'inconclusive',
            'runs':len(records),'valid_runs':len(valid),'repairs_after_block':repairs,
            'verification_refreshes':refreshes,'benefit_observed':bool(complete and repairs),
            'coding_improvement_observed':bool(complete and repairs),
            'receipt_refresh_observed':bool(complete and refreshes),
            'limits':['Eight original local runs cannot establish a population effect or speedup.',
                      'Native observations and local hash chains are not authentication or an OS security boundary.',
                      'A refreshed receipt is additional verification evidence, not necessarily a better patch.',
                      'Missing means no exact-command receipt; wrapped baseline tests may still have run.']}


def prepare_batch(destination, host='claude', seconds=240):
    if host != 'claude':
        raise ValueError('this decision pilot currently qualifies Claude exit-2 completion only')
    if type(seconds) is not int or not 1<=seconds<=240:
        raise ValueError('run budget must be 1–240 seconds')
    root=Path(destination).absolute()
    if root.exists() or any(p.is_symlink() for p in (root,*root.parents)):
        raise ValueError('new unlinked batch directory required')
    root.mkdir(parents=True)
    source=Path(__file__).resolve().parents[1]
    protocol={'schema_version':1,'host':host,'model':subscription.MODELS[host],'effort':'medium',
              'seconds_per_run':seconds,'schedule':schedule(),'cases':[cases.identity(c) for c in cases.CASES],
              'runtime_fingerprint':fingerprint(source),
              'harness_fingerprint':_harness(),'prepared_at':datetime.now(timezone.utc).isoformat()}
    write(root/'protocol.json',json.dumps(protocol,indent=2))
    for case,n,arm in schedule():
        candidate=root/f'{case}-{n}-{arm}'; cases.prepare(case,candidate)
        for args in (['init','-q'],['add','.'],['-c','user.name=Benefit pilot','-c','user.email=pilot@example.invalid','commit','-qm','Frozen completion case']):
            done=run(['git','-c',f'safe.directory={candidate.as_posix()}',*args],cwd=candidate,timeout=15,shell=False)
            if done.returncode:
                raise ValueError('candidate Git setup failed; retain this batch and choose a new destination')
        save(candidate,Config(profile='guide' if arm=='tool' else 'off',commands={'tests':'python visible.py'},auto_detect=False,strength={'enabled':False}))
        manifest={'root':str(candidate),'files':cases.names(case),'host':host,
                  'plugin':[sys.executable,str(source/'plugin/bin/ep_hook.py')] if arm=='tool' else [],
                  'history':str(root/f'{candidate.name}-proposals.jsonl'),'command':'python visible.py'}
        _write(root/f'{candidate.name}-contract.json',manifest)
        events=('SessionStart','UserPromptSubmit','PreToolUse','PostToolUse','PostToolUseFailure','Stop')
        hooks={event:[{'hooks':[{'type':'command','command':invocation([sys.executable,str(source/'eval/proposals.py'),str(root/f'{candidate.name}-contract.json'),event]),'timeout':600 if event=='Stop' else 120}]}] for event in events}
        _write(candidate/'.claude/settings.local.json',{'hooks':hooks})
        if arm=='tool':
            configured(host,candidate,candidate/'.claude/settings.local.json',changed=True)
    return protocol


def _harness():
    paths=[Path(__file__),Path(cases.__file__),Path(proposals.__file__),Path(subscription.__file__)]
    return hashlib.sha256(b''.join(p.read_bytes() for p in paths)).hexdigest()


def _seal(root,candidate):
    return hashlib.sha256(b''.join(p.read_bytes() for p in (root/'protocol.json',root/f'{candidate.name}-contract.json',candidate/'.claude/settings.local.json',candidate/'.elevenpowers/config.json'))).hexdigest()


def run_batch(root, executable, native_project):
    from core import health
    root=Path(root).resolve(strict=True)
    protocol=json.loads((root/'protocol.json').read_text())
    if (set(protocol)!={'schema_version','host','model','effort','seconds_per_run','schedule','cases','runtime_fingerprint','harness_fingerprint','prepared_at'} or
            type(protocol.get('schema_version')) is not int or protocol['schema_version']!=1 or
            protocol.get('host')!='claude' or protocol.get('model')!=subscription.MODELS['claude'] or protocol.get('effort')!='medium' or
            type(protocol.get('seconds_per_run')) is not int or not 1<=protocol['seconds_per_run']<=240 or
            protocol.get('schedule')!=[list(x) for x in schedule()] or protocol.get('harness_fingerprint')!=_harness() or protocol.get('cases')!=[cases.identity(c) for c in cases.CASES] or protocol.get('runtime_fingerprint')!=fingerprint()):
        raise ValueError('frozen protocol changed')
    if list(root.glob('*-result.json')):
        raise ValueError('batch already attempted; preserve all attempts')
    if health.inspect('claude',Path(native_project),timeout=10)['health']['state']!='observed':
        write(root/'blocked.json',json.dumps({'state':'blocked','reason':'native_pipeline_not_observed'}))
        raise ValueError('native pipeline must be observed before coding calls')
    if not subscription.auth('claude',executable,root):
        raise ValueError('subscription authentication unavailable')
    records=[]
    env={**os.environ,'PATH':str(Path(sys.executable).parent)+os.pathsep+os.environ.get('PATH','')}
    for case,n,arm in schedule():
        candidate=root/f'{case}-{n}-{arm}'; result_path=root/f'{candidate.name}-result.json'
        sealed=_seal(root,candidate)
        record={'schema_version':1,'case':case,'replicate':n,'arm':arm,'state':'running',
                'initial_grade':challenge.grade(candidate),'final_grade':None,'proposals':[],
                'model':protocol['model'],'effort':'medium','elapsed_ms':None,'exit_code':None,'observation':None,'callbacks':{}}
        write(result_path,json.dumps(record,indent=2))
        started=time.monotonic()
        try:
            done=run(subscription.command('claude',executable,candidate,cases.files(case)['TASK.txt']),cwd=candidate,timeout=protocol['seconds_per_run'],shell=False,env=env)
            record.update(exit_code=done.returncode,observation=subscription.observation('claude',done.stdout,done.stderr))
            obs=record['observation']
            if done.returncode or not obs['completed'] or obs['models']!=[protocol['model']]:
                record['state']='host_failed'
            elif not cases.contract(case,candidate) or sealed!=_seal(root,candidate) or _harness()!=protocol['harness_fingerprint'] or fingerprint()!=protocol['runtime_fingerprint']:
                record['state']='invalid'
            else:
                history=proposals.read(root/f'{candidate.name}-proposals.jsonl')
                for p in history:
                    if p.get('state')=='overflow':
                        raise ValueError('proposal limit exceeded')
                    record['proposals'].append({'decision':p['decision'],'plugin_exit':p['plugin_exit'],
                                               'before_grade':grade_snapshot(case,p['before']),
                                               'after_grade':grade_snapshot(case,p['after']),
                                               'verification_before':p.get('verification_before','unavailable'),
                                               'verification_after':p.get('verification_after','unavailable')})
                record['final_grade']=challenge.grade(candidate)
                record['state']='graded' if history and all(p['before_grade']['state']=='graded' and p['after_grade']['state']=='graded' for p in record['proposals']) and record['final_grade']['state']=='graded' else 'incomplete'
            if arm=='tool':
                record['callbacks']={k:v.get('processed',0) for k,v in activation('claude',candidate).get('phases',{}).items()}
        except subprocess.TimeoutExpired:
            record['state']='timeout'
        except (ValueError,OSError,subprocess.SubprocessError) as error:
            record['state']='setup'; record['error']=type(error).__name__
        record['elapsed_ms']=round((time.monotonic()-started)*1000,3)
        write(result_path,json.dumps(record,indent=2,allow_nan=False),force=True); records.append(record)
        print(json.dumps({'case':case,'replicate':n,'arm':arm,'state':record['state'],'final':record['final_grade']['passed'] if record['final_grade'] else None}),flush=True)
        if (record.get('observation') or {}).get('failure')=='quota_exhausted':
            break
    value=summarize(records); write(root/'summary.json',json.dumps(value,indent=2)); return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='operation',required=True)
    prep=commands.add_parser('prepare'); prep.add_argument('directory'); prep.add_argument('--seconds',type=int,default=240)
    execute=commands.add_parser('run'); execute.add_argument('directory'); execute.add_argument('--executable',required=True); execute.add_argument('--native-project',required=True)
    args=parser.parse_args()
    try:
        value=prepare_batch(args.directory,seconds=args.seconds) if args.operation=='prepare' else run_batch(args.directory,args.executable,args.native_project)
        print(json.dumps(value,indent=2))
        return 0
    except (ValueError,OSError) as error:
        parser.exit(1,str(error)+'\n')


if __name__=='__main__':
    sys.exit(main())
