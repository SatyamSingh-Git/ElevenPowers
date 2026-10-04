"""Real producer shapes and negative attribution/freshness controls."""
import hashlib
import json

import pytest

from core.impact import build, analyze
from core.impact.coverage import convert


def sample(root):
    (root/'api.py').write_text('def expire():\n    return 1\n',encoding='utf-8')
    (root/'test_api.py').write_text('def test_expire():\n    assert True\n',encoding='utf-8')
    graph=build(root)
    report={'meta':{'format':3,'version':'7.10.7','show_contexts':True},'files':{
        'api.py':{'executed_lines':[1,2],'contexts':{'1':['case'],'2':['case']}}}}
    data=json.dumps(report).encode()
    receipt={'schema':1,'producer':'coverage.py/7.10.7','run':'run-1','execution':'complete',
        'exit_code':0,'passed':1,'failed':0,'before':graph.fingerprint,'after':graph.fingerprint,
        'report_sha256':hashlib.sha256(data).hexdigest(),'contexts':{'case':'test_api.py'}}
    return graph,data,receipt


def test_current_context_edges_ingest_despite_static_semantic_gaps(tmp_path):
    (tmp_path/'broken.py').write_text('def missing(',encoding='utf-8')
    graph,data,receipt=sample(tmp_path)
    assert graph.issues
    value=convert(tmp_path,'python',data,receipt)
    assert value['complete'] and len(value['edges'])==1
    artifact=tmp_path/'.elevenpowers/observed.json'
    artifact.parent.mkdir()
    artifact.write_text(json.dumps(value),encoding='utf-8')
    current=build(tmp_path,observations=artifact)
    assert not current.quarantined
    assert not current.coverage['complete']
    report=analyze(current,['api.py'])
    assert any(n['path']=='test_api.py' and n['category']=='observed' for n in report['tests'])


@pytest.mark.parametrize('change',[
    lambda r:r.update(before='0'*64), lambda r:r.update(after='1'*64),
    lambda r:r.update(execution='incomplete'),lambda r:r.update(exit_code=1),
    lambda r:r.update(passed=0),lambda r:r.update(passed=True),
    lambda r:r.update(report_sha256='0'*64),lambda r:r.update(contexts={'case':'../outside.py'}),
    lambda r:r.update(contexts={'':'test_api.py'}),lambda r:r.update(schema=True),
])
def test_unqualified_receipt_yields_no_active_edges(tmp_path,change):
    graph,data,receipt=sample(tmp_path)
    change(receipt)
    value=convert(tmp_path,'python',data,receipt)
    assert not value['complete'] and not value['edges'] and value['issues']


def test_contextless_output_does_not_invent_attribution(tmp_path):
    graph,data,receipt=sample(tmp_path)
    report=json.loads(data)
    report['files']['api.py']['contexts']={'1':[''],'2':['']}
    data=json.dumps(report).encode()
    receipt['report_sha256']=hashlib.sha256(data).hexdigest()
    value=convert(tmp_path,'python',data,receipt)
    assert not value['complete'] and not value['edges']


def test_missing_executed_line_context_is_incomplete(tmp_path):
    graph,data,receipt=sample(tmp_path)
    report=json.loads(data)
    del report['files']['api.py']['contexts']['2']
    data=json.dumps(report).encode();receipt['report_sha256']=hashlib.sha256(data).hexdigest()
    value=convert(tmp_path,'python',data,receipt)
    assert not value['complete'] and not value['edges']


def test_invalid_declaration_still_quarantines_observations(tmp_path):
    (tmp_path/'impactgraph.json').write_text('{broken',encoding='utf-8')
    graph,data,receipt=sample(tmp_path)
    value=convert(tmp_path,'python',data,receipt)
    assert not value['complete'] and not value['edges']


def test_v8_native_ranges_and_source_maps_are_distinguished(tmp_path):
    (tmp_path/'api.cjs').write_text('exports.x=()=>1;\n',encoding='utf-8')
    (tmp_path/'test_api.cjs').write_text('require("./api.cjs");\n',encoding='utf-8')
    graph=build(tmp_path)
    report={'result':[{'url':(tmp_path/'api.cjs').as_uri(),'functions':[
        {'functionName':'','ranges':[{'startOffset':0,'endOffset':16,'count':1}],'isBlockCoverage':True}]}]}
    data=json.dumps(report).encode()
    receipt={'schema':1,'producer':'node-v8/22.17.1','run':'node-1','execution':'complete',
        'exit_code':0,'passed':1,'failed':0,'before':graph.fingerprint,'after':graph.fingerprint,
        'report_sha256':hashlib.sha256(data).hexdigest(),'test':'test_api.cjs'}
    value=convert(tmp_path,'v8',data,receipt)
    assert value['complete'] and value['edges'][0]['target']=='file:api.cjs'
    report['source-map-cache']={report['result'][0]['url']:{'data':{}}}
    data=json.dumps(report).encode();receipt['report_sha256']=hashlib.sha256(data).hexdigest()
    value=convert(tmp_path,'v8',data,receipt)
    assert not value['complete'] and not value['edges']
    assert 'source map' in ' '.join(value['issues'])


