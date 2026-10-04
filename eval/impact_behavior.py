"""Explicit independent fault/control execution in disposable frozen inputs.

Uses actual pytest JUnit and Jest JSON, not ImpactGraph's own quality judgment.
Commands execute project tests only when this evaluator is explicitly invoked.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from xml.etree import ElementTree as ET

from core.export import write
from core.impact.build import safe_path
from core.process import run
from eval.impact_benchmark import load_cases, seal


def classify(exit_code, data, kind):
    result={'status':'incomplete','passed':0,'failed':0,'skipped':0,'failures':[]}
    try:
        if len(data)>8*1024*1024 or type(exit_code) is not int or exit_code not in (0,1):
            raise ValueError('missing/oversized/non-test execution')
        errors=0
        if kind=='pytest':
            if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
                raise ValueError('XML entities are unsupported')
            xml=ET.fromstring(data)
            if xml.tag not in ('testsuites','testsuite'):
                raise ValueError('not JUnit')
            for case in xml.iter('testcase'):
                identity=case.get('classname','')+'::'+case.get('name','')
                failure=case.find('failure')
                if case.find('error') is not None:
                    errors+=1
                elif failure is not None:
                    message=' '.join([failure.get('message',''),failure.text or ''])
                    if 'AssertionError' not in message and 'DID NOT RAISE' not in message:
                        errors+=1
                    result['failed']+=1;result['failures'].append(identity)
                elif case.find('skipped') is not None:
                    result['skipped']+=1
                else:
                    result['passed']+=1
            for suite in xml.iter('testsuite'):
                cases=list(suite.iter('testcase'))
                counts={'tests':len(cases),'errors':sum(c.find('error') is not None for c in cases),
                    'failures':sum(c.find('failure') is not None for c in cases),
                    'skipped':sum(c.find('skipped') is not None for c in cases)}
                for key,count in counts.items():
                    if key in suite.attrib and int(suite.attrib[key])!=count:
                        raise ValueError('JUnit declared counts do not match cases')
        elif kind=='jest':
            value=json.loads(data)
            if not isinstance(value,dict) or not isinstance(value.get('testResults'),list):
                raise ValueError('not Jest JSON')
            for suite in value['testResults']:
                cases=suite.get('assertionResults')
                if not isinstance(cases,list) or not cases:
                    errors+=1;continue
                for case in cases:
                    status=case.get('status')
                    if status=='passed':result['passed']+=1
                    elif status in ('pending','todo','skipped'):result['skipped']+=1
                    elif status=='failed':
                        result['failed']+=1;result['failures'].append(case.get('fullName',''))
                        messages=case.get('failureMessages',[])
                        if not isinstance(messages,list) or not any(isinstance(m,str) and 'expect(' in m for m in messages):
                            errors+=1
                    else:errors+=1
            for field,key in [('numPassedTests','passed'),('numFailedTests','failed'),('numPendingTests','skipped')]:
                if type(value.get(field)) is not int or value[field]!=result[key]:
                    raise ValueError('Jest declared counts do not match assertions')
        else:raise ValueError('unknown producer')
        if errors or not result['passed']+result['failed']:
            raise ValueError('setup/error/empty execution is not an assertion result')
        if exit_code==0 and not result['failed']:result['status']='pass'
        elif exit_code==1 and result['failed']:result['status']='assertion-fail'
        else:raise ValueError('exit and machine outcome disagree')
    except (ValueError,TypeError,KeyError,AttributeError,RecursionError,ET.ParseError) as exc:
        result['issue']=str(exc)
    return result


def qualification(runs):
    return (runs.get('unchanged',{}).get('status')=='pass'
            and runs.get('equivalent',{}).get('status')=='pass'
            and runs.get('fault',{}).get('status')=='assertion-fail')


def execute(root, tests, kind, tools, directory, label, env):
    if not tests:return {'status':'incomplete','issue':'no tests selected'}
    report=directory/(label+('.xml' if kind=='pytest' else '.json'))
    if kind=='pytest':
        command=[sys.executable,'-m','pytest',*tests,'-q','--junitxml='+str(report)]
    else:
        config=directory/'jest-config.json'
        if not config.exists():
            config.write_text(json.dumps({'rootDir':str(root),'testRegex':'src/.*\\.test\\.ts$',
                'testPathIgnorePatterns':['language-server','__vitest__'],'transform':{'^.+\\.tsx?$':[
                str(tools/'node_modules/ts-jest'),{'tsconfig':{'target':'es2019','module':'commonjs','esModuleInterop':True},'diagnostics':False}]}}),encoding='utf-8')
        command=['node',str(tools/'node_modules/jest/bin/jest.js'),'--config',str(config),
            '--runInBand','--runTestsByPath',*tests,'--json','--outputFile='+str(report)]
    started=time.monotonic()
    try:
        done=run(command,cwd=root,shell=False,env=env,timeout=120)
        output=done.stdout+done.stderr
        (directory/(label+'.txt')).write_text(output,encoding='utf-8')
        data=report.read_bytes() if report.exists() else b''
        result=classify(done.returncode,data,kind)
        result.update(exit_code=done.returncode,report_sha256=hashlib.sha256(data).hexdigest(),
                      output_sha256=hashlib.sha256(output.encode()).hexdigest())
    except (OSError,subprocess.SubprocessError) as exc:
        result={'status':'incomplete','issue':str(exc)}
    result.update(tests=tests,seconds=time.monotonic()-started,producer=kind,
                  report=report.name)
    return result


def experiment(definition, corpus, roots, predictions, tools, private):
    project=next(p for p in corpus['projects'] if p['id']==definition['project'])
    source=Path(roots[project['id']]).resolve()
    row={'id':definition['id'],'project':project['id'],'query':definition['query'],
         'qualified':False,'runs':{},'seals':{},'definition':definition}
    if not seal(source,project['files'])['complete']:
        row['issue']='frozen source changed';return row
    directory=private/definition['id'];directory.mkdir(parents=True,exist_ok=False)
    root=directory/'source';root.mkdir()
    for relative in project['files']:
        origin=safe_path(source,relative)
        target=root/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(origin,target)
    # Reject path escapes before any private mutation or explicit test execution.
    path=safe_path(root,definition['query'])
    original=path.read_bytes()
    before=definition['before'].encode();after=definition['after'].encode()
    if original.count(before)!=1:
        row['issue']='fault anchor is not unique';return row
    selected={}
    for name, prediction in predictions.items():
        matches=[c for p in prediction['projects'] for c in p['cases'] if c['id']==definition['case']]
        if len(matches)!=1 or matches[0].get('status')!='observed':
            row['issue']='prediction missing/incomplete';return row
        candidates=matches[0]['candidate_test_files']
        selected[name]=sorted(set(candidates)&set(definition['full_tests']))
        row.setdefault('selection',{})[name]={'candidates':candidates,'executed_relevant':selected[name],
            'outside_relevant':sorted(set(candidates)-set(definition['full_tests']))}
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(root/(definition.get('pythonpath','')))}
    for variant in ('unchanged','equivalent','fault'):
        marker=b'\n# equivalent comment control\n' if definition['kind']=='pytest' else b'\n// equivalent comment control\n'
        changed=original if variant=='unchanged' else original+marker if variant=='equivalent' else original.replace(before,after)
        path.write_bytes(changed)
        hashes={**project['files'],definition['query']:hashlib.sha256(changed).hexdigest()}
        row['seals'][variant]={'before':seal(root,hashes)}
        result=execute(root,definition['full_tests'],definition['kind'],tools,directory,variant,env)
        row['runs'][variant]=result
        row['seals'][variant]['after']=seal(root,hashes)
        if variant=='fault':
            for name, tests in selected.items():
                row.setdefault('selected_fault',{})[name]=execute(root,tests,definition['kind'],tools,directory,'selected-'+name,env)
                selected_seal=seal(root,hashes)
                row['selected_fault'][name]['after_seal']=selected_seal
                if not selected_seal['complete']:
                    row['selected_fault'][name]['status']='incomplete'
        if not all(s['complete'] for s in row['seals'][variant].values()):
            result['status']='incomplete';result['issue']='source seal changed during execution'
    row['qualified']=qualification(row['runs'])
    row['detected']={name:row['qualified'] and r['status']=='assertion-fail' for name,r in row.get('selected_fault',{}).items()}
    return row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--roots',type=Path,required=True)
    parser.add_argument('--definitions',type=Path,required=True)
    parser.add_argument('--old',type=Path,required=True)
    parser.add_argument('--final',type=Path,required=True)
    parser.add_argument('--tools',type=Path,required=True)
    parser.add_argument('--private',type=Path,required=True,help='new disposable directory; raw outcomes retained here')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    corpus=load_cases(Path(__file__).with_name('impact_cases.json'))
    definitions=json.loads(args.definitions.read_bytes())
    roots=json.loads(args.roots.read_bytes())
    predictions={name:json.loads(path.read_bytes()) for name,path in [('old',args.old),('final',args.final)]}
    private=args.private.resolve();private.mkdir(parents=True,exist_ok=False)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(experiment,d,corpus,roots,predictions,args.tools.resolve(),private) for d in definitions]
        rows=[f.result() for f in futures]
    qualified=[r for r in rows if r['qualified']]
    result={'schema':1,'definitions_sha256':hashlib.sha256(args.definitions.read_bytes()).hexdigest(),
        'predictions_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in [('old',args.old),('final',args.final)]},
        'attempted':len(rows),'qualified':len(qualified),'detected':{k:sum(r['detected'].get(k,False) for r in qualified) for k in predictions},
        'experiments':rows,'limits':['Authored faults, not agent patches or population quality evidence.',
            'Selected commands intersect graph candidates with the named full relevant suite.',
            'Raw producer outputs retained privately; hashes and all classifications published.',
            'Equivalent controls are comments, not broad semantic equivalence proofs.']}
    write(args.output,json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('attempted','qualified','detected')}))


if __name__=='__main__':
    main()
