"""One project readiness view across the five supported hosts."""
import shutil
import os
import shlex

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


def inspect(host, root, timeout=10):
    from ..health import inspect as health_inspect
    return health_inspect(host, root, timeout)



def report(host, root, timeout=10):
    from ..health import render
    return render(inspect(host, root, timeout))


NAMES = {'claude': 'Claude Code', 'codex': 'Codex', 'gemini': 'Gemini CLI',
         'cursor': 'Cursor Agent', 'copilot': 'GitHub Copilot CLI'}
RULE_NAMES = {'cursor': 'Cursor', 'copilot': 'Copilot', 'claude': 'Claude Code', 'agents': 'AGENTS.md'}
MODES = {'strict': 'it sends the agent back, at most twice, if a check is missing or failing when it stops',
         'guide': 'it reports what is missing at the end and never blocks',
         'off': 'it records evidence and says nothing'}


def _line(*words):
    """A command a person can paste: the platform's own quoting, so a space survives."""
    import subprocess
    words = ['python', *map(str, words)]
    return subprocess.list2cmdline(words) if os.name == 'nt' else shlex.join(words)


def summary(host, root, hooks, bin_dir):
    """What setup found, in a dozen lines; `ep_ready` keeps the full view."""
    import time
    from ..config import load
    from ..evidence import scan_sources
    from ..milestones import definition, scoped

    config = load(root)
    rules, rule_issues = scoped.read(root)
    declared = definition.load(root)
    scan = scan_sources(root, deadline=time.monotonic() + 10)
    name = NAMES[host]
    counts = {}
    for rule in rules:
        counts[rule['format']] = counts.get(rule['format'], 0) + 1
    lines = [f'ElevenPowers is set up for {name} in {root}.', f'Hooks: {hooks}',
             f'Mode: {config.profile} - {MODES[config.profile]}.', '', 'Found in this project:',
             '  Checks: ' + ('; '.join(f'{need}: {command}' for need, command in sorted(config.commands.items()))
                             or 'none'),
             '  Project rules: ' + (', '.join(f'{n} {RULE_NAMES[f]}' for f, n in counts.items())
                                    + ' (shown to the agent when they apply)' if counts else 'none'),
             '  Declared rules: ' + (f"{len(declared['milestones'])} in {definition.FILE}" if declared['configured']
                                     else 'none yet (' + _line(bin_dir / 'ep_milestones.py', '--project', root, '--add-rule', 'FILE', 'OTHER') + ')'),
             f'  Source: {len(scan.files)} files read']
    attention = []
    if not config.command_for('tests'):
        attention.append('No test command found. If the project has one, declare it: '
                         + _line(bin_dir / 'ep_setup.py', host, '--project', root, '--tests', 'your test command'))
    attention += [f"{issue} ({_line(bin_dir / 'ep_milestones.py', '--project', root, '--scoped')})" for issue in rule_issues]
    attention += declared['issues'] + scan.issues
    if attention:
        lines += ['', 'Needs attention:'] + [f'  - {item}' for item in attention]
    lines += ['', f'Next: start a new {name} session in this project. Your host may ask you to approve the hooks.',
              'Full readiness view: ' + _line(bin_dir / 'ep_ready.py', host, '--project', root)]
    return '\n'.join(lines)
