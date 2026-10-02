"""Frozen cases discriminate defects without instructing an agent to skip checks."""
from pathlib import Path

from eval import benefit, benefit_cases, challenge, proposals


def test_two_cases_grade_bug_gold_and_bad_replay(tmp_path):
    for case in ('atomic-repair', 'correct-control'):
        root = tmp_path / case
        benefit_cases.prepare(case, root)
        assert benefit_cases.contract(case, root)
        result = challenge.grade(root)
        assert result['passed'] == (7 if case == 'atomic-repair' else 16)
        (root / 'bank/engine.py').write_text(challenge.GOLD)
        assert challenge.grade(root)['passed'] == 16
        (root / 'bank/engine.py').write_text(challenge.GOLD.replace('history[e[\'id\']] != signature', 'False'))
        assert challenge.grade(root)['passed'] < 16
        (root / 'visible.py').write_text('print("ok")')
        assert not benefit_cases.contract(case, root)


def test_schedule_is_eight_complete_counterbalanced_calls():
    rows = benefit.schedule()
    assert len(rows) == 8 and len(set(rows)) == 8
    for case in ('atomic-repair', 'correct-control'):
        assert (case, 0, 'baseline') in rows and (case, 0, 'tool') in rows
        assert (case, 1, 'tool') in rows and (case, 1, 'baseline') in rows
        first = [x[2] for x in rows if x[0] == case and x[1] == 0]
        second = [x[2] for x in rows if x[0] == case and x[1] == 1]
        assert first == list(reversed(second))


def test_saved_snapshot_grades_independently_and_is_readonly(tmp_path):
    root = tmp_path / 'candidate'; benefit_cases.prepare('atomic-repair', root)
    snap = proposals.snapshot(root, benefit_cases.names('atomic-repair'))
    grade = benefit.grade_snapshot('atomic-repair', snap)
    assert grade['passed'] == 7
    assert (root / 'bank/engine.py').read_text() == challenge.BUGGY
    snap['fingerprint'] = '0' * 64
    assert benefit.grade_snapshot('atomic-repair', snap)['state'] == 'unavailable'


def test_equivalent_root_path_preserves_the_frozen_contract(tmp_path):
    root=tmp_path/'candidate';benefit_cases.prepare('atomic-repair',root)
    (root/'child').mkdir()
    assert benefit_cases.contract('atomic-repair',root/'child'/'..')


def test_windows_short_temp_path_grades_the_same_source(monkeypatch):
    import ctypes,os,tempfile,pytest
    if os.name!='nt':
        pytest.skip('Windows filesystem short paths')
    with tempfile.TemporaryDirectory(prefix='ep-completion-alias-') as directory:
        root=Path(directory)/'candidate long filesystem name'
        benefit_cases.prepare('atomic-repair',root)
        buffer=ctypes.create_unicode_buffer(32768)
        size=ctypes.windll.kernel32.GetShortPathNameW(str(root),buffer,len(buffer))
        if not size or Path(buffer.value)==root:
            pytest.skip('filesystem does not expose a short alias')
        alias=Path(buffer.value)
        assert alias.resolve()==root.resolve()
        monkeypatch.setattr(tempfile,'tempdir',str(alias))
        snap=proposals.snapshot(root,benefit_cases.names('atomic-repair'))
        assert snap['state']=='complete'
        assert benefit.grade_snapshot('atomic-repair',snap)['passed']==7


def test_summary_does_not_credit_callbacks_alone_or_missing_runs():
    value = benefit.summarize([])
    assert value['state'] == 'incomplete' and value['benefit_observed'] is False
    rows = [{'case': c, 'replicate': n, 'arm': arm, 'state': 'host_failed',
             'proposals': [], 'final_grade': None} for c, n, arm in benefit.schedule()]
    value = benefit.summarize(rows)
    assert value['state'] == 'inconclusive' and value['benefit_observed'] is False


def test_receipt_refresh_alone_does_not_claim_better_code():
    grade={'state':'graded','passed':16,'total':16,'regressions':0,'checks':{}}
    rows=[{'case':c,'replicate':n,'arm':arm,'state':'graded','final_grade':grade,
           'proposals':[{'decision':'allow','before_grade':grade,'after_grade':grade,
                         'verification_before':'missing','verification_after':'fresh_pass'}]}
          for c,n,arm in benefit.schedule()]
    value=benefit.summarize(rows)
    assert value['receipt_refresh_observed'] is True
    assert value['coding_improvement_observed'] is False
    assert 'Missing means no exact-command receipt' in ' '.join(value['limits'])


def test_malformed_recorded_budget_is_rejected_before_auth(tmp_path):
    import json,pytest
    root=tmp_path/'batch'; root.mkdir()
    protocol={'schedule':[list(x) for x in benefit.schedule()],
              'harness_fingerprint':benefit._harness(),'cases':[benefit_cases.identity(c) for c in benefit_cases.CASES],
              'runtime_fingerprint':benefit.fingerprint(),'seconds_per_run':99999}
    (root/'protocol.json').write_text(json.dumps(protocol))
    with pytest.raises(ValueError,match='protocol'):
        benefit.run_batch(root,'not-a-host',root)
