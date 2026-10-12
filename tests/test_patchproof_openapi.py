import json
import os
from pathlib import Path
import subprocess

import pytest

from test_patchproof_contracts import manifest


@pytest.fixture
def engine():
    value = os.environ.get('EP_OASDIFF') or str(Path(__file__).resolve().parents[1] / '.venv/oasdiff/oasdiff.exe')
    path = Path(value)
    if not path.is_file():
        pytest.skip('explicit pinned oasdiff acceptance engine unavailable')
    return path.resolve()


def git(root, *args):
    done = subprocess.run(['git', '-c', f'safe.directory={root.as_posix()}', *args],
                          cwd=root, capture_output=True, check=True)
    return done.stdout.decode().strip()


def spec(paths=None):
    return {'openapi': '3.0.3', 'info': {'title': 'Any API', 'version': '1.0.0'},
            'paths': paths if paths is not None else {
                '/items': {'get': {'responses': {'200': {'description': 'ok'}}}}}}


def project(root, revised=None, path='api.json'):
    root.mkdir(exist_ok=True)
    git(root, 'init', '-q')
    git(root, 'config', 'user.email', 'test@example.invalid')
    git(root, 'config', 'user.name', 'Test')
    git(root, 'config', 'core.autocrlf', 'false')
    manifest(root, [{'id': 'api', 'kind': 'openapi', 'path': path}])
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_bytes(json.dumps(spec()).encode())
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'Base contract')
    (root / path).write_bytes(json.dumps(spec() if revised is None else revised).encode())
    (root / 'feature.txt').write_bytes(b'change\n')
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'Revised contract')
    return root


@pytest.mark.parametrize('revised, result', [(spec(), 'pass'), (spec({}), 'fail')])
def test_real_checker_preserves_compatible_and_incompatible(tmp_path, engine, revised, result):
    from core.patchproof.openapi import check
    from core.patchproof.contracts import load
    root = project(tmp_path, revised)
    row = check(root, 'api', engine)
    assert row['execution'] == 'complete' and row['result'] == result, row
    assert row['exit_code'] == (0 if result == 'pass' else 1)
    assert row['producer']['version'] == '1.33.0'
    assert row['base'] == git(root, 'rev-parse', 'HEAD~1') and row['head'] == git(root, 'rev-parse', 'HEAD')
    assert row['configuration']['external_refs'] is False
    assert load(root)['records'][-1] == row
    assert git(root, 'status', '--porcelain') == ''


@pytest.mark.parametrize('revised', [{'openapi': '3.0.3'},
    {**spec(), 'paths': {'/items': {'$ref': 'https://127.0.0.1:1/forbidden'}}}])
def test_real_invalid_and_external_inputs_never_pass(tmp_path, engine, revised):
    from core.patchproof.openapi import check
    row = check(project(tmp_path, revised), 'api', engine)
    assert row['execution'] == 'incomplete' and row['result'] == 'unknown' and row['issues']


def test_budget_missing_engine_and_missing_blob_retained(tmp_path):
    from core.patchproof.openapi import check
    root = project(tmp_path)
    row = check(root, 'api', root / 'not-installed', seconds=0)
    assert row['execution'] == 'incomplete' and row['result'] == 'unknown'
    row = check(root, 'api', root / 'not-installed')
    assert row['execution'] == 'incomplete'


def test_config_and_env_cannot_suppress_real_breaking_change(tmp_path, engine, monkeypatch):
    from core.patchproof.openapi import check
    root = project(tmp_path, spec({}))
    (root / '.oasdiff.yaml').write_text('fail-on: NEVER\n')
    monkeypatch.setenv('OASDIFF_CONFIG', str(root / '.oasdiff.yaml'))
    assert check(root, 'api', engine)['result'] == 'fail'


def test_observed_protocol_requires_consistent_severity_and_exit():
    from core.patchproof.openapi import findings
    assert findings('[]\n', 0)['error'] == 0
    value = '[{"id":"api-path-removed-without-deprecation","level":3}]'
    assert findings(value, 1)['error'] == 1
    for output, code in [(value, 0), ('[]', 1), ('{}', 0), ('', 0),
                         ('[{"id":"unknown","level":true}]', 0)]:
        with pytest.raises(ValueError):
            findings(output, code)


def test_real_binary_movement_during_check_retains_incomplete(tmp_path, engine, monkeypatch):
    import shutil
    import core.patchproof.openapi as runner
    copied = tmp_path.parent / (tmp_path.name + '-moving.exe')
    shutil.copyfile(engine, copied)
    copied.chmod(0o755)
    root = project(tmp_path)
    execute = runner.run

    def moved(args, **kwargs):
        done = execute(args, **kwargs)
        if 'breaking' in args:
            copied.write_bytes(copied.read_bytes() + b'changed')
        return done

    monkeypatch.setattr(runner, 'run', moved)
    row = runner.check(root, 'api', copied)
    assert row['execution'] == 'incomplete' and row['result'] == 'unknown'
