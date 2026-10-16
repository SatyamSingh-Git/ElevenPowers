"""Exercise the public CLI and an outer shell with its own successful exit."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from core.config import Config, save
from core.evidence import Result
from core.ledger import Ledger
from core.parsers import parse

CLI = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_check.py'


def fixture(root, exit_code=1):
    (root / 'check.py').write_text(f"print('ok 1 - check' if {exit_code} == 0 else 'not ok 1 - broken')\nraise SystemExit({exit_code})\n")
    command = f'"{sys.executable}" check.py'
    save(root, Config(profile='guide', commands={'tests': command}, auto_detect=False))
    Ledger(root=root, task='test-cli').save()


def test_successful_outer_shell_cannot_replace_owned_failure(tmp_path):
    fixture(tmp_path)
    invocation = f'"{sys.executable}" "{CLI}" tests --project "{tmp_path}" --json'
    command = invocation + (' & echo outer-complete' if os.name == 'nt' else '; echo outer-complete')
    done = subprocess.run(command, cwd=tmp_path, shell=True, capture_output=True, text=True, timeout=30)
    assert done.returncode == 0
    ledger = Ledger.load(tmp_path)
    rows = [e for e in ledger.evidence if e.declaration == 'tests']
    assert rows and rows[-1].result is Result.FAIL
    assert rows[-1].execution == 'complete'
    # The ordinary outer command/output must not manufacture a declared receipt.
    ledger.add(parse(command, done.stdout, done.returncode, tmp_path)); ledger.save()
    rows = [e for e in Ledger.load(tmp_path).evidence if e.declaration == 'tests']
    assert rows[-1].result is Result.FAIL


@pytest.mark.parametrize('code,state', [(0, 'passed'), (1, 'failed')])
def test_cli_reports_real_child_outcome(tmp_path, code, state):
    fixture(tmp_path, code)
    done = subprocess.run([sys.executable, str(CLI), 'tests', '--project', str(tmp_path), '--json'],
                          capture_output=True, text=True, timeout=30)
    assert done.returncode == code
    value = json.loads(done.stdout)
    assert value['state'] == state and value['exit_code'] == code
    assert 'not ok 1' not in done.stdout and 'stdout' not in value and 'stderr' not in value


def test_listing_does_not_create_private_state(tmp_path):
    (tmp_path / 'package.json').write_text(json.dumps({'scripts': {'test': 'node check.mjs'}}))
    done = subprocess.run([sys.executable, str(CLI), '--list', '--project', str(tmp_path), '--json'],
                          capture_output=True, text=True, timeout=15)
    assert done.returncode == 0
    assert json.loads(done.stdout)['commands'] == {'tests': 'npm run test'}
    assert not (tmp_path / '.elevenpowers').exists()


@pytest.mark.parametrize('args', [['unknown'], ['tests','--seconds','0'], ['tests','--seconds','nan'], ['tests','--list']])
def test_cli_refuses_invalid_request(tmp_path, args):
    fixture(tmp_path)
    done = subprocess.run([sys.executable, str(CLI), *args, '--project', str(tmp_path)],
                          capture_output=True, text=True, timeout=15)
    assert done.returncode == 2
    assert "can't open file" not in done.stderr
    assert not Ledger.load(tmp_path).evidence


def test_public_result_excludes_captured_credentials(tmp_path):
    (tmp_path / 'check.py').write_text("print('password=private-output-secret'); print('ok 1 - check')\n")
    save(tmp_path, Config(profile='guide', commands={'tests': f'"{sys.executable}" check.py'}, auto_detect=False))
    done = subprocess.run([sys.executable, str(CLI), 'tests', '--project', str(tmp_path), '--json'],
                          capture_output=True, text=True, timeout=30)
    assert done.returncode == 0
    assert 'private-output-secret' not in done.stdout + done.stderr


def test_terminated_cli_retains_provisional_attempt(tmp_path):
    fixture(tmp_path, 0)
    (tmp_path / 'check.py').write_text("from pathlib import Path\nimport time\nPath('.elevenpowers/started').write_text('yes')\ntime.sleep(30)\n")
    child = subprocess.Popen([sys.executable, str(CLI), 'tests', '--project', str(tmp_path)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 15
        while not (tmp_path / '.elevenpowers/started').exists() and time.monotonic() < deadline:
            if child.poll() is not None:
                pytest.fail('CLI exited before launching controlled child: ' + str(child.communicate()))
            time.sleep(.02)
        assert (tmp_path / '.elevenpowers/started').exists()
        child.terminate(); child.communicate(timeout=10)
        records = [e for e in Ledger.load(tmp_path).evidence if e.declaration == 'tests']
        assert records and records[-1].execution == 'incomplete'
        assert records[-1].result is not Result.PASS
    finally:
        if child.poll() is None:
            child.kill(); child.communicate(timeout=10)
