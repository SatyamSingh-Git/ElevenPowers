"""Selected-input qualification preserves source facts and legacy serialization."""
import json
import time

import pytest

from core.evidence import Evidence,Kind,Result,Freshness,source_snapshot,freshness_view
from tests.test_input_definitions import policy
from tests.test_patchproof_identity import git


@pytest.fixture
def receipt_project(tmp_path):
    from core.inputs.bindings import bind
    root=tmp_path/'project'; root.mkdir(); git(root,'init','-q')
    (root/'service.py').write_bytes(b'value=2\n')
    dependency=tmp_path/'dependency'; dependency.mkdir()
    target=dependency/'parser.py'; target.write_bytes(b'value=2\n')
    policy(root); bind(root,'deps',dependency)
    scan,digest=source_snapshot(root,fresh=True)
    item=Evidence(kind=Kind.SUITE,identity='suite',result=Result.PASS,command='python check.py',
                  counted=True,passed=1,observed=scan.files,tree=digest,scope='source',at=time.time())
    return root,target,item


def test_metadata_binds_actual_unchanged_reads_and_expires_on_drift(receipt_project):
    from core.inputs.receipts import attach,inspect
    from core.inputs.collection import capture
    root,target,item=receipt_project
    before=capture(root,time.monotonic()+10)
    attach([item],before,capture(root,time.monotonic()+10),'a'*64)
    assert inspect(item,root)['state']=='bound'
    assert item.freshness(root) is Freshness.FRESH
    target.write_bytes(b'value=9\n')
    assert item.source_freshness(root) is Freshness.FRESH
    assert inspect(item,root)['state']=='stale'
    assert item.freshness(root) is Freshness.STALE and item.result is Result.PASS


def test_old_record_cannot_invent_configured_provenance(receipt_project):
    from core.inputs.receipts import inspect
    root,_,item=receipt_project
    assert inspect(item,root)['state']=='incomplete'
    assert item.source_freshness(root) is Freshness.FRESH
    assert item.freshness(root) is Freshness.STALE
    assert 'external_inputs' not in item.to_dict()


def test_unconfigured_history_serialization_is_unchanged(tmp_path):
    from core.inputs.receipts import inspect
    item=Evidence(kind=Kind.SUITE,identity='suite',result=Result.PASS,observed=[],tree='')
    old=item.to_dict()
    assert inspect(item,tmp_path)['state']=='not_configured'
    assert item.freshness(tmp_path) is Freshness.FRESH
    assert item.to_dict()==old and 'external_inputs' not in old
    assert Evidence.from_dict(old).to_dict()==old


@pytest.mark.parametrize('bad',[None,[],{'schema':True},
    {'schema':1,'state':'bound','before':'a'*64,'after':'b'*64,'attempt':'c'*64,'issues':[]},
    {'schema':1,'state':'bound','before':'a'*64,'after':'a'*64,'attempt':'','issues':[]},
    {'schema':1,'state':[],'before':'a'*64,'after':'a'*64,'attempt':'c'*64,'issues':[]}])
def test_malformed_metadata_cannot_qualify(receipt_project,bad):
    from core.inputs.receipts import inspect
    root,_,item=receipt_project
    item.external_inputs=bad
    assert inspect(item,root)['state']=='incomplete'
    assert item.freshness(root) is Freshness.STALE


def test_incomplete_and_during_command_drift_do_not_rewrite_pass(receipt_project):
    from core.inputs.receipts import attach,inspect
    from core.inputs.collection import capture
    root,target,item=receipt_project
    before=capture(root,time.monotonic()+10)
    target.write_bytes(b'value=9\n')
    attach([item],before,capture(root,time.monotonic()+10),'a'*64)
    assert inspect(item,root)['state']=='stale' and item.result is Result.PASS
    target.unlink()
    assert inspect(item,root)['state']=='incomplete'


def test_freshness_view_shares_reads_across_receipts(receipt_project,monkeypatch):
    from core.inputs import definition
    from core.inputs.receipts import attach,inspect
    from core.inputs.collection import capture
    root,target,item=receipt_project
    before=capture(root,time.monotonic()+10); attach([item],before,before,'a'*64)
    original=definition.raw;reads=[]
    def counted(path,*a,**k):
        if path==target: reads.append(path)
        return original(path,*a,**k)
    monkeypatch.setattr(definition,'raw',counted)
    with freshness_view(root,deadline=time.monotonic()+30):
        for _ in range(100): assert inspect(item,root)['state']=='bound'
    assert len(reads)==2, 'one opening and one closing capture, not one per receipt'


def test_final_view_drift_is_an_explicit_coverage_gap(receipt_project):
    from core.inputs.receipts import attach
    from core.inputs.collection import capture
    root,target,item=receipt_project
    before=capture(root,time.monotonic()+10); attach([item],before,before,'a'*64)
    with freshness_view(root,deadline=time.monotonic()+30) as (scan,_):
        assert item.freshness(root) is Freshness.FRESH
        target.write_bytes(b'value=9\n')
    assert not scan.complete and any('external' in i for i in scan.issues)


def test_metadata_round_trips_milestone_history(receipt_project):
    from core.inputs.receipts import attach
    from core.inputs.collection import capture
    from core.milestones.history import record
    root,_,item=receipt_project
    before=capture(root,time.monotonic()+10);attach([item],before,before,'a'*64)
    assert record(item.to_dict()).external_inputs==item.external_inputs
    assert 'dependency' not in json.dumps(item.external_inputs), 'metadata contains no approved paths'


def test_project_move_during_view_is_controlled_and_resets_context(receipt_project):
    from core.evidence import _FRESHNESS_VIEW
    root,_,_=receipt_project
    destination=root.parent/'renamed-project'
    assert root.resolve().parent==destination.resolve().parent
    with freshness_view(root,deadline=time.monotonic()+30) as (scan,_):
        root.rename(destination)
    assert not scan.complete
    assert _FRESHNESS_VIEW.get() is None
