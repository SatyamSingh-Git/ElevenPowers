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


def repository(root, source_file='a.py'):
    import subprocess
    def git(*args):
        return subprocess.run(['git', '-c', f'safe.directory={root.as_posix()}', *args],
                              cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    git('init')
    git('config', 'user.email', 'tests@example.invalid')
    git('config', 'user.name', 'Tests')
    (root / source_file).write_text('value = 1\n')
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


def stryker_path():
    import os
    path = Path(os.environ.get('EP_TEST_STRYKER', '.venv/strength-js/node_modules/@stryker-mutator/instrumenter'))
    if not path.exists():
        pytest.skip('optional Stryker instrumenter not installed')
    return str(path.resolve())


def test_stryker_real_generation_js_and_typescript(tmp_path):
    import time
    from core.strength.engines import stryker
    from core.strength.execution import Budget
    engine = stryker_path()
    for name, source in [('a.js', 'export function positive(value) { return value > 0; }'),
                         ('a.ts', 'export function positive(value: number): boolean { return value > 0; }')]:
        (tmp_path / name).write_text(source)
        candidates, version = stryker(tmp_path, [name], engine, Budget(time.monotonic()+20, 8))
        assert version == '9.5.1' and len(candidates) <= 8
        assert any('>= 0' in c.content for c in candidates)
        assert all(c.line == 1 and c.path == name for c in candidates)


def test_stryker_missing_engine_is_unavailable(tmp_path):
    import time
    from core.strength.engines import stryker
    from core.strength.execution import Budget
    with pytest.raises(ValueError, match='unavailable'):
        stryker(tmp_path, ['a.js'], str(tmp_path / 'missing'), Budget(time.monotonic()+10, 1))


def test_stryker_mutations_detected_and_undetected_on_real_node_tests(tmp_path):
    import time
    from core.strength.engines import stryker
    from core.strength.execution import Budget
    from core.strength.mutations import run_candidate
    from core.strength.baseline import baseline
    engine = stryker_path()
    source = 'export function positive(value) { return value > 0; }\n'
    (tmp_path / 'a.mjs').write_text(source)
    weak = "import {test} from 'node:test'; import assert from 'node:assert/strict'; import {positive} from './a.mjs'; test('positive', () => assert.equal(positive(2),true));\n"
    (tmp_path / 'a.test.mjs').write_text(weak)
    command = 'node --test a.test.mjs'
    assert baseline(command, tmp_path, tmp_path/'original', Budget(time.monotonic()+10,1),5).status == 'passed'
    items, _ = stryker(tmp_path, ['a.mjs'], engine, Budget(time.monotonic()+20,8))
    boundary = next(c for c in items if '>= 0' in c.content)
    assert run_candidate(boundary,tmp_path,command,Budget(time.monotonic()+10,1),5).status == 'undetected'
    (tmp_path / 'a.test.mjs').write_text(weak + "test('zero', () => assert.equal(positive(0),false));\n")
    assert run_candidate(boundary,tmp_path,command,Budget(time.monotonic()+10,1),5).status == 'detected'
    assert (tmp_path / 'a.mjs').read_text() == source


def test_analysis_orchestrates_general_project_and_preserves_tree(tmp_path):
    import sys, importlib.util
    from core.strength.runner import analyze
    from core.ledger import Ledger
    from core.config import Config
    if importlib.util.find_spec('cosmic_ray') is None:
        pytest.skip('optional cosmic-ray not installed')
    base = repository(tmp_path)
    (tmp_path/'a.py').write_text('def positive(value):\n    return value > 0\n')
    (tmp_path/'test_a.py').write_text('from a import positive\ndef test_value():\n    assert positive(2)\n')
    before = (tmp_path/'a.py').read_bytes()
    ledger = Ledger(root=tmp_path, task='t', base=base)
    ledger._config = Config(commands={'tests': f'"{sys.executable}" -m pytest -q -p no:cacheprovider'},
                           strength={'max_mutants': 4})
    value = analyze(ledger)
    assert value['baseline'] == 'passed' and value['attempts'] == 4
    assert value['summary']['undetected'] > 0
    assert value['state'] == 'incomplete' and any('attempt' in issue for issue in value['issues'])
    assert (tmp_path/'a.py').read_bytes() == before


def test_analysis_disabled_and_unavailable_do_not_certify(tmp_path):
    from core.strength.runner import analyze
    from core.ledger import Ledger
    from core.config import Config
    ledger = Ledger(root=tmp_path, task='t')
    ledger._config = Config(strength={'enabled': False})
    assert analyze(ledger)['state'] == 'disabled'
    ledger._config = Config()
    assert analyze(ledger)['state'] == 'incomplete'


def test_strength_reuse_needs_identical_tests_commands_and_settings(tmp_path, monkeypatch):
    import sys
    from core.strength.runner import analyze
    from core.ledger import Ledger
    from core.config import Config
    from core.strength import engines
    base = repository(tmp_path)
    (tmp_path/'a.py').write_text('value = 2\n')
    (tmp_path/'test_a.py').write_text('def test_value():\n    assert True\n')
    ledger = Ledger(root=tmp_path, task='t', base=base)
    ledger._config = Config(commands={'tests': f'"{sys.executable}" -m pytest -q -p no:cacheprovider'},
                            strength={'python': sys.executable})
    calls = []
    def generated(*args):
        calls.append(1)
        return engines.Candidates([engines.Candidate('1','a.py',1,'operator','value = 3\n')]), '8.7.0'
    monkeypatch.setattr(engines, 'cosmic', generated)
    first = analyze(ledger)
    second = analyze(ledger)
    assert first['recorded_at'] == second['recorded_at'] and len(calls) == 1
    (tmp_path/'test_a.py').write_text('def test_value():\n    assert 1 == 1\n')
    third = analyze(ledger)
    assert third['recorded_at'] != first['recorded_at'] and len(calls) == 2


def test_interrupted_strength_record_is_not_reusable(tmp_path):
    from core.strength.reuse import reusable
    assert not reusable({'state':'running'}, task='t', base='b', command='c',
                        settings={}, fingerprint='f', paths=[], versions={})


def test_strength_cli_incomplete_is_explicit_and_invalid_option_fails(tmp_path):
    import subprocess, sys, json
    script = Path('plugin/bin/ep_strength.py').resolve()
    done = subprocess.run([sys.executable, str(script), '--root', str(tmp_path), '--json'], capture_output=True, text=True)
    assert done.returncode == 2
    assert json.loads(done.stdout)['state'] == 'incomplete'
    invalid = subprocess.run([sys.executable, str(script), '--root', str(tmp_path), '--max-mutants', '-2'], capture_output=True, text=True)
    assert invalid.returncode == 2 and 'max_mutants' in invalid.stderr


def test_automatic_strength_is_shared_silent_and_passive_when_off(tmp_path, monkeypatch):
    from core.strength import runner
    from core.ledger import Ledger
    from core.config import Config
    ledger = Ledger(root=tmp_path, task='t')
    ledger._config = Config(profile='guide')
    calls = []
    monkeypatch.setattr(runner, 'analyze', lambda current: calls.append(current.task))
    assert runner.consider(ledger) is None and calls == ['t']
    ledger._config = Config(profile='off')
    runner.consider(ledger)
    assert calls == ['t']
    ledger._config = Config(strength={'enabled':False})
    runner.consider(ledger)
    assert calls == ['t']


def test_strength_report_is_read_only_and_test_edits_make_it_stale(tmp_path, monkeypatch):
    import sys, time
    from core.strength.runner import analyze
    from core.strength import engines
    from core.ledger import Ledger
    from core.config import Config, save
    from core.export import build, markdown
    base = repository(tmp_path)
    (tmp_path/'a.py').write_text('value = 2\n')
    (tmp_path/'test_a.py').write_text('def test_value():\n    assert True\n')
    config = Config(commands={'tests': f'"{sys.executable}" -m pytest -q -p no:cacheprovider'},
                    strength={'python':sys.executable})
    save(tmp_path, config)
    ledger = Ledger(root=tmp_path, task='t', base=base)
    ledger.save()
    monkeypatch.setattr(engines, 'cosmic', lambda *args: (engines.Candidates([
        engines.Candidate('1','a.py',1,'operator','value = 3\n')]), '8.7.0'))
    analyze(ledger)
    state = (tmp_path/'.elevenpowers/strength.json').read_bytes()
    report = build(tmp_path)
    assert report['test_strength']['freshness'] == 'fresh'
    assert report['test_strength']['summary']['undetected'] == 1
    assert 'possible test gaps' in markdown(report)
    assert (tmp_path/'.elevenpowers/strength.json').read_bytes() == state
    (tmp_path/'test_a.py').write_text('def test_value():\n    assert 2 == 2\n')
    assert build(tmp_path)['test_strength']['freshness'] == 'stale'


def test_saved_strength_rejects_nested_private_fields_and_invalid_state(tmp_path):
    import json
    from core.strength.store import load
    folder = tmp_path/'.elevenpowers'
    folder.mkdir()
    template = {'schema_version':1, 'task':'t', 'state':'complete', 'issues':[],
        'observations':[], 'fingerprint':'f', 'source_fingerprint':'s', 'baseline':'failed',
        'engine_versions':{}, 'base':'b', 'command':'pytest', 'settings':{}, 'paths':[],
        'recorded_at':1, 'summary':{}, 'attempts':0, 'limitations':[]}
    for update in [{'baseline':'failed'}, {'settings':{'raw_output':'secret'}}, {'issues':'not a list'}, {'attempts':-1}]:
        value = {**template, 'baseline':'passed', **update}
        (folder/'strength.json').write_text(json.dumps(value))
        assert load(tmp_path,'t')['state'] == 'incomplete'


def test_stale_task_cannot_overwrite_new_strength(tmp_path):
    from core.strength import store
    from core.ledger import Ledger
    from core import jobs
    Ledger(root=tmp_path, task='new').save()
    value = {'schema_version':1, 'task':'old', 'state':'running', 'issues':[],
        'observations':[], 'fingerprint':'', 'source_fingerprint':'', 'baseline':'not_run',
        'engine_versions':{}, 'base':'', 'command':'', 'settings':{}, 'paths':[],
        'recorded_at':1, 'summary':{}, 'attempts':0, 'limitations':[]}
    with pytest.raises(jobs.Superseded):
        store.save(tmp_path,value)


def test_strength_deadline_and_changed_inputs_are_explicit(tmp_path, monkeypatch):
    import sys
    from core.strength.runner import analyze
    from core.strength import engines
    from core.config import Config
    from core.ledger import Ledger
    base = repository(tmp_path)
    (tmp_path/'a.py').write_text('value=2\n')
    (tmp_path/'test_a.py').write_text('def test_value():\n    assert True\n')
    ledger = Ledger(root=tmp_path, task='t', base=base)
    ledger._config = Config(commands={'tests':f'"{sys.executable}" -m pytest -q -p no:cacheprovider'},
                           strength={'python':sys.executable})
    def mutate_original(*args):
        (tmp_path/'test_a.py').write_text('def test_changed():\n    assert True\n')
        return engines.Candidates([engines.Candidate('1','a.py',1,'operator','value=3\n')]), '8.7.0'
    monkeypatch.setattr(engines,'cosmic',mutate_original)
    value = analyze(ledger)
    assert value['state'] == 'incomplete' and any('inputs changed' in issue for issue in value['issues'])
    ledger._config = Config(strength={'seconds':.001})
    value = analyze(ledger)
    assert value['state'] in ('incomplete','deferred') and value['baseline'] != 'passed'


def test_shared_completion_never_emits_mutant_feedback(tmp_path, monkeypatch):
    from core import hook
    from core.strength import runner
    from core.ledger import Ledger, Status
    from core.config import Config
    from core.obligations import Claim
    from core.hosts import edits
    ledger = Ledger(root=tmp_path, task='t', claims=[Claim.DOCS_CHANGED])
    ledger._config = Config(profile='guide')
    monkeypatch.setattr(edits,'reconcile',lambda *args: None)
    monkeypatch.setattr(hook,'_since_task_opened',lambda *args: [])
    monkeypatch.setattr(Ledger,'settle',lambda *args: Status.VERIFIED)
    monkeypatch.setattr(Ledger,'status',lambda *args: Status.VERIFIED)
    monkeypatch.setattr(hook,'stress',lambda *args: ({},[]))
    monkeypatch.setattr(hook,'confirm',lambda *args: [])
    monkeypatch.setattr(hook,'snapshot',lambda *args: None)
    monkeypatch.setattr(hook,'end_report',lambda *args: 'completion')
    emitted, considered = [], []
    monkeypatch.setattr(hook,'_emit',lambda *args,**kwargs: emitted.append(kwargs))
    def analysis(current):
        considered.append(current.task)
        return {'observations':[{'operator':'secret mutant target'}]}
    monkeypatch.setattr(runner,'analyze',analysis)
    assert hook._complete_stop({},tmp_path,ledger) == 0
    assert considered == ['t'] and 'secret mutant' not in str(emitted)


@pytest.mark.parametrize('language', ['python', 'javascript', 'typescript'])
def test_real_engine_project_acceptance_weak_then_strong(tmp_path, language):
    import sys, importlib.util
    from core.strength.runner import analyze
    from core.ledger import Ledger
    from core.config import Config
    source_file = 'a.py' if language == 'python' else 'a.ts' if language == 'typescript' else 'a.mjs'
    base = repository(tmp_path, source_file)
    strength = {'max_mutants':8, 'seconds':45, 'test_seconds':10}
    if language == 'python':
        if importlib.util.find_spec('cosmic_ray') is None:
            pytest.skip('optional Cosmic Ray missing')
        source = 'def positive(value):\n    return value > 0\n'
        target = tmp_path/'a.py'
        test = tmp_path/'test_a.py'
        weak = 'from a import positive\ndef test_value():\n    assert positive(2)\n'
        strong = weak + '\ndef test_boundaries():\n    assert not positive(-1)\n    assert not positive(0)\n    assert positive(1)\n'
        command = f'"{sys.executable}" -m pytest -q -p no:cacheprovider'
    else:
        strength['stryker'] = stryker_path()
        name = 'a.ts' if language == 'typescript' else 'a.mjs'
        target = tmp_path/name
        source = ('export function positive(value: number): boolean { return value > 0; }\n'
                  if language == 'typescript' else 'export function positive(value) { return value > 0; }\n')
        test = tmp_path/'a.test.mjs'
        weak = "import {test} from 'node:test'; import assert from 'node:assert/strict'; import {positive} from './"+name+"'; test('positive', () => assert.equal(positive(2),true));\n"
        strong = weak + "test('boundaries', () => { assert.equal(positive(-1),false); assert.equal(positive(0),false); assert.equal(positive(1),true); });\n"
        command = 'node ' + ('--experimental-strip-types ' if language == 'typescript' else '') + '--test a.test.mjs'
    target.write_text(source)
    test.write_text(weak)
    before = target.read_bytes()
    ledger = Ledger(root=tmp_path, task='acceptance-'+language, base=base)
    ledger._config = Config(commands={'tests':command}, strength=strength)
    observed_weak = analyze(ledger)
    assert observed_weak['state'] == 'complete', observed_weak['issues']
    assert observed_weak['summary']['undetected'] > 0
    test.write_text(strong)
    observed_strong = analyze(ledger)
    assert observed_strong['state'] == 'complete', observed_strong['issues']
    assert observed_strong['summary']['undetected'] == 0
    assert observed_strong['summary']['detected'] > 0
    assert target.read_bytes() == before


@pytest.mark.parametrize('dependencies', [None, 4])
def test_bad_optional_dependencies_never_interrupt_completion(tmp_path, dependencies):
    from core.strength.runner import consider
    from core.config import Config
    from core.ledger import Ledger
    ledger = Ledger(root=tmp_path, task='t')
    ledger._config = Config(strength={'dependencies':dependencies})
    assert consider(ledger) is None
    assert any(d['what'] == 'test strength incomplete' for d in ledger.decisions)


def test_each_mutation_starts_with_clean_test_inputs(tmp_path, monkeypatch):
    import sys
    from core.strength.runner import analyze
    from core.strength import engines
    from core.ledger import Ledger
    from core.config import Config
    base = repository(tmp_path)
    (tmp_path/'a.py').write_text('value=2\n')
    (tmp_path/'secondary.txt').write_text('clean')
    (tmp_path/'test_a.py').write_text("from pathlib import Path\nfrom a import value\ndef test_value():\n    assert not Path('marker').exists()\n    assert Path('secondary.txt').read_text() == 'clean'\n    Path('marker').write_text('created')\n    Path('secondary.txt').write_text('changed')\n    assert value > 0\n")
    ledger = Ledger(root=tmp_path, task='t', base=base)
    ledger._config = Config(commands={'tests':f'"{sys.executable}" -m pytest -q -p no:cacheprovider'},
                           strength={'python':sys.executable})
    monkeypatch.setattr(engines,'cosmic',lambda *args:(engines.Candidates([
        engines.Candidate('1','a.py',1,'op','value=3\n'), engines.Candidate('2','a.py',1,'op','value=4\n')]), '8.7.0'))
    value = analyze(ledger)
    assert value['baseline'] == 'passed' and value['summary']['undetected'] == 2
    assert value['summary']['detected'] == 0 and value['state'] == 'complete'
    assert (tmp_path/'secondary.txt').read_text() == 'clean' and not (tmp_path/'marker').exists()


def test_editable_python_paths_make_isolation_explicitly_incomplete(tmp_path):
    import subprocess, sys, sysconfig, time
    from core.strength.baseline import baseline
    from core.strength.execution import Budget
    original, copied, environment = (tmp_path/name for name in ('original','copied','environment'))
    for folder in (original,copied):
        (folder/'src/pkg').mkdir(parents=True)
        (folder/'src/pkg/__init__.py').write_text('value=2\n')
    (copied/'test_a.py').write_text('import pkg\ndef test_value():\n    assert pkg.value == 2\n')
    subprocess.run([sys.executable,'-m','venv','--without-pip',str(environment)],check=True,capture_output=True)
    python = environment/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
    info = subprocess.run([str(python),'-c','import sysconfig; print(sysconfig.get_paths()["purelib"])'],
                          check=True,capture_output=True,text=True)
    site = Path(info.stdout.strip())
    (site/'source.pth').write_text(str(original/'src')+'\n'+sysconfig.get_paths()['purelib']+'\n')
    value = baseline(f'"{python}" -m pytest -q -p no:cacheprovider', copied, original,
                     Budget(time.monotonic()+20,1),10)
    assert value.status == 'incomplete' and 'original' in value.reason
