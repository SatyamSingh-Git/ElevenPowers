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


def test_strength_budget_caps_attempts_and_elapsed_time():
    import time
    from core.strength.execution import Budget
    value = Budget(time.monotonic()+1, 1)
    value.attempt()
    with pytest.raises(TimeoutError, match='attempt'):
        value.attempt()
    expired = Budget(time.monotonic()-1, 1)
    with pytest.raises(TimeoutError, match='deadline'):
        expired.timeout(10)


def test_contained_strength_command_reports_timeout(tmp_path):
    import sys, time
    from core.strength.execution import Budget, execute
    value = execute([sys.executable, '-c', 'import time; time.sleep(5)'], tmp_path,
                    Budget(time.monotonic()+.2, 1), 1, shell=False)
    assert value.status == 'timed_out' and value.returncode is None


def test_baseline_requires_observed_tests_and_rejects_absolute_workspace(tmp_path):
    import sys, time
    from core.strength.baseline import baseline
    from core.strength.execution import Budget
    (tmp_path / 'test_a.py').write_text('def test_value():\n    assert True\n')
    command = f'"{sys.executable}" -m pytest -q -p no:cacheprovider'
    assert baseline(command, tmp_path, tmp_path / 'original', Budget(time.monotonic()+10, 1), 5).status == 'passed'
    assert baseline('echo no tests', tmp_path, tmp_path / 'original', Budget(time.monotonic()+10, 1), 5).status == 'incomplete'
    tied = command + ' "' + str(tmp_path / 'original' / 'tests') + '"'
    assert baseline(tied, tmp_path, tmp_path / 'original', Budget(time.monotonic()+10, 1), 5).status == 'incomplete'


def test_red_baseline_is_not_mutation_detection(tmp_path):
    import sys, time
    from core.strength.baseline import baseline
    from core.strength.execution import Budget
    (tmp_path / 'test_a.py').write_text('def test_value():\n    assert False\n')
    value = baseline(f'"{sys.executable}" -m pytest -q -p no:cacheprovider', tmp_path,
                     tmp_path / 'original', Budget(time.monotonic()+10, 1), 5)
    assert value.status == 'failed'


def test_saved_strength_is_atomic_metadata_only(tmp_path):
    from core.strength.store import save, load
    value = {'schema_version': 1, 'task': 't', 'state': 'complete', 'issues': [],
             'observations': [], 'fingerprint': 'abc', 'source_fingerprint': 'def',
             'baseline': 'passed', 'engine_versions': {}, 'base': '123',
             'command': 'pytest', 'settings': {}, 'paths': ['a.py'], 'recorded_at': 1,
             'summary': {}, 'attempts': 0, 'limitations': []}
    save(tmp_path, value)
    assert load(tmp_path, 't')['state'] == 'complete'
    assert load(tmp_path, 'different') is None
    value['raw_output'] = 'private'
    with pytest.raises(ValueError):
        save(tmp_path, value)
    assert load(tmp_path, 't')['state'] == 'complete'


def test_corrupt_strength_is_an_explicit_incomplete_record(tmp_path):
    from core.strength.store import load
    folder = tmp_path / '.elevenpowers'
    folder.mkdir()
    (folder / 'strength.json').write_text('{broken')
    assert load(tmp_path, 't')['state'] == 'incomplete'


def test_cosmic_ray_real_generation_and_optional_absence(tmp_path):
    import time, sys, importlib.util
    from core.strength.engines import cosmic
    from core.strength.execution import Budget
    if importlib.util.find_spec('cosmic_ray') is None:
        pytest.skip('optional cosmic-ray not installed')
    (tmp_path / 'a.py').write_text('def positive(value):\n    return value > 0\n')
    candidates, version = cosmic(tmp_path, ['a.py'], sys.executable, Budget(time.monotonic()+30, 4))
    assert version == '8.7.0'
    assert len(candidates) == 4 and all(c.path == 'a.py' and c.line == 2 for c in candidates)
    assert any('>= 0' in c.content for c in candidates)
    with pytest.raises(ValueError, match='unavailable'):
        cosmic(tmp_path, ['a.py'], str(tmp_path / 'missing-python'), Budget(time.monotonic()+10, 1))


def test_mutation_execution_weak_and_strong_tests(tmp_path):
    import sys, time
    from core.strength.engines import Candidate
    from core.strength.execution import Budget
    from core.strength.mutations import run_candidate
    source = 'def positive(value):\n    return value > 0\n'
    (tmp_path / 'a.py').write_text(source)
    candidate = Candidate('1', 'a.py', 2, 'comparison', source.replace('> 0', '>= 0'))
    command = f'"{sys.executable}" -m pytest -q -p no:cacheprovider'
    (tmp_path / 'test_a.py').write_text('from a import positive\ndef test_value():\n    assert positive(2)\n')
    assert run_candidate(candidate, tmp_path, command, Budget(time.monotonic()+10, 1), 5).status == 'undetected'
    (tmp_path / 'test_a.py').write_text('from a import positive\ndef test_value():\n    assert not positive(0)\n')
    assert run_candidate(candidate, tmp_path, command, Budget(time.monotonic()+10, 1), 5).status == 'detected'
    assert (tmp_path / 'a.py').read_text() == source


def test_invalid_mutation_and_empty_test_execution_are_not_detected(tmp_path):
    import time
    from core.strength.engines import Candidate
    from core.strength.execution import Budget
    from core.strength.mutations import run_candidate
    (tmp_path / 'a.py').write_text('value = 1\n')
    candidate = Candidate('1', 'a.py', 1, 'operator', 'invalid +\n')
    assert run_candidate(candidate, tmp_path, 'echo ok', Budget(time.monotonic()+5, 1), 1).status == 'invalid'
    valid = Candidate('2', 'a.py', 1, 'operator', 'value = 2\n')
    assert run_candidate(valid, tmp_path, 'echo ok', Budget(time.monotonic()+5, 1), 1).status == 'error'
