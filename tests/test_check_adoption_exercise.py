"""Actual unrelated Python/Node batch commands; callbacks remain synthetic."""
import importlib.util
import shutil

import pytest


@pytest.mark.parametrize('language',['python','javascript'])
def test_no_model_adoption_exercise_retains_independent_batch_failure_and_recovery(tmp_path,language):
    if language=='javascript' and not shutil.which('node'):
        pytest.skip('Node unavailable')
    assert importlib.util.find_spec('eval.check_adoption') is not None, 'Portable batch adoption exercise is missing'
    from eval.check_adoption import case
    value=case(tmp_path/'exercise',language)
    assert value['qualified'] and value['model_calls']==0 and not value['installed_acceptance']
    assert value['outcomes']==[['passed','passed'],['failed','passed'],['passed','passed'],['incomplete','passed']]
    assert value['milestones']==[['CURRENT','CURRENT'],['STALE','CURRENT'],['FAILED','CURRENT'],['CURRENT','CURRENT']]
    assert value['counts_before_missing']==[3,3] and value['counts_after_missing']==[3,4]
    assert value['outer_shell_exit']==0 and value['owned_failure_survived_callbacks']
    assert value['new_task_guidance_emitted'] and value['advice_launched_nothing']
