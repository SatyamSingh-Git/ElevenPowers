"""Positive test execution on unmutated isolated source comes first."""
from dataclasses import dataclass
import os
import re
import sys
import xml.etree.ElementTree as ElementTree
from ..evidence import Kind, Result, SourceScan
from ..parsers import GRADLE, parse, PYTEST_NODE, PYTEST_SHORT
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
    # Named failures are positive observations even when a runner's count summary
    # is unavailable; never turn a nonzero exit alone into a detected mutation.
    failed = max(failed, sum(r.kind is Kind.TEST and r.result is Result.FAIL for r in tests))
    errors = any(r.result is Result.ERROR for r in tests)
    errors |= any(m.group('status') == 'ERROR' for pattern in (PYTEST_NODE, PYTEST_SHORT)
                  for m in pattern.finditer(execution.stdout + '\n' + execution.stderr))
    return passed, failed, errors


def _gradle_reports(root):
    return [path for path in root.rglob('TEST-*.xml')
            if 'build/test-results/' in path.relative_to(root).as_posix()]


def _gradle_counts(root):
    passed = failed = 0
    for report in _gradle_reports(root):
        suite = ElementTree.parse(report).getroot()
        tests, skipped, failures, errors = (int(suite.get(name, 0)) for name in
                                            ('tests', 'skipped', 'failures', 'errors'))
        passed += tests - skipped - failures - errors
        failed += failures + errors
    return passed, failed


def guard(command, original):
    normalized = command.replace('\\', '/').casefold()
    # An interpreter may live in the original virtualenv; source targets may not.
    normalized = normalized.replace(sys.executable.replace('\\', '/').casefold(), '')
    if original.as_posix().casefold() in normalized:
        return 'test command is tied to the original workspace'
    for name in ('PYTHONPATH', 'NODE_PATH'):
        if original.as_posix().casefold() in os.environ.get(name, '').replace('\\', '/').casefold():
            return name + ' points to the original workspace'
    if 'PYTHONPATH' in command.upper() or re.search(r'(?<!\S)-(?:I|E|S)(?!\S)', command):
        return 'Python path/startup overrides cannot establish isolated import provenance'
    return ''


def baseline(command, copied, original, budget, seconds):
    issue = guard(command, original)
    if not command or issue:
        return Baseline('incomplete', issue or 'no declared test command')
    gradle = bool(GRADLE.search(command.lower()))
    if gradle:
        # An UP-TO-DATE run writes no report, so one already here is not this run's.
        for stale in _gradle_reports(copied):
            stale.unlink()
    execution = execute(command, copied, budget, seconds, original=original)
    if execution.status != 'complete':
        return Baseline('incomplete', execution.reason or 'baseline ' + execution.status)
    passed, failed, errors = outcomes(command, execution, copied)
    if gradle and not passed and not execution.returncode:
        # A passing Gradle run prints no count; the JUnit XML it wrote carries one.
        passed, reported = _gradle_counts(copied)
        failed = max(failed, reported)
    if execution.returncode:
        return Baseline('failed', 'unmutated test command failed')
    if not passed or failed or errors:
        return Baseline('incomplete', 'baseline did not report positive passing test counts')
    return Baseline('passed', passed=passed)
