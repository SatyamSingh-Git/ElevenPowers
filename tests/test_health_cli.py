"""Explicit acceptance CLI writes and read-only modes."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

SOURCE = Path(__file__).resolve().parents[1]
CLI = [sys.executable, str(SOURCE / 'plugin/bin/ep_doctor.py')]


def test_doctor_prepares_only_explicit_destination_and_inspects_read_only(tmp_path):
    root = tmp_path / 'exercise'
    done = subprocess.run([*CLI, '--prepare-acceptance', str(root), '--platform', 'codex',
                           '--language', 'python', '--host-version', 'operator-version', '--json'],
                          capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stdout + done.stderr
    assert json.loads(done.stdout)['state'] == 'prepared'
    before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    done = subprocess.run([*CLI, '--acceptance', str(root), '--platform', 'codex', '--json'],
                          capture_output=True, text=True, timeout=30)
    assert done.returncode == 1 and json.loads(done.stdout)['state'] == 'waiting'
    assert before == {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('options', [
    ['--acceptance'], ['--platform'], ['--host', '--platform', 'codex'],
    ['--language', 'python'], ['--host-version', 'wrong'],
    ['--acceptance', 'missing'], ['--seconds', '2'],
    ['--prepare-acceptance', 'unused', '--platform', 'codex', '--acceptance', 'unused'],
])
def test_doctor_refuses_ambiguous_or_incomplete_flags(tmp_path, options):
    done = subprocess.run([*CLI, *options], cwd=tmp_path, capture_output=True, text=True, timeout=20)
    assert done.returncode == 2, done.stdout + done.stderr
    assert not (tmp_path / 'unused').exists()


def test_existing_platform_configuration_mode_is_preserved(tmp_path):
    from core.hosts.setup import install
    install('codex', tmp_path, sys.executable, SOURCE)
    done = subprocess.run([*CLI, '--cwd', str(tmp_path), '--platform', 'codex'],
                          capture_output=True, text=True, timeout=30)
    assert done.returncode == 0 and 'Live host session: not verified' in done.stdout
