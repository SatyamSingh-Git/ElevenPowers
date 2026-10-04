"""The impact evaluator grades frozen references, never its own predictions."""
import json

import pytest

from eval.impact_benchmark import load_cases, grade, seal, evaluate


def manifest(tmp_path):
    value = {'schema': 1, 'projects': [{'id': 'sample', 'commit': 'a'*40,
        'origin': 'https://example.org/sample', 'license': 'MIT', 'files': {'api.py':'b'*64}}],
        'cases': [{'id': 'case-one', 'project': 'sample', 'split':'development',
            'query':'api.py', 'consumers':['worker.py'], 'tests':['tests/test_api.py'],
            'unrelated':['unrelated.py']}]}
    path = tmp_path / 'cases.json'
    path.write_text(json.dumps(value))
    return path, value


def test_known_sets_and_unlabelled_leads_have_separate_denominators():
    case = {'consumers':['worker.py'], 'tests':['tests/test_api.py'], 'unrelated':['unrelated.py']}
    result = grade(case, {'affected':[{'path':'worker.py'}, {'path':'extra.py'}],
                         'tests':[{'path':'tests/test_api.py'}, {'path':'tests/test_other.py'}]})
    assert result['consumer_recall'] == 1
    assert result['test_recall'] == 1
    assert result['negative_hits'] == []
    assert result['unlabelled'] == ['extra.py','tests/test_other.py']
    assert 'precision' not in result  # incomplete oracle cannot label all extras false


def test_missing_known_positive_and_explicit_negative_are_retained():
    result = grade({'consumers':['worker.py'], 'tests':['test_api.py'], 'unrelated':['other.py']},
        {'affected':[{'path':'other.py'}], 'tests':[]})
    assert result['missed_consumers'] == ['worker.py']
    assert result['missed_tests'] == ['test_api.py']
    assert result['negative_hits'] == ['other.py']


@pytest.mark.parametrize('mutate',[
    lambda v: v.update(schema=2),
    lambda v: v['cases'][0].update(query='../outside.py'),
    lambda v: v['cases'][0].update(split='invented'),
    lambda v: v['cases'].append(dict(v['cases'][0])),
    lambda v: v['cases'][0].update(project='missing'),
    lambda v: v['projects'][0].update(commit='not-a-pin'),
    lambda v: v['projects'][0].update(files={'../unsafe.py':'b'*64}),
    lambda v: v['cases'][0].update(unrelated=['worker.py']),
    lambda v: v['cases'][0].update(consumers=[{}]),
    lambda v: v['cases'][0].update(project={}),
])
def test_invalid_frozen_protocol_is_rejected(tmp_path, mutate):
    path, value = manifest(tmp_path)
    mutate(value)
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        load_cases(path)


def test_load_valid_protocol(tmp_path):
    path, value = manifest(tmp_path)
    assert load_cases(path) == value


def test_seal_checks_bytes_not_mtimes_and_rejects_missing_or_linked_input(tmp_path):
    source=tmp_path/'api.py'
    source.write_text('x=1\n')
    import hashlib
    hashes={'api.py':hashlib.sha256(source.read_bytes()).hexdigest()}
    assert seal(tmp_path, hashes)['complete']
    source.write_text('x=2\n')
    assert not seal(tmp_path, hashes)['complete']
    source.unlink()
    assert not seal(tmp_path, hashes)['complete']


def test_new_source_outside_frozen_index_is_not_silently_accepted(tmp_path):
    import hashlib
    (tmp_path/'api.py').write_text('x=1\n')
    hashes={'api.py':hashlib.sha256((tmp_path/'api.py').read_bytes()).hexdigest()}
    (tmp_path/'added.py').write_text('x=2\n')
    assert not seal(tmp_path,hashes)['complete']


def test_failed_source_qualification_retains_requested_cases(tmp_path):
    path,value=manifest(tmp_path)
    from pathlib import Path
    result=evaluate(value,{'sample':tmp_path},split='development',runtime_root=Path(__file__).parents[1])
    assert not result['complete']
    assert result['projects'][0]['cases'][0]['id']=='case-one'
    assert result['projects'][0]['cases'][0]['status']=='incomplete'


def test_unfrozen_scan_policy_cannot_change_selection_silently(tmp_path):
    import hashlib
    (tmp_path/'api.py').write_text('x=1\n')
    hashes={'api.py':hashlib.sha256((tmp_path/'api.py').read_bytes()).hexdigest()}
    state=tmp_path/'.elevenpowers';state.mkdir()
    (state/'config.json').write_text('{"scan":{"exclude":["api.py"]}}')
    assert not seal(tmp_path,hashes)['complete']
