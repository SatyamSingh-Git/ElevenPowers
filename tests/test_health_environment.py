"""Optional metadata availability must not execute or import engines."""
import json

from core.config import Config


def test_pinned_engine_metadata_and_missing_runtime_are_explicit(tmp_path, monkeypatch):
    from core.health import _engines
    path = tmp_path / 'node_modules/@stryker-mutator/instrumenter'
    path.mkdir(parents=True)
    (path / 'package.json').write_text('{"version":"9.5.1"}')
    monkeypatch.setattr('importlib.metadata.version', lambda name: '8.7.0')
    monkeypatch.setattr('shutil.which', lambda name: None)
    value = _engines(tmp_path, Config())
    assert value['cosmic_ray']['state'] == 'metadata_present'
    assert value['stryker']['state'] == 'runtime_missing'
    assert value['stryker']['version'] == '9.5.1'


def test_custom_interpreter_and_malformed_engine_metadata_remain_unchecked(tmp_path, monkeypatch):
    from core.health import _engines
    monkeypatch.setattr('importlib.metadata.version', lambda name: (_ for _ in ()).throw(AssertionError('wrong interpreter metadata')))
    path = tmp_path / 'node_modules/@stryker-mutator/instrumenter'
    path.mkdir(parents=True)
    (path / 'package.json').write_text('{bad')
    value = _engines(tmp_path, Config(strength={'python': '/custom/python'}))
    assert value['cosmic_ray']['state'] == 'unchecked'
    assert value['stryker']['state'] == 'incomplete'


def test_disabled_engines_require_no_metadata_or_execution(tmp_path, monkeypatch):
    from core.health import _engines
    monkeypatch.setattr('importlib.metadata.version', lambda *a: (_ for _ in ()).throw(AssertionError('metadata lookup')))
    assert _engines(tmp_path, Config(strength={'enabled': False})) == {'state': 'disabled'}
