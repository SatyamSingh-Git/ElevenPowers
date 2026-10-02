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
