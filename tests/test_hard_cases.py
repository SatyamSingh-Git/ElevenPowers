"""A grader must accept a real solution and reject plausible edge-case defects."""
import importlib.util

import pytest


def test_hard_case_suite_exists():
    assert importlib.util.find_spec('eval.hard_cases') is not None, 'hard comparison cases are missing'


@pytest.mark.parametrize('case', ['lease-queue', 'async-cache', 'build-planner', 'resumable-stream'])
def test_frozen_grader_discriminates_initial_gold_and_mutants(tmp_path, case):
    from eval import hard_cases as cases
    root = tmp_path / case
    cases.prepare(case, root)
    initial = cases.grade(case, root)
    assert initial['state'] == 'graded'
    assert 0 < initial['passed'] < initial['total']
    assert initial['total'] >= 16
    for name, source in cases.gold(case).items():
        (root / name).write_bytes(source.encode())
    result = cases.grade(case, root)
    assert result['state'] == 'graded' and result['passed'] == result['total'], result
    for mutation in cases.mutants(case):
        for name, source in {**cases.gold(case), **mutation}.items():
            (root / name).write_bytes(source.encode())
        result = cases.grade(case, root)
        assert result['state'] == 'graded' and result['passed'] < result['total']
    (root / 'visible.py').write_text('print("ok")')
    assert not cases.contract(case, root)


def test_added_source_cannot_evade_snapshot_grading(tmp_path):
    from eval import hard_cases as cases
    root = tmp_path / 'candidate'
    cases.prepare('lease-queue', root)
    (root / 'app/answer.py').write_text('answer=42')
    assert not cases.contract('lease-queue', root)


def test_reference_worker_setup_does_not_spend_competing_claim_barrier_budget():
    """An actual SQLite reference with slow setup still has correct claim behavior."""
    import threading
    import time
    from types import SimpleNamespace
    from eval.hard_fixtures import QUEUE
    from eval.hard_worker import lease_queue
    namespace = {}
    exec(QUEUE, namespace)
    queue = namespace['Queue']
    calls = 0
    lock = threading.Lock()
    def slow_setup(path):
        nonlocal calls
        with lock:
            calls += 1
            delayed = calls == 2
        if delayed:
            time.sleep(5.2)  # Longer than the worker's five-second barrier allowance.
        return queue(path)
    result = lease_queue(SimpleNamespace(Queue=slow_setup), {'concurrent': True})
    assert result == {'claimed': 32, 'unique': 32, 'tokens': [1], 'pending': 32}
