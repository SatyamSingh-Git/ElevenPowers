"""Real shipped-launcher recovery, with no model or host installation required."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from core.config import Config, save
from core.jobs import read
from core.ledger import Ledger
from core.obligations import Claim, Risk

LAUNCHER = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_hook.py'


def test_launcher_recovers_after_host_death_without_rerunning_completed_check(tmp_path):
    (tmp_path/'source.py').write_text('value = 1')
    (tmp_path/'first.py').write_text(
        'from pathlib import Path\n'
        'p=Path(".elevenpowers/first-count.txt")\n'
        'p.write_text(str(int(p.read_text())+1) if p.exists() else "1")\n'
        'print("TAP version 13\\nok 1 - works\\n1..1\\n# pass 1\\n# fail 0")\n')
    (tmp_path/'second.py').write_text(
        'from pathlib import Path\nimport time\n'
        'p=Path(".elevenpowers/second-started.txt")\n'
        'if not p.exists():\n p.write_text("yes")\n time.sleep(60)\n'
        'print("typecheck complete")\n')
    commands = {key:f'"{sys.executable}" {script}.py' for key, script in
                [('tests','first'), ('typecheck','second')]}
    save(tmp_path, Config(profile='guide', commands=commands, auto_detect=False))
    Ledger(root=tmp_path, task='recovery-task', request='add this feature',
           claims=[Claim.FEATURE_ADDED], risk=Risk.MEDIUM).save()
    payload = json.dumps({'cwd':str(tmp_path), 'last_assistant_message':'implemented'})
    child = subprocess.Popen([sys.executable,str(LAUNCHER),'Stop'], cwd=tmp_path,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    child.stdin.write(payload)
    child.stdin.close()
    owner = None
    try:
        deadline = time.monotonic()+15
        while time.monotonic()<deadline:
            data=read(tmp_path)
            owner=data.get('pid')
            if (tmp_path/'.elevenpowers/second-started.txt').exists():
                break
            if child.poll() is not None:
                raise AssertionError(child.stderr.read())
            time.sleep(.02)
        else:
            raise AssertionError('second command never started')
        assert any(e.command == commands['tests'] and e.execution=='complete'
                   for e in Ledger.load(tmp_path).evidence)
        os.kill(owner, signal.SIGTERM)
        child.wait(timeout=10)
    finally:
        if child.poll() is None:
            os.kill(owner or child.pid, signal.SIGTERM)
            child.wait(timeout=10)
        child.stdout.close()
        child.stderr.close()
    resumed = subprocess.run([sys.executable,str(LAUNCHER),'Stop'], cwd=tmp_path,
        input=payload, capture_output=True, text=True, timeout=20)
    assert resumed.returncode == 0, resumed.stderr
    assert (tmp_path/'.elevenpowers/first-count.txt').read_text() == '1'
    journal = read(tmp_path)
    assert any(c['status']=='incomplete' for c in journal['checks'])
    assert any(c['command']==commands['typecheck'] and c['status']=='passed'
               for c in journal['checks'])
    assert Ledger.load(tmp_path).evidence[-1].execution == 'complete'
