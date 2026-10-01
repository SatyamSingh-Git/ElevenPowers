"""Observe patch target content across a call, independent of Git dirty state.

The apply_patch header grammar is defined by openai/codex apply-patch/parser.rs.
This is target coverage, not a claim that a tool had no other side effects.
"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path, PureWindowsPath
import time
import uuid

from ..jobs import ledger_write
from ..ledger import Ledger, _keep_out_of_git
from .lifecycle import digest
from .setup import _write

MAX_PATHS = 128
MAX_BYTES = 32 * 1024 * 1024
MAX_PENDING = 128
MAX_COMPLETED = 256


@contextmanager
def state(root):
    directory = root / '.elevenpowers'
    if not directory.resolve().is_relative_to(root.resolve()):
        raise ValueError('patch state escapes project root')
    directory.mkdir(exist_ok=True)
    _keep_out_of_git(directory)
    path = directory / 'patches.json'
    with ledger_write(root):
        value = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        if not isinstance(value, dict) or any(not isinstance(value.get(k, {}), dict) for k in ('pending', 'completed')):
            raise ValueError('invalid patch observation state')
        yield value
        _write(path, value)


def targets(payload, root):
    inputs = payload.get('tool_input', {})
    where = next((inputs[k] for k in ('workdir', 'cwd', 'working_directory') if inputs.get(k)), None)
    if where:
        directory = Path(where) if isinstance(where, str) else None
        if directory is None or (directory if directory.is_absolute() else root / directory).resolve() != root.resolve():
            return [], ['patch execution directory differs from the project root']
    patch = next((inputs[k] for k in ('command', 'patch', 'input') if isinstance(inputs.get(k), str)), '')
    if len(patch.encode('utf-8')) > 4 * 1024 * 1024:
        return [], ['patch input exceeds observation budget']
    lines = patch.strip().splitlines()
    if not lines or lines[0] != '*** Begin Patch' or lines[-1] != '*** End Patch':
        return [], ['unsupported patch input; no documented patch envelope']
    paths = []
    for line in lines[1:-1]:
        for prefix in ('*** Add File: ', '*** Update File: ', '*** Delete File: ', '*** Move to: '):
            if line.startswith(prefix):
                paths.append(line[len(prefix):])
                break
    if not paths or len(paths) > MAX_PATHS:
        return [], ['patch target count is missing or exceeds observation budget']
    selected, issues = [], []
    for text in dict.fromkeys(paths):
        path = Path(text)
        path = path if path.is_absolute() else root / path
        try:
            relative = path.resolve().relative_to(root.resolve())
            if not text or (PureWindowsPath(text).drive and not Path(text).is_absolute()) or '..' in Path(text).parts:
                raise ValueError()
            if not relative.parts or relative.parts[0] in {'.elevenpowers', '.git'}:
                raise ValueError()
            # Resolving a link inside the root is still unsuitable: the path
            # being edited and the bytes being observed would be different.
            lexical = path.absolute().relative_to(root.resolve())
            cursor = root
            for part in lexical.parts:
                cursor = cursor / part
                if cursor.is_symlink() or (cursor != root and cursor.is_dir() and (cursor / '.git').exists()):
                    raise ValueError()
            selected.append(relative.as_posix())
        except (ValueError, OSError):
            issues.append('patch target is outside the project, a link, a repository boundary, or protected state')
    return selected, list(dict.fromkeys(issues))


def snapshot(root, paths, deadline=None):
    values, issues, consumed = {}, [], 0
    deadline = deadline if deadline is not None else time.monotonic() + 2
    for relative in paths:
        path = root / relative
        try:
            # Revalidate after PreToolUse; an intermediate directory may now
            # be a link. Never follow it even if the final target is absent.
            cursor = root
            for part in Path(relative).parts:
                cursor = cursor / part
                if cursor.is_symlink():
                    raise OSError('link')
            if not path.resolve().is_relative_to(root.resolve()):
                raise OSError('outside')
            if not path.exists():
                values[relative] = 'absent'
                continue
            before = path.stat()
            if not path.is_file() or consumed + before.st_size > MAX_BYTES:
                raise OSError('budget or non-file')
            hasher = hashlib.sha256()
            with path.open('rb') as stream:
                while chunk := stream.read(65536):
                    consumed += len(chunk)
                    if consumed > MAX_BYTES or time.monotonic() > deadline:
                        raise OSError('budget')
                    hasher.update(chunk)
            after = path.stat()
            if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise OSError('changed during observation')
            values[relative] = hasher.hexdigest()
        except OSError:
            issues.append(f'patch target could not be completely observed: {relative}')
    return values, issues


def identity(payload):
    call = payload.get('tool_use_id')
    session = payload.get('session_id')
    if not isinstance(call, str) or not call or not isinstance(session, str) or not session:
        return None
    return digest([payload.get('_ep_platform'), payload.get('session_id', ''), call])


def before(payload, root):
    paths, issues = targets(payload, root)
    values, more = snapshot(root, paths)
    key = identity(payload)
    if not key:
        key = 'unidentified-' + uuid.uuid4().hex
        issues.append('native patch has no stable session/call identity')
    record = {'task': Ledger.load(root).task, 'input': digest(payload.get('tool_input', {})),
              'at': time.time(), 'values': values, 'paths': paths, 'issues': issues + more}
    with state(root) as value:
        pending = value.setdefault('pending', {})
        # Retries must not replace the original pre-edit baseline.
        pending.setdefault(key, record)
        while len(pending) > MAX_PENDING:
            evicted = pending.pop(next(iter(pending)))
            gaps = value.setdefault('gaps', {})
            count = gaps.pop(evicted['task'], 0)
            gaps[evicted['task']] = min(count + 1, 1_000_000_000)
            while len(gaps) > 64:
                gaps.pop(next(iter(gaps)))


def after(payload, root):
    key = identity(payload)
    if not key:
        return [], ['native patch has no stable call identity']
    task = Ledger.load(root).task
    inputs = digest(payload.get('tool_input', {}))
    with state(root) as value:
        completed = value.setdefault('completed', {})
        previous = completed.get(key)
        if previous and previous['task'] == task and previous['input'] == inputs:
            return previous['changed'], previous['issues']
        record = value.setdefault('pending', {}).get(key)
    if not record or record['task'] != task or record['input'] != inputs or time.time() - record['at'] > 1800:
        return [], ['native patch baseline is missing, expired, or belongs to a different task/input']
    current, issues = snapshot(root, record['paths'])
    issues = record['issues'] + issues
    changed = [p for p in record['paths'] if p in record['values'] and p in current and record['values'][p] != current[p]]
    raw = payload.get('tool_response', {})
    if payload.get('is_interrupt') is True or payload.get('hook_event_name') == 'PostToolUseFailure' or (
            isinstance(raw, dict) and any(raw.get(k) is True for k in ('interrupted', 'timed_out', 'timeout', 'cancelled'))):
        issues.append('native patch execution was interrupted or failed; edit coverage may be partial')
    with state(root) as value:
        value.setdefault('pending', {}).pop(key, None)
        completed = value.setdefault('completed', {})
        completed[key] = {'task': task, 'input': inputs, 'changed': changed, 'issues': issues}
        while len(completed) > MAX_COMPLETED:
            completed.pop(next(iter(completed)))
    return changed, issues


def unfinished(root, task):
    path = root / '.elevenpowers/patches.json'
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict) or not isinstance(value.get('pending', {}), dict):
        raise ValueError('invalid patch observation state')
    return {key: record for key, record in value.get('pending', {}).items() if record.get('task') == task}


def coverage(root, task):
    pending = len(unfinished(root, task))
    path = root / '.elevenpowers/patches.json'
    value = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    return pending, value.get('gaps', {}).get(task, 0)


def reconcile(root, ledger):
    """At completion, an unpaired pre-event is an explicit gap, even in Git."""
    records = unfinished(root, ledger.task)
    _, evicted = coverage(root, ledger.task)
    if not records and not evicted:
        return
    from ..obligations import Claim
    deadline = time.monotonic() + 3
    for record in records.values():
        current, _ = snapshot(root, record['paths'], deadline)
        for path, value in current.items():
            if path in record['values'] and value != record['values'][path]:
                ledger.observe_edit(str(root / path))
    if not ledger.claims:
        ledger.claims = [Claim.FEATURE_ADDED]
    ledger.note('unattributed native edit', f'{len(records)} patch call(s) did not deliver a matching post-event; {evicted} pending observation(s) exceeded the history budget. Edit coverage is incomplete.')
    # Persist the warning before retiring observations, so a failed save is
    # retryable rather than silently losing the only record of the gap.
    ledger.save()
    with state(root) as value:
        for key in records:
            value.setdefault('pending', {}).pop(key, None)
