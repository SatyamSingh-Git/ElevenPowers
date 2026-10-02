import sys

import pytest

from core.hosts import probes


def test_actual_version_producers(tmp_path):
    script = tmp_path / 'version.py'
    script.write_text("print('Codex CLI 0.159.2')")
    value = probes._probe([sys.executable, str(script)], tmp_path, 10)
    assert value == {'state': 'observed', 'version': '0.159.2', 'source': 'installed_probe'}
    assert str(tmp_path) not in str(value)
    script.write_text("print('secret 1.2.3 and 4.5.6')")
    assert probes._probe([sys.executable, str(script)], tmp_path, 10)['state'] == 'incomplete'
    script.write_text("print('1.2.3'); raise SystemExit(1)")
    assert probes._probe([sys.executable, str(script)], tmp_path, 10)['state'] == 'incomplete'
    script.write_text('import time; time.sleep(5)')
    assert probes._probe([sys.executable, str(script)], tmp_path, .1)['state'] == 'incomplete'


def test_no_host_launch_without_available_executable(monkeypatch):
    monkeypatch.setattr(probes.shutil, 'which', lambda name: None)
    assert probes.probe('codex')['state'] == 'missing'
    with pytest.raises(ValueError):
        probes.probe('madeup')
    with pytest.raises(ValueError):
        probes.probe('codex', timeout=float('nan'))
