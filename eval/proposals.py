"""Explicit bounded proposal capture. No Git writes or product export changes.

Borrow the checkpoint concept, but read a frozen allowlist rather than staging
the tree. Hash chains detect accidental history edits, not hostile forgery.
"""
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

MAX_BYTES = 512 * 1024
MAX_RECORDS = 16
MAX_HISTORY = 24 * 1024 * 1024


def _stamp(path):
    s=path.stat()
    return s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_ino


def _names(names):
    if not isinstance(names, list) or not 1 <= len(names) <= 32 or len(set(names)) != len(names):
        raise ValueError('invalid snapshot allowlist')
    for name in names:
        if (not isinstance(name, str) or '\\' in name or ':' in name or
                not name or (name.startswith('.') and name != '.gitignore') or
                any(p in ('..', '.') for p in name.split('/')) or
                PurePosixPath(name).is_absolute()):
            raise ValueError('unsafe snapshot path')
    return sorted(names)


def snapshot(root, names):
    names = _names(names)
    root = Path(root).absolute()
    result = {'state': 'incomplete', 'files': {}, 'fingerprint': None}
    if any(p.is_symlink() for p in (root, *root.parents)):
        return result
    total, data, stamps = 0, {}, {}
    try:
        for name in names:
            path = root / name
            if any(p.is_symlink() for p in (path, *path.parents)) or not path.resolve().is_relative_to(root.resolve()):
                return result
            if not path.exists():
                data[name] = None; stamps[name] = None
                continue
            before = _stamp(path)
            if not path.is_file():
                return result
            with path.open('rb') as stream:
                raw = stream.read(MAX_BYTES - total + 1)
            total += len(raw)
            if total > MAX_BYTES or _stamp(path) != before:
                return result
            stamps[name] = before
            data[name] = base64.b64encode(raw).decode('ascii')
        for name, stamp in stamps.items():
            path = root / name
            if path.is_symlink() or (stamp is None and path.exists()) or (stamp is not None and _stamp(path) != stamp):
                return result
    except OSError:
        return result
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    return {'state': 'complete', 'files': data, 'fingerprint': digest}


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def read(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('linked history')
    if not path.exists():
        return []
    with path.open('rb') as stream:
        raw = stream.read(MAX_HISTORY + 1)
    if len(raw) > MAX_HISTORY:
        raise ValueError('history exceeds limit')
    values, previous = [], '0' * 64
    try:
        for line in raw.splitlines():
            value = json.loads(line)
            digest = value.pop('hash')
            if value['previous'] != previous or digest != _hash(value) or len(values) >= MAX_RECORDS + 1:
                raise ValueError('invalid history chain')
            value['hash'] = digest
            values.append(value); previous = digest
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('invalid proposal history') from error
    return values


def append(path, value):
    path = Path(path)
    history = read(path)
    if len(history) > MAX_RECORDS:
        return
    if len(history) == MAX_RECORDS:
        value = {'state': 'overflow'}
    record = {**value, 'previous': history[-1]['hash'] if history else '0' * 64}
    record['hash'] = _hash(record)
    encoded = json.dumps(record, allow_nan=False) + '\n'
    if path.exists() and path.stat().st_size + len(encoded.encode()) > MAX_HISTORY:
        raise ValueError('history exceeds limit')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as stream:
        stream.write(encoded)


def _receipt_path(config):
    return Path(config['history']).with_suffix('.receipt.json')


def command_receipt(config, phase, payload):
    """Same exact-command input observation in both arms, without model output."""
    from core.hosts.setup import _write
    from core.payload import read_result
    from core.parsers import parse
    from core.evidence import Result, Kind
    if (payload.get('tool_input') or {}).get('command') != config.get('command'):
        return
    call=payload.get('tool_use_id')
    if not isinstance(call,str) or not call:
        return
    root=Path(config['root']); path=_receipt_path(config)
    if phase=='PreToolUse':
        _write(path, {'state':'running','call':call,'inputs':snapshot(root,config['files'])})
    elif phase in ('PostToolUse','PostToolUseFailure'):
        before=json.loads(path.read_text()) if path.exists() else {}
        after=snapshot(root,config['files'])
        result=read_result(payload,phase)
        raw=payload.get('tool_response',{})
        moving=before.get('call')!=call or before.get('inputs')!=after or after['state']!='complete'
        incomplete=moving or result.skip or not result.readable or (isinstance(raw,dict) and (raw.get('timed_out') is True or raw.get('timeout') is True))
        rows=parse(config['command'],result.output,None if incomplete else result.exit_code,root)
        suite=next((e for e in rows if e.kind is Kind.SUITE),None)
        state='incomplete' if incomplete or suite is None or suite.execution!='complete' else 'pass' if suite.result is Result.PASS and suite.ran_tests else 'fail'
        _write(path, {'state':state,'inputs':after})


def verification(config):
    if config['plugin']:
        from core.ledger import Ledger
        from core.evidence import Kind, Result, Freshness
        rows=[e for e in Ledger.load(Path(config['root'])).evidence
              if e.kind is Kind.SUITE and e.command==config.get('command')]
        if not rows:
            return 'missing'
        e=max(rows,key=lambda e:e.at)
        if e.execution!='complete':
            return 'incomplete'
        if e.freshness(Path(config['root'])) is not Freshness.FRESH:
            return 'stale'
        return 'fresh_pass' if e.result is Result.PASS and e.ran_tests else 'fail'
    path=_receipt_path(config)
    if not path.exists():
        return 'missing'
    value=json.loads(path.read_text())
    if value['state'] not in ('pass','fail'):
        return 'incomplete'
    if value['inputs']!=snapshot(Path(config['root']),config['files']):
        return 'stale'
    return 'fresh_pass' if value['state']=='pass' else 'fail'


def observed(config):
    """Every attempted Stop must have one completed observation, in both arms."""
    history=read(config['history'])
    directory=Path(config.get('attempts',config['history']+'.attempts'))
    if not directory.is_dir() or any(p.is_symlink() for p in (directory,*directory.parents)):
        raise ValueError('proposal observation attempts unavailable')
    paths=list(directory.glob('*.json'))
    if len(paths)!=len(history) or not 1<=len(paths)<=MAX_RECORDS:
        raise ValueError('proposal observation gap or limit')
    hashes=set()
    for path in paths:
        if path.is_symlink() or path.stat().st_size>1024:
            raise ValueError('unsafe observation attempt')
        status=json.loads(path.read_text())
        if set(status)!={'state','hash'} or status['state']!='complete':
            raise ValueError('proposal observation incomplete')
        hashes.add(status['hash'])
    if len(hashes)!=len(history) or hashes!={p['hash'] for p in history}:
        raise ValueError('conflicting observation history')
    return history


def hook(manifest, phase):
    """Wrap a native command, preserving its stdout, stderr and exit status.

    The host owns the hook process deadline. This evaluation wrapper does not
    capture child output or launch any model. Passive recording errors are silent;
    plugin errors retain the plugin exit status. Only Claude's exit-2 Stop decision
    is qualified here; other hosts need their own response-decision observation.
    """
    raw = sys.stdin.buffer.read(1024 * 1024 + 1)
    attempt=None
    try:
        config = json.loads(Path(manifest).read_text(encoding='utf-8'))
        if phase=='Stop':
            from core.hosts.setup import _write
            try:
                directory=Path(config.get('attempts',config['history']+'.attempts'))
                if any(p.is_symlink() for p in (directory,*directory.parents)):
                    raise ValueError('linked observation sink')
                attempt=directory/(uuid.uuid4().hex+'.json')
                _write(attempt,{'state':'incomplete','hash':None})
            except (OSError,ValueError):
                # Recording is advisory; its failure cannot suppress the child.
                attempt=None
        payload = json.loads(raw)
        root = Path(config['root']).resolve(strict=True)
        if len(raw) > 1024 * 1024 or Path(payload['cwd']).resolve() != root:
            raise ValueError('unexpected native root or payload limit')
        before = snapshot(root, config['files']) if phase == 'Stop' else None
    except (OSError, ValueError, KeyError, TypeError):
        return 0
    try:
        verification_before=verification(config) if phase=='Stop' else None
        command_receipt(config,phase,payload)
    except (OSError,ValueError,KeyError,TypeError):
        verification_before='unavailable'
    code = None
    if config['plugin']:
        # Inherit output: an observer must not truncate or reinterpret the action.
        code = subprocess.run(config['plugin'] + [phase], cwd=root, input=raw).returncode
    if phase == 'Stop':
        try:
            append(config['history'], {'phase': phase, 'at': time.time(), 'before': before,
                   'after': snapshot(root, config['files']), 'plugin_exit': code,
                   'verification_before':verification_before,'verification_after':verification(config),
                   'decision': ('allow' if code in (None, 0) else
                                'block' if code == 2 and config['host'] == 'claude' else 'unavailable')})
            if attempt:
                _write(attempt,{'state':'complete','hash':read(config['history'])[-1]['hash']})
        except (OSError, ValueError, TypeError):
            pass
    return code or 0


if __name__ == '__main__':
    sys.exit(hook(sys.argv[1], sys.argv[2]))
