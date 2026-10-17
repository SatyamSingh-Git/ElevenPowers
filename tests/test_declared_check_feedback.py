"""Native-shaped feedback over actual Python/Node outcomes; no model calls."""
import json
import os
from pathlib import Path
import shutil
import sys

import pytest

from core.config import Config, save
from core.evidence import Freshness, Kind, Result
from core.hook import dispatch
from core.ledger import Ledger
from core.parsers import parse
from core.process import run


def project(root, language, *, passing=True, profile='guide'):
    if language=='javascript' and not shutil.which('node'):pytest.skip('Node required')
    source=root/('value.py' if language=='python' else 'value.cjs')
    source.write_text('value = 1\n' if language=='python' else 'exports.value=1;\n',encoding='utf8')
    tests=root/'tests';tests.mkdir()
    test=tests/('test_value.py' if language=='python' else 'value.test.cjs')
    def write_test(expected):
        body=(f'import unittest\nfrom value import value\nclass TestValue(unittest.TestCase):\n def test_value(self): self.assertEqual(value,{expected})\n' if language=='python' else
              f"const test=require('node:test'),assert=require('node:assert/strict');test('value',()=>assert.equal(require('../value.cjs').value,{expected}));\n")
        test.write_text(body,encoding='utf8')
    write_test(1)
    command=(f'"{sys.executable}" -m pytest tests -q' if language=='python'
             else 'node --test --test-reporter=tap')
    save(root,Config(profile=profile,auto_detect=False,commands={'tests':command},strength={'enabled':False}))
    ledger=Ledger(root=root,task='feedback-task')
    environment={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    done=run(command,cwd=root,timeout=15,shell=True,env=environment);assert done.returncode==0
    ledger.add(parse(command,done.stdout+done.stderr,done.returncode,root));ledger.save()
    source.write_text('value = 2\n' if language=='python' else 'exports.value=2;\n',encoding='utf8')
    if passing:write_test(2)
    done=run(command,cwd=root,timeout=15,shell=True,env=environment)
    assert done.returncode==(0 if passing else 1)
    return command,done


def replay(root, command, output, *, code=0, tool='Bash', **result):
    payload={'cwd':str(root),'tool_name':tool,'tool_input':{'command':command},
             'tool_response':{'stdout':output,'exit_code':code,**result}}
    assert dispatch('PostToolUse',payload)==0


def exact(root):
    return [e for e in Ledger.load(root).evidence if e.kind is Kind.SUITE and e.declaration=='tests'][-1]


@pytest.mark.parametrize('language',['python','javascript'])
@pytest.mark.parametrize('passing',[False,True])
def test_filtered_actual_outcome_keeps_exact_stale_and_offers_owned_runner(tmp_path,capsys,language,passing):
    command,done=project(tmp_path,language,passing=passing)
    replay(tmp_path,command+' 2>&1 | tail -15',done.stdout+done.stderr)
    context=capsys.readouterr().out
    assert 'Generic verification recorded' in context and 'ep_check.py' in context
    assert 'Owned check arguments:' in context
    assert exact(tmp_path).freshness(tmp_path) is Freshness.STALE
    records=Ledger.load(tmp_path).evidence
    assert not any(e.owned_execution for e in records)
    assert any(e.declaration=='' and e.result is (Result.PASS if passing else Result.FAIL) for e in records)
    # Feedback must not execute; only an explicit owned call refreshes the declaration.
    from core.checks import execute
    value=execute(tmp_path,'tests',seconds=15)
    assert value['state']==('passed' if passing else 'failed')
    assert exact(tmp_path).owned_execution and exact(tmp_path).freshness(tmp_path) is Freshness.FRESH
    replay(tmp_path,command+' 2>&1 | tail -15',done.stdout+done.stderr)
    assert 'Generic verification recorded' not in capsys.readouterr().out


def test_duplicate_feedback_is_bounded_but_new_task_can_receive_it(tmp_path,capsys):
    command,done=project(tmp_path,'python')
    for index in range(3):
        replay(tmp_path,command+' | tail -15',done.stdout+done.stderr)
        assert ('Generic verification recorded' in capsys.readouterr().out)==(index==0)
    ledger=Ledger.load(tmp_path);ledger.task='another-task';ledger.save()
    replay(tmp_path,command+' | tail -15',done.stdout+done.stderr)
    assert 'Generic verification recorded' in capsys.readouterr().out


@pytest.mark.parametrize('passing',[False,True])
def test_completed_exact_native_outcome_needs_no_owned_reminder(tmp_path,capsys,passing):
    command,done=project(tmp_path,'python',passing=passing)
    replay(tmp_path,command,done.stdout+done.stderr,code=done.returncode)
    assert 'Generic verification recorded' not in capsys.readouterr().out
    assert exact(tmp_path).freshness(tmp_path) is Freshness.FRESH


@pytest.mark.parametrize('mode',['off','empty','owned','unrelated','interrupted'])
def test_quiet_boundaries_do_not_offer_or_execute_checks(tmp_path,capsys,mode):
    command,done=project(tmp_path,'python',profile='off' if mode=='off' else 'guide')
    if mode=='empty':save(tmp_path,Config(profile='guide',auto_detect=False))
    if mode=='owned':command='python ep_check.py --all'
    if mode=='unrelated':command='echo inspected'
    replay(tmp_path,command+' | tail -15',done.stdout+done.stderr,
           interrupted=mode=='interrupted')
    assert 'Generic verification recorded' not in capsys.readouterr().out
    assert not any(e.owned_execution for e in Ledger.load(tmp_path).evidence)


def test_concurrent_callbacks_reserve_only_one_reminder(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from core.hosts.transport import collect
    command,done=project(tmp_path,'python')
    def callback(_):
        with collect() as messages:
            replay(tmp_path,command+' | tail -15',done.stdout+done.stderr)
        return json.dumps(messages)
    with ThreadPoolExecutor(max_workers=2) as pool:outputs=list(pool.map(callback,range(2)))
    assert sum('Generic verification recorded' in output for output in outputs)==1


def test_failed_verification_keeps_failure_context_with_reminder(tmp_path,capsys):
    from core.obligations import Claim
    command,done=project(tmp_path,'python',passing=False)
    ledger=Ledger.load(tmp_path);ledger.claims=[Claim.FEATURE_ADDED];ledger.save()
    replay(tmp_path,command+' | tail -15',done.stdout+done.stderr)
    text=capsys.readouterr().out
    assert 'failing' in text and 'Generic verification recorded' in text
