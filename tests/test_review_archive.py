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
