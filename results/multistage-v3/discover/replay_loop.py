"""The whole loop on a real v3 loss, at $0: propose from the kept snapshot, certify the
top pair as a person would, then replay the agent's own edits for that stage through
the real hooks and record what the agent and the reviewer would have been told.

payroll_lite stage 2: the agent changed the overtime rule and left reports/hours.py,
which keeps its own copy of it. Usage: replay_loop.py <new scratch dir>."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from core.milestones.propose import propose  # noqa: E402

NAME = 'payroll_lite--elevenpowers--3'
RERUN = set(json.loads((ROOT / 'results/multistage-v3/full-rerun-c.json').read_text(encoding='utf-8')))
SLOT = Path('E:/ep-runs/multistage-v3-full-2026-10-30-' + ('c' if NAME in RERUN else 'b')) / NAME
HOOK = ROOT / 'plugin' / 'bin' / 'ep_hook.py'
case = json.loads((ROOT / 'eval/multistage_v3/payroll_lite/case.json').read_text(encoding='utf-8'))
work = Path(sys.argv[1]).resolve() / 'work'
shutil.copytree(SLOT / 'snapshots' / '1', work)
(work / '.elevenpowers').mkdir()
shutil.copy(SLOT / 'work' / '.elevenpowers' / 'config.json', work / '.elevenpowers' / 'config.json')
for args in (['init', '-q'], ['add', '-A'], ['-c', 'user.name=r', '-c', 'user.email=r@r', 'commit', '-qm', 'base']):
    subprocess.run(['git', '-c', 'core.autocrlf=false', *args], cwd=work, check=True, capture_output=True)

# Discover.
top = propose(work, limit=5)['proposals']
print('proposals:', [(p['files'], p['shared'][:3]) for p in top[:3]])
# Certify: a person accepts the first pair and names its rule. The description is the replay's, not the case's.
entry = dict(top[0]['entry'], id='overtime-split',
             description='How ordinary and overtime hours are split for pay.')
(work / 'elevenpowers.milestones.json').write_text(json.dumps({'schema': 1, 'milestones': [entry]}, indent=2),
                                                   encoding='utf-8')
subprocess.run(['git', 'add', '-A'], cwd=work, check=True)
subprocess.run(['git', '-c', 'user.name=r', '-c', 'user.email=r@r', 'commit', '-qm', 'certified'], cwd=work, check=True)
env = {**os.environ, 'CLAUDE_PROJECT_DIR': str(work)}


def hook(event, **extra):
    payload = {'session_id': 's', 'transcript_path': '', 'cwd': str(work), 'hook_event_name': event, **extra}
    done = subprocess.run([sys.executable, str(HOOK), event], input=json.dumps(payload), text=True, cwd=work,
                          capture_output=True, env=env)
    return json.loads(done.stdout).get('hookSpecificOutput', {}) if done.stdout.strip() else {}


hook('SessionStart', source='startup')
hook('UserPromptSubmit', prompt=case['stages'][1]['request'])
after = SLOT / 'snapshots' / '2'
for path in sorted(after.rglob('*.py')):
    relative = path.relative_to(after)
    target = work / relative
    if target.exists() and target.read_bytes() == path.read_bytes():
        continue
    use = {'file_path': str(target), 'old_string': 'a', 'new_string': 'b'}
    brief = hook('PreToolUse', tool_name='Edit', tool_input=use).get('additionalContext', '')
    print(f'edit {relative.as_posix()}: brief of {len(brief)} characters')
    if 'Declared rule' in brief:
        print(f'brief before editing {relative.as_posix()}:', [l for l in brief.splitlines() if 'Declared rule' in l])
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(path, target)
    hook('PostToolUse', tool_name='Edit', tool_input=use, tool_response={'filePath': str(target)})
report = hook('Stop', last_assistant_message='Done. The tests pass.').get('systemMessage', '')
print('end report:', [l.strip() for l in report.splitlines() if 'declared rule' in l])
