"""Project-local verification ownership, deadlines and durable progress.

An OS lock is held for the completion attempt, so process death releases it.
The journal is replaced atomically and is diagnostic state, never proof itself.
"""
from __future__ import annotations

import contextvars
import json
import os
import subprocess
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from .redact import scrub_values

WORK_SECONDS = 480  # Leaves 120 seconds of the host allowance for final reporting/cleanup.
_CURRENT = contextvars.ContextVar('verification_session', default=None)


class Busy(RuntimeError):
    pass


class Superseded(RuntimeError):
    pass


def replace(temporary, target):
    """Windows readers briefly deny replacement; retry without a partial write."""
    deadline = time.monotonic() + 1
    while True:
        try:
            temporary.replace(target)
            return
        except PermissionError:
            if os.name != 'nt' or time.monotonic() >= deadline:
                raise
            time.sleep(.01)


@contextmanager
def ledger_write(root, *, timeout=5):
    """Serialize the short read/merge/replace transaction across hook writers."""
    stream = (root / '.elevenpowers/ledger.lock').open('a+b')
    with stream:
        stream.seek(0, 2)
        if not stream.tell():
            stream.write(b'0')
            stream.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                _lock(stream)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise Busy('ledger is busy; could not safely persist verification')
                time.sleep(.01)
        try:
            yield
        finally:
            _unlock(stream)


class BudgetExhausted(subprocess.SubprocessError):
    pass


class Budget:
    def __init__(self, seconds=WORK_SECONDS):
        self.deadline = time.monotonic() + max(0, seconds)

    @property
    def remaining(self):
        return max(0.0, self.deadline - time.monotonic())

    def timeout(self, maximum=300):
        remaining = self.remaining
        if remaining <= 0:
            raise BudgetExhausted('completion time budget exhausted')
        return min(maximum, remaining)


def current():
    return _CURRENT.get()


def execute(command, *, cwd, phase, timeout=300, shell=True):
    """Run an auxiliary check under the same deadline and ownership as Stop."""
    from .process import run
    session = current()
    if session is None:
        from .ledger import Ledger
        with Session(cwd, Ledger.load(cwd).task):
            return execute(command, cwd=cwd, phase=phase, timeout=timeout, shell=shell)
    item = session.queue(phase, command)
    try:
        allowance = session.budget.timeout(timeout)
    except BudgetExhausted as error:
        session.finish(item, 'deferred', str(error))
        raise
    session.begin(item)
    try:
        done = run(command, cwd=cwd, timeout=allowance, shell=shell)
    except BaseException as error:
        session.finish(item, 'incomplete', str(error) or type(error).__name__)
        raise
    session.finish(item, 'passed' if done.returncode == 0 else 'failed', exit_code=done.returncode)
    return done


def read(root: Path) -> dict:
    try:
        data = json.loads((root / '.elevenpowers/verification.json').read_text(encoding='utf-8'))
        if not isinstance(data, dict) or not isinstance(data.get('checks', []), list):
            raise ValueError('invalid verification journal')
        return data
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        return {'status': 'unreadable', 'reason': str(error), 'checks': []}


def active(root: Path):
    """Probe ownership without creating files or rewriting an abandoned journal."""
    owner = current()
    if owner is not None and owner.root.resolve() == root.resolve():
        return True
    try:
        stream = (root / '.elevenpowers/verification.lock').open('r+b')
    except FileNotFoundError:
        return False
    except OSError:
        return None
    with stream:
        try:
            _lock(stream)
        except OSError:
            return True
        _unlock(stream)
        return False


