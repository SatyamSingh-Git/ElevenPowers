"""One shared deadline and explicit mutation-attempt cap."""
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import tempfile
import time
from .. import process


@dataclass
class Budget:
    deadline: float
    maximum: int
    attempts: int = 0

    def timeout(self, maximum):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('strength deadline reached')
        return min(maximum, remaining)

    def attempt(self):
        self.timeout(300)
        if self.attempts >= self.maximum:
            raise TimeoutError('strength attempt limit reached')
        self.attempts += 1


@dataclass(frozen=True)
class Execution:
    status: str
    returncode: int | None = None
    stdout: str = ''
    stderr: str = ''
    reason: str = ''


def execute(command, root, budget, seconds, *, shell=True, original=None):
    try:
        with tempfile.TemporaryDirectory(prefix='ep-strength-guard-') as folder:
            environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
            marker = Path(folder) / 'violation'
            if original is not None:
                startup = Path(folder) / 'sitecustomize.py'
                startup.write_bytes(Path(__file__).with_name('python_guard.py').read_bytes())
                environment.update(EP_STRENGTH_GUARD_ORIGINAL=str(original),
                                   EP_STRENGTH_GUARD_MARKER=str(marker),
                                   PYTHONPATH=folder + os.pathsep + os.environ.get('PYTHONPATH', ''))
            done = process.run(command, cwd=root, timeout=budget.timeout(seconds), shell=shell,
                               env=environment)
            if marker.exists():
                return Execution('isolation_error', reason=marker.read_text(encoding='utf-8')[:512])
        return Execution('complete', done.returncode, done.stdout, done.stderr)
    except (TimeoutError, subprocess.TimeoutExpired):
        return Execution('timed_out')
    except (OSError, subprocess.SubprocessError):
        return Execution('error')
