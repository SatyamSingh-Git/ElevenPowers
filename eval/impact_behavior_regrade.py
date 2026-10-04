"""Explicit reclassification of retained producer reports; no tests execute."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from core.export import write
from core.impact.build import safe_path
from eval.impact_behavior import classify, qualification


def bounded(path, limit=8*1024*1024):
    with path.open('rb') as stream:
        data=stream.read(limit+1)
    if len(data)>limit:
        raise ValueError('saved producer input exceeds limit')
    return data


def regrade(original, private):
    result=copy.deepcopy(original)
    private=Path(private).resolve()
    result['reclassification']={'version':'impact-behavior-regrade/1',
        'controller_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'classifier_sha256':hashlib.sha256(Path(__file__).with_name('impact_behavior.py').read_bytes()).hexdigest(),
        'policy':'Historical saved reports and seals; no new execution or fresh source attestation.'}
    for row in result['experiments']:
        row['original_runs']=copy.deepcopy(row['runs'])
        row['original_selected_fault']=copy.deepcopy(row.get('selected_fault',{}))

        def replay(saved):
            revised=dict(saved)
            if 'report' not in saved:
                revised['status']='incomplete'
                return revised
            try:
                directory=safe_path(private,row['id'])
                name=saved['report']
                if Path(name).name!=name:
                    raise ValueError('producer report must be a basename')
                data=bounded(safe_path(directory,name))
                output=bounded(safe_path(directory,Path(name).stem+'.txt'),16*1024*1024)
                normalized=output.decode('utf-8').replace('\r\n','\n').encode()
                if (hashlib.sha256(data).hexdigest()!=saved['report_sha256']
                        or hashlib.sha256(normalized).hexdigest()!=saved['output_sha256']):
                    raise ValueError('saved producer identity changed')
                revised.update(classify(saved['exit_code'],data,saved['producer']))
                if revised['status']!='incomplete':
                    revised.pop('issue',None)
            except (OSError,ValueError,KeyError) as exc:
                revised.update(status='incomplete',issue=str(exc))
            return revised

        row['runs']={label:replay(saved) for label,saved in row['runs'].items()}
        row['selected_fault']={label:replay(saved) for label,saved in row.get('selected_fault',{}).items()}
        source_seals=all(row.get('seals',{}).get(v,{}).get(s,{}).get('complete') is True
            for v in ('unchanged','equivalent','fault') for s in ('before','after'))
        row['qualified']=qualification(row['runs']) and source_seals
        row['detected']={name:row['qualified'] and run['status']=='assertion-fail'
            and run.get('after_seal',{}).get('complete') is True
            for name,run in row['selected_fault'].items()}
    result['attempted']=len(result['experiments'])
    result['qualified']=sum(row['qualified'] for row in result['experiments'])
    arms={arm for row in result['experiments'] for arm in row['selected_fault']}
    result['detected']={arm:sum(row['detected'].get(arm,False) for row in result['experiments']) for arm in sorted(arms)}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result',type=Path,required=True)
    parser.add_argument('--private',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        data=bounded(args.result)
        value=regrade(json.loads(data),args.private)
        value['reclassification']['original_result_sha256']=hashlib.sha256(data).hexdigest()
        write(args.output,json.dumps(value,indent=2)+'\n')
    except (OSError,ValueError,KeyError,TypeError,RecursionError) as exc:
        parser.exit(2,str(exc)+'\n')
    print(json.dumps({k:value[k] for k in ('attempted','qualified','detected')}))


if __name__=='__main__':
    main()
