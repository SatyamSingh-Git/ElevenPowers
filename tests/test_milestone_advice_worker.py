import json
from concurrent.futures import ThreadPoolExecutor

from core.ledger import Ledger
from test_milestone_entrypoints import process_project


def opted(root, task='task'):
    process_project(root)
    state = root / '.elevenpowers'
    state.mkdir(exist_ok=True)
    (state / 'config.json').write_text(json.dumps({'profile': 'guide',
        'milestone_advice': {'enabled': True, 'seconds': 2, 'cooldown': 0, 'max_attempts': 2}}))
    ledger = Ledger(root=root, task=task, touched=['cli.py'])
    ledger.save()
    return ledger


def test_real_worker_is_read_only_and_deduplicated(tmp_path):
    from core.milestones.automatic import deliver
    ledger = opted(tmp_path)
    before = ledger.path.read_bytes()
    first = deliver(ledger)
    assert 'milestone advice' in first and 'fallback' in first
    assert deliver(ledger) == ''
    assert ledger.path.read_bytes() == before
    state = json.loads((tmp_path / '.elevenpowers/advice.json').read_text())
    assert state['tasks'][0]['attempts'][0]['status'] == 'delivered'
    assert 'command' not in json.dumps(state) and 'prompt' not in json.dumps(state)


def test_changed_inputs_and_new_task_get_bounded_allowances(tmp_path):
    from core.milestones.automatic import deliver
    ledger = opted(tmp_path)
    assert deliver(ledger)
    (tmp_path / 'cli.py').write_text('print(4)\n')
    assert deliver(ledger)
    (tmp_path / 'cli.py').write_text('print(5)\n')
    assert deliver(ledger) == ''  # per-task attempt cap
    ledger.task = 'next'; ledger.save()
    assert deliver(ledger)


def test_atomic_reservation_prevents_concurrent_duplicate_worker(tmp_path):
    from core.milestones.automatic import deliver
    ledger = opted(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        outputs = list(pool.map(lambda _: deliver(ledger), range(2)))
    assert sum('milestone advice' in v for v in outputs) == 1


def test_timeout_is_visible_retained_and_never_counts_as_evidence(tmp_path, monkeypatch):
    import subprocess
    import core.milestones.automatic as automatic
    ledger = opted(tmp_path)
    before = ledger.path.read_bytes()
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs['timeout'])
    monkeypatch.setattr(automatic, 'run', timeout)
    assert 'incomplete' in automatic.deliver(ledger).lower()
    state = json.loads((tmp_path / '.elevenpowers/advice.json').read_text())
    assert state['tasks'][0]['attempts'][0]['status'] == 'incomplete'
    assert ledger.path.read_bytes() == before
    assert automatic.deliver(ledger) == ''


def test_off_absent_and_corrupt_state_decline_work(tmp_path):
    from core.milestones.automatic import deliver
    ledger = opted(tmp_path)
    (tmp_path / '.elevenpowers/advice.json').write_text('{broken')
    assert 'unavailable' in deliver(ledger)
    (tmp_path / '.elevenpowers/config.json').write_text('{"profile":"off","milestone_advice":{"enabled":true}}')
    ledger._config = None
    assert deliver(ledger) == ''


def test_changed_task_during_worker_discards_its_context(tmp_path, monkeypatch):
    import subprocess
    import core.milestones.automatic as automatic
    ledger = opted(tmp_path)
    def changed(*args, **kwargs):
        Ledger(root=tmp_path, task='new-task').save()
        return subprocess.CompletedProcess(args[0], 0,
            json.dumps({'schema': 1, 'context': 'old task advice'}), '')
    monkeypatch.setattr(automatic, 'run', changed)
    assert 'old task advice' not in automatic.deliver(ledger)
    assert Ledger.load(tmp_path).task == 'new-task'


def test_malformed_worker_output_is_not_delivered(tmp_path, monkeypatch):
    import subprocess
    import core.milestones.automatic as automatic
    ledger = opted(tmp_path)
    monkeypatch.setattr(automatic, 'run', lambda *args, **kwargs:
        subprocess.CompletedProcess(args[0], 0, 'not JSON', ''))
    assert 'incomplete' in automatic.deliver(ledger).lower()
