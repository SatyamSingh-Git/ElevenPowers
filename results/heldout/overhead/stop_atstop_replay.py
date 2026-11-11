"""Replay a held-out assisted run through the real hook from its base tree, and time
Stop with the default config and with strength.at_stop set. Usage: <slot>..."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOOK = r'E:\ElevenPowers\plugin\bin\ep_hook.py'
SWEEP = Path('E:/ep-installed/heldout-sweep')
tasks = {t['name']: t for t in json.loads(Path('E:/ElevenPowers/results/heldout/corpus.json').read_text(encoding='utf-8'))['tasks']}


def replay(slot, strength):
    task = tasks[slot.split('--')[0]]
    source = SWEEP / slot / 'work'
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / 'work'
        shutil.copytree(source, work, symlinks=True)
        changed = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=work, capture_output=True, text=True, check=True).stdout.split()
        final = {p: (work / p).read_bytes() if (work / p).exists() else None for p in changed}
        subprocess.run(['git', 'reset', '-q', '--hard', 'HEAD'], cwd=work, check=True)
        state = work / '.elevenpowers'
        config = json.loads((state / 'config.json').read_text(encoding='utf-8'))
        config['strength'] = strength
        shutil.rmtree(state)
        state.mkdir()
        (state / 'config.json').write_text(json.dumps(config), encoding='utf-8')
        env = {**os.environ, **task['env'], 'CLAUDE_PROJECT_DIR': str(work)}
        env['PATH'] = str(Path(task['python']).parent) + os.pathsep + env['PATH']

        def hook(event, **extra):
            payload = {'session_id': 's', 'transcript_path': '', 'cwd': str(work), 'hook_event_name': event, **extra}
            start = time.perf_counter()
            done = subprocess.run([sys.executable, HOOK, event], input=json.dumps(payload), text=True, cwd=work,
                                  capture_output=True, env=env)
            return time.perf_counter() - start, done

        print('SessionStart', round(hook('SessionStart', source='startup')[0], 1), flush=True)
        print('UserPromptSubmit', round(hook('UserPromptSubmit', prompt=task['prompt'])[0], 1), flush=True)
        for relative, content in final.items():
            target = work / relative
            edit = {'tool_name': 'Edit', 'tool_input': {'file_path': str(target), 'old_string': 'a', 'new_string': 'b'}}
            print('PreToolUse', round(hook('PreToolUse', **edit)[0], 1), flush=True)
            target.parent.mkdir(parents=True, exist_ok=True)
            if content is None:
                target.unlink()
            else:
                target.write_bytes(content)
            print('PostToolUse', round(hook('PostToolUse', **edit, tool_response={'filePath': str(target)})[0], 1), flush=True)
        seconds, done = hook('Stop', last_assistant_message='Done. The tests pass.')
        checks = json.loads((state / 'verification.json').read_text(encoding='utf-8'))['checks']
        phases = {}
        for c in checks:
            if c.get('finished') and c.get('started'):
                phases[c['phase']] = round(phases.get(c['phase'], 0) + c['finished'] - c['started'], 1)
        decision = json.loads(done.stdout).get('decision', 'allow') if done.stdout.strip().startswith('{') else done.stdout[:80]
        return round(seconds, 1), phases, decision


for slot in sys.argv[1:]:
    for label, strength in (('default', {}), ('at_stop', {'at_stop': True})):
        seconds, phases, decision = replay(slot, strength)
        print(json.dumps({'slot': slot, 'config': label, 'stop_seconds': seconds, 'decision': decision, 'phases': phases}))
