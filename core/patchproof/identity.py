"""Bounded Git facts, independent of evidence interpretation or execution."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time

from ..process import run


def digest(label, values):
    return hashlib.sha256(json.dumps([label, *values], ensure_ascii=True,
                                     separators=(',', ':')).encode()).hexdigest()


class GitRead:
    def __init__(self, root, deadline):
        self.root, self.deadline = root, deadline
        # Do not inherit repository redirection, injected config, external diff,
        # alternate object stores or replacement refs from the calling host.
        self.env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        self.env.update(GIT_OPTIONAL_LOCKS='0', GIT_CONFIG_NOSYSTEM='1',
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT='0',
                        GIT_NO_REPLACE_OBJECTS='1')
        self.command = ['git', '--no-optional-locks', '-c', f'safe.directory={root.as_posix()}',
                        '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false',
                        '-c', 'core.ignoreStat=false', '-c', 'core.trustctime=true',
                        '-c', 'core.checkStat=default',
                        '-c', 'diff.external=', '-c', 'core.pager=cat']

    def read(self, *args, allow_missing=False):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('patch collection deadline reached')
        done = run([*self.command, *args], cwd=self.root, timeout=remaining,
                   shell=False, env=self.env, text=False)
        if done.returncode and not (allow_missing and done.returncode == 1):
            # Git error bodies can contain config, paths or helper commands.
            raise ValueError('Git lookup failed: ' + args[0])
        return done.stdout

    def disable_filters(self):
        keys = self.read('config', '--local', '--includes', '--null', '--name-only',
                         '--get-regexp', r'^filter\..*\.(clean|process|required)$',
                         allow_missing=True)
        drivers = set()
        for key in keys.split(b'\0'):
            if key:
                name = key.decode('utf-8', errors='strict').rsplit('.', 1)[0]
                drivers.add(name)
        for name in sorted(drivers):
            self.command += ['-c', name + '.clean=', '-c', name + '.process=',
                             '-c', name + '.required=false']
        return bool(drivers)


def _path(raw):
    value = raw.decode('utf-8', errors='strict')
    path = Path(value)
    if not value or path.is_absolute() or '..' in path.parts:
        raise ValueError('unsupported Git path')
    return value


def _changes(raw):
    fields, changes = raw.split(b'\0'), []
    i = 0
    while i < len(fields) - 1:
        meta = fields[i].decode('ascii').split()
        if len(meta) != 5 or not meta[0].startswith(':'):
            raise ValueError('unrecognized Git raw change')
        old_mode, new_mode, old_blob, new_blob, status = meta
        path = _path(fields[i + 1])
        old_path = path
        i += 2
        if status[0] in 'RC':
            path = _path(fields[i])
            i += 1
        changes.append({'path': path, 'old_path': old_path, 'kind': status[0],
                        'similarity': status[1:] or None, 'old_mode': old_mode[1:],
                        'new_mode': new_mode, 'old_blob': old_blob, 'new_blob': new_blob,
                        'binary': False})
    return changes


def _binary_paths(raw):
    fields, result, i = raw.split(b'\0'), set(), 0
    while i < len(fields) - 1:
        added, removed, path = fields[i].split(b'\t', 2)
        i += 1
        if not path:  # Rename numstat carries both NUL-separated paths.
            i += 1
            path = fields[i]
            i += 1
        if added == b'-' or removed == b'-':
            result.add(_path(path))
    return result


def collect(root, base='HEAD~1', head='HEAD', *, seconds=30):
    """Return a committed tree-pair identity; collection never executes checks."""
    if not math.isfinite(seconds) or not 0 <= seconds <= 600:
        raise ValueError('patch seconds must be between 0 and 600')
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('project must be a directory')
    value = {'schema_version': 1, 'state': 'unavailable', 'complete': False,
             'base': '', 'head': '', 'base_tree': '', 'head_tree': '',
             'patch_id': '', 'content_digest': '', 'empty': None, 'changes': [],
             'identity_algorithm': 'sha256 commit-pair-v1 / full-tree-pair-v1',
             'issues': [], 'checkout': {'head': '', 'eligible': False, 'issues': []}}
    git = GitRead(root, time.monotonic() + seconds)
    try:
        top = Path(os.fsdecode(git.read('rev-parse', '--show-toplevel').strip())).resolve()
        if top != root:
            raise ValueError('project must be the Git repository root')
        filters = git.disable_filters()
        resolved = []
        for ref in (base, head):
            if not isinstance(ref, str) or not ref or '\0' in ref:
                raise ValueError('invalid patch ref')
            commit = git.read('rev-parse', '--verify', '--end-of-options', ref + '^{commit}').strip().decode('ascii')
            if not re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', commit):
                raise ValueError('invalid resolved commit')
            resolved.append(commit)
        value['base'], value['head'] = resolved
        for name in ('base', 'head'):
            value[name + '_tree'] = git.read('rev-parse', '--verify', '--end-of-options',
                                            value[name] + '^{tree}').strip().decode('ascii')
        changes = _changes(git.read('diff-tree', '--no-commit-id', '--raw', '-r', '-z',
                                    '--no-abbrev', '--find-renames=50%', '--no-ext-diff',
                                    '--no-textconv', *resolved, '--'))
        binaries = _binary_paths(git.read('diff', '--numstat', '-z', '--find-renames=50%',
                                         '--no-ext-diff', '--no-textconv', *resolved, '--'))
        for change in changes:
            change['binary'] = change['path'] in binaries
        value['changes'] = changes
        value['patch_id'] = digest('commit-pair-v1', resolved)
        value['content_digest'] = digest('full-tree-pair-v1', [value['base_tree'], value['head_tree']])
        value['empty'] = value['base_tree'] == value['head_tree']
        checkout = value['checkout']
        checkout['head'] = git.read('rev-parse', '--verify', 'HEAD').strip().decode('ascii')
        if checkout['head'] != value['head']:
            checkout['issues'].append('checkout HEAD differs from the requested patch head')
        if filters:
            checkout['issues'].append('configured clean/process filters disabled; checkout normalization unqualified')
        inventory = git.read('ls-tree', '-r', '-z', '--full-tree', value['head'])
        if any(entry.startswith((b'120000 ', b'160000 ')) for entry in inventory.split(b'\0')):
            checkout['issues'].append('linked inputs or submodules in the requested tree are unsupported binding inputs')
        flags = git.read('ls-files', '-v', '-z')
        if any(entry and (entry[:1].islower() or entry.startswith(b'S ')) for entry in flags.split(b'\0')):
            checkout['issues'].append('assume-unchanged or skip-worktree index entries leave checkout contents unqualified')
        status = git.read('status', '--porcelain=v1', '-z', '--untracked-files=all', '--ignore-submodules=none')
        if status:
            checkout['issues'].append('tracked, staged or nonignored untracked checkout changes exist')
        checkout['eligible'] = not checkout['issues']
        value['complete'], value['state'] = True, 'available'
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError, TimeoutError) as exc:
        value['issues'].append(str(exc) if isinstance(exc, (ValueError, TimeoutError))
                               else type(exc).__name__ + ': Git collection unavailable or incomplete')
        value['state'] = 'incomplete' if value['head'] else 'unavailable'
        value['checkout']['eligible'] = False
        value['empty'] = None
    return value
