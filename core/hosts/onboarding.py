"""One project readiness view across the five supported hosts."""
from pathlib import Path
import shutil
import sys
import time
import os
import shlex

from ..config import load
from ..evidence import scan_sources
from ..ledger import Ledger
from .doctor import report as configuration_report
from .readiness import activation
from .setup import PATHS

HOSTS = tuple(PATHS)
EXECUTABLES = {'claude': ('claude',), 'codex': ('codex',), 'gemini': ('gemini',),
               'cursor': ('cursor-agent', 'agent', 'cursor'), 'copilot': ('copilot',)}


def runtime_name(command):
    """Read the executable token without expanding or executing shell text."""
    try:
        words = shlex.split(command, posix=os.name != 'nt')
    except ValueError:
        return ''
    if words[:1] == ['&']:
        words = words[1:]
    while words and '=' in words[0] and not words[0].startswith(('"', "'")):
        words = words[1:]
    return words[0].strip('\"\'') if words else ''


def available(root):
    return {host: next((found for name in names if (found := shutil.which(name))), '')
            for host, names in EXECUTABLES.items()}


def select_host(host, root):
    if host != 'auto':
        if host not in HOSTS:
            raise ValueError(f'unsupported host: {host}')
        return host
    detected = [h for h, executable in available(root).items() if executable]
    if len(detected) == 1:
        return detected[0]
    if detected:
        raise ValueError('multiple available hosts: ' + ', '.join(detected) + '; select a host explicitly')
    raise ValueError('no host executable found on PATH; select a host explicitly for desktop or custom installations')


def inspect(host, root):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('project must be a directory')
    host = select_host(host, root)
    text, configured = configuration_report(host, root)
    live = activation(host, root)
    config = load(root)
    scan = scan_sources(root, deadline=time.monotonic() + 5)
    commands = config.commands
    runtimes = {name: bool(shutil.which(name)) for command in commands.values()
                if (name := runtime_name(command))}
    ledger = Ledger.load(root)
    from .edits import coverage
    pending_patches, patch_gaps = coverage(root, ledger.task)
    records = [e for e in ledger.evidence if e.declaration]
    latest = records[-1] if records else None
    receipt = ({'command': latest.command, 'result': latest.result.value,
                'execution': latest.execution, 'freshness': 'unchecked',
                'coverage_issues': latest.coverage_issues} if latest else None)
    actions = []
    if pending_patches:
        actions.append(f'{pending_patches} patch call(s) await post-events; completion will report unpaired calls as incomplete edit coverage.')
    if patch_gaps:
        actions.append(f'{patch_gaps} patch baseline(s) exceeded the history budget; native edit coverage is incomplete for this task.')
    if not configured:
        actions.append(f'Run ep_setup.py {host} --project "{root}" to repair configuration.')
    if live['state'] in {'waiting', 'unobserved', 'configuration-changed', 'removed'}:
        actions.append('Review host hook enablement/trust and start a new session in this project; then check readiness again.')
    elif live['state'] == 'received':
        actions.append('Callbacks are arriving; start a new project session to confirm startup processing.')
    elif live['state'] == 'error':
        actions.append('Inspect the hook stderr in the host; the latest callback could not be processed (' + live.get('error', 'unknown') + ').')
    if live.get('errors') and live['state'] != 'error':
        actions.append(f"{live['errors']} earlier callback(s) failed ({live.get('last_error', 'unknown')}); inspect host stderr for lost observations.")
    actions.extend(f'Install or activate {name} on the host PATH.' for name, found in runtimes.items() if not found)
    if not commands:
        actions.append('Declare verification commands in .elevenpowers/config.json; no unambiguous command was discovered.')
    if not scan.complete:
        actions.append('Resolve source coverage issues or adjust project scan budgets before relying on complete coverage.')
    if not receipt:
        actions.append('Run a declared verification command in the host to record its execution outcome.')
    elif receipt['execution'] != 'complete' or receipt['result'] != 'pass':
        actions.append('Complete or fix the latest declared verification run, then run it again.')
    else:
        actions.append('Use ep_status.py to check whether the latest receipt still matches current source inputs.')
    return {'host': host, 'project': str(root), 'python': sys.version.split()[0],
            'configuration_ok': configured, 'configuration_report': text,
            'activation': live, 'commands': commands, 'runtimes': runtimes,
            'coverage': {'complete': scan.complete, 'files': len(scan.files), 'bytes': scan.bytes, 'issues': scan.issues},
            'latest_receipt': receipt, 'pending_patches': pending_patches, 'patch_gaps': patch_gaps, 'profile': config.profile, 'next_actions': actions}


def report(host, root):
    value = inspect(host, root)
    live, scan = value['activation'], value['coverage']
    lines = [f"ElevenPowers readiness: {value['host']}", f"Project: {value['project']}",
             value['configuration_report'], f"Activation: {live['state']}",
             f"Source coverage: {'complete' if scan['complete'] else 'incomplete'}; {scan['files']} files, {scan['bytes']} bytes"]
    lines.extend(scan['issues'])
    lines.extend(f'Command {need}: {command}' for need, command in sorted(value['commands'].items()))
    lines.extend(f"Runtime {name}: {'available' if found else 'missing on PATH'}" for name, found in value['runtimes'].items())
    receipt = value['latest_receipt']
    lines.append(f"Latest declared run: {receipt['execution']} / {receipt['result']}; freshness unchecked; {receipt['command']}"
                 if receipt else 'Latest declared run: none recorded')
    lines.extend('Next action: ' + action for action in value['next_actions'])
    return '\n'.join(lines)
