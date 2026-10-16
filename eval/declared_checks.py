"""Disposable actual Python/Node owned checks with synthetic host callbacks."""
import argparse
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from core.checks import execute
from core.hosts.bridge import run as bridge
from core.hosts.provenance import fingerprint
from core.hook import dispatch
from core.ledger import Ledger
from core.milestones import build
from core.evidence import Result
from .input_scopes import project, counts
from .input_sessions import HOSTS

CLI = Path(__file__).resolve().parents[1] / 'plugin/bin/ep_check.py'


def _outer(root, command, host, output):
    payload = {'cwd': str(root), 'session_id': 'synthetic-outer', 'tool_use_id': 'outer-' + host,
               'tool_name': 'Bash', 'tool_input': {'command': command},
               'tool_response': {'stdout': output, 'exit_code': 0}}
    event = 'PostToolUse'
    if host == 'gemini':
        event = 'AfterTool'; payload['tool_name'] = 'run_shell_command'
        payload['tool_response'] = {'llmContent': output, 'data': {'exit_code': 0}}
    if host == 'cursor':
        event = 'postToolUse'; payload['tool_name'] = 'Shell'
        payload['tool_output'] = payload['tool_response']
    if host == 'copilot':
        event = 'postToolUse'
        payload.update(sessionId='synthetic-outer', toolName='bash', toolArgs=payload['tool_input'],
                       toolResult={'textResultForLlm': output, 'exit_code': 0})
    with redirect_stdout(io.StringIO()):
        dispatch(event, payload) if host == 'claude' else bridge(host, event, payload)


def case(directory, language):
    directory = Path(directory).absolute()
    directory.mkdir(parents=True)
    root, base, head, target, other, good, bad, args, commands = project(directory, language)
    Ledger(root=root, task='owned-check-task').save()
    outcomes = [execute(root, key)['state'] for key in ('tests', 'build')]
    target.write_bytes(bad)
    fault = [m['state'] for m in build(root)['milestones']]
    invocation = f'"{sys.executable}" "{CLI}" tests --project "{root}" --json'
    shell = invocation + (' & echo outer-complete' if os.name == 'nt' else '; echo outer-complete')
    outer = subprocess.run(shell, cwd=root, shell=True, capture_output=True, text=True, timeout=45)
    # CLI emits only metadata, followed by an outer-shell line.
    failed = json.loads(outer.stdout[:outer.stdout.rfind('}') + 1])
    outcomes.append(failed['state'])
    for host in HOSTS:
        _outer(root, shell, host, outer.stdout)
    retained = [e for e in Ledger.load(root).evidence if e.declaration == 'tests' and e.kind.value == 'test_suite']
    survived = bool(retained and retained[-1].result is Result.FAIL and retained[-1].execution == 'complete')
    failed_states = [m['state'] for m in build(root)['milestones']]
    target.write_bytes(good)
    outcomes.append(execute(root, 'tests')['state'])
    repaired = [m['state'] for m in build(root)['milestones']]
    before_missing = counts(root)
    target.unlink()
    outcomes.append(execute(root, 'tests')['state'])
    if counts(root) != before_missing:
        raise ValueError('missing owned input still launched a command')
    value = {'language': language, 'outcomes': outcomes, 'milestones_after_fault': fault,
             'milestones_after_failure': failed_states, 'milestones_after_repair': repaired,
             'counts_before_missing': before_missing, 'outer_shell_exit': outer.returncode,
             'owned_failure_survived_callbacks': survived, 'synthetic_hosts': HOSTS,
             'model_calls': 0, 'installed_acceptance': False}
    value['qualified'] = (outcomes == ['passed', 'passed', 'failed', 'passed', 'incomplete']
                          and fault == ['STALE','CURRENT'] and failed_states == ['FAILED','CURRENT']
                          and repaired == ['CURRENT','CURRENT'] and before_missing == [3,1]
                          and outer.returncode == 0 and survived)
    return value


def exercise(destination):
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink() or destination.resolve() != destination:
        raise ValueError('exercise needs a new unlinked directory')
    destination.mkdir(parents=True)
    started = time.monotonic()
    before = fingerprint()
    value = {'schema_version': 1, 'producer': before, 'model_calls': 0,
             'installed_acceptance': False, 'observations': [],
             'limits': ['Actual local child processes with synthetic outer-host callbacks.',
                        'No installed-session acceptance, causal coding benefit or universal dependency coverage.']}
    for language in ('python', 'javascript'):
        value['observations'].append(case(destination / language, language))
    value['qualified'] = all(r['qualified'] for r in value['observations']) and before == fingerprint()
    value['seconds'] = round(time.monotonic() - started, 3)
    (destination / 'result.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf8')
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = exercise(args.output)
    print(json.dumps(value, indent=2))
    return 0 if value['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