def progress(root: Path, task: str) -> list[str]:
    """A small, read-only view; a journal is progress, never verification proof."""
    data = read(root)
    if not data or (data.get('task') != task and data.get('status') != 'unreadable'):
        return []
    status = data.get('status', 'unknown')
    interrupted = status == 'running' and active(root) is False
    if interrupted:
        status = 'interrupted; unfinished checks are reconsidered at the next completion'
    checks = [c for c in data.get('checks', []) if isinstance(c, dict)]
    if status == 'running' and not any(c.get('status') in {'queued', 'running'} for c in checks):
        status = 'checks recorded; completion finishing'
    lines = [f'verification {status}']
    for check in checks[-6:]:
        state = check.get('status', 'unknown')
        if interrupted and state in {'running', 'queued'}:
            state = 'incomplete'
        history = ' (previous attempt)' if check.get('run') != data.get('id') else ''
        command = str(check.get('command', ''))[:180].replace('\n', ' ')
        reason = str(check.get('reason', ''))[:180].replace('\n', ' ')
        lines.append(f"  {check.get('phase', 'check')}: {state}{history} — {command}"
                     + (f'; {reason}' if reason else ''))
    if len(checks) > 6:
        lines.append(f'  {len(checks) - 6} earlier entries in .elevenpowers/verification.json')
    if data.get('status') == 'unreadable':
        lines.append('  progress could not be read; the next completion will rebuild it')
    from .redact import scrub
    return [scrub(line) for line in lines]


def _lock(stream):
    stream.seek(0)
    if os.name == 'nt':
        import msvcrt
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(stream):
    stream.seek(0)
    if os.name == 'nt':
        import msvcrt
        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class Session:
    def __init__(self, root: Path, task: str, seconds=WORK_SECONDS):
        self.root, self.task = root, task
        self.budget = Budget(seconds)
        self.path = root / '.elevenpowers/verification.json'
        self.data = {}
        self.stream = None

    def __enter__(self):
        from .ledger import _keep_out_of_git
        self.path.parent.mkdir(parents=True, exist_ok=True)
        _keep_out_of_git(self.path.parent)
        self.stream = (self.path.parent / 'verification.lock').open('a+b')
        self.stream.seek(0, 2)
        if self.stream.tell() == 0:
            self.stream.write(b'0')
            self.stream.flush()
        try:
            _lock(self.stream)
        except OSError as error:
            self.stream.close()
            raise Busy('verification is already running for this project') from error
        try:
            old = read(self.root)
            checks = old.get('checks', [])[-100:] if old.get('task') == self.task else []
            checks = [dict(c) for c in checks if isinstance(c, dict)]
            for check in checks:
                if check.get('status') in {'running', 'queued'}:
                    check.update(status='incomplete', reason='previous verification owner was interrupted',
                                 finished=time.time())
            self.data = {'task': self.task, 'id': uuid.uuid4().hex, 'pid': os.getpid(),
                         'status': 'running', 'started': time.time(), 'checks': checks}
            if old.get('status') == 'unreadable':
                self.data['recovery_warning'] = old.get('reason', '')
            self.save()
            self.token = _CURRENT.set(self)
            return self
        except BaseException:
            _unlock(self.stream)
            self.stream.close()
            raise

    def save(self):
        self.data['updated'] = time.time()
        temporary = self.path.with_suffix(f'.{os.getpid()}.tmp')
        try:
            with temporary.open('w', encoding='utf-8') as stream:
                json.dump(scrub_values(self.data), stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    def queue(self, phase, command):
        item = {'id': uuid.uuid4().hex, 'run': self.data['id'], 'phase': phase,
                'command': command, 'status': 'queued', 'queued': time.time()}
        self.data['checks'].append(item)
        self.save()
        return item

    def begin(self, item):
        item.update(status='running', started=time.time())
        self.save()

    def finish(self, item, status, reason='', **details):
        item.update(status=status, reason=reason, finished=time.time(), **details)
        self.save()

    def __exit__(self, kind, error, traceback):
        try:
            for item in self.data['checks']:
                if item.get('status') == 'running':
                    item.update(status='incomplete', reason='verification interrupted before completion',
                                finished=time.time())
                elif item.get('status') == 'queued':
                    item.update(status='deferred', reason='not executed in this completion attempt',
                                finished=time.time())
            statuses = {i.get('status') for i in self.data['checks'] if i.get('run') == self.data['id']}
            self.data['status'] = ('incomplete' if kind or 'incomplete' in statuses else
                                   'deferred' if 'deferred' in statuses else 'finished')
            self.data['finished'] = time.time()
            self.save()
        finally:
            _CURRENT.reset(self.token)
            _unlock(self.stream)
            self.stream.close()
        return False
