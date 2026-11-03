"""Time each hook of a replayed v3 stage: the pre-stage snapshot is committed, the
stage's request is submitted, the post-stage files are written with Edit events,
and Stop runs. Usage: stopreplay.py <conversation folder> <stage> <scratch dir>."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HOOK = r'E:\ElevenPowers\plugin\bin\ep_hook.py'
conversation, n, scratch = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
case = json.loads((Path(r'E:\ElevenPowers\eval\multistage_v3') / conversation.name.split('--')[0] / 'case.json')
                  .read_text(encoding='utf-8'))
work = scratch / f'{conversation.name}-{n}'
shutil.rmtree(work, ignore_errors=True)
shutil.copytree(conversation / 'snapshots' / str(n - 1), work)
(work / '.elevenpowers').mkdir()
shutil.copy(conversation / 'work' / '.elevenpowers' / 'config.json', work / '.elevenpowers' / 'config.json')
for args in (['-c', 'core.autocrlf=false', 'init', '-q'], ['add', '-A'], ['-c', 'user.name=r', '-c', 'user.email=r@r', 'commit', '-qm', 'base']):
    subprocess.run(['git', *args], cwd=work, check=True)


def hook(event, **extra):
    payload = {'session_id': 's', 'transcript_path': '', 'cwd': str(work), 'hook_event_name': event, **extra}
    start = time.perf_counter()
    done = subprocess.run([sys.executable, HOOK, event], input=json.dumps(payload), text=True, cwd=work,
                          capture_output=True, env={**os.environ, 'CLAUDE_PROJECT_DIR': str(work)})
    return time.perf_counter() - start, done


timings = {}
timings['SessionStart'] = hook('SessionStart', source='startup')[0]
timings['UserPromptSubmit'] = hook('UserPromptSubmit', prompt=case['stages'][n - 1]['request'])[0]
after = conversation / 'snapshots' / str(n)
changed = []
for path in after.rglob('*'):
    if path.is_file():
        relative = path.relative_to(after)
        target = work / relative
        if not target.exists() or target.read_bytes() != path.read_bytes():
            changed.append(relative)
edits = 0.0
for relative in changed:
    target = work / relative
    edits += hook('PreToolUse', tool_name='Edit', tool_input={'file_path': str(target), 'old_string': 'a', 'new_string': 'b'})[0]
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(after / relative, target)
    edits += hook('PostToolUse', tool_name='Edit', tool_input={'file_path': str(target), 'old_string': 'a', 'new_string': 'b'},
                  tool_response={'filePath': str(target)})[0]
timings[f'Edit hooks ({len(changed)} files)'] = edits
seconds, done = hook('Stop', last_assistant_message='Done. The tests pass.')
timings['Stop'] = seconds
print(json.dumps({k: round(v, 2) for k, v in timings.items()}))
print(done.stdout[:1500])
checks = json.loads((work / '.elevenpowers' / 'verification.json').read_text(encoding='utf-8'))['checks']
for check in checks:
    print(f"  {check['phase']:28} {check['status']:10} {check.get('finished', 0) - check.get('started', 0):6.2f}s")
