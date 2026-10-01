"""Positive and adversarial controls for optional changed-code test strength."""
from pathlib import Path
import pytest


def test_observations_are_informational_and_count_all_states():
    from core.strength.model import Observation, summary
    items = [Observation(str(i), 'src/a.py', 2, 'operator', status)
             for i, status in enumerate(('detected', 'undetected', 'invalid', 'timed_out', 'error', 'not_run'))]
    value = summary(items)
    assert value['detected'] == value['undetected'] == 1
    assert value['incomplete'] == 3 and value['invalid'] == 1
    assert 'score' not in value and 'verdict' not in value


def test_observation_rejects_unknown_or_unsafe_metadata():
    from core.strength.model import Observation
    for path, status in [('../a.py', 'detected'), ('/a.py', 'detected'), ('a.py', 'pass')]:
        with pytest.raises(ValueError):
            Observation('1', path, 1, 'operator', status)


def test_strength_config_preserved_and_validated(tmp_path):
    import json
    from core.config import load, save
    from core.strength.settings import settings
    folder = tmp_path / '.elevenpowers'
    folder.mkdir()
    (folder / 'config.json').write_text(json.dumps({'strength': {'enabled': False, 'max_mutants': 3}}))
    config = load(tmp_path)
    assert not settings(config.strength).enabled
    save(tmp_path, config)
    assert json.loads((folder / 'config.json').read_text())['strength']['max_mutants'] == 3


@pytest.mark.parametrize('raw', [{'seconds': float('nan')}, {'max_mutants': -1},
                                 {'enabled': 'yes'}, {'dependencies': ['../elsewhere']}])
def test_strength_settings_reject_invalid_limits(raw):
    from core.strength.settings import settings
    with pytest.raises(ValueError):
        settings(raw)


def repository(root):
    import subprocess
    def git(*args):
        return subprocess.run(['git', '-c', f'safe.directory={root.as_posix()}', *args],
                              cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    git('init')
    git('config', 'user.email', 'tests@example.invalid')
    git('config', 'user.name', 'Tests')
    (root / 'a.py').write_text('value = 1\n')
    (root / '.gitignore').write_text('generated/\n')
    git('add', '.')
    git('commit', '-m', 'base')
    return git('rev-parse', 'HEAD')


def test_scope_respects_repository_ignores_and_tests(tmp_path):
    import time
    from core.strength.scope import select
    base = repository(tmp_path)
    (tmp_path / 'a.py').write_text('value = 2\n')
    (tmp_path / 'test_a.py').write_text('assert True\n')
    (tmp_path / 'generated').mkdir()
    (tmp_path / 'generated/x.py').write_text('value = 3\n')
    value = select(tmp_path, base, time.monotonic() + 10)
    assert value.paths == ['a.py'] and not value.issues


def test_scope_missing_base_and_dirty_attribution_are_incomplete(tmp_path):
    import time
    from core.strength.scope import select
    base = repository(tmp_path)
    (tmp_path / 'a.py').write_text('value = 2\n')
    assert select(tmp_path, '', time.monotonic()+10).issues
    assert select(tmp_path, base, time.monotonic()+10, opened_dirty=['a.py']).issues


def test_copy_plan_includes_assets_but_excludes_ignored_data(tmp_path):
    import time
    from core.strength.isolation import copy_plan
    from core.strength.settings import Settings
    repository(tmp_path)
    (tmp_path / 'fixture.json').write_text('{}')
    (tmp_path / 'generated').mkdir()
    (tmp_path / 'generated/secret.txt').write_text('secret')
    paths = copy_plan(tmp_path, Settings(), time.monotonic()+10)
    assert 'fixture.json' in paths and 'generated/secret.txt' not in paths
    assert not any(p.startswith('.git/') for p in paths)


def test_copy_plan_limits_are_explicit(tmp_path):
    import time
    from core.strength.isolation import copy_plan
    from core.strength.settings import Settings
    repository(tmp_path)
    with pytest.raises(ValueError, match='file limit'):
        copy_plan(tmp_path, Settings(max_files=1), time.monotonic()+10)


def test_snapshot_is_private_and_cleaned_on_failure(tmp_path):
    import time
    from core.strength.isolation import snapshot
    from core.strength.settings import Settings
    repository(tmp_path)
    original = (tmp_path / 'a.py').read_bytes()
    with pytest.raises(RuntimeError):
        with snapshot(tmp_path, Settings(), time.monotonic()+10) as copied:
            isolated = copied.root
            (isolated / 'a.py').write_text('value = 99\n')
            assert copied.stamp
            raise RuntimeError('interrupt')
    assert not isolated.exists()
    assert (tmp_path / 'a.py').read_bytes() == original


def test_snapshot_rejects_symlink_input(tmp_path):
    import time
    from core.strength.isolation import snapshot
    from core.strength.settings import Settings
    repository(tmp_path)
    try:
        (tmp_path / 'alias.py').symlink_to(tmp_path / 'a.py')
    except OSError:
        pytest.skip('symlink privilege unavailable')
    with pytest.raises(ValueError, match='linked'):
        with snapshot(tmp_path, Settings(), time.monotonic()+10):
            pass
