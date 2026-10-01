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
