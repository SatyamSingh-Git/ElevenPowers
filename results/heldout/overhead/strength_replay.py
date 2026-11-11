import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SWEEP = Path('E:/ep-installed/heldout-sweep')
RUNTIME = Path('E:/ElevenPowers')
SLOTS = sys.argv[1:]

for slot in SLOTS:
    work = SWEEP / slot / 'work'
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / 'work'
        shutil.copytree(work, copy, symlinks=True)
        env = dict(os.environ)
        venv = copy / '.venv' / 'Scripts'
        if venv.is_dir():
            env['PATH'] = str(venv) + os.pathsep + env['PATH']
        start = time.monotonic()
        out = subprocess.run([sys.executable, str(RUNTIME / 'plugin/bin/ep_strength.py'), '--root', str(copy), '--json'],
                             capture_output=True, text=True, env=env, cwd=copy)
        seconds = time.monotonic() - start
        try:
            value = json.loads(out.stdout)
            print(json.dumps({'slot': slot, 'seconds': round(seconds, 1), 'state': value['state'],
                              'attempts': value['attempts'], 'baseline': value['baseline'],
                              'issues': [i[:70] for i in value['issues']]}))
        except ValueError:
            print(json.dumps({'slot': slot, 'seconds': round(seconds, 1), 'stdout': out.stdout[-300:], 'stderr': out.stderr[-300:]}))
