"""Four-stage outcome accounting and source reproduction; no model calls."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import tempfile

from core.redact import scrub
from .workflow_cases import case, NAMES
from .workflow_oracles import grade, oracle, PY_GROUPS, JS_GROUPS
from .preservation import _read, _write, _safe, _manifest, verify, _harness


def metrics(previous,current,stage):
    if not current or current.get('state')!='graded':
        return {'regressed':None,'earlier_failed':None,'new_failed':None}
    earlier=[g['id'] for g in current['groups'] if g['introduced_stage']<stage and g['state']=='failed']
    before={g['id']:g['state'] for g in previous['groups']} if previous and previous.get('state')=='graded' else None
    return {'regressed':[name for name in earlier if before.get(name)=='passed'] if before is not None else None,
            'earlier_failed':earlier,
            'new_failed':[g['id'] for g in current['groups'] if g['introduced_stage']==stage and g['state']=='failed']}


def _sources(folder,stage,value):
    data=_read(_safe(folder,f'source-{stage}.json'))
    if not isinstance(data,dict) or set(data)!=set(value['production']): raise ValueError('invalid source snapshot')
    if any(not isinstance(s,str) or len(s.encode())>256*1024 for s in data.values()):
        raise ValueError('invalid source bytes')
    return data


def _public_case_hash(value):
    keys=('id','language','files','production','public_command','new_test_paths','milestones','requests')
    return hashlib.sha256(json.dumps({k:value[k] for k in keys},sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _arm(batch,slot,protocol):
    value=case(slot.rsplit('-',1)[0]);folder=_safe(batch,slot)
    result={'state':'not_attempted','qualified':False,'delivery_verified':False,'stages':[],
            'model_seconds':None,'issues':[]}
    path=folder/'result.json'
    if not path.exists():return result
    try:
        record=_read(path);result['state']=record.get('state','incomplete')
        verify(batch,slot)
        if record.get('schema')!=2 or record.get('slot')!=slot:raise ValueError('record identity')
        stages=record['stages']
        if not isinstance(stages,list) or len(stages)>4:raise ValueError('stage list')
        previous=_read(folder/'baseline.json');spent=0;tasks=[];valid=True
        expected_session=protocol['seals'][slot]['session']
        for index,item in enumerate(stages,1):
            stage=item.get('stage');g=item.get('independent_grade',{})
            rows=g.get('groups',[]);canonical=[r for r in (PY_GROUPS if value['language']=='python' else JS_GROUPS) if r[1]<=index]
            ids=[(r.get('id'),r.get('introduced_stage')) for r in rows]
            grade_valid=(g.get('state')=='graded' and ids==[(r[0],r[1]) for r in canonical]
                         and all(r.get('state') in ('passed','failed') for r in rows)
                         and g.get('passed')==sum(r['state']=='passed' for r in rows)
                         and g.get('failed')==sum(r['state']=='failed' for r in rows))
            source=_sources(folder,index,value)
            hashes={name:hashlib.sha256(s.encode()).hexdigest() for name,s in source.items()}
            source_valid=(hashes==g.get('source_sha256') and all(item.get('source_after',{}).get(n)==h for n,h in hashes.items())
                          and g.get('oracle_sha256')==hashlib.sha256(oracle(value,index).encode()).hexdigest())
            cap=item.get('seconds_cap');elapsed=item.get('elapsed_ms',-1)/1000
            time_valid=(type(cap) in (int,float) and math.isfinite(cap) and 0<cap<=(protocol['seconds_per_session']-spent)/(5-index)+.001
                        and math.isfinite(elapsed) and 0<=elapsed<=cap+5)
            obs=item.get('host_observation',{})
            identified=(item.get('conversation_identity')==expected_session and obs.get('completed') is True
                        and obs.get('models')==[protocol['model']])
            ok=(stage==index and item.get('state')=='completed' and item.get('scope')=='preserved'
                and grade_valid and source_valid and time_valid and identified)
            valid=valid and ok;spent+=elapsed
            native=item.get('native',{});tasks.append(native.get('task',''))
            result['stages'].append({'stage':index,'state':item.get('state','incomplete'),
                'grade_state':g.get('state','incomplete'),'passed':g.get('passed'),'failed':g.get('failed'),
                'source_sha256':hashes,'oracle_sha256':g.get('oracle_sha256'),
                'model_seconds':elapsed,'delivery_verified':native.get('state')=='observed' and native.get('native_runner_adoption') is True,
                **metrics(previous,g,index)})
            previous=g if grade_valid else None
        total=record.get('model_seconds')
        valid=(valid and len(stages)==4 and record.get('state')=='completed' and type(total) in (int,float)
               and math.isfinite(total) and abs(total-spent)<.002 and total<=protocol['seconds_per_session']+5)
        if stages and stages[-1].get('source_after')!=_manifest(folder/'candidate'): valid=False
        result.update(qualified=bool(valid),model_seconds=total,
                      delivery_verified=bool(valid and all(s['delivery_verified'] for s in result['stages'])
                          and len(set(tasks))==4 and all(len(t)==64 for t in tasks)))
        if not valid:result['issues'].append('incomplete_unidentified_or_changed_attempt')
    except (OSError,ValueError,KeyError,TypeError,AttributeError,ZeroDivisionError):
        result['issues'].append('protocol_scope_or_snapshot_invalid')
    return result


def summarize(batch):
    batch=Path(batch).resolve(strict=True);protocol=_read(batch/'protocol.json')
    if protocol.get('schema')!=2:raise ValueError('four-stage protocol required')
    slots=protocol.get('slots',[])
    if (not slots or len(slots)>4 or len(set(slots))!=len(slots)
            or any(s.rsplit('-',1)[0] not in NAMES or s.rsplit('-',1)[-1] not in ('ordinary','assisted') for s in slots)):
        raise ValueError('invalid scheduled slots')
    names=list(dict.fromkeys(s.rsplit('-',1)[0] for s in slots));pairs=[]
    for name in names:
        arms={arm:_arm(batch,name+'-'+arm,protocol) if name+'-'+arm in slots else
              {'state':'not_scheduled','qualified':False,'stages':[],'delivery_verified':False}
              for arm in ('ordinary','assisted')}
        comparable=all(a['qualified'] for a in arms.values())
        if comparable:
            left={k:v for k,v in protocol['seals'][name+'-ordinary']['initial'].items() if not k.startswith('.claude/')}
            right={k:v for k,v in protocol['seals'][name+'-assisted']['initial'].items() if not k.startswith('.claude/')}
            comparable=left==right
        difference=arms['assisted']['stages'][-1]['passed']-arms['ordinary']['stages'][-1]['passed'] if comparable else None
        pairs.append({'case':name,**arms,'outcome_comparable':comparable,
                      'delivery_verified':arms['assisted']['delivery_verified'],'difference':difference})
    complete=all(pair['outcome_comparable'] for pair in pairs)
    return {'schema':2,'state':'complete' if complete else 'incomplete','scheduled':len(slots),
            'attempted':sum((_safe(batch,s)/'result.json').exists() for s in slots),
            'outcome_comparable':complete,'delivery_verified':all(p['delivery_verified'] for p in pairs),
            'readiness':'separate_installed_acceptance_required','pairs':pairs,
            'paired_correctness_advantage_observed':complete and any(p['difference']>0 for p in pairs),
            'limits':protocol.get('limits',[])}


def publish(destination,selection):
    out=Path(destination).absolute()
    if not selection or out.exists() or any(p.is_symlink() or getattr(p,'is_junction',lambda:False)() for p in (out,*out.parents)):
        raise ValueError('new unlinked archive required')
    batches={Path(b).resolve(strict=True) for b in selection.values()}
    if len(batches)!=1:raise ValueError('archive one frozen matched batch at a time')
    batch=next(iter(batches));protocol=_read(batch/'protocol.json')
    if set(selection)!=set(protocol['slots']):raise ValueError('retain every scheduled slot')
    summary=summarize(batch);out.mkdir(parents=True)
    manifest={'schema':2,'scheduled_slots':list(protocol['slots']),'stage_count':4,
              'protocol_sha256':hashlib.sha256((batch/'protocol.json').read_bytes()).hexdigest(),
              'harness_sha256':_harness(2),
              'public_case_sha256':{name:_public_case_hash(case(name)) for name in dict.fromkeys(s.rsplit('-',1)[0] for s in protocol['slots'])},
              'sources':[]}
    matches=True
    for slot in protocol['slots']:
        value=case(slot.rsplit('-',1)[0]);folder=batch/slot
        record=_read(folder/'result.json') if (folder/'result.json').exists() else {'stages':[]}
        for item in record.get('stages',[]):
            stage=item.get('stage')
            try:
                source=_sources(folder,stage,value)
                if any(scrub(s)!=s or str(batch) in s or batch.as_posix() in s for s in source.values()):
                    raise ValueError('source needs privacy review')
                filename=f'{slot}-source-{stage}.json';_write(out/filename,source)
                with tempfile.TemporaryDirectory(prefix='ep-workflow-export-') as temp:
                    root=Path(temp)
                    for name,text in source.items():(root/name).write_bytes(text.encode())
                    current=grade(value,stage,root)
                original=item.get('independent_grade',{})
                same=(current['state']=='graded' and current.get('groups')==original.get('groups')
                      and current['source_sha256']==original.get('source_sha256')
                      and current['oracle_sha256']==original.get('oracle_sha256'))
                matches=matches and same
                manifest['sources'].append({'slot':slot,'stage':stage,'file':filename,
                    'file_sha256':hashlib.sha256((out/filename).read_bytes()).hexdigest(),
                    'groups':current['groups'],'oracle_sha256':current['oracle_sha256'],'grade_matches':same})
            except (OSError,ValueError,KeyError,TypeError):
                matches=False
        from core.export import build as evidence
        from core.patchproof.identity import collect
        try:
            report=evidence(folder/'candidate',timeout=30)
            _write(out/f'{slot}-evidence.json',report)
            patch=collect(folder/'candidate','HEAD','HEAD',seconds=10)
            _write(out/f'{slot}-patchproof.json',{'state':'not_exported',
                'committed_checkout_eligible':patch['checkout']['eligible'],
                'issues':patch['issues']+patch['checkout']['issues'],
                'reason':'No committed final patch subject supplied; source grades and owned receipts are separate evidence.'})
        except (OSError,ValueError,KeyError,TypeError):
            _write(out/f'{slot}-evidence.json',{'state':'incomplete','issues':['Evidence export unavailable.']})
    summary.update(state='regraded' if summary['outcome_comparable'] and matches else 'incomplete',
                   source_grades_match=matches)
    _write(out/'manifest.json',manifest);_write(out/'summary.json',summary)
    return summary


def reproduce(archive):
    archive=Path(archive).resolve(strict=True);manifest=_read(archive/'manifest.json')
    result={'qualified':False,'stages':0,'issues':[],'grading_only':True,
            'historical_harness_matches':manifest.get('harness_sha256')==_harness(2)}
    try:
        if manifest.get('schema')!=2:raise ValueError('archive schema changed')
        slots=manifest.get('scheduled_slots',[])
        if (not slots or len(set(slots))!=len(slots) or len(slots)>4 or manifest.get('stage_count')!=4
                or any(s.rsplit('-',1)[0] not in NAMES or s.rsplit('-',1)[-1] not in ('ordinary','assisted') for s in slots)):
            raise ValueError('invalid scheduled source set')
        expected={(slot,stage) for slot in slots for stage in range(1,5)}
        actual=[(row['slot'],row['stage']) for row in manifest['sources']]
        if len(actual)!=len(expected) or set(actual)!=expected:raise ValueError('missing scheduled source')
        for row in manifest['sources']:
            path=_safe(archive,row['file'])
            if hashlib.sha256(path.read_bytes()).hexdigest()!=row['file_sha256']:raise ValueError('source changed')
            value=case(row['slot'].rsplit('-',1)[0]);source=_read(path)
            if manifest.get('public_case_sha256',{}).get(value['id'])!=_public_case_hash(value):raise ValueError('case changed')
            if set(source)!=set(value['production']):raise ValueError('source set changed')
            with tempfile.TemporaryDirectory(prefix='ep-workflow-reproduce-') as temp:
                root=Path(temp)
                for name,text in source.items():(root/name).write_bytes(text.encode())
                current=grade(value,row['stage'],root)
            if current['state']!='graded' or current['groups']!=row['groups'] or current['oracle_sha256']!=row['oracle_sha256']:
                raise ValueError('independent grade changed')
            result['stages']+=1
        result['qualified']=bool(result['stages'])
    except (OSError,ValueError,KeyError,TypeError):result['issues'].append('archive_or_grade_changed')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--reproduce',type=Path,required=True)
    result=reproduce(parser.parse_args().reproduce);print(json.dumps(result,indent=2))
    return 0 if result['qualified'] else 1


if __name__=='__main__':raise SystemExit(main())
