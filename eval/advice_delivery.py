"""Actual local checks with replay/synthetic native launchers, never model acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

from core import health
from core.hosts.acceptance import prepare
from core.hosts.provenance import fingerprint
from core.hosts.setup import PATHS
from core.ledger import Ledger
from core.process import run

SOURCE = Path(__file__).resolve().parents[1]
EVENTS = {'claude': ('SessionStart', 'PostToolUse'), 'codex': ('SessionStart', 'PostToolUse'),
          'gemini': ('SessionStart', 'AfterTool'), 'cursor': ('sessionStart', 'postToolUse'),
          'copilot': ('sessionStart', 'postToolUse')}
PROMPTS = {'claude': 'UserPromptSubmit', 'codex': 'UserPromptSubmit', 'gemini': 'BeforeAgent',
           'cursor': 'beforeSubmitPrompt', 'copilot': 'userPromptSubmitted'}


def _callback(root, host, mode, phase, *, command=None, output='', code=0, prompt=None):
    payload = {'cwd': str(root), 'session_id': 'advice-control',
               'tool_name': 'Bash' if command else 'Write',
               'tool_input': {'command': command} if command else {'file_path': str(root / ('app.py' if (root / 'app.py').exists() else 'app.mjs'))},
               'tool_response': {'stdout': output, 'exit_code': code}}
    if prompt is not None:
        payload['prompt'] = prompt
    if code is None:
        payload['tool_response'] = {'stdout': output, 'interrupted': True}
    if host == 'gemini':
        payload['tool_name'] = 'run_shell_command' if command else 'write_file'
        payload['tool_response'] = {'llmContent': output, 'data': {'exitCode': code}}
    if host == 'cursor':
        payload['tool_name'] = 'Shell' if command else 'Write'
        payload['tool_output'] = payload['tool_response']
    if host == 'copilot':
        payload.update(sessionId='advice-control', toolName='bash' if command else 'create',
                       toolArgs=payload['tool_input'], toolResult={'exitCode': code, 'textResultForLlm': output})
    args = ([sys.executable, str(SOURCE / 'plugin/bin/ep_hook.py'), phase] if host == 'claude'
            else [sys.executable, str(SOURCE / 'plugin/bin/ep_host.py'), host, phase])
    if mode == 'replay':
        args.append('--replay')
    done = subprocess.run(args, input=json.dumps(payload), cwd=SOURCE, capture_output=True,
                          text=True, timeout=15)
    response = json.loads(done.stdout) if done.returncode == 0 and done.stdout.strip() else {}
    return {'exit': done.returncode, 'context_chars': len(done.stdout),
            'has_advice': 'milestone advice' in json.dumps(response)}


def _view(root, host):
    value = health.inspect(host, root, timeout=15)['milestone_advice']
    return {key: value[key] for key in ('state', 'generated', 'emitted', 'matching_native_receipts',
                                       'checks', 'issues', 'model_consumption')}


def _observe(root, host, language, mode, *, ordinary_prompts=False):
    started = time.monotonic()
    manifest = prepare(host, root, language, SOURCE, advice=True)
    if not ordinary_prompts:
        Ledger(root=root, task='advice-control').save()
    callbacks = [_callback(root, host, mode, EVENTS[host][0])]
    if ordinary_prompts:
        callbacks.append(_callback(root, host, mode, PROMPTS[host],
                                   prompt='Read EXERCISE.md and follow its instructions.'))
    task = Ledger.load(root)
    def check(command, *, interrupted=False):
        try:
            done = run(command, cwd=root, shell=True, timeout=.02 if interrupted else 15)
            code, output = done.returncode, done.stdout + done.stderr
        except subprocess.TimeoutExpired as error:
            code, output = None, (error.stdout or '') + (error.stderr or '')
        callbacks.append(_callback(root, host, mode, EVENTS[host][1], command=command,
                                   output=output, code=code))
        return code
    initial = check(manifest['command'])
    app = root / manifest['source_file']
    original = app.read_text()
    app.write_text(original.replace('value > 10', 'value >= 10'))
    edit = _callback(root, host, mode, EVENTS[host][1])
    callbacks.append(edit)
    after_edit = Ledger.load(root)
    before = _view(root, host)
    command = 'cd . && ' + manifest['command']
    codes, views = [], []
    codes.append(check(command)); views.append(_view(root, host))
    app.write_text(original)
    codes.append(check(command)); views.append(_view(root, host))
    (root / 'wait.flag').write_text('intentional bounded interruption\n')
    codes.append(check(command, interrupted=True)); views.append(_view(root, host))
    (root / 'wait.flag').unlink()
    app.write_text(original.replace('value > 10', 'value >= 10'))
    codes.append(check(command)); views.append(_view(root, host))
    followups = [view['checks'][0]['state'] if view['checks'] else 'unobserved' for view in views]
    expected = ['current', 'failed', 'incomplete', 'current'] if mode == 'native-control' else ['unobserved'] * 4
    qualified = (initial == 1 and codes == [0, 1, None, 0] and all(row['exit'] == 0 for row in callbacks)
                 and edit['has_advice'] and before['matching_native_receipts'] == 0 and followups == expected
                 and before['state'] == ('emitted' if mode == 'native-control' else 'generated')
                 and all(view['model_consumption'] == 'unproven' for view in views))
    if ordinary_prompts:
        qualified = qualified and bool(task.task) and not task.claims and after_edit.task == task.task
    return {'host': host, 'language': language, 'mode': mode, 'qualified': qualified,
            'initial_process_exit': initial, 'process_exits': codes, 'callbacks': callbacks,
            'before_check': before, 'followups': followups, 'observations': views,
            'task_opened_by_prompt': bool(task.task) if ordinary_prompts else False,
            'task_preserved_after_edit': after_edit.task == task.task,
            'prompt_claims': [claim.value for claim in task.claims],
            'seconds': round(time.monotonic() - started, 3),
            'test_sha256': hashlib.sha256((root / manifest['test_file']).read_bytes()).hexdigest()}


def exercise(destination, *, hosts=tuple(PATHS), languages=('python', 'javascript'),
             modes=('replay', 'native-control'), ordinary_prompts=False):
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError('exercise destination must be new')
    if (type(ordinary_prompts) is not bool or not hosts or not languages or not modes or set(hosts) - set(PATHS) or
            set(languages) - {'python', 'javascript'} or set(modes) - {'replay', 'native-control'}):
        raise ValueError('unsupported exercise selection')
    destination.mkdir(parents=True)
    value = {'schema': 1, 'runtime': fingerprint(), 'model_calls': 0, 'installed_acceptance': False,
             'ordinary_prompts': ordinary_prompts,
             'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             'observations': [], 'unavailable': [], 'qualified': False,
             'limits': ['Native-control means synthetic launcher ingress, not an installed agent session.',
                        'Matching subsequent native receipts do not prove model comprehension or causal coding benefit.',
                        'Actual local commands and bounded interruption run on disposable authored projects.']}
    for language in languages:
        if language == 'javascript' and not shutil.which('node'):
            value['unavailable'].append('Node unavailable')
            continue
        for host in hosts:
            for mode in modes:
                row = _observe(destination / f'{language}-{host}-{mode}', host, language, mode,
                               ordinary_prompts=ordinary_prompts)
                value['observations'].append(row)
                (destination / 'summary.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')
    value['qualified'] = (not value['unavailable'] and
                          len(value['observations']) == len(languages)*len(hosts)*len(modes) and
                          all(row['qualified'] for row in value['observations']) and fingerprint() == value['runtime'])
    (destination / 'summary.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--ordinary-prompts', action='store_true',
                        help='Open tasks through host prompt callbacks instead of controller-seeded IDs')
    args = parser.parse_args()
    value = exercise(args.destination, ordinary_prompts=args.ordinary_prompts)
    print(json.dumps(value, indent=2))
    return 0 if value['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
