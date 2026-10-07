"""Private isolated inspection worker; never invokes project checks."""
import json
from pathlib import Path
import sys

# -I ignores project PYTHONPATH and cwd when loading the trusted runtime.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.milestones import build
from core.milestones.advice import render
from core.milestones.automatic import digest
from core.milestones.report import read_ledger
import time


def main():
    root = Path(sys.argv[1]).resolve(strict=True)
    seconds = float(sys.argv[2])
    payload, _, issues = read_ledger(root, time.monotonic() + seconds)
    if issues or digest(payload.get('task')) != sys.argv[3]:
        raise ValueError('task changed or unavailable before inspection')
    report = build(root, seconds=seconds, impact=True)
    print(json.dumps({'schema': 1, 'context': render(report)}))


if __name__ == '__main__':
    main()
