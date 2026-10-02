"""Explicit fixed-patch review helpers; never run during plugin installation."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time
import zipfile

from core.process import run, OutputLimitExceeded

MARKER = '.ep-review-checkpoint.json'
IGNORED = {'.git', '.claude', '.elevenpowers', '.pytest_cache', '.hypothesis', '__pycache__'}
GIT = ['git', '-c', 'core.autocrlf=false', '-c', 'core.eol=lf']


def _path(name):
    from core.strength.model import relative
    relative(name)
    if name.startswith('.') or any(part in IGNORED for part in Path(name).parts):
        raise ValueError('unsafe checkpoint path')
    return name


def git(root, *args):
    done = run([*GIT, '-c', f'safe.directory={Path(root).as_posix()}', '-C', str(root), *args],
               cwd=Path(root), timeout=30, shell=False)
    if done.returncode:
        raise ValueError('checkpoint Git operation failed')
    return done.stdout.strip()


def _files(root):
    values = {}
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root)
        if any(part in IGNORED for part in rel.parts) or path.suffix == '.pyc':
            continue
        if path.is_symlink():
            raise ValueError('linked checkpoint input')
        if path.is_file():
            if path.stat().st_size > 64*1024*1024 or len(values) >= 20000:
                raise ValueError('checkpoint input limit exceeded')
            values[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return values


def prepare(case, root):
    root = Path(root).absolute()
    if root.exists() or any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError('new unlinked checkpoint directory required')
    if not re.fullmatch('[a-z0-9][a-z0-9-]{0,79}', case['id']) or not re.fullmatch('[0-9a-f]{40}', case['base']):
        raise ValueError('invalid checkpoint identity')
    for name in case['source_paths']:
        _path(name)
    patch = case['patch']
    if not isinstance(patch, str) or len(patch.encode()) > 4*1024*1024:
        raise ValueError('invalid checkpoint patch')
    root.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='ep-review-seed-', dir=root.parent) as directory:
        archive = Path(directory) / 'source.zip'
        git(case['repository'], 'archive', '--format=zip', '-o', str(archive), case['base'])
        with zipfile.ZipFile(archive) as data:
            items = data.infolist()
            if len(items)>20000 or sum(i.file_size for i in items)>64*1024*1024:
                raise ValueError('checkpoint archive exceeds bounds')
            for item in items:
                name = item.filename.rstrip('/')
                if not name or ':' in name or '\\' in name or name.startswith('/') or '..' in Path(name).parts:
                    raise ValueError('unsafe archived path')
                if stat.S_ISLNK(item.external_attr >> 16):
                    raise ValueError('linked archived input')
            data.extractall(root)
        where = case.get('environment', {}).get('PYTHONPATH')
        if where and not (root/'conftest.py').exists():
            _path(where)
            (root/'conftest.py').write_text(
                'import os, sys\nfrom pathlib import Path\n'
                f'_ep_source = str(Path(__file__).resolve().parent / {where!r})\n'
                'sys.path.insert(0, _ep_source)\n'
                'os.environ["PYTHONPATH"] = _ep_source\n', encoding='utf-8')
        if where:
            (root/'ep_review_pytest.py').write_text(
                'import os, sys\nfrom pathlib import Path\n'
                f'_ep_source = str(Path(__file__).resolve().parent / {where!r})\n'
                'sys.path.insert(0, _ep_source)\n'
                'os.environ["PYTHONPATH"] = os.pathsep.join(p for p in (_ep_source, os.environ.get("PYTHONPATH", "")) if p)\n'
                'import pytest\nraise SystemExit(pytest.main(sys.argv[1:]))\n', encoding='utf-8')
        git(root, 'init', '-q')
        git(root, 'add', '.')
        git(root, '-c', 'user.name=Checkpoint review', '-c', 'user.email=review@example.invalid', 'commit', '-qm', 'Original inputs')
        base = git(root, 'rev-parse', 'HEAD')
        if patch:
            file = Path(directory)/'candidate.patch'
            file.write_bytes(patch.encode('utf-8'))
            git(root, 'apply', '--binary', '--whitespace=nowarn', str(file))
        protected = _files(root)
        (root/MARKER).write_text(json.dumps({'schema_version':1, 'case':case['id'], 'base':base,
            'protected':sorted(protected)}, sort_keys=True), encoding='utf-8')
    return seal(root)


def seal(root):
    root = Path(root).resolve(strict=True)
    marker = root/MARKER
    if marker.is_symlink() or marker.stat().st_size > 2*1024*1024:
        raise ValueError('invalid checkpoint marker')
    value = json.loads(marker.read_text(encoding='utf-8'))
    protected = set(value['protected']) | {MARKER}
    files = _files(root)
    # Only new Python test files are editable. Existing tests/source stay fixed.
    return {name:digest for name,digest in files.items()
            if name in protected or not (name.startswith('tests/') and Path(name).name.startswith('test_') and name.endswith('.py'))}


def capture_additions(root, expected):
    root = Path(root).resolve(strict=True)
    if seal(root) != expected:
        raise ValueError('protected checkpoint inputs changed')
    value = json.loads((root/MARKER).read_text(encoding='utf-8'))
    protected = set(value['protected']) | {MARKER}
    added = {}
    size = 0
    for name in _files(root):
        if name in protected:
            continue
        path = root/name
        size += path.stat().st_size
        if size > 1024*1024 or len(added) >= 32:
            raise ValueError('added test limit exceeded')
        added[name] = path.read_text(encoding='utf-8')
    return added


def execute_tests(root, command, *, seconds=60, environment=None):
    started = time.monotonic()
    try:
        done = run(command, cwd=Path(root), timeout=seconds, shell=False,
                   env={**os.environ, **(environment or {})})
        output = done.stdout + '\n' + done.stderr
        counts = {word:int(re.findall(r'\b(\d+) '+word+r'\b', output)[-1]) if re.search(r'\b\d+ '+word+r'\b', output) else 0
                  for word in ('passed','failed','skipped','error')}
        state = ('passed' if done.returncode==0 and counts['passed']>0 else
                 'empty' if done.returncode==5 else 'failed' if counts['failed'] else 'setup')
        return {'state':state, 'exit_code':done.returncode, **counts,
                'elapsed_ms':round((time.monotonic()-started)*1000,3)}
    except (subprocess.TimeoutExpired, OSError, OutputLimitExceeded) as exc:
        state = ('timeout' if isinstance(exc,subprocess.TimeoutExpired) else
                 'output_limit' if isinstance(exc,OutputLimitExceeded) else 'unavailable')
        return {'state':state, 'exit_code':None, 'passed':0, 'failed':0, 'skipped':0, 'error':0,
                'elapsed_ms':round((time.monotonic()-started)*1000,3)}


def review_brief(root, strength):
    """Surface locations as function-level review leads, never mutant targets."""
    locations = set()
    for item in strength.get('observations', []):
        if item.get('status') != 'undetected':
            continue
        name = _path(item['path'])
        path = Path(root)/name
        if path.is_symlink() or not path.resolve().is_relative_to(Path(root).resolve()):
            raise ValueError('unsafe feedback source')
        tree = ast.parse(path.read_text(encoding='utf-8'))
        functions = [n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))
                     and n.lineno <= item['line'] <= n.end_lineno]
        function = min(functions,key=lambda n:n.end_lineno-n.lineno).name if functions else 'module behavior'
        locations.add((name,function))
    lines = ['ElevenPowers test-strength review observations',
             f'Analysis state: {strength.get("state", "unavailable")}.',
             'This bounded sample can be incomplete. Undetected changes may have equivalent behavior.',
             'Use the public contracts to investigate; a location is a review lead, not a confirmed defect.']
    for name,function in sorted(locations):
        lines.append(f'- Passing tests left sampled changes undetected in {name}: {function}. Review its observable behavior and boundary/error cases.')
    if not locations:
        lines.append('No completed undetected observation supplies a function-level lead in this sample.')
    return '\n'.join(lines)
