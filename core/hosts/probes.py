"""Explicit, contained installed-version probes; never a model invocation."""
import math
from pathlib import Path
import re
import shutil
import subprocess

from ..process import run

EXECUTABLES = {
    'claude': ('claude',), 'codex': ('codex',), 'gemini': ('gemini',),
    'cursor': ('cursor-agent', 'agent'), 'copilot': ('copilot',),
}


def _probe(command, cwd, timeout):
    value = {'state': 'incomplete', 'version': '', 'source': 'installed_probe'}
    try:
        result = run(command, cwd=Path(cwd), timeout=timeout, shell=False)
        versions = set(re.findall(r'(?<![\w.])\d+\.\d+\.\d+(?:[-+][\w.-]+)?(?![\w.])', result.stdout))
        if result.returncode == 0 and len(versions) == 1:
            value.update(state='observed', version=versions.pop())
    except (OSError, subprocess.SubprocessError):
        pass
    return value


def probe(host, timeout=5):
    if host not in EXECUTABLES:
        raise ValueError('unsupported host')
    if isinstance(timeout, bool) or not math.isfinite(timeout) or not 0 < timeout <= 10:
        raise ValueError('probe timeout must be finite and within 0–10 seconds')
    executable = next((path for name in EXECUTABLES[host] if (path := shutil.which(name))), None)
    if not executable:
        return {'state': 'missing', 'version': '', 'source': 'installed_probe'}
    return _probe([executable, '--version'], Path.cwd(), timeout)
