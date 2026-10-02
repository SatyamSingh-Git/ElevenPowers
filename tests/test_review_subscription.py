import json
from pathlib import Path
import pytest


def test_review_auth_failure_is_retained_and_cannot_be_retried(tmp_path,monkeypatch):
    from eval.review_pilot import review
    from eval import subscription
    import subprocess
    repo=tmp_path/'repo';repo.mkdir()
    (repo/'logic.py').write_text('def value(): return 1\n')
    for args in [('init','-q'),('add','.'),('-c','user.name=Review','-c','user.email=r@example.invalid','commit','-qm','base')]:
        subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True)
    base=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD']).decode().strip()
    case={'id':'one','repository':str(repo),'base':base,'patch':'','source_paths':['logic.py']}
    monkeypatch.setattr(subscription,'auth',lambda *args:False)
    result=review(case,'ordinary','',tmp_path/'slot','unused')
    assert result['state']=='authentication_unavailable'
    assert json.loads((tmp_path/'slot/result.json').read_text())['state']==result['state']
    with pytest.raises(ValueError,match='existing'):
        review(case,'ordinary','',tmp_path/'slot','unused')


def test_review_budget_and_arm_are_validated_before_preparation(tmp_path):
    from eval.review_pilot import review
    for arm,seconds in [('wrong',480),('ordinary',481),('ordinary',float('nan'))]:
        with pytest.raises(ValueError):
            review({},arm,'',tmp_path/'slot','unused',seconds=seconds)
    assert not (tmp_path/'slot').exists()
