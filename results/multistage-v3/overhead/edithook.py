"""Time Pre+PostToolUse for one Edit and PostToolUse for one Read on a copy of a real
end-of-conversation work tree (its .elevenpowers state as the run left it), and on
the same tree with that state reset to the config only. Unloaded, one at a time.
Usage: edithook.py <conversation folder> <new scratch dir>."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HOOK = str(Path(__file__).resolve().parents[3] / 'plugin' / 'bin' / 'ep_hook.py')
source, scratch = Path(sys.argv[1]), Path(sys.argv[2])


def hook(work, event, **extra):
    payload = {'session_id': 's', 'transcript_path': '', 'cwd': str(work), 'hook_event_name': event, **extra}
    start = time.perf_counter()
    subprocess.run([sys.executable, HOOK, event], input=json.dumps(payload), text=True, cwd=work,
                   capture_output=True, env={**os.environ, 'CLAUDE_PROJECT_DIR': str(work)})
    return time.perf_counter() - start


for label in ('state as left', 'config only'):
    work = scratch / source.name / label.replace(' ', '-')
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(source / 'work', work)
    if label == 'config only':
        config = (work / '.elevenpowers/config.json').read_bytes()
        shutil.rmtree(work / '.elevenpowers')
        (work / '.elevenpowers').mkdir()
        (work / '.elevenpowers/config.json').write_bytes(config)
    ledger = work / '.elevenpowers/ledger.json'
    size = ledger.stat().st_size if ledger.exists() else 0
    target = next(p for p in sorted((work / 'src').rglob('*.py')) if p.stat().st_size > 200)
    edits, reads = [], []
    for _ in range(5):
        use = {'file_path': str(target), 'old_string': 'a', 'new_string': 'a'}
        edits.append(hook(work, 'PreToolUse', tool_name='Edit', tool_input=use)
                     + hook(work, 'PostToolUse', tool_name='Edit', tool_input=use, tool_response={'filePath': str(target)}))
        reads.append(hook(work, 'PostToolUse', tool_name='Read', tool_input={'file_path': str(target)},
                          tool_response={'file': {'filePath': str(target)}}))
    print(f'{label:14} ledger {size:>8} bytes  Edit pre+post {sorted(edits)[2]:.2f} s  Read post {sorted(reads)[2]:.2f} s (medians of 5)')
