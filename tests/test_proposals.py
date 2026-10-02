"""A recorder must not change candidate/index or hide an unavailable proposal."""
import base64
import json
import subprocess
import sys
from pathlib import Path

import pytest

from eval import proposals


def test_snapshot_is_index_neutral_and_includes_deletion(tmp_path):
    root = tmp_path / 'candidate'; root.mkdir()
    (root / 'app.py').write_text('old\n')
    (root / 'gone.py').write_text('delete\n')
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
    index = (root / '.git/index').read_bytes()
    (root / 'app.py').write_bytes(b'new\n')
    (root / 'gone.py').unlink()
    (root / 'new.py').write_bytes(b'added\n')
    value = proposals.snapshot(root, ['app.py', 'gone.py', 'new.py'])
    assert value['state'] == 'complete'
    assert base64.b64decode(value['files']['app.py']) == b'new\n'
    assert value['files']['gone.py'] is None
    assert base64.b64decode(value['files']['new.py']) == b'added\n'
    assert (root / '.git/index').read_bytes() == index
    assert (root / 'app.py').read_bytes() == b'new\n'


@pytest.mark.parametrize('names', [['../outside'], ['/absolute'], ['.git/index'], ['a', 'a']])
def test_unsafe_allowlist_cannot_capture_source(tmp_path, names):
    with pytest.raises(ValueError):
        proposals.snapshot(tmp_path, names)


def test_byte_limit_is_incomplete_not_an_empty_success(tmp_path):
    (tmp_path / 'big.py').write_bytes(b'x' * (512 * 1024 + 1))
    value = proposals.snapshot(tmp_path, ['big.py'])
    assert value['state'] == 'incomplete' and value['files'] == {}
    assert value['fingerprint'] is None


def test_link_is_not_followed(tmp_path):
    target = tmp_path / 'outside'; target.write_text('private')
    root = tmp_path / 'root'; root.mkdir()
    try:
        (root / 'app.py').symlink_to(target)
    except OSError:
        pytest.skip('link permission unavailable')
    value = proposals.snapshot(root, ['app.py'])
    assert value['state'] == 'incomplete' and 'private' not in str(value)


def test_record_roundtrip_and_tampered_history_rejected(tmp_path):
    (tmp_path / 'app.py').write_text('candidate\n')
    path = tmp_path / 'proposals.jsonl'
    first = proposals.snapshot(tmp_path, ['app.py'])
    proposals.append(path, {'phase': 'Stop', 'before': first, 'after': first,
                            'decision': 'allow', 'plugin_exit': None})
    assert proposals.read(path)[0]['before'] == first
    text = path.read_text().replace('allow', 'block')
    path.write_text(text)
    with pytest.raises(ValueError, match='history'):
        proposals.read(path)


def test_capacity_preserves_first_proposals_and_marks_overflow(tmp_path):
    path = tmp_path / 'history.jsonl'
    for _ in range(17):
        proposals.append(path, {'phase': 'Stop', 'before': None, 'after': None,
                                'decision': 'unavailable', 'plugin_exit': None})
    value = proposals.read(path)
    assert len(value) == 17
    assert value[-1]['state'] == 'overflow'


def test_stop_wrapper_preserves_real_child_decision(tmp_path):
    root = tmp_path / 'candidate'; root.mkdir()
    (root / 'app.py').write_bytes(b'before\n')
    child = tmp_path / 'producer.py'
    child.write_text("import sys\nfrom pathlib import Path\nPath('app.py').write_bytes(b'after\\n')\nprint('block reason', file=sys.stderr)\nraise SystemExit(2)\n")
    manifest = tmp_path / 'contract.json'
    manifest.write_text(json.dumps({'root': str(root), 'files': ['app.py'], 'host': 'claude',
                                   'plugin': [sys.executable, str(child)], 'history': str(tmp_path / 'history.jsonl')}))
    result = subprocess.run([sys.executable, str(Path(proposals.__file__)), str(manifest), 'Stop'],
                            cwd=root, input=json.dumps({'cwd': str(root)}), capture_output=True, text=True)
    assert result.returncode == 2 and result.stderr == 'block reason\n'
    record = proposals.read(tmp_path / 'history.jsonl')[0]
    assert record['decision'] == 'block'
    assert base64.b64decode(record['before']['files']['app.py']) == b'before\n'
    assert base64.b64decode(record['after']['files']['app.py']) == b'after\n'


def test_passive_stop_and_broken_sink_never_block(tmp_path):
    root = tmp_path / 'candidate'; root.mkdir()
    (root / 'app.py').write_text('candidate')
    manifest = tmp_path / 'contract.json'
    history = tmp_path / 'history.jsonl'; history.write_text('broken')
    manifest.write_text(json.dumps({'root': str(root), 'files': ['app.py'], 'host': 'claude',
                                   'plugin': [], 'history': str(history)}))
    result = subprocess.run([sys.executable, str(Path(proposals.__file__)), str(manifest), 'Stop'],
                            input=json.dumps({'cwd': str(root)}), capture_output=True, text=True)
    assert result.returncode == 0 and result.stdout == '' and result.stderr == ''
