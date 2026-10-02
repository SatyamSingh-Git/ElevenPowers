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


def schedule(*,suite=cases,repeats=2):
    return [(case,n,arm) for n in range(repeats) for i,case in enumerate(suite.CASES)
            for arm in (('baseline','tool') if (n+(i if suite is not cases else 0))%2 == 0 else ('tool','baseline'))]


def grade_snapshot(case, value, *,suite=cases):
    unavailable = {'state':'unavailable','passed':0,'total':0,'regressions':None,'checks':{}}
    try:
        if value['state'] != 'complete' or set(value['files']) != set(suite.names(case)):
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
            if not suite.contract(case,root):
                return unavailable
            return _grade(case,root,suite)
    except (ValueError,KeyError,TypeError,OSError):
        return unavailable


def _grade(case,root,suite):
    return challenge.grade(root) if suite is cases else suite.grade(case,root)


def summarize(records, *,suite=cases,repeats=2):
    expected=set(schedule(suite=suite,repeats=repeats))
    keys=[(r['case'],r['replicate'],r['arm']) for r in records]
    complete=len(keys)==len(expected) and set(keys)==expected
    valid=[r for r in records if r['state']=='graded']
    repairs=[]; refreshes=[]
    for r in valid:
        for p in r['proposals']:
            if r['arm']=='tool' and p['decision']=='block' and p['before_grade']['state']=='graded' and r['final_grade']['state']=='graded' and p['before_grade']['passed'] < r['final_grade']['passed']:
                repairs.append([r['case'],r['replicate']])
            if r['arm']=='tool' and p.get('verification_before') in ('missing','stale','fail') and p.get('verification_after')=='fresh_pass':
                refreshes.append([r['case'],r['replicate']])
    value={'schema_version':1,'state':'incomplete' if not complete else 'qualified' if len(valid)==len(expected) else 'inconclusive',
            'runs':len(records),'valid_runs':len(valid),'repairs_after_block':repairs,
            'verification_refreshes':refreshes,'benefit_observed':bool(complete and repairs),
            'coding_improvement_observed':bool(complete and repairs),
            'receipt_refresh_observed':bool(complete and refreshes),
            'limits':['Eight original local runs cannot establish a population effect or speedup.',
                      'Native observations and local hash chains are not authentication or an OS security boundary.',
                      'A refreshed receipt is additional verification evidence, not necessarily a better patch.',
                      'Missing means no exact-command receipt; wrapped baseline tests may still have run.']}
    if suite is not cases:
        outcomes=[]
        for case in suite.CASES:
            pair={r['arm']:r for r in records if r['case']==case and r['replicate']==0}
            row={'case':case,'baseline':None,'tool':None,'difference':None}
            for arm in ('baseline','tool'):
                r=pair.get(arm)
                if r and r['state']=='graded':
                    g=r['final_grade'];row[arm]={'passed':g['passed'],'total':g['total'],'elapsed_ms':r.get('elapsed_ms')}
            if row['baseline'] and row['tool']:
                row['difference']=row['tool']['passed']-row['baseline']['passed']
            outcomes.append(row)
        value.update(paired_outcomes=outcomes,paired_correctness_advantage_observed=bool(complete and any(r['difference'] is not None and r['difference']>0 for r in outcomes)))
        value['limits'][0]='Eight authored scenario runs cannot establish a population effect, statistical significance or speedup.'
        value['limits'].append('A paired correctness advantage without a linked intervention does not establish a causal repair.')
    return value


