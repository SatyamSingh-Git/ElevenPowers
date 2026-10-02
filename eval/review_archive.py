"""Inspect/regrade saved review tests; neither operation launches a model."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

from .benefit_archive import _read, verify_checksums
from .review_checkpoint import grade

HARNESS_FILES=('eval/review_checkpoint.py','eval/review_pilot.py','eval/review_archive.py',
               'core/process.py','core/parsers.py')


def _execution(value):
    states={'passed','failed','setup','empty','timeout','output_limit','unavailable','invalid','not_run','modified_inputs'}
    fields={'state','exit_code','passed','failed','skipped','error','elapsed_ms'}
    if not isinstance(value,dict) or set(value)-fields or value.get('state') not in states:
        raise ValueError('invalid execution state')
    for key in ('passed','failed','skipped','error'):
        if key in value and (type(value[key]) is not int or not 0<=value[key]<=100_000_000):
            raise ValueError('invalid execution count')
    if 'elapsed_ms' in value and (type(value['elapsed_ms']) not in (int,float) or not math.isfinite(value['elapsed_ms']) or value['elapsed_ms']<0):
        raise ValueError('invalid execution timing')
    state=value['state']
    if state in ('passed','failed'):
        if not fields<=value.keys() or value['exit_code']!=(0 if state=='passed' else 1) or value['error'] or (state=='passed' and (not value['passed'] or value['failed'])) or (state=='failed' and not value['failed']):
            raise ValueError('execution summary contradicts outcome')


def _grade(value, ids):
    if not isinstance(value,dict) or set(value)!={'baseline','faults'} or not isinstance(value['faults'],list) or [f.get('id') for f in value['faults']]!=ids:
        raise ValueError('invalid saved grade')
    _execution(value['baseline'])
    for fault in value['faults']:
        if set(fault)!={'id','state','execution'}:
            raise ValueError('invalid saved fault outcome')
        _execution(fault['execution'])
        state=fault['execution']['state']
        expected='detected' if state=='failed' else 'undetected' if state=='passed' else state
        if fault['state']!=expected or (value['baseline']['state']!='passed' and state!='not_run'):
            raise ValueError('saved detection contradicts execution')


def _slot(value, protocol):
    if value.get('seconds_cap')!=protocol['seconds_per_review'] or type(value.get('elapsed_ms')) not in (int,float) or not math.isfinite(value['elapsed_ms']) or value['elapsed_ms']<0:
        raise ValueError('invalid recorded review budget')
    obs=value.get('host_observation')
    if obs is not None:
        if not isinstance(obs,dict) or set(obs)!={'completed','usage','models','completion_language','failure'} or type(obs['completed']) is not bool or type(obs['completion_language']) is not bool or not isinstance(obs['models'],list) or any(not isinstance(m,str) or not re.fullmatch('[a-z0-9.-]{1,80}',m) for m in obs['models']):
            raise ValueError('invalid observed host identity')
        if obs['usage'] is not None and (not isinstance(obs['usage'],dict) or any(type(n) is not int or not 0<=n<=1_000_000_000 for n in obs['usage'].values())):
            raise ValueError('invalid observed host usage')
    if value['state']=='completed' and (not value['launch_attempted'] or not obs or not obs['completed'] or value.get('exit_code')!=0):
        raise ValueError('completion lacks native evidence')
    additions=value.get('additions')
    if not isinstance(additions,dict) or len(additions)>32 or any(not isinstance(n,str) or not isinstance(v,str) for n,v in additions.items()) or sum(len(v.encode()) for v in additions.values())>1024*1024:
        raise ValueError('invalid saved additions')
    from .review_checkpoint import _path
    for name in additions:
        _path(name)
        if not (name.startswith('tests/') and Path(name).name.startswith('test_') and name.endswith('.py')):
            raise ValueError('unapproved saved test path')
    return bool(value['state']=='completed' and value['scope']=='preserved' and obs['models']==[protocol['model']])


def grade_identity(value):
    def execution(item):
        return {key:item.get(key) for key in ('state','passed','failed','skipped','error')}
    return {'baseline':execution(value['baseline']),
            'faults':[{'id':v['id'],'state':v['state'],'execution':execution(v['execution'])} for v in value['faults']]}


def inspect(directory, *, repositories=None, destination=None, python=None):
    directory=Path(directory).resolve(strict=True)
    verify_checksums(directory/'checksums.json')
    protocol=_read(directory/'protocol.json')
    names=protocol.get('cases')
    if protocol.get('schema_version')!=1 or not isinstance(names,list) or not 1<=len(names)<=4 or len(set(names))!=len(names) or any(not re.fullmatch('[a-z0-9][a-z0-9-]{0,79}',n) for n in names):
        raise ValueError('invalid review protocol')
    wanted={(name,arm) for name in names for arm in ('ordinary','assisted')}
    schedule=protocol.get('schedule')
    if not isinstance(schedule,list) or len(schedule)!=len(wanted) or {tuple(v) for v in schedule}!=wanted:
        raise ValueError('invalid review schedule')
    if protocol.get('model')!='claude-sonnet-5' or protocol.get('effort')!='medium' or protocol.get('seconds_per_review')!=480:
        raise ValueError('unsupported review protocol')
    hashes=protocol.get('harness_files')
    if not isinstance(hashes,dict) or set(hashes)!=set(HARNESS_FILES) or any(not isinstance(v,str) or not re.fullmatch('[a-f0-9]{64}',v) for v in hashes.values()):
        raise ValueError('invalid harness identity')
    if type(protocol.get('seconds_per_grade')) is not int or not 0<protocol['seconds_per_grade']<=120:
        raise ValueError('invalid local grading cap')
    manifest=_read(directory/'checksums.json')['files']
    required={'protocol.json'} | {f'{kind}-{name}.json' for name in names for kind in ('case','reviews','observations')}
    if not required<=manifest.keys():
        raise ValueError('unsealed review inputs')
    regrade=destination is not None
    if regrade:
        destination=Path(destination).absolute()
        if destination.exists() or any(p.is_symlink() for p in (destination,*destination.parents)):
            raise ValueError('new unlinked regrade directory required')
        if not isinstance(repositories,dict):
            raise ValueError('local repository cache mapping is required')
    records=[]
    reproduced=True
    for name in names:
        fixture=_read(directory/f'case-{name}.json')
        case=fixture['case']; faults=fixture['faults']; initial=fixture['no_review']
        if case['id']!=name or not re.fullmatch('[a-f0-9]{40}',case['base']) or 'repository' in case:
            raise ValueError('invalid portable checkpoint identity')
        ids=[f['id'] for f in faults]
        if len(ids)!=len(set(ids)) or len(ids)>32 or any(f['path'] not in case['source_paths'] for f in faults):
            raise ValueError('invalid frozen fault identities')
        _grade(initial,ids)
        saved=_read(directory/f'reviews-{name}.json')
        if not isinstance(saved,list) or len(saved)!=2 or {r['arm'] for r in saved}!={'ordinary','assisted'}:
            raise ValueError('missing retained review slots')
        for record in saved:
            if record['case']!=name or record['requested_model']!=protocol['model'] or record['effort']!='medium' or type(record['launch_attempted']) is not bool:
                raise ValueError('invalid retained slot identity')
            qualified=_slot(record,protocol)
            if record['scope']=='preserved':
                _grade(record.get('grade'),ids)
                qualified &= record['grade']['baseline']['state']=='passed'
                qualified &= 'equivalent-format-control' in ids
                qualified &= all(f['state']=='undetected' for f in record['grade']['faults'] if f['id']=='equivalent-format-control')
            records.append({'case':name,'arm':record['arm'],'state':record['state'],'scope':record['scope'],
                            'added_files':len(record['additions']),'condition_qualified':bool(qualified)})
        if regrade:
            case={**case,'repository':repositories[case['repository_key']]}
            command=[python or sys.executable,'ep_review_pytest.py','tests','-q','-p','no:cacheprovider']
            actual=grade(case,{},faults,destination/name/'no-review',command,seconds=protocol['seconds_per_grade'])
            reproduced &= grade_identity(actual)==grade_identity(initial)
            for record in saved:
                if record['scope']!='preserved' or 'grade' not in record:
                    continue
                actual=grade(case,record['additions'],faults,destination/name/record['arm'],command,
                             seconds=protocol['seconds_per_grade'])
                reproduced &= grade_identity(actual)==grade_identity(record['grade'])
    current=True
    for name,digest in hashes.items():
        path=Path(__file__).resolve().parents[1]/name
        current &= path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==digest
    return {'checksums_valid':True,'current_harness':bool(current),'slots':records,
            'regraded':regrade,'grades_match':bool(reproduced) if regrade else None,
            'integrity':'unsigned internal consistency; no provenance authentication'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--repositories',type=Path,help='JSON object mapping repository keys to local caches')
    parser.add_argument('--regrade',type=Path,help='new directory; explicit local tests only')
    parser.add_argument('--python',help='interpreter with the pinned upstream test dependencies')
    args=parser.parse_args()
    try:
        value=inspect(args.archive,repositories=_read(args.repositories) if args.repositories else None,
                      destination=args.regrade,python=args.python)
        print(json.dumps(value,indent=2))
        return 2 if value['grades_match'] is False else 0
    except (ValueError,OSError,KeyError,TypeError):
        parser.exit(2,'Review archive could not be validated or reproduced.\n')


if __name__=='__main__':
    raise SystemExit(main())
