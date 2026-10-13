"""Local root approval is explicit, private and scoped to a project."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time
import uuid

from ..jobs import ledger_write, replace as atomic_replace
from . import definition

FILE = 'input-roots.json'


def identity(root):
    return hashlib.sha256(str(Path(root).resolve(strict=True)).encode()).hexdigest()


def directory(root, value):
    if not isinstance(value, (str, Path)):
        raise ValueError('input root must be a directory path')
    path = Path(value).absolute()
    if path.resolve() != path or path.is_symlink() or not path.is_dir():
        raise ValueError('linked or unavailable approved input root')
    root = Path(root).resolve(strict=True)
    if root == path or root.is_relative_to(path):
        raise ValueError('approved input root cannot contain the project')
    for state in (root/'.elevenpowers', root/'.git'):
        if path == state or path.is_relative_to(state) or state.is_relative_to(path):
            raise ValueError('approved input root overlaps project state')
    return path


def target(root):
    path = Path(root)/'.elevenpowers'/FILE
    if path.resolve() != path.absolute() or path.is_symlink():
        raise ValueError('linked local input approval is unsupported')
    return path


def private(root, deadline):
    if not (Path(root)/'.git').exists():
        return
    redirects = ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE','GIT_COMMON_DIR',
                 'GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES',
                 'GIT_CONFIG_COUNT','GIT_CONFIG_PARAMETERS','GIT_CONFIG')
    if any(name in os.environ for name in redirects):
        raise ValueError('ambient Git redirects cannot qualify local input approval')
    remaining = deadline-time.monotonic()
    if remaining <= 0:
        raise TimeoutError('input approval inspection deadline reached')
    env = {**os.environ, 'GIT_OPTIONAL_LOCKS':'0'}
    done = subprocess.run(['git','-c',f'safe.directory={Path(root).as_posix()}',
        '-c','core.fsmonitor=false','-c',f'core.hooksPath={os.devnull}',
        'ls-files','--error-unmatch','--','.elevenpowers/'+FILE], cwd=root,
        capture_output=True, timeout=min(5,remaining), env=env)
    if done.returncode == 0:
        raise ValueError('Git-tracked input approval is not local approval')
    if done.returncode != 1:
        raise ValueError('input approval tracking is unavailable')


def load(root, declaration, deadline):
    private(root, deadline)
    data = definition.raw(target(root))
    value = definition.decode(data)
    if (not isinstance(value, dict) or set(value) != {'schema','project','roots'}
            or type(value['schema']) is not int or value['schema'] != 1
            or value['project'] != identity(root) or not isinstance(value['roots'], dict)
            or not 1 <= len(value['roots']) <= 32):
        raise ValueError('input approval is malformed or belongs to another project')
    roots = {}
    required = {w['root'] for w in declaration['witnesses']}
    for name, path in value['roots'].items():
        definition.label(name)
        if not isinstance(path, str) or not Path(path).is_absolute():
            raise ValueError('input approval requires canonical absolute roots')
        approved = directory(root, path) if name in required else Path(path).absolute()
        if str(approved) != path:
            raise ValueError('input approval root is not canonical')
        roots[name] = path
    if any(w['root'] not in roots for w in declaration['witnesses']):
        raise ValueError('required input root has not been locally approved')
    return {**value, '_digest': hashlib.sha256(data).hexdigest()}


def bind(root, name, approved, replace=False):
    root = Path(root).resolve(strict=True)
    declaration = definition.load(root)
    if declaration is None or name not in {w['root'] for w in declaration['witnesses']}:
        raise ValueError('root label is not declared by this project')
    approved = directory(root, approved)
    path = target(root)
    private(root, time.monotonic()+5)
    path.parent.mkdir(exist_ok=True)
    with ledger_write(root):
        data = definition.raw(path, optional=True)
        value = {'schema':1,'project':identity(root),'roots':{}}
        if data is not None:
            # Existing approval may cover a subset while explicit binding fills it.
            value = definition.decode(data)
            if (not isinstance(value,dict) or set(value) != {'schema','project','roots'}
                    or type(value['schema']) is not int or value['schema'] != 1
                    or value['project'] != identity(root) or not isinstance(value['roots'],dict)):
                raise ValueError('existing input approval is malformed')
            for key, bound in value['roots'].items():
                definition.label(key)
                if not isinstance(bound,str) or not Path(bound).is_absolute():
                    raise ValueError('existing input approval root is malformed')
        if name in value['roots'] and value['roots'][name] != str(approved) and not replace:
            raise ValueError('replacing input approval requires explicit replace')
        value['roots'][name] = str(approved)
        if len(value['roots']) > 32:
            raise ValueError('too many local root bindings')
        ignored = path.parent/'.gitignore'
        prior = definition.raw(ignored, optional=True) or b''
        text = prior.decode('utf-8')
        if FILE not in text.splitlines():
            text += ('\n' if text and not text.endswith('\n') else '') + FILE+'\n'
            _write(ignored,text.encode())
        _write(path,json.dumps(value,ensure_ascii=True,indent=2).encode())


def _write(path,data):
    temporary = path.with_suffix('.'+uuid.uuid4().hex+'.tmp')
    try:
        with temporary.open('xb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        atomic_replace(temporary,path)
    finally:
        temporary.unlink(missing_ok=True)