def test_capture_input_size_and_json_failure_are_explicit(tmp_path):
    graph,data,receipt=sample(tmp_path)
    assert not convert(tmp_path,'python',b'{broken',receipt)['complete']
    assert not convert(tmp_path,'python',b' '* (8*1024*1024+1),receipt)['complete']


def test_lines_outside_current_source_are_not_execution_evidence(tmp_path):
    graph,data,receipt=sample(tmp_path)
    report=json.loads(data)
    report['files']['api.py']['executed_lines']=[99999]
    report['files']['api.py']['contexts']={'99999':['case']}
    data=json.dumps(report).encode();receipt['report_sha256']=hashlib.sha256(data).hexdigest()
    value=convert(tmp_path,'python',data,receipt)
    assert not value['complete'] and not value['edges']


def test_coverage_cli_refuses_overwrite_and_records_actual_producer(tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    graph,data,receipt=sample(tmp_path)
    report=tmp_path.parent/(tmp_path.name+'-report.json');report.write_bytes(data)
    journal=tmp_path.parent/(tmp_path.name+'-receipt.json');journal.write_text(json.dumps(receipt),encoding='utf-8')
    output=tmp_path/'.elevenpowers/observed.json'
    cli=Path(__file__).parents[1]/'plugin/bin/ep_impact_capture.py'
    command=[sys.executable,str(cli),'--project',str(tmp_path),'--kind','python',
        '--report',str(report),'--receipt',str(journal),'--output',str(output)]
    result=subprocess.run(command,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert json.loads(output.read_bytes())['receipt']['producer']=='coverage.py/7.10.7'
    saved=output.read_bytes()
    assert subprocess.run(command,capture_output=True).returncode==2
    assert output.read_bytes()==saved


@pytest.mark.parametrize('kind',['python','v8'])
def test_actual_producer_round_trip(tmp_path,kind):
    import os
    from pathlib import Path
    import shutil
    import sys
    from core.process import run
    root=tmp_path/'project';root.mkdir()
    reports=tmp_path/'reports';reports.mkdir()
    if kind=='python':
        pytest.importorskip('coverage')
        (root/'api.py').write_text('def expire():\n    return 1\n',encoding='utf-8')
        (root/'test_api.py').write_text('from api import expire\ndef test_expire():\n    assert expire()==1\n',encoding='utf-8')
        command=[sys.executable,'-m','coverage','run','--context','case','-m','pytest','test_api.py','-q']
        env={**os.environ,'COVERAGE_FILE':str(reports/'.coverage'),'PYTHONDONTWRITEBYTECODE':'1'}
        producer='coverage.py/7.10.7'
        extras={'contexts':{'case':'test_api.py'}}
    else:
        node=shutil.which('node')
        if not node:pytest.skip('Node not installed')
        version=run([node,'--version'],cwd=root,shell=False,timeout=10).stdout.strip().lstrip('v')
        if not version.startswith('22.'):pytest.skip('Node 22 producer acceptance')
        (root/'api.cjs').write_text('exports.expire=()=>1;\n',encoding='utf-8')
        (root/'test_api.cjs').write_text('const t=require("node:test"),a=require("node:assert/strict"),api=require("./api.cjs");t("expire",()=>a.equal(api.expire(),1));\n',encoding='utf-8')
        command=[node,'--test','test_api.cjs']
        env={**os.environ,'NODE_V8_COVERAGE':str(reports)}
        producer='node-v8/'+version
        extras={'test':'test_api.cjs'}
    before=build(root).fingerprint
    done=run(command,cwd=root,shell=False,env=env,timeout=30)
    assert done.returncode==0,done.stderr
    if kind=='python':
        output=reports/'coverage.json'
        result=run([sys.executable,'-m','coverage','json','--show-contexts','-o',str(output)],cwd=root,shell=False,env=env,timeout=15)
        assert result.returncode==0,result.stderr
    else:
        output=next(reports.glob('coverage-*.json'))
    data=output.read_bytes()
    receipt={'schema':1,'producer':producer,'run':'actual-run','execution':'complete','exit_code':done.returncode,
        'passed':1,'failed':0,'before':before,'after':build(root).fingerprint,
        'report_sha256':hashlib.sha256(data).hexdigest(),**extras}
    converted=convert(root,kind,data,receipt)
    assert converted['complete'],converted['issues']
    assert any(e['target']=='file:api.'+('py' if kind=='python' else 'cjs') for e in converted['edges'])