def prepare_batch(destination, host='claude', seconds=240, *,suite=cases,repeats=2,model=None):
    if host != 'claude':
        raise ValueError('this decision pilot currently qualifies Claude exit-2 completion only')
    from . import hard_cases
    if suite not in (cases,hard_cases) or repeats!=(2 if suite is cases else 1):
        raise ValueError('unsupported frozen suite or repetition count')
    maximum=240 if suite is cases else 480
    if type(seconds) is not int or not 1<=seconds<=maximum:
        raise ValueError('run budget exceeds frozen suite allowance')
    selected=model or subscription.MODELS[host]
    if selected not in subscription.SUPPORTED_MODELS[host] or (suite is cases and selected!=subscription.MODELS[host]):
        raise ValueError('unsupported frozen model')
    root=Path(destination).absolute()
    if root.exists() or any(p.is_symlink() for p in (root,*root.parents)):
        raise ValueError('new unlinked batch directory required')
    root.mkdir(parents=True)
    source=Path(__file__).resolve().parents[1]
    protocol={'schema_version':2 if suite is cases else 3,'host':host,'model':selected,'effort':'medium',
              'seconds_per_run':seconds,'schedule':schedule(suite=suite,repeats=repeats),'cases':[suite.identity(c) for c in suite.CASES],
              'runtime_fingerprint':fingerprint(source),
              'harness_fingerprint':_harness(suite),'prepared_at':datetime.now(timezone.utc).isoformat(),'candidate_seals':{}}
    if suite is not cases:protocol.update(suite=suite.SUITE,repeats=repeats)
    for case,n,arm in schedule(suite=suite,repeats=repeats):
        candidate=root/f'{case}-{n}-{arm}'; suite.prepare(case,candidate)
        for args in (['init','-q'],['add','.'],['-c','user.name=Benefit pilot','-c','user.email=pilot@example.invalid','commit','-qm','Frozen completion case']):
            done=run(['git','-c',f'safe.directory={candidate.as_posix()}',*args],cwd=candidate,timeout=15,shell=False)
            if done.returncode:
                raise ValueError('candidate Git setup failed; retain this batch and choose a new destination')
        save(candidate,Config(profile='guide' if arm=='tool' else 'off',commands={'tests':'python visible.py'},auto_detect=False,strength={'enabled':False}))
        manifest={'root':str(candidate),'files':suite.names(case),'host':host,
                  'plugin':[sys.executable,str(source/'plugin/bin/ep_hook.py')] if arm=='tool' else [],
                  'history':str(root/f'{candidate.name}-proposals.jsonl'),'command':'python visible.py',
                  'attempts':str(root/f'{candidate.name}-observations')}
        _write(root/f'{candidate.name}-contract.json',manifest)
        events=('SessionStart','UserPromptSubmit','PreToolUse','PostToolUse','PostToolUseFailure','Stop')
        hooks={event:[{'hooks':[{'type':'command','command':invocation([sys.executable,str(source/'eval/proposals.py'),str(root/f'{candidate.name}-contract.json'),event]),'timeout':600 if event=='Stop' else 120}]}] for event in events}
        _write(candidate/'.claude/settings.local.json',{'hooks':hooks})
        if arm=='tool':
            configured(host,candidate,candidate/'.claude/settings.local.json',changed=True)
        protocol['candidate_seals'][candidate.name]=_seal(root,candidate,suite=suite)
    write(root/'protocol.json',json.dumps(protocol,indent=2))
    return protocol


def _harness(suite=cases):
    paths=[Path(__file__),Path(suite.__file__),Path(proposals.__file__),Path(subscription.__file__),
           Path(challenge.__file__),Path(__file__).with_name('challenge_grader.py'),Path(__file__).with_name('challenge_worker.py')]
    if suite is not cases:paths+=suite.evaluator_files()
    return hashlib.sha256(b''.join(p.read_bytes() for p in paths)).hexdigest()


