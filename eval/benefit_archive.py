"""Whitelisted completion pilot archive; regrading is explicit, never a model call."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

from . import benefit, benefit_cases as cases, proposals, subscription


def _pairs(pairs):
    value={}
    for k,v in pairs:
        if k in value:
            raise ValueError('duplicate archive key')
        value[k]=v
    return value


def _read(path):
    path=Path(path)
    if path.is_symlink():
        raise ValueError('linked archive')
    with path.open('rb') as stream:
        raw=stream.read(8*1024*1024+1)
    if len(raw)>8*1024*1024:
        raise ValueError('archive byte limit exceeded')
    return json.loads(raw,object_pairs_hook=_pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite archive value')))


def _grade(g):
    from .challenge_grader import CHECK_NAMES
    return (isinstance(g,dict) and set(g)=={'state','passed','total','regressions','checks'} and
            g['state']=='graded' and type(g['passed']) is int and type(g['total']) is int and g['total']==16 and
            isinstance(g['checks'],dict) and set(g['checks'])==set(CHECK_NAMES) and all(type(v) is bool for v in g['checks'].values()) and
            g['passed']==sum(g['checks'].values()) and type(g['regressions']) is int and
            g['regressions']==sum(not g['checks'][k] for k in ('view_total','view_statement','basic_transfer','empty')))


def inspect(path, regrade=False):
    value=_read(path)
    if not isinstance(value,dict) or set(value)!={'schema_version','protocol','runs'} or value['schema_version']!=1 or type(value['schema_version']) is not int:
        raise ValueError('invalid archive fields')
    protocol=value['protocol']
    fields={'schema_version','host','model','effort','seconds_per_run','schedule','cases','runtime_fingerprint','harness_fingerprint','prepared_at'}
    if (not isinstance(protocol,dict) or set(protocol)!=fields or type(protocol['schema_version']) is not int or protocol['schema_version']!=1 or
            protocol['host']!='claude' or protocol['model']!=subscription.MODELS['claude'] or protocol['effort']!='medium' or
            type(protocol['seconds_per_run']) is not int or not 1<=protocol['seconds_per_run']<=240 or
            protocol['schedule']!=[list(x) for x in benefit.schedule()] or protocol['cases']!=[cases.identity(c) for c in cases.CASES] or
            any(not isinstance(protocol[k],str) or not re.fullmatch('[a-f0-9]{64}',protocol[k]) for k in ('runtime_fingerprint','harness_fingerprint'))):
        raise ValueError('unsupported recorded protocol')
    runs=value['runs']
    if not isinstance(runs,list) or len(runs)!=8:
        raise ValueError('eight retained runs required')
    records=[]; grades_match=True
    record_fields={'schema_version','case','replicate','arm','state','initial_grade','final_grade','proposals','model','effort','elapsed_ms','exit_code','observation','callbacks'}
    for entry in runs:
        if not isinstance(entry,dict) or set(entry)!={'record','history','final_snapshot'}:
            raise ValueError('invalid archived run')
        r=entry['record']; hist=entry['history']
        if (not isinstance(r,dict) or set(r)!=record_fields or r['schema_version']!=1 or type(r['schema_version']) is not int or
                r['case'] not in cases.CASES or type(r['replicate']) is not int or r['replicate'] not in (0,1) or r['arm'] not in ('baseline','tool') or
                r['state']!='graded' or r['model']!=protocol['model'] or r['effort']!='medium' or
                type(r['elapsed_ms']) not in (int,float) or not math.isfinite(r['elapsed_ms']) or r['elapsed_ms']<0 or
                type(r['exit_code']) is not int or r['exit_code']!=0 or not _grade(r['initial_grade']) or not _grade(r['final_grade']) or
                not isinstance(r['proposals'],list) or not isinstance(hist,list) or not 1<=len(hist)<=16 or len(hist)!=len(r['proposals'])):
            raise ValueError('invalid archived result')
        obs=r['observation']
        if (not isinstance(obs,dict) or set(obs)!={'completed','usage','models','completion_language','failure'} or
                obs['completed'] is not True or type(obs['completion_language']) is not bool or obs['models']!=[protocol['model']] or
                obs['failure'] not in ('unavailable','quota_exhausted','blocked_by_policy') or
                not isinstance(r['callbacks'],dict) or set(r['callbacks'])-{'SessionStart','UserPromptSubmit','PreToolUse','PostToolUse','PostToolUseFailure','Stop'} or
                any(type(v) is not int or not 0<=v<=10000 for v in r['callbacks'].values())):
            raise ValueError('invalid private host metadata')
        if obs['usage'] is not None and (not isinstance(obs['usage'],dict) or set(obs['usage'])-{'input_tokens','output_tokens','cached_input_tokens','cache_read_input_tokens','cache_creation_input_tokens','reasoning_output_tokens'} or any(type(v) is not int or not 0<=v<=1_000_000_000 for v in obs['usage'].values())):
            raise ValueError('invalid usage metadata')
        previous='0'*64
        for p,h in zip(r['proposals'],hist):
            h_fields={'phase','at','before','after','plugin_exit','verification_before','verification_after','decision','previous','hash'}
            p_fields={'decision','plugin_exit','before_grade','after_grade','verification_before','verification_after'}
            if not isinstance(h,dict) or set(h)!=h_fields or not isinstance(p,dict) or set(p)!=p_fields:
                raise ValueError('invalid archived proposal')
            body={k:v for k,v in h.items() if k!='hash'}
            if h['previous']!=previous or proposals._hash(body)!=h['hash'] or h['phase']!='Stop' or type(h['at']) not in (int,float) or not math.isfinite(h['at']):
                raise ValueError('invalid archived history chain')
            previous=h['hash']
            if any(p[k]!=h[k] for k in ('decision','plugin_exit','verification_before','verification_after')) or not _grade(p['before_grade']) or not _grade(p['after_grade']):
                raise ValueError('conflicting proposal result')
            for k in ('verification_before','verification_after'):
                if p[k] not in ('missing','stale','fail','incomplete','fresh_pass','unavailable'):
                    raise ValueError('invalid verification state')
            if p['decision'] not in ('allow','block','unavailable') or p['plugin_exit'] not in (None,0,2):
                raise ValueError('unsupported completion decision')
            if regrade:
                grades_match &= benefit.grade_snapshot(r['case'],h['before'])==p['before_grade']
                grades_match &= benefit.grade_snapshot(r['case'],h['after'])==p['after_grade']
        if regrade:
            grades_match &= benefit.grade_snapshot(r['case'],entry['final_snapshot'])==r['final_grade']
        records.append(r)
    keys=[(r['case'],r['replicate'],r['arm']) for r in records]
    if len(set(keys))!=8 or set(keys)!=set(benefit.schedule()):
        raise ValueError('duplicate or missing run identity')
    return {'archive_schema_version':1,'current_harness':protocol['harness_fingerprint']==benefit._harness(),
            'regraded':bool(regrade),'grades_match':grades_match if regrade else None,
            'summary':benefit.summarize(records)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive');parser.add_argument('--regrade',action='store_true')
    args=parser.parse_args()
    try:
        result=inspect(args.archive,args.regrade);print(json.dumps(result,indent=2))
        raise SystemExit(0 if result['grades_match'] is not False else 1)
    except (ValueError,OSError) as error:
        parser.exit(1,str(error)+'\n')
