from pathlib import Path
import subprocess
from types import SimpleNamespace

from eval import challenge, paired


def stub(monkeypatch, change=None):
    monkeypatch.setattr(paired.subscription, 'auth', lambda *a: True)
    real = paired.run
    def run(args, **kw):
        if args[0] == 'fake-host':
            if change:
                change(Path(kw['cwd']))
            return SimpleNamespace(returncode=0, stdout='{"type":"turn.completed","usage":{"input_tokens":1}}', stderr='')
        return real(args, **kw)
    monkeypatch.setattr(paired, 'run', run)


def test_paired_grades_gold_and_invalidates_visible_edits(monkeypatch, tmp_path):
    stub(monkeypatch, lambda p: (p / 'bank/engine.py').write_text(challenge.GOLD))
    result = paired.run_case('codex', 'baseline', tmp_path / 'good', 'fake-host')
    assert result['state'] == 'resolved' and result['grade']['passed'] == 16
    stub(monkeypatch, lambda p: (p / 'visible.py').write_text('print("ok")'))
    result = paired.run_case('codex', 'baseline', tmp_path / 'bad', 'fake-host')
    assert result['state'] == 'invalid'
    assert (tmp_path / 'bad-result.json').exists()


def test_balanced_schedule_and_partial_summaries():
    order = paired.schedule()
    assert len(order) == 8 and len(set(order)) == 8
    assert paired.summarize([])['state'] == 'incomplete'


def test_setup_timeout_and_duplicate_records_cannot_complete(monkeypatch, tmp_path):
    monkeypatch.setattr(paired.subscription, 'auth', lambda *a: False)
    record = paired.run_case('codex', 'baseline', tmp_path / 'setup', 'fake-host')
    assert record['state'] == 'setup'
    assert paired.summarize([record])['state'] == 'incomplete'
    assert paired.summarize([record] * 8)['state'] == 'incomplete'
    stub(monkeypatch)
    real = paired.run
    def timeout(args, **kw):
        if args[0] == 'fake-host':
            raise subprocess.TimeoutExpired(args, .1)
        return real(args, **kw)
    monkeypatch.setattr(paired, 'run', timeout)
    assert paired.run_case('codex', 'baseline', tmp_path / 'timeout', 'fake-host')['state'] == 'timeout'