def _seal(root,candidate, *,suite=cases):
    paths=[root/f'{candidate.name}-contract.json',candidate/'.claude/settings.local.json',candidate/'.elevenpowers/config.json']
    # Both project and local settings are active; expected absence is an input.
    for folder in (candidate/'.claude',candidate/'.elevenpowers'):
        paths += [folder/name for name in ('settings.json','CLAUDE.md','CLAUDE.local.md','config.json') if folder/name not in paths]
    paths += [candidate/'CLAUDE.local.md',candidate/'AGENTS.md',candidate/'AGENTS.override.md']
    paths += [candidate/name for name in suite.names(candidate.name.rsplit('-',2)[0])]
    values={}
    for path in paths:
        if any(p.is_symlink() for p in (path,*path.parents)):
            raise ValueError('linked prepared input')
        values[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()


def _configuration_seal(root,candidate):
    # Production edits are expected after launch, but host config remains frozen.
    paths=[root/f'{candidate.name}-contract.json',candidate/'.claude/settings.local.json',candidate/'.claude/settings.json',
           candidate/'.elevenpowers/config.json',candidate/'CLAUDE.md',candidate/'CLAUDE.local.md',candidate/'AGENTS.md',candidate/'AGENTS.override.md']
    values={}
    for path in paths:
        if any(p.is_symlink() for p in (path,*path.parents)):
            raise ValueError('linked configuration')
        values[path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()


def run_batch(root, executable, native_project):
    from core import health
    root=Path(root).resolve(strict=True)
    if (root/'attempt.json').exists() or list(root.glob('*-result.json')):
        raise ValueError('batch already attempted; preserve all attempts')
    attempt={'schema_version':1,'state':'running','phase':'protocol','started_at':datetime.now(timezone.utc).isoformat()}
    write(root/'attempt.json',json.dumps(attempt,indent=2))
    try:
        protocol=json.loads((root/'protocol.json').read_text())
        from . import hard_cases
        suite=hard_cases if protocol.get('suite')==hard_cases.SUITE else cases
        repeats=2 if suite is cases else 1
        fields={'schema_version','host','model','effort','seconds_per_run','schedule','cases','runtime_fingerprint','harness_fingerprint','prepared_at','candidate_seals'}
        if suite is not cases:fields|={'suite','repeats'}
        if (set(protocol)!=fields or
            type(protocol.get('schema_version')) is not int or protocol['schema_version']!=(2 if suite is cases else 3) or
            protocol.get('host')!='claude' or protocol.get('model') not in (subscription.SUPPORTED_MODELS['claude'] if suite is not cases else (subscription.MODELS['claude'],)) or protocol.get('effort')!='medium' or
            (suite is not cases and protocol.get('repeats')!=1) or
            type(protocol.get('seconds_per_run')) is not int or not 1<=protocol['seconds_per_run']<=(240 if suite is cases else 480) or
            protocol.get('schedule')!=[list(x) for x in schedule(suite=suite,repeats=repeats)] or protocol.get('harness_fingerprint')!=_harness(suite) or protocol.get('cases')!=[suite.identity(c) for c in suite.CASES] or protocol.get('runtime_fingerprint')!=fingerprint()):
            raise ValueError('frozen protocol changed')
        attempt['phase']='prepared_inputs'
        expected={f'{c}-{n}-{a}' for c,n,a in schedule(suite=suite,repeats=repeats)}
        if not isinstance(protocol['candidate_seals'],dict) or set(protocol['candidate_seals'])!=expected:
            raise ValueError('prepared candidate seals unavailable')
        for name in expected:
            if _seal(root,root/name,suite=suite)!=protocol['candidate_seals'][name]:
                raise ValueError('prepared candidate changed')
        attempt['phase']='native_health'
        if health.inspect('claude',Path(native_project),timeout=10)['health']['state']!='observed':
            raise ValueError('native pipeline must be observed before coding calls')
        attempt['phase']='subscription_auth'
        if not subscription.auth('claude',executable,root):
            raise ValueError('subscription authentication unavailable')
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        attempt.update(state='setup_failed',error=type(error).__name__)
        write(root/'attempt.json',json.dumps(attempt,indent=2),force=True)
        raise ValueError('batch setup failed: '+attempt['phase']+'; '+str(error)) from error
    records=[]
    env={**os.environ,'PATH':str(Path(sys.executable).parent)+os.pathsep+os.environ.get('PATH','')}
    for case,n,arm in schedule(suite=suite,repeats=repeats):
        candidate=root/f'{case}-{n}-{arm}'; result_path=root/f'{candidate.name}-result.json'
        record={'schema_version':1,'case':case,'replicate':n,'arm':arm,'state':'running',
                'initial_grade':_grade(case,candidate,suite),'final_grade':None,'proposals':[],
                'model':protocol['model'],'effort':'medium','elapsed_ms':None,'exit_code':None,'observation':None,'callbacks':{}}
        write(result_path,json.dumps(record,indent=2))
        started=time.monotonic()
        try:
            if _seal(root,candidate,suite=suite)!=protocol['candidate_seals'][candidate.name]:
                raise ValueError('prepared candidate changed before launch')
            sealed=_configuration_seal(root,candidate)
            done=run(subscription.command('claude',executable,candidate,suite.files(case)['TASK.txt'],model=protocol['model']),cwd=candidate,timeout=protocol['seconds_per_run'],shell=False,env=env)
            record.update(exit_code=done.returncode,observation=subscription.observation('claude',done.stdout,done.stderr))
            obs=record['observation']
            if done.returncode or not obs['completed'] or obs['models']!=[protocol['model']]:
                record['state']='host_failed'
            elif not suite.contract(case,candidate) or sealed!=_configuration_seal(root,candidate) or _harness(suite)!=protocol['harness_fingerprint'] or fingerprint()!=protocol['runtime_fingerprint'] or json.loads((root/'protocol.json').read_text())!=protocol:
                record['state']='invalid'
            else:
                config=json.loads((root/f'{candidate.name}-contract.json').read_text())
                history=proposals.observed(config)
                for p in history:
                    if p.get('state')=='overflow':
                        raise ValueError('proposal limit exceeded')
                    record['proposals'].append({'decision':p['decision'],'plugin_exit':p['plugin_exit'],
                                               'before_grade':grade_snapshot(case,p['before'],suite=suite),
                                               'after_grade':grade_snapshot(case,p['after'],suite=suite),
                                               'verification_before':p.get('verification_before','unavailable'),
                                               'verification_after':p.get('verification_after','unavailable')})
                record['final_grade']=_grade(case,candidate,suite)
                record['state']='graded' if history and all(p['before_grade']['state']=='graded' and p['after_grade']['state']=='graded' for p in record['proposals']) and record['final_grade']['state']=='graded' else 'incomplete'
            if arm=='tool':
                record['callbacks']={k:v.get('processed',0) for k,v in activation('claude',candidate).get('phases',{}).items()}
                if record['state']=='graded' and record['callbacks'].get('Stop')!=len(record['proposals']):
                    record['state']='incomplete'
        except subprocess.TimeoutExpired:
            record['state']='timeout'
        except (ValueError,OSError,subprocess.SubprocessError) as error:
            record['state']='setup'; record['error']=type(error).__name__
        if suite is not cases:
            record['final_snapshot']=proposals.snapshot(candidate,suite.names(case))
            if record['final_grade'] is None:
                record['final_grade']=grade_snapshot(case,record['final_snapshot'],suite=suite)
        record['elapsed_ms']=round((time.monotonic()-started)*1000,3)
        write(result_path,json.dumps(record,indent=2,allow_nan=False),force=True); records.append(record)
        print(json.dumps({'case':case,'replicate':n,'arm':arm,'state':record['state'],'final':record['final_grade']['passed'] if record['final_grade'] else None}),flush=True)
        if (record.get('observation') or {}).get('failure')=='quota_exhausted':
            break
    value=summarize(records,suite=suite,repeats=repeats); write(root/'summary.json',json.dumps(value,indent=2))
    attempt.update(state='finished',phase='coding_calls',runs=len(records))
    write(root/'attempt.json',json.dumps(attempt,indent=2),force=True)
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='operation',required=True)
    prep=commands.add_parser('prepare'); prep.add_argument('directory'); prep.add_argument('--seconds',type=int,default=240)
    prep.add_argument('--suite',choices=('original','hard'),default='original');prep.add_argument('--model',choices=subscription.SUPPORTED_MODELS['claude'])
    execute=commands.add_parser('run'); execute.add_argument('directory'); execute.add_argument('--executable',required=True); execute.add_argument('--native-project',required=True)
    args=parser.parse_args()
    try:
        from . import hard_cases
        value=prepare_batch(args.directory,seconds=args.seconds,suite=hard_cases if args.suite=='hard' else cases,repeats=1 if args.suite=='hard' else 2,model=args.model) if args.operation=='prepare' else run_batch(args.directory,args.executable,args.native_project)
        print(json.dumps(value,indent=2))
        return 0
    except (ValueError,OSError) as error:
        parser.exit(1,str(error)+'\n')


if __name__=='__main__':
    sys.exit(main())
