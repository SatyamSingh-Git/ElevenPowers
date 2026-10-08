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


def test_four_source_matching_records_without_protocol_cannot_claim_gain(tmp_path):
    from eval.preservation_archive import publish, EXPECTED
    from eval.preservation_cases import case
    import hashlib
    batch = tmp_path / 'batch'; batch.mkdir(); (batch / 'protocol.json').write_text('{}')
    for slot in EXPECTED:
        folder = batch / slot; folder.mkdir(); value = case(slot.rsplit('-', 1)[0]); stages = []
        for stage in (1, 2):
            source = {'service.py': value['gold' if slot.endswith('assisted') else 'fault'][stage-1],
                      'formatting.py': value['files']['formatting.py']}
            (folder / f'source-{stage}.json').write_text(json.dumps(source))
            stages.append({'stage': stage, 'state': 'completed', 'scope': 'preserved',
                'source_after': {n:hashlib.sha256(s.encode()).hexdigest() for n,s in source.items()},
                'native': {'state': 'incomplete'}})
        (folder / 'result.json').write_text(json.dumps({'slot':slot,'state':'completed','model_seconds':10,'stages':stages}))
    result = publish(tmp_path / 'out', {slot:batch for slot in EXPECTED})
    assert result['state'] == 'incomplete'
    assert result['paired_correctness_advantage_observed'] is False


def test_valid_protocol_qualifies_but_over_budget_record_does_not(tmp_path):
    from eval.preservation import prepare
    from eval.preservation_archive import _qualification
    from eval.preservation_cases import case
    batch = tmp_path / 'batch'; protocol = prepare(batch, names=('queue',))
    slot = 'queue-ordinary'
    stages = [{'seconds_cap':240, 'elapsed_ms':1000,
               'host_observation':{'completed':True,'models':['claude-sonnet-5']}},
              {'seconds_cap':479, 'elapsed_ms':2000,
               'host_observation':{'completed':True,'models':['claude-sonnet-5']}}]
    record = {'stages':stages, 'model_seconds':3}
    assert _qualification(batch,slot,protocol,record,case('queue'))['state'] == 'qualified'
    record['model_seconds'] = 9999
    assert _qualification(batch,slot,protocol,record,case('queue'))['state'] == 'incomplete'
