import json
import pytest


def test_archive_requires_sealed_files_and_complete_schedule(tmp_path):
    from eval.review_archive import inspect
    (tmp_path/'protocol.json').write_text(json.dumps({'schema_version':1,'cases':['one'],'schedule':[['one','ordinary'],['one','assisted']]}))
    with pytest.raises((ValueError,OSError)):
        inspect(tmp_path)


def test_archive_grade_comparison_ignores_timing_but_not_failures():
    from eval.review_archive import grade_identity
    a={'baseline':{'state':'passed','passed':3,'failed':0,'skipped':0,'error':0,'elapsed_ms':10},
       'faults':[{'id':'one','state':'detected','execution':{'state':'failed','passed':2,'failed':1,'skipped':0,'error':0,'elapsed_ms':20}}]}
    import copy
    b=copy.deepcopy(a);b['baseline']['elapsed_ms']=999
    assert grade_identity(a)==grade_identity(b)
    b['faults'][0]['state']='undetected'
    assert grade_identity(a)!=grade_identity(b)


def _archive(tmp_path):
    import hashlib
    from eval.review_archive import HARNESS_FILES
    protocol={'schema_version':1,'cases':['one'],'schedule':[['one','ordinary'],['one','assisted']],
              'model':'claude-sonnet-5','effort':'medium','seconds_per_review':480,'seconds_per_grade':120,
              'harness_files':{name:'0'*64 for name in HARNESS_FILES}}
    g={'baseline':{'state':'passed','exit_code':0,'passed':1,'failed':0,'skipped':0,'error':0,'elapsed_ms':1},'faults':[]}
    case={'case':{'id':'one','base':'0'*40,'source_paths':['logic.py']},'faults':[],'no_review':g}
    records=[{'case':'one','arm':arm,'requested_model':'claude-sonnet-5','effort':'medium',
              'launch_attempted':True,'state':'completed','scope':'preserved','seconds_cap':480,'elapsed_ms':1,'exit_code':0,
              'host_observation':{'completed':True,'usage':None,'models':['claude-sonnet-5'],'completion_language':False,'failure':'unavailable'},
              'additions':{},'grade':g} for arm in ('ordinary','assisted')]
    values={'protocol.json':protocol,'case-one.json':case,'reviews-one.json':records,'observations-one.json':{}}
    def write():
        for name,value in values.items():(tmp_path/name).write_text(json.dumps(value))
        hashes={name:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest() for name,v in values.items()}
        (tmp_path/'checksums.json').write_text(json.dumps({'format':'json-canonical-v1','files':hashes}))
    return values,write


def test_archive_validates_caps_grades_and_actual_model(tmp_path):
    from eval.review_archive import inspect
    values,write=_archive(tmp_path);write()
    assert inspect(tmp_path)['slots'][0]['condition_qualified'] is True
    values['reviews-one.json'][0]['host_observation']['models']=['claude-opus-5-5'];write()
    assert inspect(tmp_path)['slots'][0]['condition_qualified'] is False
    values['reviews-one.json'][0]['seconds_cap']=999;write()
    with pytest.raises(ValueError):inspect(tmp_path)
    values['reviews-one.json'][0]['seconds_cap']=480
    values['case-one.json']['no_review']={};write()
    with pytest.raises(ValueError):inspect(tmp_path)
