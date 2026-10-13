"""Actual explicit binding CLI writes only local approval, never external bytes."""
import json
from pathlib import Path
import subprocess
import sys
import shutil

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


def test_busy_approval_reports_controlled_failure_without_traceback(tmp_path):
    from core.inputs.bindings import bind
    from core.jobs import ledger_write
    root = tmp_path/'project'; root.mkdir(); policy(root)
    directory = tmp_path/'deps'; directory.mkdir()
    bind(root,'deps',directory)
    with ledger_write(root):
        done = subprocess.run([sys.executable,'-I','-B',str(CLI),'bind','--project',str(root),
                               '--name','deps','--path',str(directory)],capture_output=True,text=True,timeout=15)
    assert done.returncode == 2
    assert 'Traceback' not in done.stderr and str(directory) not in done.stderr


def test_cold_inspection_is_read_only_and_explicit_gate_distinguishes_incomplete(tmp_path):
    from core.inputs.bindings import bind
    from tests.test_input_collection import snapshot
    root = tmp_path/'project'; root.mkdir(); policy(root)
    directory = tmp_path/'deps'; directory.mkdir()
    (directory/'parser.py').write_bytes(b'value=2\n')
    bind(root,'deps',directory)
    source = CLI.parents[2]
    shutil.copytree(source/'core',root/'core',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    target = root/'plugin/bin/ep_inputs.py'; target.parent.mkdir(parents=True)
    shutil.copy2(CLI,target)
    before = snapshot(root)
    args = [sys.executable,'-I',str(target),'inspect','--project',str(root),'--check']
    done = subprocess.run(args,capture_output=True,text=True,timeout=30)
    assert done.returncode == 0, done.stderr
    value = json.loads(done.stdout)
    assert value['state'] == 'available' and str(directory) not in done.stdout
    assert snapshot(root) == before and not list(root.rglob('*.pyc'))
    (directory/'parser.py').unlink()
    missing = subprocess.run(args,capture_output=True,text=True,timeout=30)
    assert missing.returncode == 1
    assert json.loads(missing.stdout)['state'] == 'incomplete'
