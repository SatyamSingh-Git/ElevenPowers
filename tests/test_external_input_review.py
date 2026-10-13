"""Independent review regressions exercise actual reads, checks and reuse."""
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace

import pytest

from tests.test_input_definitions import policy
from tests.test_patchproof_identity import git


def project(tmp_path):
    from tests.test_external_input_reuse import dependency_project
    return dependency_project.__wrapped__(tmp_path, SimpleNamespace(param='python'))


@pytest.mark.parametrize('stage', ['report', 'preflight', 'report-policy'])
def test_source_edit_during_external_read_refuses_reuse_or_launch(tmp_path, monkeypatch, stage):
    from core.inputs import definition
    from core.patchproof import report, execution_state
    from core.patchproof.execution import verify
    from core.patchproof.planning import plan
    root, base, head, target, *_ = project(tmp_path)
    assert verify(root, base, head, seconds=120)['state'] == 'passed'
    module = report if stage.startswith('report') else execution_state
    original_capture, original_raw = module.input_capture, definition.raw
    scans = 0
    def capture(*args, **kwargs):
        nonlocal scans
        scans += 1
        def changing_read(path, *a, **k):
            if scans == (2 if stage.startswith('report') else 3) and Path(path) == target:
                if stage == 'report-policy':
                    (root/'.git/info/exclude').write_bytes(b'unobserved-neighbor\n')
                else:
                    (root/'service.py').write_bytes(b'value=99\n')
            return original_raw(path, *a, **k)
        with monkeypatch.context() as patch:
            patch.setattr(definition, 'raw', changing_read)
            return original_capture(*args, **kwargs)
    monkeypatch.setattr(module, 'input_capture', capture)
    if stage.startswith('report'):
        result = plan(root, base, head, seconds=120)
        assert not result['ready']
        assert result['checks'][0]['action'] != 'reuse'
        assert result['bundle']['execution']['checks'][0]['association'] == 'unavailable'
    else:
        result = verify(root, base, head, seconds=120, reuse=False)
        assert result['state'] == 'incomplete'
        assert result['checks'][0]['status'] == 'deferred'
    assert (root/'.elevenpowers/count.txt').read_text() == '1'


def test_empty_directory_changes_actual_behavior_and_refuses_reuse(tmp_path):
    from core.patchproof.execution import verify
    from core.patchproof.planning import plan
    from tests.test_patchproof_identity import commit
    from core.inputs.collection import capture
    root, base, _, target, *_ = project(tmp_path)
    policy(root, witnesses=[{'id':'dependencies','root':'deps','paths':['.']}])
    with (root/'check.py').open('a') as stream:
        stream.write(f'assert not Path({str(target.parent / "disabled")!r}).exists()\n')
    head = commit(root, 'check dependency directory behavior')
    assert verify(root, base, head, seconds=120)['state'] == 'passed'
    before = capture(root, time.monotonic()+10)
    (target.parent/'disabled').mkdir()
    after = capture(root, time.monotonic()+10)
    assert before['fingerprint'] != after['fingerprint']
    result = plan(root, base, head, seconds=120)
    assert result['ready'] and result['checks'][0]['action'] == 'run'
    assert verify(root, base, head, seconds=120)['state'] == 'failed'
    assert (root/'.elevenpowers/count.txt').read_text() == '2'


def test_guard_refuses_hardlinked_input_state_before_read(tmp_path, monkeypatch):
    from core.patchproof.report import _guard
    marker = tmp_path/'private-marker'; marker.write_bytes(b'disposable private data')
    os.link(marker, tmp_path/'elevenpowers.inputs.json')
    original = Path.open
    reads = []
    def observed(path, *args, **kwargs):
        if path.name == 'elevenpowers.inputs.json':
            reads.append(path)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', observed)
    with pytest.raises(ValueError):
        _guard(tmp_path, time.monotonic()+10)
    assert reads == []


def test_nested_tracked_approval_is_refused_without_file_read(tmp_path):
    from core.inputs.bindings import bind
    from core.inputs.collection import capture
    git(tmp_path, 'init', '-q')
    root = tmp_path/'nested'; root.mkdir(); policy(root)
    dependency = tmp_path/'deps'; dependency.mkdir()
    (dependency/'parser.py').write_bytes(b'value=2\n')
    bind(root, 'deps', dependency)
    git(tmp_path, 'add', '-f', 'nested/.elevenpowers/input-roots.json')
    result = capture(root, time.monotonic()+10)
    assert result['state'] == 'incomplete'
    assert result['counts']['files'] == 0


def test_huge_seconds_is_controlled_incomplete(tmp_path):
    from core.inputs.collection import capture
    policy(tmp_path, limits={'seconds':10**400})
    result = capture(tmp_path, time.monotonic()+10)
    assert result['state'] == 'incomplete'
    assert result['fingerprint'] is None
