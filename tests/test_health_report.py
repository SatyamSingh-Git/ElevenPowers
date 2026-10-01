"""Report metadata shared with health without extra source reads."""
from core import export
from core.config import Config, save
from core.hosts.readiness import receipt_key
from core.ledger import Ledger
from core.parsers import parse


def test_source_coverage_remains_distinct_from_unavailable_revision(tmp_path, monkeypatch):
    (tmp_path / 'app.py').write_text('answer = 1\n')
    monkeypatch.setattr(export, '_revision', lambda *a: ('', 'unavailable', ['revision lookup unavailable']))
    value = export.build(tmp_path)
    assert value['coverage']['source_complete']
    assert not value['coverage']['complete']
    assert value['coverage']['source_issues'] == []
    assert value['timings']['report_ms'] >= value['timings']['source_snapshot_ms'] >= 0


def test_private_receipt_key_survives_portable_command_scrubbing(tmp_path):
    (tmp_path / 'app.py').write_text('answer = 1\n')
    command = 'python ' + str(tmp_path / 'check.py')
    save(tmp_path, Config(commands={'tests': command}))
    ledger = Ledger(root=tmp_path, task='task')
    receipts = parse(command, '1 passed in 0.01s', 0, tmp_path)
    ledger.add(receipts)
    ledger.save()
    value = export.build(tmp_path)
    assert value['receipts'][0]['receipt_key'] == receipt_key(receipts[0])
    assert '<project>' in value['receipts'][0]['command']
    assert value['receipts'][0]['declaration'] == 'tests'
