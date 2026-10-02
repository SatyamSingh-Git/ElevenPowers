"""The new frozen suite must not alter original protocols or credit mere receipts."""
import json

import pytest

from eval import benefit, hard_cases, proposals, subscription


def test_explicit_hard_protocol_freezes_sonnet_five_and_eight_calls(tmp_path):
    root=tmp_path/'batch'
    protocol=benefit.prepare_batch(root,seconds=480,suite=hard_cases,repeats=1,model='claude-sonnet-5')
    assert protocol['model']=='claude-sonnet-5' and protocol['effort']=='medium'
    assert protocol['suite']==hard_cases.SUITE and len(protocol['schedule'])==8
    assert len({row[0] for row in protocol['schedule']})==4
    assert protocol['schedule'][0][2]=='baseline' and protocol['schedule'][2][2]=='tool'
    for case,n,arm in protocol['schedule']:
        candidate=root/f'{case}-{n}-{arm}'
        assert benefit._seal(root,candidate,suite=hard_cases)==protocol['candidate_seals'][candidate.name]
    args=subscription.command('claude','claude',root,'task',model=protocol['model'])
    assert args[args.index('--model')+1]=='claude-sonnet-5'


def test_hard_snapshot_rejects_modified_seed_and_accepts_added_regression(tmp_path):
    root=tmp_path/'candidate';hard_cases.prepare('build-planner',root)
    (root/'tests/test_regression.py').write_text('import unittest\n')
    snapshot=proposals.snapshot(root,hard_cases.names('build-planner'))
    assert benefit.grade_snapshot('build-planner',snapshot,suite=hard_cases)['state']=='graded'
    (root/'tests/test_seed.py').write_text('')
    snapshot=proposals.snapshot(root,hard_cases.names('build-planner'))
    assert benefit.grade_snapshot('build-planner',snapshot,suite=hard_cases)['state']=='unavailable'


def test_hard_partial_or_duplicate_batches_cannot_claim_benefit():
    records=[]
    for c,n,arm in benefit.schedule(suite=hard_cases,repeats=1):
        records.append({'case':c,'replicate':n,'arm':arm,'state':'graded','proposals':[],
                        'final_grade':{'state':'graded','passed':2,'total':10},'elapsed_ms':10})
    assert benefit.summarize(records,suite=hard_cases,repeats=1)['state']=='qualified'
    for values in (records[:-1],records+[records[0]]):
        summary=benefit.summarize(values,suite=hard_cases,repeats=1)
        assert summary['state']=='incomplete' and not summary['benefit_observed']


def test_unsupported_model_cannot_launch_a_subscription_command(tmp_path):
    with pytest.raises(ValueError):subscription.command('claude','claude',tmp_path,'task',model='different-model')
