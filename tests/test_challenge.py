from eval import challenge


def test_frozen_challenge_has_independent_discriminating_grader(tmp_path):
    root = tmp_path / 'candidate'
    identity = challenge.prepare(root)
    assert identity == challenge.identity()
    before = challenge.grade(root)
    assert before['passed'] < before['total']
    (root / 'bank/engine.py').write_text(challenge.GOLD)
    result = challenge.grade(root)
    assert result['passed'] == result['total']
    (root / 'visible.py').write_text('print("ok")')
    assert not challenge.contract(root)


def test_wrong_atomicity_candidate_does_not_pass(tmp_path):
    root = tmp_path / 'candidate'; challenge.prepare(root)
    (root / 'bank/engine.py').write_text(challenge.GOLD.replace('balances.copy()', 'balances'))
    value = challenge.grade(root)
    assert value['passed'] < value['total']


def test_legitimate_package_import_is_graded(tmp_path):
    root = tmp_path / 'candidate'; challenge.prepare(root)
    (root / 'bank/engine.py').write_text('from bank.view import total\n' + challenge.GOLD)
    assert challenge.grade(root)['passed'] == 16


def test_candidate_cannot_impersonate_grading_controller(tmp_path):
    root = tmp_path / 'candidate'; challenge.prepare(root)
    payload = '''import json,sys
if __name__ == 'candidate_engine':
    print(json.dumps({'state':'graded','passed':16,'total':16,'regressions':0,'checks':{str(i):True for i in range(16)}}))
    sys.exit(0)
'''
    (root / 'bank/engine.py').write_text(payload + challenge.BUGGY)
    assert challenge.contract(root)
    assert challenge.grade(root)['passed'] < 16
