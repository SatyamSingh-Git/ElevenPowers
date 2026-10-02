"""Bounded hard-task evidence, including failed calls; regrading is explicit."""
import argparse
import base64
import json
import math
from pathlib import Path
import re

from core.export import write
from . import benefit, benefit_archive, hard_cases as cases, hard_scenarios, proposals, subscription


def valid_grade(case,value):
    if type(value) is not dict or set(value)!={'state','passed','total','regressions','checks'}:return False
    if value['state'] in ('setup','unavailable'):
        return type(value['passed']) is int and value['passed']==0 and type(value['total']) is int and value['total']==0 and value['regressions'] is None and value['checks']=={}
    names=[r[0] for r in hard_scenarios.SCENARIOS[case]()]
    return (value['state']=='graded' and type(value['checks']) is dict and set(value['checks'])==set(names)
            and all(type(v) is bool for v in value['checks'].values()) and type(value['passed']) is int
            and value['passed']==sum(value['checks'].values()) and type(value['total']) is int and value['total']==len(names)
            and type(value['regressions']) is int and value['regressions']==sum(not value['checks'][n] for n in names[:2]))


def _snapshot(case,value):
    if type(value) is not dict or set(value)!={'state','files','fingerprint'}:raise ValueError('invalid snapshot')
    if value['state']=='incomplete':
        if value['files'] or value['fingerprint'] is not None:raise ValueError('invalid incomplete snapshot')
        return
    if value['state']!='complete' or type(value['files']) is not dict or set(value['files'])!=set(cases.names(case)):raise ValueError('invalid snapshot files')
    size=0
    for encoded in value['files'].values():
        if encoded is not None:
            if type(encoded) is not str:raise ValueError('invalid snapshot encoding')
            size+=len(base64.b64decode(encoded,validate=True))
    import hashlib
    if size>proposals.MAX_BYTES or hashlib.sha256(json.dumps(value['files'],sort_keys=True).encode()).hexdigest()!=value['fingerprint']:raise ValueError('snapshot fingerprint or byte bound')


def publish(root,destination):
    root=Path(root).resolve();protocol=benefit_archive._read(root/'protocol.json');runs=[]
    for c,n,a in benefit.schedule(suite=cases,repeats=1):
        name=f'{c}-{n}-{a}';path=root/f'{name}-result.json'
        if not path.exists():continue
        record=benefit_archive._read(path);snapshot=record.pop('final_snapshot')
        contract=benefit_archive._read(root/f'{name}-contract.json')
        try:
            history=proposals.observed(contract);history_state='complete'
        except (OSError,ValueError):
            history=proposals.read(contract['history']);history_state='incomplete'
        runs.append({'record':record,'history':history,'history_state':history_state,'final_snapshot':snapshot})
    value={'schema_version':1,'protocol':protocol,'attempt':benefit_archive._read(root/'attempt.json'),'runs':runs}
    if (root/'continuation.json').exists():
        value.update(schema_version=2,prior_attempt=value['attempt'],attempt=benefit_archive._read(root/'continuation.json'))
    write(Path(destination),json.dumps(value,indent=2,allow_nan=False))
    return inspect(destination)


