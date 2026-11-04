"""Private isolated inspection worker; never invokes project checks."""
import json
from pathlib import Path
import sys

# -I ignores project PYTHONPATH and cwd when loading the trusted runtime.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.milestones import build
from core.milestones.advice import render_with_checks
from core.milestones.automatic import digest
from core.milestones.report import read_ledger
from core.milestones.delivery import check_hash
import time


def main():
    root = Path(sys.argv[1]).resolve(strict=True)
    # The parent's deadline on the monotonic clock, which both processes share (QueryPerformanceCounter
    # on Windows, CLOCK_MONOTONIC elsewhere). A late start leaves less time, never more.
    deadline = float(sys.argv[2])
    payload, _, issues = read_ledger(root, deadline)
    if issues or digest(payload.get('task')) != sys.argv[3]:
        raise ValueError('task changed or unavailable before inspection')
    report = build(root, seconds=max(0.0, deadline - time.monotonic()), impact=True)
    context, visible = render_with_checks(report)
    from core.checks import guidance
    runner = guidance(root, commands=[row['command'] for row in visible])
    if runner and len(context) + len(runner) + 1 <= 6000:
        context += '\n' + runner
    checks = [check_hash(row['kind'], row['command']) for row in visible]
    print(json.dumps({'schema': 1, 'context': context, 'checks': checks}))


if __name__ == '__main__':
    main()
