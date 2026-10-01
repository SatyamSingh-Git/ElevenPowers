"""Positive test execution on unmutated isolated source comes first."""
from dataclasses import dataclass
import os
import sys
from ..evidence import Kind, Result, SourceScan
from ..parsers import parse
from .execution import execute


@dataclass(frozen=True)
class Baseline:
    status: str
    reason: str = ''
    passed: int = 0


def outcomes(command, execution, root):
    records = parse(command, execution.stdout + '\n' + execution.stderr,
                    execution.returncode, root, snapshot=(SourceScan(), ''))
    tests = [r for r in records if r.kind in (Kind.SUITE, Kind.TEST)]
    passed = max([r.passed or 0 for r in tests if r.counted] + [0])
    failed = max([r.failed or 0 for r in tests if r.counted] + [0])
    errors = any(r.result is Result.ERROR for r in tests)
    return passed, failed, errors


def guard(command, original):
    normalized = command.replace('\\', '/').casefold()
    # An interpreter may live in the original virtualenv; source targets may not.
    normalized = normalized.replace(sys.executable.replace('\\', '/').casefold(), '')
    if original.as_posix().casefold() in normalized:
        return 'test command is tied to the original workspace'
    for name in ('PYTHONPATH', 'NODE_PATH'):
        if original.as_posix().casefold() in os.environ.get(name, '').replace('\\', '/').casefold():
            return name + ' points to the original workspace'
    return ''


def baseline(command, copied, original, budget, seconds):
    issue = guard(command, original)
    if not command or issue:
        return Baseline('incomplete', issue or 'no declared test command')
    execution = execute(command, copied, budget, seconds)
    if execution.status != 'complete':
        return Baseline('incomplete', 'baseline ' + execution.status)
    passed, failed, errors = outcomes(command, execution, copied)
    if execution.returncode:
        return Baseline('failed', 'unmutated test command failed')
    if not passed or failed or errors:
        return Baseline('incomplete', 'baseline did not report positive passing test counts')
    return Baseline('passed', passed=passed)