def inspect(path,regrade=False):
    value=benefit_archive._read(path)
    if type(value) is not dict or type(value.get('schema_version')) is not int or value['schema_version'] not in (1,2) or set(value)!=({'schema_version','protocol','attempt','runs'}|({'prior_attempt'} if value['schema_version']==2 else set())):raise ValueError('invalid hard archive')
    protocol=value['protocol'];expected=benefit.schedule(suite=cases,repeats=1)
    fields={'schema_version','host','model','effort','seconds_per_run','schedule','cases','runtime_fingerprint','harness_fingerprint','prepared_at','candidate_seals','suite','repeats'}
    now=[cases.identity(c) for c in cases.CASES]
    if (type(protocol) is not dict or set(protocol)!=fields or type(protocol['schema_version']) is not int or protocol['schema_version']!=3
        or protocol['suite']!=cases.SUITE or type(protocol['repeats']) is not int or protocol['repeats']!=1 or protocol['host']!='claude'
        or protocol['model'] not in subscription.SUPPORTED_MODELS['claude'] or protocol['effort']!='medium'
        or type(protocol['seconds_per_run']) is not int or not 1<=protocol['seconds_per_run']<=480
        or protocol['schedule']!=[list(r) for r in expected] or type(protocol['cases']) is not list or len(protocol['cases'])!=4):raise ValueError('unsupported hard protocol')
    for old,current in zip(protocol['cases'],now):
        if type(old) is not dict or set(old)!=set(current) or any(old[k]!=current[k] for k in ('case','task','prompt')) or not isinstance(old['grader'],str) or not re.fullmatch('[a-f0-9]{64}',old['grader']):raise ValueError('changed task contract')
    hashes={'runtime_fingerprint','harness_fingerprint'}
    if any(type(protocol[k]) is not str or not re.fullmatch('[a-f0-9]{64}',protocol[k]) for k in hashes):raise ValueError('invalid producer identity')
    seals=protocol['candidate_seals']
    if type(seals) is not dict or set(seals)!={f'{c}-{n}-{a}' for c,n,a in expected} or any(type(h) is not str or not re.fullmatch('[a-f0-9]{64}',h) for h in seals.values()):raise ValueError('invalid prepared identities')
    attempt=value['attempt']
    attempt_fields={'schema_version','state','phase','started_at','runs','error','controller_pid','prior_attempt_preserved','recorded_harness','execution_harness'}
    if type(attempt) is not dict or set(attempt)-attempt_fields or type(attempt.get('schema_version')) is not int or attempt.get('schema_version')!=1 or attempt.get('state') not in ('finished','setup_failed'):raise ValueError('unfinished archive attempt')
    if value['schema_version']==2:
        prior=value['prior_attempt']
        if type(prior) is not dict or set(prior)-attempt_fields or prior.get('state')!='running' or prior.get('schema_version')!=1 or attempt.get('prior_attempt_preserved') is not True or attempt.get('recorded_harness')!=protocol['harness_fingerprint'] or type(attempt.get('execution_harness')) is not str or not re.fullmatch('[a-f0-9]{64}',attempt['execution_harness']):raise ValueError('invalid continuation identity')
    if type(value['runs']) is not list or len(value['runs'])>8:raise ValueError('hard run bound exceeded')
    records=[];matched=True;regraded=0
    rf={'schema_version','case','replicate','arm','state','initial_grade','final_grade','proposals','model','effort','elapsed_ms','exit_code','observation','callbacks'}
    for entry in value['runs']:
        if type(entry) is not dict or set(entry)!={'record','history','history_state','final_snapshot'}:raise ValueError('invalid hard run fields')
        r=entry['record'];history=entry['history']
        if type(r) is not dict or set(r)-{'error'}!=rf or r['schema_version']!=1 or type(r['schema_version']) is not int or r['case'] not in cases.CASES or type(r['replicate']) is not int or r['replicate']!=0 or r['arm'] not in ('tool','baseline') or r['state'] not in ('graded','host_failed','invalid','incomplete','timeout','setup','interrupted'):raise ValueError('invalid hard result')
        c=r['case']
        timing_ok=(r['state']=='interrupted' and r['elapsed_ms'] is None) or (type(r['elapsed_ms']) in (int,float) and math.isfinite(r['elapsed_ms']) and r['elapsed_ms']>=0)
        if r['model']!=protocol['model'] or r['effort']!='medium' or not timing_ok or (r['exit_code'] is not None and type(r['exit_code']) is not int) or not valid_grade(c,r['initial_grade']) or not valid_grade(c,r['final_grade']):raise ValueError('invalid measured result')
        if 'error' in r and (type(r['error']) is not str or not re.fullmatch('[A-Za-z]{1,80}',r['error'])):raise ValueError('unsafe error metadata')
        obs=r['observation']
        if obs is not None:
            if type(obs) is not dict or set(obs)!={'completed','usage','models','completion_language','failure'} or type(obs['completed']) is not bool or type(obs['completion_language']) is not bool or type(obs['models']) is not list or any(type(m) is not str or not re.fullmatch('[a-z0-9.-]{1,80}',m) for m in obs['models']) or obs['failure'] not in ('unavailable','quota_exhausted','blocked_by_policy'):raise ValueError('invalid host observation')
            if obs['usage'] is not None and (type(obs['usage']) is not dict or set(obs['usage'])-{'input_tokens','output_tokens','cached_input_tokens','cache_read_input_tokens','cache_creation_input_tokens','reasoning_output_tokens'} or any(type(v) is not int or not 0<=v<=1_000_000_000 for v in obs['usage'].values())):raise ValueError('invalid usage metadata')
        if type(r['callbacks']) is not dict or set(r['callbacks'])-{'SessionStart','UserPromptSubmit','PreToolUse','PostToolUse','PostToolUseFailure','Stop'} or any(type(n) is not int or not 0<=n<=10000 for n in r['callbacks'].values()):raise ValueError('invalid callback metadata')
        if type(history) is not list or len(history)>proposals.MAX_RECORDS+1 or entry['history_state'] not in ('complete','incomplete') or type(r['proposals']) is not list or len(r['proposals'])>proposals.MAX_RECORDS:raise ValueError('invalid history bound')
        previous='0'*64
        for h in history:
            if type(h) is not dict or h.get('previous')!=previous or proposals._hash({k:v for k,v in h.items() if k!='hash'})!=h.get('hash'):raise ValueError('changed history chain')
            previous=h['hash']
            if h.get('state')=='overflow':continue
            if set(h)!={'phase','at','before','after','plugin_exit','verification_before','verification_after','decision','previous','hash'} or h['phase']!='Stop' or type(h['at']) not in (int,float) or not math.isfinite(h['at']):raise ValueError('invalid history observation')
            for k in ('before','after'):_snapshot(c,h[k])
        for p,h in zip(r['proposals'],history):
            if type(p) is not dict or set(p)!={'decision','plugin_exit','before_grade','after_grade','verification_before','verification_after'} or any(p[k]!=h.get(k) for k in ('decision','plugin_exit','verification_before','verification_after')) or not valid_grade(c,p['before_grade']) or not valid_grade(c,p['after_grade']):raise ValueError('invalid proposal grade')
            if p['decision'] not in ('allow','block','unavailable') or p['plugin_exit'] not in (None,0,2) or any(p[k] not in ('missing','stale','fail','incomplete','fresh_pass','unavailable') for k in ('verification_before','verification_after')):raise ValueError('invalid intervention')
            if regrade:
                for k in ('before','after'):
                    matched &= benefit.grade_snapshot(c,h[k],suite=cases)==p[k+'_grade'];regraded+=1
        _snapshot(c,entry['final_snapshot'])
        if r['state']=='graded' and (entry['history_state']!='complete' or not history or len(history)!=len(r['proposals']) or r['exit_code']!=0 or obs is None or not obs['completed'] or obs['models']!=[protocol['model']] or r['final_grade']['state']!='graded' or (r['arm']=='tool' and r['callbacks'].get('Stop')!=len(history))):raise ValueError('unqualified completion')
        if regrade:
            matched &= benefit.grade_snapshot(c,entry['final_snapshot'],suite=cases)==r['final_grade'];regraded+=1
        records.append(r)
    keys=[(r['case'],r['replicate'],r['arm']) for r in records]
    if len(keys)!=len(set(keys)) or not set(keys)<=set(expected) or (attempt['state']=='finished' and attempt.get('runs')!=len(keys)):raise ValueError('duplicate or missing attempted run')
    return {'archive_schema_version':value['schema_version'],'current_harness':protocol['harness_fingerprint']==benefit._harness(cases),
            'continuation_harness_current':attempt.get('execution_harness')==benefit._harness(cases) if value['schema_version']==2 else None,
            'current_evaluator':protocol['cases']==now,'regraded':bool(regrade),'snapshots_regraded':regraded,
            'grades_match':matched if regrade else None,'summary':benefit.summarize(records,suite=cases,repeats=1)}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('archive');parser.add_argument('--regrade',action='store_true');parser.add_argument('--checksums')
    args=parser.parse_args()
    try:
        if args.checksums:benefit_archive.verify_checksums(args.checksums)
        result=inspect(args.archive,args.regrade);print(json.dumps(result,indent=2));return int(result['grades_match'] is False)
    except (ValueError,OSError) as error:parser.exit(1,str(error)+'\n')


if __name__=='__main__':raise SystemExit(main())
