import json
from pathlib import Path
import subprocess
import sys

from test_patchproof_openapi import engine, project, spec

CLI = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_contract.py'


def invoke(root, engine, *args):
    return subprocess.run([sys.executable, str(CLI), '--project', str(root),
        '--id', 'api', '--engine', str(engine), *args], capture_output=True, encoding='utf-8', timeout=60)


def test_real_cli_json_and_privacy(tmp_path, engine):
    root = project(tmp_path / 'project')
    done = invoke(root, engine, '--format', 'json')
    assert done.returncode == 0, done.stderr
    value = json.loads(done.stdout)
    assert value['result'] == 'pass' and 'executable' not in value['producer']
    assert str(engine) not in done.stdout


def test_real_cli_incompatible_and_incomplete_exits(tmp_path, engine):
    root = project(tmp_path / 'project', spec({}))
    assert invoke(root, engine).returncode == 1
    assert invoke(root, engine, '--seconds', '0').returncode == 2


def test_explicit_output_refuses_overwrite_and_allows_force(tmp_path, engine):
    root = project(tmp_path / 'project')
    output = tmp_path / 'observation.json'
    output.write_text('keep')
    assert invoke(root, engine, '--format', 'json', '--output', str(output)).returncode == 2
    assert output.read_text() == 'keep'
    assert invoke(root, engine, '--format', 'json', '--output', str(output), '--force').returncode == 0
    assert json.loads(output.read_text())['execution'] == 'complete'
