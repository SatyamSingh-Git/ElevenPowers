"""Fresh selected bytes, partial coverage and approved boundaries are distinct."""
import json
import os
from pathlib import Path
import time

import pytest

from core.inputs.bindings import bind
from tests.test_input_definitions import policy


@pytest.fixture
def inputs(tmp_path):
    root = tmp_path/'project'; root.mkdir()
    directory = tmp_path/'private inputs'; directory.mkdir()
    (directory/'parser.py').write_text('value=2\n')
    policy(root)
    bind(root,'deps',directory)
    return root,directory


def read(root):
    from core.inputs.collection import capture
    return capture(root,time.monotonic()+20)


def snapshot(root):
    return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_missing_policy_is_not_implicit_environment_proof(tmp_path):
    value = read(tmp_path)
    assert value['state'] == 'not_configured' and value['fingerprint'] is None
    assert list(tmp_path.iterdir()) == []


def test_unchanged_reads_are_deterministic_private_and_read_only(inputs):
    root,directory = inputs
    before = snapshot(root)
    first,second = read(root),read(root)
    assert first['state'] == second['state'] == 'available'
    assert first['fingerprint'] == second['fingerprint']
    assert first['counts']['files'] == 1 and first['counts']['bytes'] == (directory/'parser.py').stat().st_size
    assert str(directory) not in json.dumps(first) and 'value=2' not in json.dumps(first)
    assert snapshot(root) == before
    (directory/'parser.py').write_text('value=9\n')
    assert read(root)['fingerprint'] != first['fingerprint']


def test_tree_addition_deletion_names_and_shared_limits(inputs):
    root,directory = inputs
    policy(root,witnesses=[{'id':'tree','root':'deps','paths':['.']},
                           {'id':'file','root':'deps','paths':['parser.py']}])
    first = read(root)
    assert first['state'] == 'available' and first['counts']['files'] == 1
    (directory/'added').write_bytes(b'new')
    second = read(root)
    assert second['state'] == 'available' and second['fingerprint'] != first['fingerprint']
    assert second['counts']['files'] == 2
    (directory/'added').rename(directory/'renamed')
    third = read(root)
    assert third['fingerprint'] != second['fingerprint']
    (directory/'renamed').unlink()
    assert read(root)['fingerprint'] == first['fingerprint']


def test_empty_scope_missing_file_and_unapproved_root_stay_incomplete(inputs):
    root,directory = inputs
    (directory/'parser.py').unlink()
    for paths in [['parser.py'],['.']]:
        policy(root,witnesses=[{'id':'deps','root':'deps','paths':paths}])
        value = read(root)
        assert value['state'] == 'incomplete' and value['fingerprint'] is None
    (root/'.elevenpowers/input-roots.json').unlink()
    assert read(root)['state'] == 'incomplete'


def test_missing_approval_still_names_the_declared_witness_and_root(inputs):
    root,_ = inputs
    (root/'.elevenpowers/input-roots.json').unlink()
    value = read(root)
    assert value['state'] == 'incomplete'
    assert [(w['id'],w['root'],w['state']) for w in value['witnesses']] == [('dependencies','deps','incomplete')]


@pytest.mark.parametrize('limits', [{'bytes':1},{'seconds':0},{'files':1}])
def test_aggregate_limits_never_return_a_partial_fingerprint(inputs,limits):
    root,directory = inputs
    (directory/'other').write_bytes(b'other')
    policy(root,witnesses=[{'id':'all','root':'deps','paths':['.']}],limits=limits)
    value = read(root)
    assert value['state'] == 'incomplete' and value['fingerprint'] is None
    assert value['issues']


def test_empty_directories_count_toward_entry_budget(inputs):
    root,directory = inputs
    for i in range(4):
        (directory/str(i)).mkdir()
    policy(root,witnesses=[{'id':'all','root':'deps','paths':['.']}],limits={'files':1})
    assert read(root)['state'] == 'incomplete'


def test_symlink_and_hard_link_content_is_not_qualified(inputs,tmp_path):
    root,directory = inputs
    outside = tmp_path/'outside'; outside.write_bytes(b'private outside')
    target = directory/'parser.py'; target.unlink()
    try:
        target.symlink_to(outside)
    except OSError:
        pytest.skip('symlinks unavailable')
    assert read(root)['state'] == 'incomplete'
    target.unlink(); os.link(outside,target)
    assert read(root)['state'] == 'incomplete'


def test_special_file_is_not_opened_or_hashed(inputs):
    if not hasattr(os,'mkfifo'):
        pytest.skip('FIFO unavailable on this platform')
    root,directory = inputs
    target = directory/'parser.py'; target.unlink(); os.mkfifo(target)
    assert read(root)['state'] == 'incomplete'


def test_directory_depth_is_bounded(inputs):
    root,directory = inputs
    current = directory
    for _ in range(34):
        current = current/'d'; current.mkdir()
    policy(root,witnesses=[{'id':'all','root':'deps','paths':['.']}])
    assert read(root)['state'] == 'incomplete'


def test_real_content_change_during_collection_cannot_qualify(inputs,monkeypatch):
    from core.inputs import collection
    root,directory = inputs
    original = collection.definition.raw
    def changing(path,*args,**kwargs):
        data = original(path,*args,**kwargs)
        if Path(path) == directory/'parser.py':
            (directory/'parser.py').write_bytes(b'changed actual bytes')
        return data
    monkeypatch.setattr(collection.definition,'raw',changing)
    value = read(root)
    assert value['state'] == 'incomplete' and value['fingerprint'] is None


def test_policy_change_during_collection_cannot_qualify(inputs,monkeypatch):
    from core.inputs import collection
    root,directory = inputs
    original = collection.definition.raw
    def changing(path,*args,**kwargs):
        data = original(path,*args,**kwargs)
        if Path(path) == directory/'parser.py':
            policy(root,limits={'bytes':20})
        return data
    monkeypatch.setattr(collection.definition,'raw',changing)
    assert read(root)['state'] == 'incomplete'
