"""The shipped CLI separates read-only planning from explicit execution."""
import json
from pathlib import Path
import subprocess
import sys

from tests.test_patchproof_execution import runnable
from tests.test_process import alive

CLI = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_patchproof.py'


def invoke(root, base, head, *args):
    return subprocess.run([sys.executable, '-S', str(CLI), '--project', str(root),
        '--base', base, '--head', head, *args], capture_output=True, text=True,
        encoding='utf-8', timeout=150)


def test_ordinary_report_and_plan_never_execute(runnable):
    root, base, head, _ = runnable
    ordinary = invoke(root, base, head, '--format', 'json')
    assert ordinary.returncode == 0
    planned = invoke(root, base, head, '--plan', '--format', 'json')
    assert planned.returncode == 0, planned.stderr
    assert json.loads(planned.stdout)['kind'] == 'patchproof_plan'
    assert not (root / '.elevenpowers/count.txt').exists()
    assert not (root / '.elevenpowers/patch-verification.json').exists()


def test_verify_exports_actual_associations_and_qualified_reuse(runnable):
    root, base, head, _ = runnable
    first = invoke(root, base, head, '--verify', '--seconds', '120', '--command-seconds', '5', '--format', 'json')
    assert first.returncode == 0, first.stderr + first.stdout
    value = json.loads(first.stdout)
    assert value['state'] == 'passed'
    assert value['bundle']['execution']['checks'][0]['executed_at_patch_head'] == head
    readable = invoke(root, base, head, '--verify', '--seconds', '120')
    assert readable.returncode == 0, readable.stderr + readable.stdout
    assert 'reused' in readable.stdout
    assert 'verified actual behavior' not in readable.stdout
    assert (root / '.elevenpowers/count.txt').read_text() == '1'


def test_incomplete_and_invalid_cli_budgets_are_distinct_from_success(runnable):
    root, base, head, _ = runnable
    exhausted = invoke(root, base, head, '--verify', '--seconds', '0', '--format', 'json')
    assert exhausted.returncode == 2
    assert json.loads(exhausted.stdout)['state'] == 'incomplete'
    invalid = invoke(root, base, head, '--verify', '--command-seconds', 'nan')
    assert invalid.returncode != 0
    assert not (root / '.elevenpowers/count.txt').exists()
    both = invoke(root, base, head, '--plan', '--verify')
    assert both.returncode == 2


def test_output_refusal_happens_before_explicit_commands(runnable):
    root, base, head, _ = runnable
    output = root.parent / 'existing-result.json'
    output.write_text('keep original')
    done = invoke(root, base, head, '--verify', '--output', str(output))
    assert done.returncode != 0
    assert output.read_text() == 'keep original'
    assert not (root / '.elevenpowers/count.txt').exists()


def test_real_interruption_retains_completed_progress_and_stops_child(runnable):
    import os
    import signal
    import time
    from core.config import Config, save
    from tests.test_patchproof_identity import commit
    root, base, head, command = runnable
    (root / 'long.py').write_text(
        "import os,time\nfrom pathlib import Path\n"
        "p=Path('.elevenpowers/child.pid'); marker=Path('.elevenpowers/long-started')\n"
        "p.write_text(str(os.getpid()))\n"
        "if not marker.exists():\n marker.touch()\n time.sleep(60)\n")
    head = commit(root, 'interruption control')
    save(root, Config(auto_detect=False, commands={'tests': command, 'build': f'"{sys.executable}" -B long.py'}))
    with (root / '.elevenpowers/cli-out.txt').open('w') as output:
        child = subprocess.Popen([sys.executable, '-S', str(CLI), '--project', str(root),
            '--base', base, '--head', head, '--verify'], stdout=output, stderr=output)
        try:
            deadline = time.monotonic() + 90
            while not (root / '.elevenpowers/long-started').exists() and time.monotonic() < deadline:
                assert child.poll() is None, (root / '.elevenpowers/cli-out.txt').read_text()
                time.sleep(.05)
            assert (root / '.elevenpowers/long-started').exists()
            os.kill(child.pid, signal.SIGTERM)
            child.wait(timeout=15)
        finally:
            if child.poll() is None:
                child.kill(); child.wait(timeout=15)
    pid = int((root / '.elevenpowers/child.pid').read_text())
    deadline = time.monotonic() + 5
    while alive(pid) and time.monotonic() < deadline:
        time.sleep(.02)
    assert not alive(pid), 'command survived actual CLI termination'
    saved = json.loads((root / '.elevenpowers/patch-verification.json').read_text())
    assert saved['attempts'][-1]['status'] == 'incomplete'
    assert saved['attempts'][0]['status'] == 'passed'
    resumed = invoke(root, base, head, '--verify', '--format', 'json')
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    value = json.loads(resumed.stdout)
    assert [c['status'] for c in value['checks']] == ['reused', 'passed']
    assert (root / '.elevenpowers/count.txt').read_text() == '1'
