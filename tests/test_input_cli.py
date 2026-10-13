"""Actual explicit binding CLI writes only local approval, never external bytes."""
import json
from pathlib import Path
import subprocess
import sys

from tests.test_input_definitions import policy

CLI = Path(__file__).resolve().parents[1]/'plugin/bin/ep_inputs.py'


def test_binding_cli_approves_declared_root_without_exporting_private_path(tmp_path):
    root = tmp_path/'project'; root.mkdir(); policy(root)
    directory = tmp_path/'private dependency'; directory.mkdir()
    (directory/'parser.py').write_text('value=2\n')
    before = (directory/'parser.py').read_bytes()
    args = [sys.executable, '-I', '-B', str(CLI), 'bind', '--project', str(root),
            '--name', 'deps', '--path', str(directory)]
    done = subprocess.run(args, capture_output=True, text=True, timeout=20)
    assert done.returncode == 0, done.stderr
    value = json.loads(done.stdout)
    assert value == {'root':'deps','state':'bound'}
    assert str(directory) not in done.stdout
    assert (directory/'parser.py').read_bytes() == before
    assert json.loads((root/'.elevenpowers/input-roots.json').read_text())['roots']['deps'] == str(directory.resolve())


def test_binding_cli_refuses_undeclared_root_without_state_write(tmp_path):
    root = tmp_path/'project'; root.mkdir(); policy(root)
    directory = tmp_path/'deps'; directory.mkdir()
    done = subprocess.run([sys.executable, '-I', '-B', str(CLI), 'bind', '--project', str(root),
                           '--name', 'unknown', '--path', str(directory)], capture_output=True, text=True, timeout=20)
    assert done.returncode == 2
    assert 'input approval unavailable' in done.stderr.lower()
    assert not (root/'.elevenpowers').exists()
