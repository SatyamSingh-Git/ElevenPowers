"""Full deterministic protocol exercises cannot masquerade as model comparisons."""
import importlib.util
import shutil
import pytest


def test_all_four_stage_rehearsals_reproduce_without_model_calls(tmp_path,monkeypatch):
    if not shutil.which('node'):pytest.skip('Node unavailable')
    assert importlib.util.find_spec('eval.workflow_rehearsal'),'integrated no-model rehearsal missing'
    from eval import subscription,workflow_rehearsal
    monkeypatch.setattr(subscription,'auth',lambda *a:pytest.fail('live authentication from rehearsal'))
    result=workflow_rehearsal.rehearse(tmp_path/'new')
    assert result['qualified'] and result['model_calls']==0
    assert not result['installed_acceptance'] and not result['benefit_comparison']
    assert result['scheduled_slots']==4
    assert all(row['stage_passes']==[4,6,8,10] for row in result['observations'])
    assert result['reproduction']['qualified'] and result['reproduction']['stages']==16
