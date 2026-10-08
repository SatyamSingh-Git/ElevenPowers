"""Archive independent regrades without replacing original observations."""
import importlib.util
import json


def test_archive_keeps_original_grade_and_regrades_saved_source(tmp_path):
    assert importlib.util.find_spec('eval.preservation_archive'), 'versioned preservation archive is missing'
    from eval.preservation_archive import publish
    from eval.preservation_cases import case
    batch = tmp_path / 'batch'; folder = batch / 'queue-ordinary'; folder.mkdir(parents=True)
    value = case('queue')
    stages = []
    import hashlib
    for stage in (1, 2):
        source = {'service.py': value['gold'][stage - 1], 'formatting.py': value['files']['formatting.py']}
        (folder / f'source-{stage}.json').write_text(json.dumps(source))
        stages.append({'stage': stage, 'state': 'completed', 'scope': 'preserved',
            'source_after': {k: hashlib.sha256(v.encode()).hexdigest() for k, v in source.items()},
            'independent_grade': {'state': 'graded', 'passed': 0, 'failed': 99, 'oracle_sha256': 'old'},
            'native': {'state': 'incomplete', 'receipt_links': 0, 'phases': {}, 'advice_attempts': []}})
    original = {'slot': 'queue-ordinary', 'state': 'completed', 'model_seconds': 10, 'stages': stages}
    raw = json.dumps(original).encode(); (folder / 'result.json').write_bytes(raw)
    (batch / 'protocol.json').write_text('{}')
    result = publish(tmp_path / 'out', {'queue-ordinary': batch})
    assert result['state'] == 'incomplete'
    saved = json.loads((tmp_path / 'out/queue-ordinary.json').read_text())
    assert saved['original']['stages'][1]['independent_grade']['failed'] == 99
    assert saved['regrades'][1]['passed'] == 8
    assert (folder / 'result.json').read_bytes() == raw


def test_changed_snapshot_is_unqualified(tmp_path):
    assert importlib.util.find_spec('eval.preservation_archive'), 'versioned preservation archive is missing'
    from eval.preservation_archive import publish
    batch = tmp_path / 'batch'; folder = batch / 'queue-ordinary'; folder.mkdir(parents=True)
    (batch / 'protocol.json').write_text('{}')
    (folder / 'source-1.json').write_text('{"service.py":"print(1)","formatting.py":"print(2)"}')
    (folder / 'result.json').write_text(json.dumps({'slot': 'queue-ordinary', 'state': 'completed',
        'stages': [{'stage': 1, 'state': 'completed', 'scope': 'preserved', 'source_after': {}}]}))
    result = publish(tmp_path / 'out', {'queue-ordinary': batch})
    assert result['state'] == 'incomplete'
    assert result['paired_correctness_advantage_observed'] is False
