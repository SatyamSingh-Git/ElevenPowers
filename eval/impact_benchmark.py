"""Explicit frozen impact evaluation; known references are controller-owned."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from core.export import write
from core.impact.build import safe_path
from core.process import run

HEX = re.compile(r'^[0-9a-f]+$')
SKIP = {'.git','node_modules','__pycache__','.pytest_cache','.elevenpowers'}


def _relative(value):
    if (not isinstance(value,str) or not value or len(value)>500 or '\\' in value
            or ':' in value or value.startswith('/') or '..' in Path(value).parts
            or Path(value).as_posix()!=value or '.git' in Path(value).parts):
        raise ValueError('unsafe corpus path')
    return value


def _query(value):
    if isinstance(value, str) and value.startswith('symbol:'):
        path, separator, symbol = value[7:].partition('#')
        _relative(path)
        if not separator or not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', symbol):
            raise ValueError('invalid symbol query')
        return value
    return _relative(value)


def load_cases(path):
    with Path(path).open('rb') as stream:
        data=stream.read(4*1024*1024+1)
    if len(data)>4*1024*1024:
        raise ValueError('corpus exceeds 4 MiB')
    try:
        value=json.loads(data)
    except (ValueError,RecursionError) as exc:
        raise ValueError('invalid corpus JSON') from exc
    if not isinstance(value,dict) or type(value.get('schema')) is not int or value['schema']!=1:
        raise ValueError('unsupported corpus schema')
    projects=value.get('projects')
    cases=value.get('cases')
    if not isinstance(projects,list) or not 1<=len(projects)<=20 or not isinstance(cases,list) or not 1<=len(cases)<=500:
        raise ValueError('invalid corpus lists')
    names=set()
    for project in projects:
        if not isinstance(project,dict) or not isinstance(project.get('id'),str) or project['id'] in names:
            raise ValueError('duplicate/invalid project')
        names.add(project['id'])
        pin=project.get('commit','')
        if not isinstance(pin,str) or len(pin)!=40 or not HEX.fullmatch(pin):
            raise ValueError('invalid project pin')
        hashes=project.get('files')
        if not isinstance(hashes,dict) or not 1<=len(hashes)<=20000:
            raise ValueError('invalid project seal')
        for name,digest in hashes.items():
            _relative(name)
            if not isinstance(digest,str) or len(digest)!=64 or not HEX.fullmatch(digest):
                raise ValueError('invalid input hash')
    ids=set()
    for case in cases:
        if (not isinstance(case,dict) or not isinstance(case.get('project'),str)
                or case['project'] not in names or case.get('split') not in ('development','held-out')):
            raise ValueError('invalid case project/split')
        identity=case.get('id')
        if not isinstance(identity,str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,100}',identity) or identity in ids:
            raise ValueError('duplicate/invalid case')
        ids.add(identity)
        _query(case.get('query'))
        for field in ('consumers','tests','unrelated'):
            rows=case.get(field)
            if (not isinstance(rows,list) or len(rows)>1000 or any(not isinstance(x,str) for x in rows)
                    or len(set(rows))!=len(rows)):
                raise ValueError('invalid reference set')
            for name in rows:
                _relative(name)
        if (set(case['consumers'])|set(case['tests'])) & set(case['unrelated']):
            raise ValueError('contradictory positive/negative reference')
    return value


def seal(root, hashes):
    root=Path(root).absolute()
    issues=[]
    if any(p.is_symlink() for p in (root,*root.parents)):
        return {'complete':False,'issues':['linked root']}
    if (root/'.elevenpowers/config.json').exists() and '.elevenpowers/config.json' not in hashes:
        issues.append('unfrozen scan policy: .elevenpowers/config.json')
    for name,digest in hashes.items():
        try:
            path=safe_path(root.resolve(),name)
            with path.open('rb') as stream:
                data=stream.read(64*1024*1024+1)
            if len(data)>64*1024*1024 or hashlib.sha256(data).hexdigest()!=digest:
                issues.append('changed/oversized input: '+name)
        except (OSError,ValueError):
            issues.append('missing/unsafe input: '+name)
    count=0
    for directory,folders,files in os.walk(root,followlinks=False):
        folders[:]=[f for f in folders if f not in SKIP]
        for filename in files:
            if filename.endswith('.pyc') or filename=='.coverage':
                continue
            count+=1
            if count>20000:
                issues.append('source inventory limit exceeded')
                break
            relative=(Path(directory)/filename).relative_to(root).as_posix()
            if relative not in hashes:
                issues.append('unfrozen input: '+relative)
        if count>20000:
            break
    return {'complete':not issues,'issues':issues}


def grade(case, report):
    affected={n['path'] for n in report['affected'] if n['path']}
    tests={n['path'] for n in report['tests'] if n['path']}
    predicted=affected|tests
    consumers=set(case['consumers'])
    expected_tests=set(case['tests'])
    known=consumers|expected_tests|set(case['unrelated'])
    selection = None
    if isinstance(report.get('test_selection'), dict):
        selection = {'safe_to_exclude_fallback': report['test_selection']['safe_to_exclude_fallback']}
        for group in ('focused', 'fallback', 'support'):
            paths = {n['path'] for n in report['test_selection'][group] if n['path']}
            selection[group] = {'candidate_files': sorted(paths),
                'known_test_hits': sorted(paths & expected_tests),
                'negative_hits': sorted(paths & set(case['unrelated'])),
                'unlabelled': sorted(paths - known)}
    return {'consumer_recall':len(consumers&affected)/len(consumers) if consumers else None,
            'test_recall':len(expected_tests&tests)/len(expected_tests) if expected_tests else None,
            'missed_consumers':sorted(consumers-affected),'missed_tests':sorted(expected_tests-tests),
            'negative_hits':sorted(set(case['unrelated'])&predicted),
            'unlabelled':sorted(predicted-known),'candidate_test_files':sorted(tests),
            'test_selection':selection}


WORKER = '''import json,sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from core.impact import build,analyze
started=time.monotonic()
options=json.loads(sys.argv[4])
graph=build(Path(sys.argv[2]),**options)
built=time.monotonic()-started
queries=json.loads(sys.argv[3])
reports={identity:analyze(graph,[query],max_results=1000,max_depth=20) for identity,query in queries}
print(json.dumps(dict(build_seconds=built,source_fingerprint=graph.fingerprint,nodes=len(graph.nodes),
edges=len(graph.edges),coverage=graph.to_dict()['coverage'],reports=reports)))
'''


def evaluate(manifest, roots, *, split, runtime_root, output=None, typescript=None):
    if split not in ('development','held-out','all'):
        raise ValueError('invalid requested split')
    runtime_root=Path(runtime_root).resolve()
    runtime_files={p.relative_to(runtime_root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted((runtime_root/'core').rglob('*')) if p.suffix in ('.py','.cjs')}
    if not runtime_files:
        raise ValueError('runtime root has no impact implementation')
    corpus_hash=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    result={'schema':1,'corpus_hash':corpus_hash,'split':split,'runtime_files':runtime_files,'projects':[]}
    options={}
    if typescript is not None:
        engine=Path(typescript).resolve(strict=True)
        options['typescript']=str(engine)
        result['compiler']={'sha256':hashlib.sha256(engine.read_bytes()).hexdigest(),
                            'qualified_version':'5.7.3','trust':'explicit compiler path'}
    for project in manifest['projects']:
        cases=[c for c in manifest['cases'] if c['project']==project['id'] and (split=='all' or c['split']==split)]
        if not cases:
            continue
        row={'project':project['id'],'commit':project['commit'],'cases':[
            {'id':c['id'],'query':c['query'],'split':c['split'],'status':'incomplete'} for c in cases],
            'complete':False}
        result['projects'].append(row)
        if project['id'] not in roots:
            row['issue']='project root not supplied'
            continue
        root=Path(roots[project['id']]).resolve()
        before=seal(root,project['files'])
        row['input_seal']=before
        if not before['complete']:
            row['issue']='frozen source seal failed'
            continue
        queries=[(c['id'],c['query']) for c in cases]
        started=time.monotonic()
        try:
            done=run([sys.executable,'-c',WORKER,str(runtime_root),str(root),json.dumps(queries),json.dumps(options)],
                     cwd=root,timeout=60,shell=False,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
            row['worker_exit']=done.returncode
            if done.returncode:
                raise ValueError('graph worker failed: '+done.stderr[-2000:])
            worker=json.loads(done.stdout)
            for item,case in zip(row['cases'],cases):
                report=worker['reports'][case['id']]
                item.update(status='observed',**grade(case,report),coverage=report['coverage'])
            row.update({k:worker[k] for k in ('build_seconds','source_fingerprint','nodes','edges','coverage')})
            row['after_seal']=seal(root,project['files'])
            row['complete']=row['after_seal']['complete']
        except (ValueError,OSError,subprocess.SubprocessError) as exc:
            row['issue']=str(exc)
        row['elapsed_seconds']=time.monotonic()-started
    result['complete']=all(p['complete'] for p in result['projects']) and bool(result['projects'])
    if output is not None:
        write(Path(output),json.dumps(result,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',type=Path,default=Path(__file__).with_name('impact_cases.json'))
    parser.add_argument('--roots',type=Path,required=True,help='explicit project ID to disposable root JSON')
    parser.add_argument('--runtime-root',type=Path,required=True)
    parser.add_argument('--split',choices=('development','held-out','all'),default='development')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--typescript',type=Path,help='explicit trusted compiler, only for a supporting runtime')
    args=parser.parse_args()
    try:
        value=evaluate(load_cases(args.cases),json.loads(args.roots.read_text()),split=args.split,
                       runtime_root=args.runtime_root,output=args.output,typescript=args.typescript)
    except (ValueError,OSError) as exc:
        parser.exit(2,str(exc)+'\n')
    print(json.dumps({'complete':value['complete'],'projects':[{'id':p['project'],
                     'cases':len(p['cases']),'issue':p.get('issue')} for p in value['projects']]}))
    return 0 if value['complete'] else 1


if __name__=='__main__':
    raise SystemExit(main())
