"""Changed production files, qualified by the repository's existing scanner."""
from dataclasses import dataclass, field
import fnmatch
import hashlib
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
    regions: dict[str, list[list[int]]] = field(default_factory=dict)
    deletions: dict[str, list[int]] = field(default_factory=dict)
    source_hashes: dict[str, str] = field(default_factory=dict)
    coverage_issues: list[str] = field(default_factory=list)


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
        # Missing current files cannot supply mutations, but removed production
        # behavior must not disappear behind a not-applicable result.
        from ..config import load
        policy = load(root).scan
        excludes = policy.get('exclude', []) if isinstance(policy, dict) else []
        excludes = excludes if isinstance(excludes, list) and all(isinstance(p,str) for p in excludes) else []
        removed = git(root, ['diff', '--name-only', '-z', '--diff-filter=D', base, '--'], deadline)
        deleted = []
        for path in sorted(set(removed.split('\0')) - {''}):
            relative(path)
            if (Path(path).suffix in SUFFIXES and not TEST_NAME.search(path) and
                    not any(fnmatch.fnmatchcase(path, p.rstrip('/')+'/*' if p.endswith('/') else p) for p in excludes) and
                    not any((root/parent/'.git').exists() for parent in Path(path).parents if str(parent) != '.')):
                deleted.append(path)
        value.coverage_issues.extend('removed production source cannot be mutation-sampled: ' + p for p in deleted[:128])
        if len(deleted) > 128:
            value.coverage_issues.append(f'deleted-source diagnostic limit: {len(deleted)-128} additional removed paths unlisted')
        candidates = set((changed + untracked).split('\0')) - {''}
        untracked_paths = set(untracked.split('\0'))
        allowed = set(scan.files)
        for path in sorted(candidates):
            relative(path)
            if path not in allowed or Path(path).suffix not in SUFFIXES or TEST_NAME.search(path):
                continue
            if path in opened_dirty:
                value.issues.append('changed source was already dirty when the task opened: ' + path)
            value.paths.append(path)
            source = (root / path).read_bytes()
            if len(source) > 1024 * 1024:
                raise ValueError('mutation source exceeds producer size limit: ' + path)
            value.source_hashes[path] = hashlib.sha256(source).hexdigest()
            count = len(source.splitlines())
            hunks = []
            anchors = []
            if path in untracked_paths:
                hunks = [[1, count]] if count else []
            else:
                diff = git(root, ['diff', '--no-ext-diff', '--no-textconv', '--no-renames',
                                  '--color=never', '-U0', base, '--', path], deadline)
                for match in re.finditer(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', diff, re.M):
                    start, length = int(match[1]), int(match[2] or 1)
                    if length:
                        if start < 1 or start + length - 1 > count:
                            raise ValueError('changed lines no longer match source: ' + path)
                        hunks.append([start, start + length - 1])
                    else:
                        anchors.append(max(1, min(start, count)))
            if sum(map(len, value.regions.values())) + sum(map(len, value.deletions.values())) + len(hunks) + len(anchors) > 2048:
                raise ValueError('changed-region limit exceeded')
            value.regions[path] = hunks
            if anchors:
                value.deletions[path] = sorted(set(anchors))
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError, TimeoutError) as exc:
        value.issues.append(str(exc))
    return value
