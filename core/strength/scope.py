"""Changed production files, qualified by the repository's existing scanner."""
from dataclasses import dataclass, field
from pathlib import Path
import re
import subprocess
import time
from ..evidence import source_snapshot
from ..surface import TEST_NAME
from .model import relative

SUFFIXES = {'.py', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.mts', '.cts'}


@dataclass
class Scope:
    paths: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    fingerprint: str = ''


def git(root, args, deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError('strength deadline reached')
    done = subprocess.run(['git', '-c', f'safe.directory={root.as_posix()}', *args],
                          cwd=root, capture_output=True, timeout=min(10, remaining))
    if done.returncode:
        raise ValueError('repository query failed')
    return done.stdout.decode('utf-8', errors='strict')


def select(root, base, deadline, *, opened_dirty=()):
    value = Scope()
    try:
        if not re.fullmatch(r'[0-9a-fA-F]{40,64}', base or ''):
            raise ValueError('recorded base commit is missing or invalid')
        top = Path(git(root, ['rev-parse', '--show-toplevel'], deadline).strip()).resolve()
        if top != root.resolve():
            raise ValueError('project must be the repository root for change attribution')
        changed = git(root, ['diff', '--name-only', '-z', '--diff-filter=ACMRT', base, '--'], deadline)
        untracked = git(root, ['ls-files', '--others', '--exclude-standard', '-z'], deadline)
        scan, value.fingerprint = source_snapshot(root, fresh=True, deadline=deadline)
        value.issues.extend(scan.issues)
        candidates = set((changed + untracked).split('\0')) - {''}
        allowed = set(scan.files)
        for path in sorted(candidates):
            relative(path)
            if path not in allowed or Path(path).suffix not in SUFFIXES or TEST_NAME.search(path):
                continue
            if path in opened_dirty:
                value.issues.append('changed source was already dirty when the task opened: ' + path)
            value.paths.append(path)
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError, TimeoutError) as exc:
        value.issues.append(str(exc))
    return value
