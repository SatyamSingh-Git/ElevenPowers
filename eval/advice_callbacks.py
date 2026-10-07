"""Explicit disposable launcher-replay timing, never installed-session proof."""
import json
from pathlib import Path
import subprocess
import sys
import time

from core.config import Config, save
from core.ledger import Ledger
from core.milestones.advice import policy

TOOL_ROOT = Path(__file__).resolve().parents[1]
HOSTS = {'claude': 'PostToolUse', 'codex': 'PostToolUse', 'gemini': 'AfterTool',
         'cursor': 'postToolUse', 'copilot': 'postToolUse'}


def measure(root, *, changed, hosts=tuple(HOSTS), repeats=3, seconds=1, checkpoint=None):
    """Caller owns disposable root; this intentionally writes config/task state."""
    root = Path(root).resolve(strict=True)
    settings = {'enabled': True, 'seconds': seconds, 'cooldown': 30, 'max_attempts': 3}
    policy(settings)
    if type(repeats) is not int or not 1 <= repeats <= 20 or any(h not in HOSTS for h in hosts):
        raise ValueError('invalid callback measurement bounds')
    value = {'schema': 1, 'source': 'launcher replay', 'seconds': seconds,
             'samples': [], 'limits': ['No model, installed edit session or project check is executed.',
                                     'Includes launcher and optional worker cost on this machine.']}
    def capture(host):
        payload = {'cwd': str(root), 'tool_name': 'Write',
                   'tool_input': {'file_path': str(root / changed)},
                   'tool_response': {'exit_code': 0}, 'session_id': 'callback-measurement'}
        if host == 'gemini':
            payload['tool_name'] = 'write_file'
        if host == 'copilot':
            payload.update(toolName='create', toolArgs=payload['tool_input'])
        args = ([sys.executable, str(TOOL_ROOT / 'plugin/bin/ep_hook.py'), HOSTS[host], '--replay']
                if host == 'claude' else
                [sys.executable, str(TOOL_ROOT / 'plugin/bin/ep_host.py'), host, HOSTS[host], '--replay'])
        started = time.monotonic()
        done = subprocess.run(args, cwd=TOOL_ROOT, input=json.dumps(payload),
                              capture_output=True, text=True, timeout=seconds + 10)
        elapsed = round((time.monotonic() - started) * 1000, 3)
        output = json.loads(done.stdout) if done.returncode == 0 and done.stdout.strip() else {}
        text = json.dumps(output)
        return {'ms': elapsed, 'exit_code': done.returncode,
                'has_advice': 'milestone advice' in text,
                'incomplete': 'incomplete' in text.lower(), 'output_chars': len(done.stdout)}
    for host in hosts:
        for repeat in range(repeats):
            sample = {'host': host, 'repeat': repeat, 'state': 'incomplete'}
            value['samples'].append(sample)
            if checkpoint:
                checkpoint(value)
            Ledger(root=root, task=f'{host}-{repeat}', touched=[changed]).save()
            save(root, Config(profile='guide', auto_detect=False))
            sample['baseline'] = capture(host)
            save(root, Config(profile='guide', auto_detect=False, milestone_advice=settings))
            sample['advised'] = capture(host)
            sample['duplicate'] = capture(host)
            sample['added_ms'] = round(sample['advised']['ms'] - sample['baseline']['ms'], 3)
            sample['state'] = 'complete'
            if checkpoint:
                checkpoint(value)
    return value
