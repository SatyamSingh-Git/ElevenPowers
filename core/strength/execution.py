"""One shared deadline and explicit mutation-attempt cap."""
from dataclasses import dataclass
import os
import subprocess
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


def execute(command, root, budget, seconds, *, shell=True):
    try:
        done = process.run(command, cwd=root, timeout=budget.timeout(seconds), shell=shell,
                           env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        return Execution('complete', done.returncode, done.stdout, done.stderr)
    except (TimeoutError, subprocess.TimeoutExpired):
        return Execution('timed_out')
    except (OSError, subprocess.SubprocessError):
        return Execution('error')
