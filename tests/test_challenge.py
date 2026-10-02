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


def test_worker_preserves_status_and_journal_python_types(tmp_path):
    root = tmp_path / 'candidate'; challenge.prepare(root)
    (root / 'bank/engine.py').write_text(challenge.GOLD.replace('return statuses', 'return tuple(statuses)'))
    assert challenge.grade(root)['passed'] < 16
    altered = challenge.GOLD.replace('history[e[\'id\']] = signature', 'history[e[\'id\']] = list(signature)')
    altered = altered.replace('history[e[\'id\']] != signature', 'tuple(history[e[\'id\']]) != signature')
    (root / 'bank/engine.py').write_text(altered)
    assert challenge.grade(root)['passed'] < 16


def test_behavior_transport_is_bounded_and_preserves_container_types():
    import pytest
    from eval.challenge_worker import encode
    assert encode({'b': ('x', 2), 'a': []}) == encode({'a': [], 'b': ('x', 2)})
    assert encode(['x', 2]) != encode(('x', 2))
    assert encode(True) != encode(1)
    recursive = []
    recursive.append(recursive)
    with pytest.raises(ValueError):
        encode(recursive)
    with pytest.raises(ValueError):
        encode([None] * 10001)
